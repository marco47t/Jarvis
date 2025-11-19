# main.py
import multiprocessing
import shlex
import eel
import os
import json
import threading
import tempfile
import webbrowser
import uuid
import base64
import traceback
import keyboard
from win10toast import ToastNotifier


# --- CONFIG IMPORT ADDED ---
from config import CHATS_DIR

from commands.tools.memory_tools import save_feedback
from commands.tools.gmail_bot import GmailBot 
from commands.tools.gmail_tools import get_email_details
from commands.tools.visual_query import trigger_visual_query
from commands.tools.image_tools import analyze_image_content
from commands.config_manager import (
    get_config_values, 
    update_config_value, 
    load_profile, 
    save_profile
)

from commands import agent
from commands.tools.weather_bot import WeatherBot
from commands.tools.voice_tools import transcribe_audio
from commands.tools.system_monitor import SystemMonitor
from commands.tools.system_health import SystemHealthMonitor 
from commands.ai_chat import GeminiClient
from commands.agent_analyzer import AgentAnalyzer
from commands.briefing_manager import generate_and_execute_briefing
from commands.tool_executor import execute_tool
from commands.tools import gtasks_tools, tool_definitions
eel.init('web')
confirmation_handler = None
toaster = ToastNotifier()
is_recording_globally = False

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'

# --- Initializations ---
try:
    weather_bot = WeatherBot()
    weather_bot.start()
    print("WeatherBot started successfully.")
except Exception as e:
    print(f"Error starting WeatherBot: {e}")
    weather_bot = None

try:
    gemini_client = GeminiClient()
    print("Gemini Client initialized successfully.")
    
    agent_analyzer = AgentAnalyzer(gemini_client=gemini_client)
    agent_analyzer.start()
    print("Agent Analyzer started in the background.")
    
    system_monitor = SystemMonitor(gemini_client=gemini_client)
    print("System Monitor initialized.")
    
    health_monitor = SystemHealthMonitor(gemini_client=gemini_client)
    print("System Health Monitor initialized.")
    
    gmail_bot = GmailBot()
    gmail_bot.start()
    print("GMail Bot initialized and started.")
except Exception as e:
    print(f"Error initializing services: {e}")
    gemini_client, system_monitor, health_monitor, gmail_bot, agent_analyzer = None, None, None, None, None


# --- Exposed Functions ---
@eel.expose
def set_user_confirmation(confirmed: bool):
    global confirmation_handler
    if confirmation_handler:
        confirmation_handler.set_response(confirmed)

def trigger_recording_toggle():
    global is_recording_globally
    is_recording_globally = not is_recording_globally
    title = "Recording Started" if is_recording_globally else "Recording Stopped"
    message = "Press Ctrl+Alt+R again to stop." if is_recording_globally else "Processing..."
    toaster.show_toast(title, message, duration=3, threaded=True)
    eel.toggle_recording_from_shortcut()

@eel.expose
def submit_briefing_feedback(rating, comment):
    return save_feedback(feature="morning_briefing", rating=rating, comment=comment)

@eel.expose
def get_email_content(email_id: str): return get_email_details(email_id)

@eel.expose
def open_in_browser(url): webbrowser.open(url, new=2)

@eel.expose
def get_important_emails(): return gmail_bot.get_important_emails() if gmail_bot else []

@eel.expose
def get_other_emails(): return gmail_bot.get_other_emails() if gmail_bot else []

@eel.expose
def dismiss_email(email_id: str):
    if gmail_bot: gmail_bot.dismiss_email(email_id)

@eel.expose
def get_settings():
    keys = ['GEMINI_API_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_ADMIN_USER_ID', 'WEATHER_API_KEY', 'DEFAULT_AI_MODEL', 'VISION_MODEL_NAME', 'GOOGLE_CSE_API_KEY', 'GOOGLE_CSE_ENGINE_ID', 'AI_TEMPERATURE', 'MAX_WEB_SCRAPE_CONTENT_LENGTH']
    return get_config_values(keys)

