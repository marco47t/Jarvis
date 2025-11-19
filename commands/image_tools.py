# commands/image_tools.py
import logging
import os
from pathlib import Path

import google.generativeai as genai
from google.api_core import exceptions
from PIL import Image

from config import (ENABLE_LOGGING, GEMINI_API_KEY, LOG_FILE,
                    VISION_MODEL_NAME)

# --- Logger Setup ---
if ENABLE_LOGGING:
    # Use a specific logger name for this module
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

def _configure_genai():
    """Configures the Generative AI client."""
    if not GEMINI_API_KEY or "YOUR_GOOGLE_GEMINI_API_KEY" in GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in config.py or environment variables.")
    genai.configure(api_key=GEMINI_API_KEY)

def analyze_image_content(file_path: str, analysis_type: str = 'describe', custom_prompt: str = None) -> str:
    """
    Analyzes the content of an image file using a vision model.
    Can either describe the image or perform Optical Character Recognition (OCR).

    Args:
        file_path (str): The local path to the image file (e.g., 'screenshots/receipt.png').
        analysis_type (str): The type of analysis. Use 'describe' for a general description or 'ocr' to extract text. Defaults to 'describe'.
        custom_prompt (str): An optional custom prompt to guide the analysis. If provided, it overrides the default behavior of 'analysis_type'.

    Returns:
        str: The analysis result or an error message.
    """
    try:
        _configure_genai()

        image_path = Path(file_path)
        if not image_path.exists():
            logger.error(f"Image file not found at path: {file_path}")
            return f"Error: Image file not found at '{file_path}'."

        img = Image.open(image_path)

        model = genai.GenerativeModel(VISION_MODEL_NAME)

        if custom_prompt:
            prompt = custom_prompt
        elif analysis_type.lower() == 'ocr':
            prompt = "Extract all text from this image, including numbers and symbols. Provide only the raw text content."
        else:  # 'describe' is the default
            # Changed the prompt to provide a simpler overview
            prompt = "Provide a simple overview of the image."

        logger.info(f"Analyzing image '{file_path}' with analysis type '{analysis_type}'")
        response = model.generate_content([prompt, img])

        result_text = response.text.strip()
        logger.info(f"Image analysis successful for '{file_path}'.")
        return f"Image Analysis Result for '{file_path}':\n{result_text}"

    except Exception as e:
        logger.error(f"An unexpected error occurred during image analysis of '{file_path}': {e}", exc_info=True)
        return f"Error: An unexpected error occurred while analyzing the image. It might be corrupted or in an unsupported format. Details: {e}"

