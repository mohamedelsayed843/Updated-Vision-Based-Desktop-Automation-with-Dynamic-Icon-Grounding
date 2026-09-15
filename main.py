import os
import time
import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
import requests
import json
import pyperclip
import webbrowser
import mss


# Import configuration constants
from config import (
    ICON_PATH,
    OUTPUT_DIR,
    ANNOTATED_DIR,
    POSTS_API,
    MAX_POSTS,
    RETRY_ATTEMPTS,
    RETRY_DELAY,
)
from vision_grounding import detect_icon_coordinates


def fallback_fetch_posts_via_default_browser():
    print("Opening API URL in default browser...")
    try:
        pyperclip.copy("")
        webbrowser.open(POSTS_API)
        time.sleep(6)

        chrome_windows = None
        for title in ["Chrome", "Google Chrome", "chromium"]:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                chrome_windows = windows[0]
                break
        
        if chrome_windows:
            # Check if window is maximized
            if not chrome_windows.isMaximized:
                print("Browser window is not maximized. Maximizing...")
                chrome_windows.maximize()
                time.sleep(1)  # Wait for maximize animation
                print("Browser maximized successfully.")
            else:
                print("Browser window is already maximized.")
            
        else:
            print("Could not find browser window. Using keyboard shortcut to maximize.")
            # Fallback: Try to maximize using keyboard shortcut (Win+Up)
            pyautogui.hotkey('win', 'up')
            time.sleep(1)

        pyautogui.click(400, 300)
        time.sleep(1)

        for _ in range(2):    
            pyautogui.hotkey('ctrl', 'a')
            time.sleep(1)
            pyautogui.hotkey('ctrl', 'c')
            time.sleep(2)

            data = pyperclip.paste()

        posts = json.loads(data)
        print(f"Fetched {len(posts)} posts via browser.")

        chrome_windows = (
            gw.getWindowsWithTitle("Chrome") or
            gw.getWindowsWithTitle("Google Chrome") or
            gw.getWindowsWithTitle("chromium")
        )
        if chrome_windows:
            chrome_windows[0].minimize()
        else:
            pyautogui.hotkey('win', 'down')

        return posts[:MAX_POSTS]

    except Exception as e:
        print(f"Browser fallback failed: {e}")
        pyautogui.hotkey('win', 'down')
        return []


def fetch_posts():
    """Fetch posts from the API - try to open/fetch link directly, fallback to browser method."""
    try:
        response = requests.get(POSTS_API)
        response.raise_for_status()
        return response.json()[:MAX_POSTS]
    except:
        print("API unavailable, opening Chrome to fetch posts.")
        print("=" * 60)
        posts = fallback_fetch_posts_via_default_browser()

        return posts

def close_unexpected_popups(main_window_title):
    
    windows = gw.getAllTitles()
    for w in windows:
        if w and main_window_title not in w:
            try:
                win = gw.getWindowsWithTitle(w)[0]
                win.activate()
                time.sleep(0.3)
                pyautogui.press('esc')
                time.sleep(0.2)
                pyautogui.hotkey('alt', 'f4')
                time.sleep(0.2)
            except Exception as e:
                print(f"Could not close window '{w}': {e}")

# NOTEPAD FUNCTIONS

def _show_desktop():
    """Minimize open windows so the desktop is visible for screenshot."""
    for keyword in ("Cursor", "Code", "PowerShell", "cmd", "Terminal", "Chrome", "Notepad"):
        for win in gw.getAllWindows():
            try:
                if win.title and keyword.lower() in win.title.lower() and win.visible:
                    win.minimize()
            except Exception:
                pass

    # Win+M minimizes all windows (non-toggle). Win+D toggles and can restore
    # windows on retry, which is why Cursor appeared in later screenshots.
    pyautogui.hotkey('win', 'm')
    time.sleep(0.8)


def _capture_desktop_screenshot(screenshot_index=0):
    """Show desktop and capture a screenshot. Returns (path, image array)."""
    _show_desktop()

    screenshot_path = os.path.join(ANNOTATED_DIR, f"icon_detect{screenshot_index}.png")
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        img = np.array(screenshot)
        desktop_color = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        cv2.imwrite(screenshot_path, desktop_color)

    return screenshot_path, desktop_color