@eel.expose
def open_file_path(path):
    """Opens a file in the default application or its containing folder."""
    try:
        # os.startfile is Windows-specific but very convenient
        if os.name == 'nt':
            os.startfile(path)
        else:
            # For Mac/Linux, open the parent directory
            webbrowser.open(os.path.dirname(path))
    except Exception as e:
        print(f"Could not open path {path}: {e}")

@eel.expose
def save_settings(settings_data: dict):
    for key, value in settings_data.items():
        try:
            if isinstance(value, str):
                if '.' in value and value.replace('.', '', 1).isdigit(): value = float(value)
                elif value.isdigit(): value = int(value)
        except (ValueError, AttributeError): pass
        update_config_value(key, value)
    return {"success": True, "message": "Settings saved. Please restart the app."}

@eel.expose
def get_profile_data(): return load_profile()

@eel.expose
def save_profile_data(profile_data: dict): return save_profile(profile_data)

@eel.expose
def toggle_health_monitoring(is_enabled):
    if health_monitor:
        if is_enabled: health_monitor.start_watching()
        else: health_monitor.stop_watching()

@eel.expose
def get_latest_weather_data(): return weather_bot.get_latest_weather_data() if weather_bot else {"status": "error"}

@eel.expose
def toggle_monitoring(is_enabled):
    if system_monitor:
        if is_enabled: system_monitor.start_watching()
        else: system_monitor.stop_watching()

@eel.expose
def get_monitor_notifications():
    notifications = []
    if system_monitor: notifications.extend(system_monitor.get_actions())
    if health_monitor: notifications.extend(health_monitor.get_alerts())
    if agent_analyzer: notifications.extend(agent_analyzer.get_suggestions())
    return sorted(notifications, key=lambda x: x.get('text', ''))

@eel.expose
def dismiss_notification(notification_id):
    if system_monitor: system_monitor.dismiss_action(notification_id)
    if health_monitor: health_monitor.dismiss_alert(notification_id)
    if agent_analyzer: agent_analyzer.dismiss_suggestion(notification_id)

@eel.expose
def approve_improvement_suggestion(suggestion_id: str):
    if not agent_analyzer or not gemini_client: return {"status": "error"}
    
    suggestion_to_approve = next((s for s in agent_analyzer.pending_suggestions if s['id'] == suggestion_id), None)
    if not suggestion_to_approve: return {"status": "error", "message": "Suggestion not found."}
    
    details = suggestion_to_approve['details']
    user_goal = ""
    if details['suggestion_type'] == 'new_tool':
        commands_str = "', '".join(details['commands'])
        user_goal = f"An analysis of my actions suggests creating a new tool. Use `create_new_tool` to make a tool that runs these shell commands in sequence: '{commands_str}'. Name it logically and descriptively based on what the commands do."
    
    if user_goal:
        agent_analyzer.dismiss_suggestion(suggestion_id)
        threading.Thread(target=lambda: agent.think(gemini_client, user_goal)).start()
        return {"status": "success", "message": "Agent is working on the improvement."}
        
    return {"status": "error", "message": "Unknown suggestion type."}

