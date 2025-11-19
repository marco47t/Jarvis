# commands/ai_chat.py
import json
import logging
import os
import traceback
import uuid
from datetime import datetime
from typing import Dict, List

import google.generativeai as genai
from google.generativeai.types import (HarmCategory, HarmBlockThreshold)

from config import (AI_TEMPERATURE, DEFAULT_AI_MODEL, ENABLE_LOGGING,
                    GEMINI_API_KEY, LOG_FILE, MAX_RESPONSE_TOKENS,
                    CHATS_DIR)

# --- Logger Setup ---
if ENABLE_LOGGING:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(LOG_FILE, encoding='utf-8'),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False


class GeminiClient:
    def __init__(self):
        """Initializes the Gemini AI client and the chat session management."""
        if not GEMINI_API_KEY or "YOUR_GOOGLE_GEMINI_API_KEY" in GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in config.py or environment variables.")

        genai.configure(api_key=GEMINI_API_KEY)
        self.model_name = DEFAULT_AI_MODEL
        # This base model is used for stateless generation tasks (like agent reasoning, title generation).
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
        
        # Manages the state of the current user-facing chat
        self.current_chat_id: str = None
        self.history: List[Dict] = []
        self.start_new_chat()

        logger.info(f"GeminiClient initialized with model: {self.model_name}")

    def start_new_chat(self):
        """Starts a new, empty chat session with a unique ID."""
        self.current_chat_id = str(uuid.uuid4())
        self.history = []
        logger.info(f"Started new chat session with ID: {self.current_chat_id}")

    def load_chat_session(self, chat_id: str) -> bool:
        """Loads a previous chat session from its JSON file into the history list."""
        chat_file_path = self._get_chat_filepath(chat_id)
        if not chat_file_path:
            logger.error(f"Could not load chat {chat_id}, file not found.")
            return False
        try:
            with open(chat_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.history = data.get('history', [])
            self.current_chat_id = chat_id
            logger.info(f"Successfully loaded chat session: {chat_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load chat session {chat_id}: {e}", exc_info=True)
            self.start_new_chat() # Fallback to a clean state
            return False
            
    def generate_text(self, prompt: str) -> str:
        """
        Generates a response using the base model without affecting the chat history.
        This is used for non-chat tasks like generating titles or the agent's internal reasoning.
        """
        try:
            response = self.model.generate_content(prompt)
            if response.parts:
                return "".join(part.text for part in response.parts)
            else:
                finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
                logger.error(f"Error in stateless generate_text: No content part returned. Finish Reason: {finish_reason.name}")
                return f"Error: Model returned no content (Reason: {finish_reason.name})."
        except Exception as e:
            logger.error(f"Error in stateless generate_text: {e}")
            return f"Error: {e}"

    def add_turn_to_history(self, user_message: str, model_message: str):
        """
        Adds a clean user/model turn to the current chat history and saves it.
        This is the primary method for updating the user-facing chat log.
        """
        # --- FIX: Store history in the canonical format ---
        self.history.append({'role': 'user', 'parts': [{'text': user_message}]})
        self.history.append({'role': 'model', 'parts': [{'text': model_message}]})
        self._save_chat_session()

    def _save_chat_session(self):
        """Saves the current conversation history list to its session file."""
        if not self.current_chat_id:
            return

        chat_file_path = os.path.join(CHATS_DIR, f"{self.current_chat_id}.json")
        is_new_chat = not os.path.exists(chat_file_path)
        title = "New Chat"

        # If this is the first time saving this chat, generate a title
        if is_new_chat and self.history:
            first_user_prompt = self.history[0]['parts'][0]['text'] # Updated to access text property
            title_prompt = f"Create a very short, concise title (4-5 words max) for a chat that begins with this prompt: '{first_user_prompt}'. Respond with only the title."
            title = self.generate_text(title_prompt).strip().replace('"', '').replace('*', '')

        try:
            # If the file already exists, read it to preserve the title and timestamp
            existing_data = {}
            if not is_new_chat:
                with open(chat_file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            chat_data = {
                "id": self.current_chat_id,
                "title": existing_data.get('title', title),
                "timestamp": existing_data.get('timestamp', datetime.utcnow().isoformat()),
                "history": self.history
            }
            
            with open(chat_file_path, 'w', encoding='utf-8') as f:
                json.dump(chat_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved chat session {self.current_chat_id}")
        except Exception as e:
            logger.error(f"Error saving chat session {self.current_chat_id}: {e}")

    def _get_chat_filepath(self, chat_id: str):
        """Helper to find a chat file by its ID."""
        path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        return path if os.path.exists(path) else None