import logging
logger = logging.getLogger(__name__)

import pytesseract
from PIL import ImageGrab
import pyautogui
import os

# You may need to point pytesseract to the exact installation path on Windows
# Default path if installed on D drive as requested:
pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract-OCR\tesseract.exe'

def find_text_on_screen(target_text):
    """
    Takes a screenshot, runs OCR, and returns the (x, y) center coordinates
    of the first instance of target_text. Returns None if not found.
    """
    try:
        # Take a screenshot
        screenshot = ImageGrab.grab()
        
        # Run OCR and get bounding box data
        data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
        
        target_text_lower = target_text.lower()
        
        # Loop through all detected words
        for i in range(len(data['text'])):
            detected_word = data['text'][i].strip().lower()
            
            if target_text_lower in detected_word and detected_word != '':
                # Get the bounding box of the word
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # Calculate the center point to click
                center_x = x + (w // 2)
                center_y = y + (h // 2)
                
                return (center_x, center_y)
                
        return None
    except Exception as e:
        logger.info(f"[Vision Error] Failed to find text on screen: {e}")
        return None

def read_screen_text():
    """
    Takes a screenshot, runs OCR, and returns all text found on the screen.
    """
    try:
        screenshot = ImageGrab.grab()
        text = pytesseract.image_to_string(screenshot)
        return text.strip()
    except Exception as e:
        logger.info(f"[Vision Error] Failed to read screen text: {e}")
        return f"Error reading screen: {e}"

def find_icon_on_screen(icon_path):
    """
    Uses PyAutoGUI to find a specific image/icon on the screen.
    Returns the (x, y) center coordinates, or None if not found.
    """
    if not os.path.exists(icon_path):
        logger.info(f"[Vision Error] Icon image not found at {icon_path}")
        return None
        
    try:
        location = pyautogui.locateCenterOnScreen(icon_path, confidence=0.8)
        return location
    except pyautogui.ImageNotFoundException:
        return None
    except Exception as e:
        logger.info(f"[Vision Error] Image matching failed: {e}")
        return None

def analyze_screen(prompt="Describe what is on the screen in detail.", image_path=None):
    """
    Takes a screenshot (or loads an image) and sends it to a local Vision Language Model 
    via Ollama to answer questions about the screen.
    """
    import base64
    from io import BytesIO
    import urllib.request
    import json
    from assistant.config import get_setting

    try:
        if image_path:
            screenshot = Image.open(image_path)
        else:
            # 1. Take screenshot and compress it
            screenshot = ImageGrab.grab()
            
        # Resize to max 1024x1024 to save memory and speed up VLM processing
        screenshot.thumbnail((1024, 1024))
        
        # 2. Convert to Base64
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG", quality=80)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        # 3. Get VLM model name from config (default to moondream)
        vlm_model = get_setting("vlm_model", "moondream")
        
        # 4. Query Ollama API
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": vlm_model,
            "prompt": prompt,
            "images": [img_str],
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", "I could not analyze the screen.")
            
    except urllib.error.URLError as e:
        return f"Error: Could not connect to local Vision Model. Make sure Ollama is running and '{vlm_model}' is installed."
    except Exception as e:
        logger.info(f"[Vision Error] Screen analysis failed: {e}")
        return f"Error analyzing screen: {e}"