def _click_icon_and_open(center_x, center_y):
    _show_desktop()
    time.sleep(0.3)
    pyautogui.moveTo(center_x, center_y)
    pyautogui.doubleClick()
    print(f"Notepad icon found and opened at ({center_x}, {center_y})")
    return True


def open_notepad_via_gemini(screenshot_path, desktop_color):
    """Primary method: ask Gemini where the Notepad icon is on the screenshot."""
    print("Trying Gemini vision detection...")
    result = detect_icon_coordinates(screenshot_path)
    if not result:
        print("Gemini vision detection did not find the Notepad icon.")
        return False

    center_x, center_y, bbox = result
    if bbox:
        x1, y1, x2, y2 = bbox
        cv2.rectangle(desktop_color, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.circle(desktop_color, (center_x, center_y), 8, (0, 255, 0), -1)
    cv2.imwrite(screenshot_path, desktop_color)
    print(f"Annotated desktop saved as {screenshot_path}")
    return _click_icon_and_open(center_x, center_y)


def open_notepad_via_edge_detection(screenshot_path, desktop_color, scales=None, threshold=0.5):
    """Fallback method: edge detection + template matching with notepad.png."""
    if scales is None:
        scales = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

    print("Trying edge detection fallback...")
    desktop_gray = cv2.cvtColor(desktop_color, cv2.COLOR_BGR2GRAY)

    desktop_edges = cv2.Canny(desktop_gray, 50, 150)
    contours, _ = cv2.findContours(desktop_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 20 and h > 20:
            cv2.rectangle(desktop_color, (x, y), (x + w, y + h), (0, 0, 255), 2)

    target_img = cv2.imread(ICON_PATH, cv2.IMREAD_GRAYSCALE)
    if target_img is None:
        print("Icon image not found for edge detection fallback.")
        return False
    target_edges = cv2.Canny(target_img, 50, 150)

    for scale in scales:
        resized_target = cv2.resize(target_edges, (0, 0), fx=scale, fy=scale)
        res = cv2.matchTemplate(desktop_edges, resized_target, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)

        if max_val >= threshold:
            x, y = max_loc
            h, w = resized_target.shape
            cv2.rectangle(desktop_color, (x, y), (x + w, y + h), (0, 255, 0), 3)

            center_x = x + w // 2
            center_y = y + h // 2
            cv2.imwrite(screenshot_path, desktop_color)
            print(f"Annotated desktop saved as {screenshot_path}")
            return _click_icon_and_open(center_x, center_y)

    cv2.imwrite(screenshot_path, desktop_color)
    print(f"Annotated desktop saved as {screenshot_path}")
    print("Edge detection fallback did not find the Notepad icon.")
    return False


def open_notepad(screenshot_index=0):
    """Open Notepad via Gemini vision first, then edge detection fallback."""
    screenshot_path, desktop_color = _capture_desktop_screenshot(screenshot_index)

    if open_notepad_via_gemini(screenshot_path, desktop_color):
        return True

    return open_notepad_via_edge_detection(screenshot_path, desktop_color)

def wait_for_notepad(timeout=10):

    start_time = time.time()
    while time.time() - start_time < timeout:
        windows = gw.getWindowsWithTitle("Untitled - Notepad")
        if windows:
            try:
                windows[0].activate()
                time.sleep(0.5)
            except:
                pass
            if windows[0].isActive:
                return windows[0]
        time.sleep(0.5)
    return None

def check_replacement_dialog_appeared(timeout=1.5):
    
    start_time = time.time()
    dialog_titles = [
        "Confirm Save As",
        "Save As",
        "Confirm File Replace",
        "File Already Exists"
    ]
    
    while time.time() - start_time < timeout:
        all_windows = gw.getAllWindows()
        for window in all_windows:
            if window.title:
                for dialog_title in dialog_titles:
                    if dialog_title.lower() in window.title.lower():
                        print(f"Replacement dialog detected: '{window.title}'")
                        return True
        time.sleep(0.1)  # Check every 100ms
    
    return False


def type_and_save_post(post):
    """Type the post content and save it as a file."""
    # Format the content
    content = f"Title: {post['title']}\n\n{post['body']}\n\n"
    
    # Type each line
    for line in content.splitlines():
        pyautogui.write(line, interval=0.03)
        pyautogui.press('enter')
    time.sleep(0.5)
    
    # Save file - keep old file and automatically handle replacement popup
    filename = f"post_{post['id']}.txt"
    full_path = os.path.join(OUTPUT_DIR, filename)

    # Use Notepad save dialog - let Windows show replacement popup if file exists
    # Open save dialog
    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)
    
    # Type the full path
    pyautogui.write(full_path)
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.8)  # Wait for replacement dialog to appear if file exists

    # Check if replacement dialog appeared
    dialog_appeared = check_replacement_dialog_appeared(timeout=1.5)
    
    if dialog_appeared:
        # Automatically handle Windows "File already exists" confirmation dialog
        # The dialog asks: "Do you want to replace it?" with Yes/No buttons
        # We automatically press 'y' (Yes) or Enter to confirm replacement
        print("Replacement dialog detected. Confirming replacement...")
        try:
            time.sleep(0.2)
            # Press 'y' to confirm replacement (works for Yes button)
            pyautogui.press('y')
            time.sleep(0.2)
            print("Automatically confirmed file replacement")
        except:
            # If 'y' doesn't work, try Enter key (some dialogs use Enter as default)
            try:
                time.sleep(0.2)
                pyautogui.press('left')
                time.sleep(0.2)
                pyautogui.press('enter')
                print("Confirmed replacement using Enter key")
            except Exception as e:
                print(f"Could not confirm replacement: {e}")
    else:
        print("No replacement dialog appeared. File saved directly (file doesn't exist yet).")
    
    time.sleep(0.5)
    
    # Verify file was saved
    if os.path.exists(full_path):
        print(f"Post {post['id']} saved as {filename} (replaced old file automatically)")
    else:
        print(f"Warning: Could not verify if file {filename} was saved")
    
    # Close Notepad
    pyautogui.hotkey('ctrl', 'w')
    time.sleep(0.5)

