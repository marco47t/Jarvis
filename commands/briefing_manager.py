# commands/briefing_manager.py
import json
import re
import traceback
from .ai_chat import GeminiClient
from .tools.weather_bot import WeatherBot # <-- Import the CLASS, not the instance

# Import all the necessary tool modules
from .tools import gcalendar_tools, gtasks_tools, gmail_tools

def generate_and_execute_briefing(gemini_client: GeminiClient, weather_bot: WeatherBot): # <-- CHANGE #1: Accept weather_bot as an argument
    print("--- DEBUG: briefing_manager.generate_and_execute_briefing called ---")
    
    # --- CHANGE #2: A single, robust try...except block for the whole function ---
    try:
        # Step 1: Gather REAL Data
        print("--- DEBUG: Gathering real data... ---")
        weather_data = weather_bot.get_latest_weather_data()
        calendar_events = gcalendar_tools.list_upcoming_events(max_results=5)
        tasks = gtasks_tools.get_todays_tasks()
        important_emails_meta = gmail_tools.search_and_fetch_emails("in:inbox is:unread", max_results=2)
        
        email_content = []
        if important_emails_meta:
            for email in important_emails_meta:
                # Add a check for errors when fetching email details
                content = gmail_tools.get_email_details(email['id'])
                if not content.get("error"):
                    email_content.append({"from": content.get("from"), "subject": content.get("subject"), "id": email['id']})

        # Step 2: AI Analysis, Scripting, and Planning Pass
        prompt = f"""
        You are a proactive AI assistant. Generate a JSON response with three keys: "briefing_script", "briefing_points", and "action_plan".

        - "briefing_script": A conversational audio script that summarizes the day and narrates the proactive actions you will take. This should be plain text.
        - "briefing_points": A structured list of items from the script. Each item must have `type`, `text`, and an optional `data` object for interactivity.
        - "action_plan": A list of the corresponding machine-readable tool calls in JSON format. Each tool call MUST have a "tool_name" and an "args" object.

        **CRITICAL INSTRUCTIONS:**
        - To read the content of an email, you MUST use the `get_email_details` tool with the email's ID.
        - To archive an email, you MUST use the `archive_email` tool with the email's ID.
        - Do NOT invent other email-related tools like 'read_email' or 'mark_as_read'.
        - When you plan an action like `create_document`, you MUST provide all required arguments for it.

        **Example of a valid action_plan:**
        `"action_plan": [ {{ "tool_name": "create_document", "args": {{ "filename": "Weekly Report Draft.docx", "content": "Initial draft for the weekly marketing report." }} }}, {{ "tool_name": "archive_email", "args": {{ "email_id": "190abcde230fghij" }} }} ]`

        Here is the user's data for today:
        Weather: {json.dumps(weather_data)}
        Calendar: {json.dumps(calendar_events)}
        Tasks: {json.dumps(tasks)}
        Emails: {json.dumps(email_content)}

        Generate the final JSON object now.
        """
        
        print("--- DEBUG: Calling Gemini for briefing plan... ---")
        response_text = gemini_client.generate_text(prompt)
        print("--- DEBUG: Got response from Gemini. Raw text:", response_text[:200] + "...") # Print first 200 chars

        # Robust JSON parsing
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not match:
            raise ValueError("No valid JSON object found in the AI response.")
        
        response_json = json.loads(match.group(0))
        
        briefing_script = response_json.get("briefing_script", "I'm sorry, I couldn't generate a briefing script.")
        briefing_points = response_json.get("briefing_points", [])
        action_plan = response_json.get("action_plan", []) # Get the plan from the top-level key

    except Exception as e:
        print(f"--- CRITICAL ERROR in briefing_manager: {e} ---")
        traceback.print_exc()
        briefing_script = "I'm sorry, an error occurred while I was preparing your briefing. Please check the system logs."
        briefing_points = []
        action_plan = []
    
    return briefing_script, briefing_points, action_plan