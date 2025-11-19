# commands/agent_analyzer.py
import os
import threading
import time
import json
import logging
from typing import List
import uuid
from collections import Counter
from config import DATA_DIR

logger = logging.getLogger(__name__)
TRANSACTION_LOG_PATH = f"{DATA_DIR}/transaction_log.jsonl"
SUGGESTION_COOLDOWN = 3600 # seconds (1 hour) to not suggest the same thing

class AgentAnalyzer:
    """
    Analyzes the agent's transaction log in the background to find patterns
    and suggest improvements.
    """
    def __init__(self, gemini_client):
        self.gemini_client = gemini_client
        self.is_running = False
        self.thread = None
        self._lock = threading.Lock()
        
        self.pending_suggestions = []
        self.suggestion_history = {} # Keeps track of when a suggestion was last made

    def _get_shell_command_sequences(self):
        """Finds sequences of 2 consecutive shell commands from the log."""
        try:
            if not os.path.exists(TRANSACTION_LOG_PATH):
                return []
            
            with open(TRANSACTION_LOG_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            records = []
            for line in lines:
                try: records.append(json.loads(line))
                except json.JSONDecodeError: continue

            # Filter for successful shell commands
            shell_commands = [
                r['parameters']['command'] 
                for r in records 
                if r.get('tool_name') == 'execute_shell_command' and r.get('success')
            ]
            
            # Create pairs of consecutive commands
            sequences = list(zip(shell_commands, shell_commands[1:]))
            return sequences
        except Exception as e:
            logger.error(f"Error reading transaction log for analysis: {e}")
            return []

    def _analyze_patterns(self):
        """The core analysis logic."""
        logger.info("Agent Analyzer: Starting analysis run...")
        
        # 1. Analyze Shell Command Patterns
        sequences = self._get_shell_command_sequences()
        if not sequences:
            logger.info("Agent Analyzer: No command sequences to analyze.")
            return

        most_common_sequences = Counter(sequences).most_common(3)
        
        for seq, count in most_common_sequences:
            if count >= 3: # Only suggest if it has been done at least 3 times
                suggestion_id = f"new_tool_{abs(hash(seq))}"
                
                # Check cooldown
                last_suggested = self.suggestion_history.get(suggestion_id, 0)
                if time.time() - last_suggested < SUGGESTION_COOLDOWN:
                    continue

                suggestion = {
                    "id": suggestion_id,
                    "type": "improvement",
                    "text": f"Create a new tool for the repeated command sequence: `{seq[0]}` -> `{seq[1]}`?",
                    "details": {
                        "suggestion_type": "new_tool",
                        "commands": list(seq)
                    }
                }
                with self._lock:
                    # Avoid duplicate suggestions
                    if not any(s['id'] == suggestion_id for s in self.pending_suggestions):
                        self.pending_suggestions.append(suggestion)
                        self.suggestion_history[suggestion_id] = time.time()
                        logger.info(f"Generated new tool suggestion: {suggestion['text']}")

        # (Future placeholder for preference analysis)
        logger.info("Agent Analyzer: Analysis run finished.")


    def run(self):
        """The main loop for the analyzer thread."""
        logger.info("Agent Self-Improvement Analyzer thread started.")
        while self.is_running:
            try:
                self._analyze_patterns()
            except Exception as e:
                logger.error(f"Error in AgentAnalyzer loop: {e}", exc_info=True)
            
            # Sleep for a long interval (e.g., 15 minutes)
            for _ in range(900):
                if not self.is_running:
                    break
                time.sleep(1)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread and self.thread.is_alive():
            self.thread.join()

    def get_suggestions(self) -> List[dict]:
        with self._lock:
            return self.pending_suggestions.copy()

    def dismiss_suggestion(self, suggestion_id: str):
        with self._lock:
            self.pending_suggestions = [s for s in self.pending_suggestions if s.get("id") != suggestion_id]