def fallback_open_notepad_via_search(main_window_title="Untitled - Notepad"):
    """Open Notepad using Run dialog (Win+R) with Notepad path as a fallback."""
    print("Fallback: Opening Notepad via Run dialog (Win+R)...")
    
    # Open Run dialog with Win+R
    pyautogui.hotkey('win', 'r')
    time.sleep(0.5)
    
    # Type Notepad path - using the full path to notepad.exe
    # Common paths: C:\Windows\System32\notepad.exe or just notepad.exe
    notepad_path = "notepad.exe"
    pyautogui.write(notepad_path)
    time.sleep(0.5)
    
    # Press Enter to execute
    pyautogui.press('enter')
    time.sleep(1.5)  # wait for Notepad to open

    # Close any unexpected popups
    close_unexpected_popups(main_window_title)

# MAIN EXECUTION 

if __name__ == "__main__":
    main_window_title = "Untitled - Notepad"

    # Step 1: Fetch posts from API
    print("Fetching posts from API...")
    posts = fetch_posts()
    if not posts:
        print("No posts available. Exiting.")
        exit(1)
    
    # Step 2: Process each post
    for idx, post in enumerate(posts):
        print(f"\nProcessing post {post['id']} ({idx + 1}/{len(posts)})...")
        
        # Attempt to open Notepad
        success = False
        for attempt in range(RETRY_ATTEMPTS):
            if open_notepad(screenshot_index=idx):
                notepad_window = wait_for_notepad()
                if notepad_window:
                    success = True
                    print("Notepad opened successfully!")
                    break
            print(f"Attempt {attempt + 1} failed to open Notepad. Retrying in {RETRY_DELAY} sec...")
            time.sleep(RETRY_DELAY)

        # If still not successful, use fallback
        if not success:
            print("Icon detection failed. Using fallback method...")
            fallback_open_notepad_via_search(main_window_title)
            notepad_window = wait_for_notepad()
            if notepad_window:
                success = True
                print("Notepad opened successfully using fallback method!")

        if not success:
            print(f"Failed to open Notepad for post {post['id']}. Skipping...")
            continue

        # Type and save the post
        type_and_save_post(post)
        time.sleep(1)
    
    print(f"\nAll {len(posts)} posts processed successfully!")
