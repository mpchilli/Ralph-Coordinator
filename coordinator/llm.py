import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Configure API
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=API_KEY)

# Safety Settings (Allow coding tools)
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

def get_model(role="developer"):
    """Routes the role to the correct Gemini Model."""
    if role == "architect":
        return genai.GenerativeModel('gemini-2.0-pro-exp-02-05') # High Reasoning
    elif role == "designer":
        return genai.GenerativeModel('gemini-2.0-flash-exp') # Vision Capable
    else:
        return genai.GenerativeModel('gemini-2.5-flash-preview-09-25') # Fast Coding

def generate(prompt, role="developer"):
    """Generates text response."""
    model = get_model(role)
    try:
        response = model.generate_content(
            prompt,
            safety_settings=SAFETY_SETTINGS
        )
        return response.text
    except Exception as e:
        return f"LLM Error: {str(e)}"

def see_and_critique(image_path, prompt):
    """Vision capability for the Designer Hat."""
    model = get_model("designer")
    
    # Load image file
    sample_file = genai.upload_file(path=image_path, display_name="UI Snapshot")
    
    response = model.generate_content([prompt, sample_file])
    return response.text
