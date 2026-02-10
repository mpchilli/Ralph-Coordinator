"""
coordinator/llm.py — Production Gemini Client for Ralph-Coordinator.

Provides text generation, vision analysis, and budget tracking.
"""

import os
import yaml
import google.generativeai as genai


_CONFIG_CACHE = None
_TOTAL_TOKENS_USED = 0
_ESTIMATED_COST_USD = 0.0

# Rough cost estimates per 1M tokens (input + output averaged)
_COST_PER_1M_TOKENS = {
    "gemini-2.0-pro-exp-02-05": 7.00,
    "gemini-2.5-flash-preview-09-25": 0.15,
    "gemini-2.0-flash-exp": 0.10,
}


def load_config():
    """Load coordinator/config.yaml and return the parsed dict."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE


def _configure_api():
    """Ensure the Gemini API key is set."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Set it before running the coordinator."
        )
    genai.configure(api_key=api_key)


def _check_budget():
    """Raise if estimated spend exceeds the configured budget."""
    config = load_config()
    budget = config.get("system", {}).get("budget_max_usd", 5.00)
    if _ESTIMATED_COST_USD >= budget:
        raise RuntimeError(
            f"Budget exceeded: ${_ESTIMATED_COST_USD:.2f} / ${budget:.2f}. "
            "Terminating to prevent overspend."
        )


def _track_usage(model_name, response):
    """Update global token and cost counters from a GenerateContentResponse."""
    global _TOTAL_TOKENS_USED, _ESTIMATED_COST_USD

    usage = getattr(response, "usage_metadata", None)
    if usage is None:
        return

    total = getattr(usage, "total_token_count", 0)
    _TOTAL_TOKENS_USED += total

    rate = _COST_PER_1M_TOKENS.get(model_name, 0.50)
    _ESTIMATED_COST_USD += (total / 1_000_000) * rate


def get_usage_summary():
    """Return a dict of current usage stats."""
    return {
        "total_tokens": _TOTAL_TOKENS_USED,
        "estimated_cost_usd": round(_ESTIMATED_COST_USD, 4),
    }


def generate(prompt, model_name=None, system_instruction=None):
    """
    Generate text using a Gemini model.

    Args:
        prompt: The user prompt string.
        model_name: Override model name. Defaults to config executor.
        system_instruction: Optional system prompt for role context.

    Returns:
        The generated text string.
    """
    _configure_api()
    _check_budget()

    config = load_config()
    if model_name is None:
        model_name = config["models"]["executor"]

    kwargs = {}
    if system_instruction:
        kwargs["system_instruction"] = system_instruction

    model = genai.GenerativeModel(model_name, **kwargs)
    response = model.generate_content(prompt)
    _track_usage(model_name, response)
    _check_budget()

    return response.text


def generate_with_planner(prompt, system_instruction=None):
    """Generate using the high-reasoning Planner model (Pro)."""
    config = load_config()
    return generate(
        prompt,
        model_name=config["models"]["planner"],
        system_instruction=system_instruction,
    )


def generate_vision(prompt, image_path):
    """
    Send an image + prompt to the Vision model for analysis.

    Args:
        prompt: The text prompt describing what to evaluate.
        image_path: Absolute path to a PNG/JPG screenshot.

    Returns:
        The vision model's text response.
    """
    _configure_api()
    _check_budget()

    config = load_config()
    model_name = config["models"].get("vision", "gemini-2.0-flash-exp")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Screenshot not found: {image_path}")

    # Upload the image file
    uploaded = genai.upload_file(image_path)

    model = genai.GenerativeModel(model_name)
    response = model.generate_content([prompt, uploaded])
    _track_usage(model_name, response)
    _check_budget()

    return response.text
