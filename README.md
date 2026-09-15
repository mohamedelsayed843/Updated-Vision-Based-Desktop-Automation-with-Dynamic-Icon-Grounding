# Updated-Vision-Based-Desktop-Automation-with-Dynamic-Icon-Grounding
A Python-based desktop automation project that fetches post data from a website/API, identifies the Notepad application on the Windows desktop, opens it automatically, pastes the retrieved content, and saves it as a text file.

The project was designed to demonstrate real desktop automation, computer vision, API integration, intelligent fallback mechanisms, and automated file management.

## Project Overview

The automation workflow starts by retrieving a post from a web API.

After getting the post data, the system needs to open Notepad on the Windows desktop. Instead of relying on a fixed screen position, the project uses multiple approaches to locate the Notepad icon:

AI/API-based icon localization
Computer vision / template matching
Windows Run dialog (Win + R) as a final fallback

Once Notepad is opened, the automation pastes the post content, saves it using the post ID, and automatically replaces the file if it already exists.

🔄 Overall Workflow 
```
Web API  
   ↓  
Fetch Post Data  
   ↓  
Locate Notepad Icon  
   ↓  
┌───────────────────────────────┐  
│  1. AI/API-based Localization │  
└───────────────┬───────────────┘  
                │ Failed  
                ↓  
┌───────────────────────────────┐  
│  2. Template Matching / CV    │  
└───────────────┬───────────────┘  
                │ Failed  
                ↓  
┌───────────────────────────────┐  
│  3. Windows Run (Win + R)     │  
└───────────────┬───────────────┘  
                ↓  
          Open Notepad  
                ↓  
        Paste Post Content  
                ↓  
          Save as post_ID.txt  
                ↓  
       Replace if File Exists
```

## Intelligent Notepad Detection

The project does not depend on a fixed Notepad icon position.

It uses multiple detection strategies:

- AI/API-based localization
  - Captures a screenshot of the desktop.
  - Sends the screenshot to an API.
  - The API identifies the Notepad icon and returns its location.
  - The returned coordinates are used to click and open Notepad.
- Computer Vision fallback
  - If the AI-based method fails, the system captures another screenshot.
It compares the desktop screenshot with a provided Notepad icon template.
Template matching is used to locate the icon.
If a match is found above the required confidence threshold, the system clicks the detected location.
Windows Run fallback
If both detection methods fail, the system uses Win + R.
Notepad is launched directly through Windows.

This multi-level fallback system makes the automation more reliable than depending on a single detection technique.

## API Integration

The project retrieves post data from a web API.

The default API is:

https://jsonplaceholder.typicode.com/posts

The system can retrieve information such as:

- Post ID
- Post title
- Post body

The retrieved data is then passed to the desktop automation workflow.

## Desktop Automation

The project uses Python to control the Windows desktop automatically.

It can:

- Capture the desktop screen
- Locate application icons
- Move and click the mouse
- Open applications
- Paste text
- Control keyboard shortcuts
- Interact with Notepad
- Save files automatically

The main automation tools include PyAutoGUI, MSS, PyGetWindow, and Pyperclip.

## Automated File Management

After opening Notepad, the system:

- Pastes the retrieved post content.
- Opens the Save dialog.
- Uses the post ID to generate the filename.
- Checks whether a file with the same name already exists.
- Replaces the existing file when necessary.

Example:

post_1.txt  
post_2.txt  
post_3.txt  

## How It Works
#### 1. Fetch the Post

The system sends a request to the configured API and retrieves the required post.

API → Post ID + Title + Body
#### 2. Capture the Desktop

Before opening Notepad, the automation captures the current desktop screen.

This screenshot is used by the icon detection methods.

#### 3. Detect Notepad Using AI

The first approach uses an AI vision/API-based method.

The screenshot is analyzed to determine where the Notepad icon is located.

The system receives the location and converts it into screen coordinates that can be used by PyAutoGUI.
```
Desktop Screenshot
        ↓
    Vision API
        ↓
Notepad Location
        ↓
Screen Coordinates
        ↓
      Click
 ```
#### 4. Template Matching Fallback

If the AI-based detection fails, the project uses computer vision.

A reference image of the Notepad icon is stored in the project:
```
notepad.png
```
The system captures the desktop and searches for the reference icon using image matching.

If the similarity is high enough, the detected coordinates are used to open Notepad.
```
Desktop Screenshot
        +
  notepad.png
        ↓
Template Matching
        ↓
Notepad Location
        ↓
      Click
```
Annotated screenshots can also be saved for debugging and verification.

#### 5. Windows Run Fallback

If both icon detection methods fail, the system uses the Windows Run dialog:
```
Win + R
   ↓
notepad
   ↓
Enter
```
This provides a final reliable way to launch Notepad without depending on the desktop icon.

#### 6. Paste the Post

After Notepad is opened, the post content is copied/pasted automatically.

The content includes the post title and body.

#### 7. Save the File

The automation saves the content using the post ID:
```
post_<id>.txt
```
For example:
```
post_1.txt
```
If the file already exists, the old file is replaced with the new content.

### Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| PyAutoGUI | Mouse and keyboard automation |
| OpenCV | Image processing and template matching |
| MSS | Desktop screenshot capture |
| Pillow | Image processing |
| PyGetWindow | Windows window management |
| Pyperclip | Clipboard operations |
| Requests | HTTP/API requests |
| NumPy | Image and numerical processing |
| AI Vision API | Intelligent icon localization |

### Usage

Run:
```
python main.py
```
The automation will:

- Fetch a post from the API.
- Capture the desktop.
- Try to locate the Notepad icon using the AI/API-based method.
- If that fails, try template matching.
- If both methods fail, open Notepad using Win + R.
- Paste the post title and body.
- Save the file as post_<id>.txt.
- Replace the file if it already exists.

### Debugging

When template matching is used, the project can generate annotated screenshots showing the detected location.

Example:

annotated_screenshot/
└── icon_detect_1.png

These screenshots help verify:

- Whether the desktop was captured correctly
- Whether the Notepad icon was detected
- Where the system detected the icon
- Whether the detection confidence was sufficient

### Reliability & Fallback Strategy

A key part of the project is its fallback architecture.

Instead of depending on a single automation technique, the system progressively switches to another method when the previous one fails.

             Start
               │
               ▼
          Fetch Post
               │
               ▼
     AI/API Icon Detection
               │
        ┌──────┴──────┐
      Success        Failed
        │              │
        ▼              ▼
     Open          Template
    Notepad        Matching
                       │
                ┌──────┴──────┐
              Success        Failed
                │              │
                ▼              ▼
              Open          Win + R
             Notepad        Notepad
                │              │
                └──────┬───────┘
                       ▼
                 Paste Content
                       │
                       ▼
                  Save File
                       │
                       ▼
                Replace Existing

This approach makes the automation more robust against differences in desktop layout and failures in individual detection methods.

### Project Goals

This project demonstrates practical experience with:

- Desktop automation
- Python scripting
- API integration
- Computer vision
- AI-assisted automation
- Image recognition
- Windows automation
- Mouse and keyboard control
- Clipboard automation
- Automated file handling
- Error handling and fallback strategies

It also demonstrates how different automation techniques can be combined to solve a real-world desktop interaction problem.
