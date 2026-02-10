"""
coordinator/llm.py — Production Gemini Client for Ralph-Coordinator.

Spec-compliant: Role-based routing, vision analysis.
"""

import os
import google.generativeai as genai

# Production Configuration
MODELS = {
    "planner": "gemini-2.0-pro-exp-02-05",   # High IQ
    "executor": "gemini-2.5-flash-preview-09-25",  # High Speed
    "vision": "gemini-2.0-flash-exp"          # Multimodal
}


def configure():
    """Ensure the Gemini API key is set."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY not found in environment.")
    genai.configure(api_key=api_key)


def generate(prompt, role="executor"):
    """
    Generates text/code using the specific model role.

    Args:
        prompt: The user prompt string.
        role: One of 'planner', 'executor', 'vision'. Defaults to 'executor'.

    Returns:
        The generated text string, or an error string prefixed with LLM_ERROR.
    """
    configure()
    model_name = MODELS.get(role, MODELS["executor"])
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"LLM_ERROR: {str(e)}"


def generate_vision(prompt, image_path):
    """
    Analyzes an image and returns a text verdict.

    Args:
        prompt: The text prompt describing what to evaluate.
        image_path: Path to a PNG/JPG screenshot.

    Returns:
        The vision model's text response, or an error string.
    """
    configure()
    if not os.path.exists(image_path):
        return "ERROR: Image file not found."

    try:
        model = genai.GenerativeModel(MODELS["vision"])

        # Load local image data
        with open(image_path, "rb") as f:
            image_data = f.read()

        response = model.generate_content([
            {'mime_type': 'image/png', 'data': image_data},
            prompt
        ])
        return response.text
    except Exception as e:
        return f"VISION_ERROR: {str(e)}"
