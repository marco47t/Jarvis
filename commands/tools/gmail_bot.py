# commands/gmail_bot.py
import threading
import time
import logging
from datetime import datetime
from typing import List, Dict

from .gmail_tools import search_and_fetch_emails
from config import GMAIL_CHECK_INTERVAL, GMAIL_IMPORTANT_SENDERS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GmailBot:
    """A background bot to monitor a GMail inbox for new messages."""
    def __init__(self):
        self.is_running = False
        self.thread = None
        self._lock = threading.Lock()
        
        # Data stores
        self.important_emails: List[Dict] = []
        self.other_emails: List[Dict] = []
        self.processed_ids = set() # Avoids reprocessing emails
        self.start_time = None

    def _check_emails(self):
        """Fetches and sorts new emails."""
        if self.start_time is None:
            return

        query = f"in:inbox is:unread after:{self.start_time.strftime('%Y/%m/%d')}"
        logger.info(f"GmailBot: Checking for new emails with query: '{query}'")
        
        try:
            new_emails = search_and_fetch_emails(query)
            
            with self._lock:
                for email in new_emails:
                    if email['id'] in self.processed_ids:
                        continue # Skip already processed emails

                    is_important = False
                    # Check against the important senders list (case-insensitive)
                    for keyword in GMAIL_IMPORTANT_SENDERS:
                        if keyword.lower() in email['from_full'].lower():
                            is_important = True
                            break
                    
                    if is_important:
                        self.important_emails.insert(0, email)
                    else:
                        self.other_emails.insert(0, email)
                        
                    self.processed_ids.add(email['id'])

                # Keep lists trimmed to a reasonable size
                self.important_emails = self.important_emails[:20]
                self.other_emails = self.other_emails[:50]
                
        except Exception as e:
            logger.error(f"GmailBot: Error during email check: {e}", exc_info=True)

    def run(self):
        """The main loop for the bot, running in a separate thread."""
        logger.info("GmailBot background thread is starting.")
        # Fetch data immediately on start
        self._check_emails()
        
        while self.is_running:
            time.sleep(GMAIL_CHECK_INTERVAL)
            if self.is_running:
                self._check_emails()
        
        logger.info("GmailBot background thread has stopped.")

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = datetime.now()
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()
            logger.info("GmailBot has started.")

    def stop(self):
        if self.is_running:
            self.is_running = False
            if self.thread and self.thread.is_alive():
                self.thread.join()
            logger.info("GmailBot has stopped.")

    def get_important_emails(self) -> List[Dict]:
        with self._lock:
            return self.important_emails.copy()

    def get_other_emails(self) -> List[Dict]:
        with self._lock:
            return self.other_emails.copy()

    def dismiss_email(self, email_id: str):
        with self._lock:
            self.important_emails = [e for e in self.important_emails if e.get("id") != email_id]
            self.other_emails = [e for e in self.other_emails if e.get("id") != email_id]
            logger.info(f"Dismissed email with ID: {email_id}")