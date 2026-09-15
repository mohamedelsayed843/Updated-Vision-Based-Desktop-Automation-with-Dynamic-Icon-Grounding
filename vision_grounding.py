import base64
import json
import re

import cv2
import requests

from config import (
    GEMINI_API_KEY,
    GEMINI_API_URL,
    GEMINI_MODEL,
    VISION_TARGET,
    VISION_JPEG_QUALITY,
    VISION_API_TIMEOUT,
)


def _encode_image_base64(image_path, jpeg_quality=VISION_JPEG_QUALITY):
    image = cv2.imread(image_path)
    if image is None:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8"), "image/png"

    _, buffer = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
    return base64.b64encode(buffer).decode("utf-8"), "image/jpeg"


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    raise ValueError(f"Could not parse JSON from model response: {text}")


def _to_pixels(value, image_size):
    value = float(value)
    if 0 <= value <= 1000:
        return int(round(value / 1000 * image_size))
    return int(round(value))


def _bbox_to_pixels(bbox, width, height):
    x1, y1, x2, y2 = (float(v) for v in bbox[:4])
    x1 = _to_pixels(x1, width)
    y1 = _to_pixels(y1, height)
    x2 = _to_pixels(x2, width)
    y2 = _to_pixels(y2, height)
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2
    return center_x, center_y, (x1, y1, x2, y2)


def _parse_coordinates(response_text, image_width, image_height):
    data = _extract_json(response_text)

    if not data.get("found", True):
        return None

    if "bbox" in data:
        return _bbox_to_pixels(data["bbox"], image_width, image_height)

    x = data.get("x")
    y = data.get("y")
    if x is None or y is None:
        return None

    center_x = _to_pixels(x, image_width)
    center_y = _to_pixels(y, image_height)
    return center_x, center_y, None


def detect_icon_coordinates(screenshot_path, target=VISION_TARGET):
    """Send a desktop screenshot to Gemini and return (center_x, center_y, bbox)."""
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not set. Set it in your environment before running.")
        return None

    image = cv2.imread(screenshot_path)
    if image is None:
        print(f"Could not read screenshot: {screenshot_path}")
        return None

    height, width = image.shape[:2]
    base64_image, mime_type = _encode_image_base64(screenshot_path)

    prompt = f"""You are a vision grounding assistant for desktop automation.

Analyze this Windows desktop screenshot ({width}x{height} pixels).
Find the desktop shortcut icon for: {target}
Look for the Notepad app icon (document/notepad image with the label "Notepad" under it).

Return ONLY valid JSON with no markdown:
{{"found": true, "bbox": [x1, y1, x2, y2]}}

Use a bounding box around the clickable icon area.
Coordinates must be normalized to a 0-1000 scale relative to image width (x) and height (y).
If the icon is not visible, return: {{"found": false}}"""

    url = f"{GEMINI_API_URL.rstrip('/')}/models/{GEMINI_MODEL}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": GEMINI_API_KEY},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt},
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image,
                                }
                            },
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 1500,
                },
            },
            timeout=VISION_API_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["candidates"][0]["content"]["parts"][0]["text"]
        print(f"Gemini response: {content}")
        return _parse_coordinates(content, width, height)
    except Exception as error:
        print(f"Gemini vision detection failed: {error}")
        return None
