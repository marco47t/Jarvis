import json
import logging
import os
import time
import traceback
from typing import Dict, List, Tuple

import google.generativeai as genai
import httpx
from google.api_core import exceptions
from google.generativeai.types import (HarmCategory, HarmBlockThreshold,
                                        StopCandidateException)

from config import (AI_TEMPERATURE, DEFAULT_AI_MODEL, ENABLE_LOGGING,
                    GEMINI_API_KEY, LOG_FILE, MAX_RESPONSE_TOKENS,
                    get_daily_memory_file_path)

# --- Logger Setup ---
def setup_logger(web_mode=False):
    logger = logging.getLogger(__name__)
    if web_mode:
        # Disable all logging to stdout for web
        logger.handlers = []
        logger.setLevel(logging.CRITICAL + 1)
        logger.propagate = False
    else:
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8')])
    return logger

logger = setup_logger(web_mode=True)

class GeminiClient:
    def __init__(self):
        """Initializes the Gemini AI client and conversation history."""
        if not GEMINI_API_KEY or "YOUR_GOOGLE_GEMINI_API_KEY" in GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in config.py or environment variables.")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = DEFAULT_AI_MODEL
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": AI_TEMPERATURE,
                "max_output_tokens": MAX_RESPONSE_TOKENS,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }
        )
        self.history = self._load_memory()
        self.chat = self.model.start_chat(history=self.history)
        logger.info(f"GeminiClient initialized with model: {self.model_name}")
        logger.debug(f"Loaded {len(self.history)} entries into chat history.")

    def _load_memory(self) -> List[Dict[str, any]]:
        """Loads conversation history from the daily memory file."""
        memory_file = get_daily_memory_file_path()
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r', encoding='utf-8') as f:
                    loaded_history = json.load(f)
                if isinstance(loaded_history, list):
                    logger.info(f"Loaded {len(loaded_history)} entries from {memory_file}.")
                    return loaded_history
                else:
                    logger.warning(f"Memory file {memory_file} is not a list. Starting fresh.")
                    return []
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading memory from {memory_file}: {e}. Starting fresh.")
                return []
        return []

    def _save_memory(self):
        """Saves the current conversation history to the daily memory file."""
        memory_file = get_daily_memory_file_path()
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                serializable_history = [
                    {'role': msg.role, 'parts': [part.text for part in msg.parts]}
                    for msg in self.chat.history
                ]
                json.dump(serializable_history, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.chat.history)} entries to {memory_file}.")
        except (IOError, TypeError) as e:
            logger.error(f"Error saving memory to {memory_file}: {e}")

    def generate_text(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini model and returns the response.
        Manages history and implements a retry mechanism for transient errors.
        """
        max_retries = 4
        for i in range(max_retries):
            try:
                logger.info(f"Sending prompt to AI (attempt {i+1}/{max_retries}): '{prompt[:200]}...'")
                response = self.chat.send_message(prompt)

                if not response.parts:
                    finish_reason = response.candidates[0].finish_reason if response.candidates else 'N/A'
                    logger.warning(f"AI response was empty (no parts). Finish Reason: {finish_reason}")
                    return "AI returned an empty response. This may be due to a content filter or the model finishing its turn without a text output."

                ai_response_text = response.text
                logger.info(f"AI response received: '{ai_response_text[:200]}...'")
                
                self._save_memory()
                return ai_response_text

            except (exceptions.InternalServerError, exceptions.ServiceUnavailable, exceptions.ResourceExhausted) as e:
                if i < max_retries - 1:
                    wait_time = 2 ** (i + 1)
                    error_type = type(e).__name__
                    logger.warning(f"API Error ({error_type}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"API error after {max_retries} retries: {e}")
                    return f"The AI service is currently unavailable or busy after multiple retries ({type(e).__name__}). Please try again later."
            
            except (genai.types.BlockedPromptException, StopCandidateException) as e:
                logger.error(f"AI response blocked due to safety concerns: {e}")
                return "AI response blocked due to safety concerns. Please rephrase your query or adjust the safety settings."

            except httpx.ReadTimeout:
                logger.error("AI request timed out.")
                return "The AI took too long to respond. Please try again."
            
            except ValueError as e:
                if "response.text" in str(e):
                    finish_reason = response.candidates[0].finish_reason if response.candidates else 'N/A'
                    logger.warning(f"AI response had no content parts. Finish Reason: {finish_reason}. Error: {e}")
                    return "AI returned a response with no valid text content. This can happen if the model's turn ends without generating text."
                else:
                    logger.error(f"A ValueError occurred during AI text generation: {e}\n{traceback.format_exc()}")
                    return f"An unexpected Value error occurred: {e}"

            except Exception as e:
                logger.error(f"An unexpected error occurred during AI text generation: {e}\n{traceback.format_exc()}")
                return f"An unexpected error occurred: {e}"
        
        return "An unexpected error occurred after exhausting all retries."
