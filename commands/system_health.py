# commands/system_health.py
import threading
import time
import logging
import uuid
from typing import List, Dict

from .ai_chat import GeminiClient
from .system_info_tools import get_system_information, get_process_list

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """
    A monitor that periodically checks system health (CPU, RAM, Processes)
    using psutil and an AI for analysis, avoiding direct shell command execution.
    """
    def __init__(self, gemini_client: GeminiClient, interval: int = 300):
        self.gemini_client = gemini_client
        self.interval = interval
        self.is_running = False
        self.thread = None
        self.health_alerts: List[Dict] = [] # MODIFIED: Store dicts, not strings
        self._lock = threading.Lock()

    def _get_health_analysis_prompt(self) -> str:
        # ... (This function remains the same)
        system_info = get_system_information()
        process_info = get_process_list(limit=15)

        prompt = f"""
        Analyze the following system health data and identify any potential issues.
        Focus on:
        1. High RAM usage (above 85%).
        2. A single non-system process consuming high CPU (> 50%).
        3. Any unusual process names that might indicate malware or are unexpected.
        4. Any errors reported in the data gathering itself.

        If there are no significant issues, respond ONLY with "OK".
        If you find a potential issue, describe it concisely in one sentence.
        Example: "High memory usage detected (92%) primarily by 'chrome.exe'."

        --- SYSTEM INFORMATION ---
        {system_info}

        --- TOP 15 PROCESSES (by Memory) ---
        {process_info}

        ANALYSIS:
        """
        return prompt

    def _check_health(self):
        while self.is_running:
            logger.info("SystemHealthMonitor: Running health check...")
            try:
                prompt = self._get_health_analysis_prompt()
                analysis = self.gemini_client.generate_text(prompt)
                logger.info(f"SystemHealthMonitor: AI Analysis result: '{analysis.strip()}'")

                if analysis and not analysis.strip().upper().startswith("OK"):
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    alert_text = f"❤️ Health Alert at {timestamp}: {analysis.strip()}"
                    
                    # MODIFIED: Create a dictionary for the alert
                    alert_obj = {
                        "id": str(uuid.uuid4()),
                        "text": alert_text
                    }
                    
                    with self._lock:
                        self.health_alerts.append(alert_obj)
                        self.health_alerts = self.health_alerts[-20:]
                        
            except Exception as e:
                logger.error(f"SystemHealthMonitor: Error during health check: {e}", exc_info=True)
            
            for _ in range(self.interval):
                if not self.is_running:
                    break
                time.sleep(1)

    def start_watching(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._check_health, daemon=True)
            self.thread.start()
            logger.info("System Health Monitor has started.")

    def stop_watching(self):
        if self.is_running:
            self.is_running = False
            if self.thread and self.thread.is_alive():
                self.thread.join()
            logger.info("System Health Monitor has stopped.")

    def get_alerts(self) -> List[Dict]:
        with self._lock:
            return self.health_alerts.copy()
            
    # NEW: Method to dismiss a notification by its ID
    def dismiss_alert(self, alert_id: str):
        with self._lock:
            self.health_alerts = [alert for alert in self.health_alerts if alert.get("id") != alert_id]
            logger.info(f"Dismissed health alert with ID: {alert_id}")