@eel.expose
def run_agent_think(user_goal):
    if user_goal.strip().startswith("/test"):
        parts = shlex.split(user_goal.strip())
        command = parts[0]
        tool_name = parts[1] if len(parts) > 1 else None
        
        print(f"--- DEBUG: Running test command for tool: {tool_name} ---")

        if tool_name == "get_todays_tasks":
            result = gtasks_tools.get_todays_tasks()
            return f"--- TEST RESULT ---\n{json.dumps(result, indent=2)}"
        
        elif tool_name == "create_task":
            # Simple argument parsing for testing
            title = None
            for i, part in enumerate(parts):
                if part == "--title" and i + 1 < len(parts):
                    title = parts[i+1]
            
            if not title:
                return "--- TEST FAILED ---\nUsage: /test create_task --title \"Your task title\""
            
            result = gtasks_tools.create_task(title=title)
            return f"--- TEST RESULT ---\n{json.dumps(result, indent=2)}"

        else:
            return f"--- TEST FAILED ---\nUnknown test tool: '{tool_name}'"
    if not gemini_client: return "Error: AI client not available."
    
    final_answer = agent.think(gemini_client, user_goal, user_id=919340565)
    
    def save_history_in_background(goal, answer):
        print("Saving chat history in the background...")
        gemini_client.add_turn_to_history(goal, answer)
        print("Background history save complete.")
    threading.Thread(target=save_history_in_background, args=(user_goal, final_answer)).start()
    
    return final_answer

@eel.expose
def start_new_chat_session():
    if gemini_client:
        gemini_client.start_new_chat()
        return {"status": "success"}

@eel.expose
def load_chat_session(chat_id: str):
    if gemini_client and gemini_client.load_chat_session(chat_id):
        return {"status": "success", "content": gemini_client.history}
    return {"status": "error", "message": f"Could not load chat {chat_id}."}

@eel.expose
def get_chat_history_list():
    # --- FIX: Use the imported CHATS_DIR ---
    history = []
    if not os.path.exists(CHATS_DIR): return []
    
    files = [os.path.join(CHATS_DIR, f) for f in os.listdir(CHATS_DIR) if f.endswith(".json")]
    files.sort(key=os.path.getmtime, reverse=True)
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                history.append({"id": data.get("id"), "title": data.get("title", "Untitled"), "timestamp": data.get("timestamp")})
        except (IOError, json.JSONDecodeError): continue
    return history

