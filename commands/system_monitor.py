# commands/system_monitor.py
import threading
import time
import os
import logging
import uuid
from typing import List, Dict, Callable
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .ai_chat import GeminiClient
from .agent import ACTION_REGISTRY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FileMonitorHandler(FileSystemEventHandler):
    def __init__(self, on_new_file: Callable[[str], None]):
        self.on_new_file = on_new_file

    def on_created(self, event):
        if not event.is_directory:
            # Add a small delay to ensure the file is fully written
            time.sleep(1)
            self.on_new_file(event.src_path)

class SystemMonitor:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.path_to_watch = str(Path.home() / "Downloads")
        self.observer = None
        self.is_running = False
        self.actions: List[Dict] = [] # MODIFIED: Store dicts
        self._lock = threading.Lock()

    def _get_analysis_prompt(self, file_path: str) -> str:
        filename = os.path.basename(file_path)
        tool_list = "\n".join([
            f"- {name}: {func.__doc__.strip().splitlines()[0]}" 
            for name, func in ACTION_REGISTRY.items() 
            if name.startswith("handle_") or name.startswith("delete_")
        ])
        
        prompt = f"""
        A new file has been downloaded: '{filename}'.
        Based on the filename and common file types, decide which tool is best to organize it.
        Your goal is to categorize and file it appropriately.

        Here are the available organizing tools:
        {tool_list}

        Rules:
        - If it's an invoice, use handle_invoice. Extract company name and date from the filename if possible.
        - If it's a screenshot, use handle_screenshot. Briefly describe the subject from the filename.
        - If it's a project asset (e.g., 'logo.png', 'requirements.docx' for project 'WebApp'), use handle_project_asset.
        - If it's clearly temporary junk (e.g., 'tmp123.dat', 'download.part'), use delete_junk_file with a brief reason.
        - Use handle_image for generic images (e.g., 'cat.jpg', 'wallpaper.png').
        - Use handle_generic_document for other documents (e.g., 'report.pdf', 'notes.txt').

        Respond ONLY with a JSON object for the single best tool to use.
        The JSON MUST have 'tool_name' and 'args' (as an object). For 'args', `file_path` is always required.
        Example for a file named 'Invoice_ACME_2023-10-26.pdf':
        ```json
        {{
            "tool_name": "handle_invoice",
            "args": {{
                "file_path": "{file_path}",
                "company": "ACME",
                "date": "2023-10-26"
            }}
        }}
        ```
        """
        return prompt

    def _process_new_file(self, file_path: str):
        logger.info(f"New file detected: {file_path}")
        try:
            prompt = self._get_analysis_prompt(file_path)
            # Use a more direct call for this focused task
            response_text = self.gemini_client.generate_text(prompt)

            # Extract JSON from the response
            import json
            import re
            match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
            if not match:
                logger.warning(f"No valid JSON tool call found in AI response for {file_path}")
                return

            tool_call = json.loads(match.group(1))
            tool_name = tool_call.get("tool_name")
            tool_args = tool_call.get("args", {})

            action_func = ACTION_REGISTRY.get(tool_name)
            if action_func:
                logger.info(f"Executing tool '{tool_name}' for file '{os.path.basename(file_path)}'")
                result = action_func(**tool_args)
                logger.info(f"Tool execution result: {result}")
                
                # MODIFIED: Create a dictionary for the action
                action_obj = {
                    "id": str(uuid.uuid4()),
                    "text": result
                }
                
                with self._lock:
                    self.actions.append(action_obj)
                    self.actions = self.actions[-20:] # Keep the list trimmed
            else:
                logger.error(f"Tool '{tool_name}' not found in registry.")

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)

    def start_watching(self):
        if not self.is_running:
            self.is_running = True
            event_handler = FileMonitorHandler(on_new_file=self._process_new_file)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.path_to_watch, recursive=False)
            self.observer.start()
            logger.info(f"System Monitor started watching '{self.path_to_watch}'.")

    def stop_watching(self):
        if self.is_running and self.observer:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("System Monitor has stopped.")

    def get_actions(self) -> List[Dict]:
        with self._lock:
            return self.actions.copy()

    # NEW: Method to dismiss a notification by its ID
    def dismiss_action(self, action_id: str):
        with self._lock:
            self.actions = [action for action in self.actions if action.get("id") != action_id]
            logger.info(f"Dismissed action with ID: {action_id}")