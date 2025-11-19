# knowledge_extractor.py
# This script processes daily conversation logs to extract successful "Goal-Tool-Outcome"
# patterns, building a valuable knowledge base from the AI's successful interactions.

import os
import json
import logging
import datetime
import re
from typing import List, Dict, Any

# Ensure we can import from the commands directory
from commands.ai_chat import GeminiClient
from config import (
    ENABLE_LOGGING, LOG_FILE, MEMORY_DIR, INSIGHTS_FILE, DATA_DIR
)

# --- Setting up the Logger ---
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

# --- State Management Files ---
PROCESSED_LOG_FILE = os.path.join(DATA_DIR, "processed_knowledge_files.log")

# --- Helper Functions ---

def load_insights() -> List[Dict[str, Any]]:
    """Loads the existing knowledge base from ai_insights.json."""
    if not os.path.exists(INSIGHTS_FILE):
        return []
    try:
        with open(INSIGHTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.error(f"Could not read insights file at {INSIGHTS_FILE}. Starting fresh.")
        return []

def save_insights(insights: List[Dict[str, Any]]):
    """Saves the updated knowledge base to ai_insights.json."""
    try:
        with open(INSIGHTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=4)
        logger.info(f"Successfully saved {len(insights)} insights to {INSIGHTS_FILE}.")
    except IOError as e:
        logger.error(f"Error saving insights: {e}")

def load_processed_files() -> set:
    """Loads the list of already processed memory files to prevent duplicate work."""
    if not os.path.exists(PROCESSED_LOG_FILE):
        return set()
    try:
        with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f)
    except IOError:
        return set()

def mark_file_as_processed(filename: str):
    """Adds a file to the log of processed files."""
    try:
        with open(PROCESSED_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{filename}\n")
    except IOError as e:
        logger.error(f"Could not write to processed log file: {e}")

# --- Core AI Logic ---

def extract_knowledge_from_log(client: GeminiClient, conversation_log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyzes an entire conversation log and extracts successful "Goal-Tool-Outcome" triplets.
    Makes ONE API call per log file.
    """
    if not conversation_log:
        return []

    # Format the entire conversation into a single block of text for analysis
    formatted_conversation = ""
    for turn in conversation_log:
        role = turn.get('role', 'unknown').capitalize()
        text = turn.get('parts', [{}])[0].get('text', '')
        # Simple formatting to make it readable for the AI
        if text:
            formatted_conversation += f"{role}: {text}\n---\n"

    # A clear, direct prompt for the AI
    prompt = f"""
    You are a data extraction AI. Your task is to analyze an entire conversation log between a User and an AI Model and extract meaningful, completed tasks.

    A "completed task" is defined as a sequence that includes:
    1. A clear 'goal' from the User.
    2. The 'tool_sequence' of one or more tools the Model used to achieve the goal. You can infer this from the conversation flow.
    3. The final 'outcome' or answer the Model provided to the User that successfully resolved the goal.

    Analyze the complete conversation log provided below. Identify all such completed tasks.
    Return your findings as a JSON array of objects. Each object should represent one completed task.
    If no completed tasks are found in this log, return an empty array `[]`.

    Example JSON structure:
    ```json
    [
      {{
        "goal": "What is the capital of France and what is the weather there?",
        "tool_sequence": ["search_and_browse", "get_current_weather"],
        "outcome": "The capital of France is Paris, where the current weather is 18°C and partly cloudy."
      }}
    ]
    ```

    CONVERSATION LOG:
    ---
    {formatted_conversation}
    ---

    JSON Output:
    """
    try:
        logger.info("Sending entire conversation log to AI for analysis...")
        # Use a fresh, history-free generation call
        response = client.model.generate_content(prompt)
        ai_response_text = response.text

        json_match = re.search(r'```json\n(.*?)```', ai_response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
            extracted_data = json.loads(json_str)
            if isinstance(extracted_data, list):
                logger.info(f"AI successfully extracted {len(extracted_data)} knowledge items.")
                return extracted_data
        
        logger.warning("AI analysis did not return a valid JSON array.")
        return []
    except Exception as e:
        logger.error(f"An error occurred during AI extraction: {e}")
        return []

# --- Main Execution Block ---

def run_knowledge_extraction():
    """
    Main function to orchestrate the entire knowledge extraction process.
    """
    logger.info("--- Starting Knowledge Extraction Process ---")
    
    try:
        client = GeminiClient()
        client.chat.history = [] # Ensure the analysis client is clean
    except Exception as e:
        logger.critical(f"Fatal Error: Could not initialize GeminiClient. Exiting. Error: {e}")
        return

    all_insights = load_insights()
    processed_files = load_processed_files()

    try:
        all_memory_files = sorted([f for f in os.listdir(MEMORY_DIR) if f.endswith('.json')])
    except FileNotFoundError:
        logger.error(f"Memory directory '{MEMORY_DIR}' not found. Nothing to process.")
        return

    files_to_process = [f for f in all_memory_files if f not in processed_files]

    if not files_to_process:
        logger.info("No new memory files to process. Knowledge base is up to date.")
        return

    logger.info(f"Found {len(files_to_process)} new memory file(s) to analyze.")

    for filename in files_to_process:
        # Skip today's file as it might still be in use
        if filename.startswith(datetime.date.today().strftime("%Y-%m-%d")):
            continue
        
        logger.info(f"--- Analyzing: {filename} ---")
        file_path = os.path.join(MEMORY_DIR, filename)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation_log = json.load(f)
            
            new_insights = extract_knowledge_from_log(client, conversation_log)
            
            if new_insights:
                all_insights.extend(new_insights)
                save_insights(all_insights)
            
            # Mark as processed regardless of whether insights were found, to avoid re-analyzing
            mark_file_as_processed(filename)
            logger.info(f"--- Finished analyzing: {filename} ---")

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Could not read or parse {filename}. Skipping. Error: {e}")

    logger.info("--- Knowledge Extraction Process Finished ---")

if __name__ == "__main__":
    # If you have old, potentially bad insight/log files, you can delete them before the first run
    # if os.path.exists(INSIGHTS_FILE): os.remove(INSIGHTS_FILE)
    # if os.path.exists(PROCESSED_LOG_FILE): os.remove(PROCESSED_LOG_FILE)
    
    run_knowledge_extraction()