@eel.expose
def delete_chat_session(chat_id: str):
    if not chat_id or '..' in chat_id or os.path.sep in chat_id:
        return {"status": "error", "message": "Invalid chat ID."}
    try:
        # --- FIX: Use the imported CHATS_DIR ---
        chat_file_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(chat_file_path):
            os.remove(chat_file_path)
            return {"status": "success"}
        else:
            return {"status": "error", "message": "Chat not found."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@eel.expose
def process_visual_query_request(image_base64, prompt):
    if not gemini_client:
        eel.displayVisualQueryResult(image_base64, prompt, "Error: AI client not initialized.")
        return
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_image_path = os.path.join(temp_dir, f"visual_query_{uuid.uuid4()}.png")
    
    try:
        image_data_bytes = base64.b64decode(image_base64)
        with open(temp_image_path, 'wb') as f: f.write(image_data_bytes)
        enhanced_prompt = f"Directly answer the user's question based on the image. User's Question: \"{prompt}\""
        ai_answer = analyze_image_content(file_path=temp_image_path, custom_prompt=enhanced_prompt)
        if ai_answer.startswith("Image Analysis Result for"):
            ai_answer = ai_answer.split("\n", 1)[-1].strip()
        eel.activateAndShowChat()
        eel.sleep(0.1)
        eel.displayVisualQueryResult(image_base64, prompt, ai_answer)
    except Exception as e:
        eel.displayVisualQueryResult(image_base64, prompt, f"An error occurred: {e}")
    finally:
        if os.path.exists(temp_image_path): os.remove(temp_image_path)

@eel.expose
def process_audio_recording(audio_data_base64):
    global is_recording_globally
    is_recording_globally = False
    
    if not gemini_client:
        return { "transcription": "Error", "final_answer": "AI client not ready." }
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_audio_path = os.path.join(temp_dir, f"{uuid.uuid4()}.webm")
    try:
        audio_data_bytes = base64.b64decode(audio_data_base64)
        with open(temp_audio_path, 'wb') as f: f.write(audio_data_bytes)
        transcribed_text = transcribe_audio(temp_audio_path)
        if transcribed_text.startswith("Error:"):
            return { "transcription": "Voice Message", "final_answer": f"Audio Error: {transcribed_text}" }
        final_answer = run_agent_think(transcribed_text)
        return { "transcription": transcribed_text, "final_answer": final_answer }
    except Exception as e:
        traceback.print_exc()
        return { "transcription": "Error", "final_answer": f"Python Backend Error: {e}" }
    finally:
        if os.path.exists(temp_audio_path): os.remove(temp_audio_path)

@eel.expose
def start_morning_briefing():
    try:
        print("--- DEBUG: start_morning_briefing called from JS ---")
        
        # --- THIS IS THE FIX ---
        # We now correctly pass the weather_bot instance to the function.
        script, briefing_points, action_plan = generate_and_execute_briefing(gemini_client, weather_bot)
        
        print(f"--- DEBUG: Script generated. Length: {len(script)} chars ---")
        print(f"--- DEBUG: Action plan: {action_plan} ---")

        # Call the simplified TTS function which now returns a dictionary or an error string
        tts_result = tool_definitions.TOOL_DEFINITIONS['text_to_speech']['function'](text_to_synthesize=script)
        
        # Check if TTS returned an error object
        if isinstance(tts_result, dict) and 'error' in tts_result:
             print(f"--- CRITICAL ERROR from TTS: {tts_result['error']} ---")
             return {"error": tts_result['error']}
        
        # Assuming success if it's not an error object
        audio_file_path = tts_result.get("audio_path") if isinstance(tts_result, dict) else tts_result
        print(f"--- DEBUG: Audio file generated at: {audio_file_path} ---")
        
        def run_actions():
            if not action_plan:
                update_system_message("INFO: No proactive actions were identified for today.")
                return

            update_system_message("🚀 Morning kickstart routine is running in the background...")
            for action in action_plan:
                tool_name = action.get("tool_name")
                tool_args = action.get("args")
                tool_def = tool_definitions.TOOL_DEFINITIONS.get(tool_name)
                
                # --- THIS IS THE SAFETY CHECK ---
                if tool_args is None:
                    print(f"--- WARNING: AI generated a tool call for '{tool_name}' with null arguments. Skipping. ---")
                    update_system_message(f"⚠️ AI planned to use '{tool_name}' but forgot the arguments. Skipping this step.")
                    continue # Move to the next action
                # --- END OF SAFETY CHECK ---

                if tool_def:
                    result = execute_tool(tool_def['function'], tool_def['args_model'], tool_args)
                    status_icon = "✅" if result['status'] == 'ok' else "❌"
                    message = result.get('data', result.get('message', 'Action completed.'))
                    update_system_message(f"{status_icon} {message}")
                else:
                    update_system_message(f"❌ Action failed: Tool '{tool_name}' not found.")
            update_system_message("🏁 Morning kickstart complete. Your workspace is ready.")            
        threading.Thread(target=run_actions, daemon=True).start()
        
        return {
            "audio_path": audio_file_path,
            "briefing_points": briefing_points
        }
    except Exception as e:
        print(f"--- CRITICAL ERROR in start_morning_briefing: {e} ---")
        traceback.print_exc()
        return None
@eel.expose
def update_system_message(message):
    """
    This Python function is exposed to Eel. Its only job is to call the
    JavaScript function 'addSystemMessage' that we also exposed.
    This allows background Python threads to send messages to the UI.
    """
    eel.addSystemMessage(message)
if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        keyboard.add_hotkey('ctrl+alt+r', trigger_recording_toggle)
        keyboard.add_hotkey('ctrl+alt+s', trigger_visual_query)
        print("Global hotkeys ('Ctrl+Alt+R', 'Ctrl+Alt+S') registered successfully.")
    except Exception as e:
        print(f"Warning: Could not register global hotkey. Error: {e}")
    
    print("Starting the AI Chat application...")
    eel.start('index.html', mode='edge', cmdline_args=['--start-maximized'])