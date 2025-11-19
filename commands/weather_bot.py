# commands/weather_bot.py
import threading
import time
import json
import logging
from typing import Dict, Any

from commands.weather_tools import get_current_weather
from config import WEATHER_UPDATE_INTERVAL, ENABLE_LOGGING, LOG_FILE

# --- Logger Setup ---
if ENABLE_LOGGING:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

class WeatherBot:
    """
    A background bot that periodically fetches and caches weather data.
    """
    def __init__(self):
        """Initializes the WeatherBot."""
        self.latest_data: Dict[str, Any] = {"status": "initializing"}
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.run, daemon=True)
        logger.info("WeatherBot initialized.")

    def _fetch_and_update(self):
        """Fetches weather data and updates the internal cache."""
        logger.info("WeatherBot is fetching new weather data...")
        try:
            weather_json_string = get_current_weather()
            # The tool returns a string, so we need to parse it into a Python dict
            self.latest_data = json.loads(weather_json_string)
            logger.info(f"WeatherBot updated data for {self.latest_data.get('location_name', 'N/A')}.")
        except json.JSONDecodeError as e:
            logger.error(f"WeatherBot: Failed to parse weather data JSON. Error: {e}")
            self.latest_data = {"status": "error", "message": "Failed to parse weather data."}
        except Exception as e:
            logger.error(f"WeatherBot: An unexpected error occurred during fetch. Error: {e}")
            self.latest_data = {"status": "error", "message": f"An unexpected error occurred: {e}"}

    def run(self):
        """The main loop for the bot, running in a separate thread."""
        logger.info("WeatherBot background thread is starting.")
        # Fetch data immediately on start
        self._fetch_and_update()
        
        while not self._stop_event.is_set():
            # Wait for the specified interval before the next fetch
            self._stop_event.wait(WEATHER_UPDATE_INTERVAL)
            if not self._stop_event.is_set():
                self._fetch_and_update()
        
        logger.info("WeatherBot background thread has stopped.")

    def start(self):
        """Starts the bot's background thread."""
        if not self._thread.is_alive():
            self._thread.start()

    def stop(self):
        """Stops the bot's background thread gracefully."""
        self._stop_event.set()

    def get_latest_weather_data(self) -> Dict[str, Any]:
        """
        Returns the most recently fetched weather data.
        This method is safe to call from the main thread.
        """
        logger.debug(f"UI requested weather data. Providing: {self.latest_data}")
        return self.latest_data