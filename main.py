# main.py
import eel
import os
import tempfile
import uuid
import base64
import traceback
import keyboard  # <-- For global hotkeys
from win10toast import ToastNotifier # <-- For Windows notifications
from commands.gmail_bot import GmailBot 
from commands.gmail_tools import get_email_details

# --- NEW: Import the config manager ---
from commands.config_manager import (
    get_config_values, 
    update_config_value, 
    load_profile, 
    save_profile
)

from commands import agent
from commands.weather_bot import WeatherBot
from commands.voice_tools import transcribe_audio
from commands.system_monitor import SystemMonitor
from commands.system_health import SystemHealthMonitor 

eel.init('web')

# --- NEW: Global state for shortcut recording ---
toaster = ToastNotifier()
is_recording_globally = False

# ... (keep existing initialization blocks for weather_bot, gemini_client, etc.) ...
try:
    weather_bot = WeatherBot()
    weather_bot.start()
    print("WeatherBot started successfully in the background.")

except Exception as e:
    print(f"Error starting WeatherBot: {e}")
    weather_bot = None

try:
    gemini_client = agent.GeminiClient()
    print("Gemini Client initialized successfully.")

    system_monitor = SystemMonitor(gemini_client=gemini_client)
    print("System Monitor initialized.")

    health_monitor = SystemHealthMonitor(gemini_client=gemini_client)
    print("System Health Monitor initialized.")

    gmail_bot = GmailBot()
    gmail_bot.start()
    print("GMail Bot initialized and started.")
except Exception as e:
    print(f"Error initializing GeminiClient: {e}")
    gemini_client = None
    system_monitor = None
    health_monitor = None
    gmail_bot = None


# --- NEW: Functions to be called by the global hotkey ---
def trigger_recording_toggle():
    """
    This function is called by the keyboard library when the shortcut is pressed.
    It shows a notification and calls the JavaScript function.
    """
    global is_recording_globally
    is_recording_globally = not is_recording_globally

    if is_recording_globally:
        title = "Recording Started"
        message = "Press Ctrl+Alt+R again to stop."
        # Use a non-blocking call to show the toast
        toaster.show_toast(title, message, duration=3, threaded=True)
    else:
        title = "Recording Stopped"
        message = "Processing your voice command..."
        toaster.show_toast(title, message, duration=3, threaded=True)
    
    # Call the JavaScript function to update the UI
    eel.toggle_recording_from_shortcut()

@eel.expose
def get_email_content(email_id: str):
    if not email_id:
        return {"error": "No email ID provided."}
    return get_email_details(email_id)

@eel.expose
def get_other_emails():
    if gmail_bot:
        return gmail_bot.get_other_emails()
    return []

@eel.expose
def dismiss_email(email_id: str):
    if gmail_bot:
        gmail_bot.dismiss_email(email_id)


# --- NEW: Eel functions for Settings and Profile ---
@eel.expose
def get_settings():
    """Fetches a specific list of settings from config.py to display in the UI."""
    # Define which keys from config.py you want to be user-editable
    editable_keys = [
        'GEMINI_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_ADMIN_USER_ID',
        'WEATHER_API_KEY',
        'DEFAULT_AI_MODEL',
        'VISION_MODEL_NAME',
        'GOOGLE_CSE_API_KEY',
        'GOOGLE_CSE_ENGINE_ID',
        'AI_TEMPERATURE',
        'MAX_WEB_SCRAPE_CONTENT_LENGTH'
    ]
    return get_config_values(editable_keys)

@eel.expose
def save_settings(settings_data: dict):
    """
    Receives a dictionary of settings from the UI and saves them to config.py.
    """
    print(f"Received settings to save: {settings_data}")
    success_count = 0
    for key, value in settings_data.items():
        # The JS might send numbers as strings, so we try to convert them
        try:
            # Attempt to convert to float if it looks like a number
            if '.' in value or 'e' in value:
                value = float(value)
            # Attempt to convert to int if it looks like an integer
            elif value.isdigit():
                 value = int(value)
        except (ValueError, AttributeError):
            # Keep as string if conversion fails
            pass
            
        if update_config_value(key, value):
            success_count += 1
    
    print(f"Successfully saved {success_count}/{len(settings_data)} settings.")
    # In a real app, you might need to restart/re-initialize modules that use these settings.
    # For now, a browser refresh after saving will be needed for changes to take effect.
    return {"success": True, "message": f"Saved {success_count} settings. Please restart the app for all changes to take effect."}

@eel.expose
def get_profile_data():
    """Exposes the load_profile function to the frontend."""
    return load_profile()

@eel.expose
def save_profile_data(profile_data: dict):
    """Exposes the save_profile function to the frontend."""
    return save_profile(profile_data)
# --- END NEW ---
    
@eel.expose
def toggle_health_monitoring(is_enabled):
    if not health_monitor:
        return
    if is_enabled:
        health_monitor.start_watching()
    else:
        health_monitor.stop_watching()
        
@eel.expose
def get_latest_weather_data():
    if weather_bot:
        return weather_bot.get_latest_weather_data()
    return {"status": "error", "message": "Weather bot is not available."}

@eel.expose
def toggle_monitoring(is_enabled):
    if not system_monitor:
        return
    if is_enabled:
        system_monitor.start_watching()
    else:
        system_monitor.stop_watching()

@eel.expose
def get_monitor_notifications():
    if not system_monitor and not health_monitor:
        return []
    notifications = []
    if system_monitor:
        notifications.extend(system_monitor.get_actions())
    if health_monitor:
        notifications.extend(health_monitor.get_alerts())
    notifications.sort(key=lambda x: x.get('text', ''))
    return notifications

@eel.expose
def dismiss_notification(notification_id):
    if system_monitor:
        system_monitor.dismiss_action(notification_id)
    if health_monitor:
        health_monitor.dismiss_alert(notification_id)
        
@eel.expose
def run_agent_think(user_goal):
    if not gemini_client:
        return "Error: The AI client is not available."
    final_answer = agent.think(gemini_client, user_goal, user_id=919340565)
    return final_answer

@eel.expose
def process_audio_recording(audio_data_base64):
    global is_recording_globally
    is_recording_globally = False # Reset state after processing
    
    if not gemini_client:
        return { "transcription": "Error", "final_answer": "AI client not ready." }
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_audio_path = os.path.join(temp_dir, f"{uuid.uuid4()}.webm")
    try:
        audio_data_bytes = base64.b64decode(audio_data_base64)
        with open(temp_audio_path, 'wb') as f:
            f.write(audio_data_bytes)
        transcribed_text = transcribe_audio(temp_audio_path)
        if transcribed_text.startswith("Error:"):
             return { "transcription": "Voice Message", "final_answer": f"Could not process audio. Reason: {transcribed_text}" }
        final_answer = run_agent_think(transcribed_text)
        return { "transcription": transcribed_text, "final_answer": final_answer }
    except Exception as e:
        traceback.print_exc()
        return { "transcription": "Error", "final_answer": f"Python Backend Error: {e}" }
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

# --- NEW: Set up the global hotkey ---
try:
    keyboard.add_hotkey('ctrl+alt+r', trigger_recording_toggle)
    print("Global hotkey 'Ctrl+Alt+R' for recording registered successfully.")
    print("NOTE: This may require running the script with administrator privileges.")
except Exception as e:
    print(f"Warning: Could not register global hotkey. You might need to run as administrator. Error: {e}")


print("Starting the AI Chat application...")
eel.start('index.html', mode='edge', cmdline_args=['--start-maximized'])