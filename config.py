import os

# Gemini Vision (primary icon detection)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = os.environ.get(
    "GEMINI_API_URL",
    "",
)
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")
VISION_TARGET = "Notepad desktop icon"

# Reduce payload size sent to Gemini (JPEG compress only, no resizing)
VISION_JPEG_QUALITY = int(os.environ.get("VISION_JPEG_QUALITY", "75"))
VISION_API_TIMEOUT = int(os.environ.get("VISION_API_TIMEOUT", "120"))

# Edge Detection Fallback
ICON_PATH = "notepad.png"

# Output Directories
OUTPUT_DIR = r"C:\Users\Mohamed\OneDrive\Desktop\tjm-project"
ANNOTATED_DIR = os.path.join(OUTPUT_DIR, "annotated_screenshot")

# API Configuration
POSTS_API = "https://jsonplaceholder.typicode.com/posts"


# Processing Configuration
MAX_POSTS = 2
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds

# Create required directories on import
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)
