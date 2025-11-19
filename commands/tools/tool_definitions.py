# commands/tools/tool_definitions.py

# ==========================================================
# 1. IMPORT ALL MODULES THAT CONTAIN TOOL FUNCTIONS
# ==========================================================
from commands.tools import gcalendar_tools, gtasks_tools
from . import (
    backup_tools,
    clipboard_tools,
    document_tools,
    file_organizer,
    gmail_tools,
    image_tools,
    system_info_tools,
    system_tools,
    task_runner,
    voice_tools,
    web_tools,
    weather_tools,
    python_script_tool,
    memory_tools # Ensure memory_tools is imported
)

# ==========================================================
# 2. IMPORT ALL PYDANTIC MODELS
# ==========================================================
from .tool_models import *

# ==========================================================
# 3. DEFINE THE CENTRAL TOOL REGISTRY (SINGLE SOURCE OF TRUTH)
# ==========================================================
TOOL_DEFINITIONS = {
    # --- Backup Tools ---
    "create_project_backup": {
        "function": backup_tools.create_project_backup,
        "args_model": CreateProjectBackupArgs,
        "category": "File Ops"
    },

    # --- Clipboard Tools ---
    "get_clipboard_content": {
        "function": clipboard_tools.get_clipboard_content,
        "args_model": NoArgs,
        "category": "Clipboard"
    },
    "set_clipboard_content": {
        "function": clipboard_tools.set_clipboard_content,
        "args_model": SetClipboardContentArgs,
        "category": "Clipboard"
    },

    # --- Document Tools ---
    "read_pdf_content": {
        "function": document_tools.read_pdf_content,
        "args_model": ReadPdfOrDocxContentArgs,
        "category": "Multimedia Analysis"
    },
    "read_docx_content": {
        "function": document_tools.read_docx_content,
        "args_model": ReadPdfOrDocxContentArgs,
        "category": "Multimedia Analysis"
    },

    # --- File Organizer Tools ---
    "create_document": {
        "function": file_organizer.create_document,
        "args_model": CreateDocumentArgs,
        "category": "File Ops"
    },
    "move_file": {
        "function": file_organizer.move_file,
        "args_model": MoveFileArgs,
        "category": "File Ops"
    },
    "rename_file": {
        "function": file_organizer.rename_file,
        "args_model": RenameFileArgs,
        "category": "File Ops"
    },
    "handle_invoice": {
        "function": file_organizer.handle_invoice,
        "args_model": HandleInvoiceArgs,
        "category": "File Ops"
    },
    "handle_screenshot": {
        "function": file_organizer.handle_screenshot,
        "args_model": HandleScreenshotArgs,
        "category": "File Ops"
    },
    "handle_project_asset": {
        "function": file_organizer.handle_project_asset,
        "args_model": HandleProjectAssetArgs,
        "category": "File Ops"
    },
    "handle_generic_document": {
        "function": file_organizer.handle_generic_document,
        "args_model": HandleGenericDocumentOrImageArgs,
        "category": "File Ops"
    },
    "handle_image": {
        "function": file_organizer.handle_image,
        "args_model": HandleGenericDocumentOrImageArgs,
        "category": "File Ops"
    },
    "delete_junk_file": {
        "function": file_organizer.delete_junk_file,
        "args_model": DeleteJunkFileArgs,
        "category": "File Ops"
    },

    # --- GMail Tools ---
    "send_gmail_message": {
        "function": gmail_tools.send_gmail_message,
        "args_model": SendGmailMessageArgs,
        "category": "Communication"
    },
    "search_and_fetch_emails": {
        "function": gmail_tools.search_and_fetch_emails,
        "args_model": SearchEmailsArgs,
        "category": "Communication"
    },
    "archive_email": {  
        "function": gmail_tools.archive_email,
        "args_model": ArchiveEmailArgs,
        "category": "Communication"
    },

    # --- GTasks Tools ---
    "get_todays_tasks": {
        "function": gtasks_tools.get_todays_tasks,
        "args_model": GetTodaysTasksArgs,
        "category": "Task-Specific"
    },
    "create_task": {
        "function": gtasks_tools.create_task,
        "args_model": CreateTaskArgs,
        "category": "Task-Specific"
    },

    # --- GCalendar Tools ---
    "list_upcoming_events": {
        "function": gcalendar_tools.list_upcoming_events,
        "args_model": ListUpcomingEventsArgs,
        "category": "Task-Specific"
    },

    # --- Image Tools ---
    "analyze_image_content": {
        "function": image_tools.analyze_image_content,
        "args_model": AnalyzeImageContentArgs,
        "category": "Multimedia Analysis"
    },

    # --- Memory Tools ---
    "save_task_summary_to_memory": {
        "function": memory_tools.save_task_summary_to_memory,
        "args_model": SaveTaskSummaryArgs,
        "category": "System Info"
    },
    "save_user_preference": {
        "function": memory_tools.save_user_preference,
        "args_model": SaveUserPreferenceArgs,
        "category": "System Info"
    },
    "get_user_preferences": {
        "function": memory_tools.get_user_preferences,
        "args_model": NoArgs,
        "category": "System Info"
    },

    # --- System Info Tools ---
    "get_system_information": {
        "function": system_info_tools.get_system_information,
        "args_model": NoArgs,
        "category": "System Info"
    },
    "get_process_list": {
        "function": system_info_tools.get_process_list,
        "args_model": GetProcessListArgs,
        "category": "System Info"
    },

    # --- System Tools (Execution) ---
    "execute_shell_command": {
        "function": system_tools.execute_shell_command,
        "args_model": ExecuteShellCommandArgs,
        "category": "System Info & Execution"
    },
    "create_new_tool": {
        "function": python_script_tool.create_new_tool,
        "args_model": CreateNewToolArgs,
        "category": "System Info & Execution"
    },
    "execute_generated_python_script": {
        "function": python_script_tool.execute_generated_python_script,
        "args_model": ExecuteGeneratedPythonScriptArgs,
        "category": "System Info & Execution"
    },
    
    # --- Task Runner Tools ---
    "run_report_builder_task": {
        "function": task_runner.run_report_builder_task,
        "args_model": RunReportBuilderTaskArgs,
        "category": "Task-Specific"
    },

    # --- Voice Tools ---
    "transcribe_audio": {
        "function": voice_tools.transcribe_audio,
        "args_model": TranscribeAudioArgs,
        "category": "Multimedia Analysis"
    },
    "text_to_speech": {
        "function": voice_tools.text_to_speech,
        "args_model": TextToSpeechArgs,
        "category": "Multimedia Analysis"
    },

    # --- Web Tools ---
    "browse_web_page": {
        "function": lambda url: (web_tools.browse_web_page(url) or ("Error", None))[0],
        "args_model": BrowseWebPageArgs,
        "category": "Web Search"
    },
    "search_and_browse": {
        "function": web_tools.search_and_browse,
        "args_model": SearchAndBrowseArgs,
        "category": "Web Search"
    },

    # --- Weather Tools ---
    "get_current_weather": {
        "function": weather_tools.get_current_weather,
        "args_model": NoArgs,
        "category": "Weather"
    },
}