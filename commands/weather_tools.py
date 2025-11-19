# commands/weather_tools.py
import requests
import json
import logging
from config import ENABLE_LOGGING, LOG_FILE, WEATHER_API_KEY

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

def get_current_weather() -> str:
    """
    Fetches the current weather for the user's location based on their IP address.

    This function first determines the user's city by calling an IP geolocation API,
    and then uses that city to fetch weather data from WeatherAPI.com.

    The function is designed to be called without arguments.

    Returns:
        str: A JSON string containing structured weather data if successful.
             This includes location name, temperature, condition, icon URL,
             and whether it is day or night.
             Returns a JSON string with an error message on failure.
    """
    if not WEATHER_API_KEY or "your_actual_api_key" in WEATHER_API_KEY:
        logger.error("Weather API key is not configured in config.py.")
        return json.dumps({"error": "Weather service is not configured by the administrator."})

    location = ""
    try:
        # Step 1: Get location from IP address
        logger.info("Fetching location based on public IP address.")
        ip_response = requests.get('http://ip-api.com/json/', timeout=5)
        ip_response.raise_for_status()
        ip_data = ip_response.json()
        
        if ip_data.get('status') == 'success' and 'city' in ip_data:
            location = ip_data['city']
            logger.info(f"Successfully determined location as: {location}")
        else:
            logger.warning("Could not determine city from IP address. Defaulting to WeatherAPI's auto IP.")
            location = "auto:ip" # Fallback to WeatherAPI's automatic IP lookup

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get location from IP address: {e}")
        # If IP lookup fails, we can still let WeatherAPI try to resolve it.
        location = "auto:ip"
        logger.info("Falling back to WeatherAPI's automatic IP lookup.")

    try:
        # Step 2: Get weather for the determined location
        weather_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}&aqi=no"
        logger.info(f"Fetching weather data for location: {location}")
        
        weather_response = requests.get(weather_url, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        # Step 3: Extract and structure the relevant data
        if "error" in weather_data:
            error_message = weather_data["error"].get("message", "Unknown error from weather service.")
            logger.error(f"Weather API error: {error_message}")
            return json.dumps({"error": error_message})

        location_info = weather_data.get('location', {})
        current_info = weather_data.get('current', {})
        condition_info = current_info.get('condition', {})

        structured_data = {
            "location_name": location_info.get('name'),
            "region": location_info.get('region'),
            "country": location_info.get('country'),
            "localtime": location_info.get('localtime'),
            "temp_c": current_info.get('temp_c'),
            "temp_f": current_info.get('temp_f'),
            "is_day": current_info.get('is_day'),  # 1 for day, 0 for night
            "condition_text": condition_info.get('text'),
            "condition_icon": "https:" + condition_info.get('icon') if condition_info.get('icon') else None
        }

        logger.info(f"Successfully fetched weather for {structured_data['location_name']}: {structured_data['condition_text']}, {structured_data['temp_c']}°C")
        return json.dumps(structured_data)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get weather data: {e}")
        return json.dumps({"error": f"Could not connect to the weather service. Details: {e}"})
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_current_weather: {e}", exc_info=True)
        return json.dumps({"error": f"An unexpected error occurred while fetching weather. Details: {e}"})