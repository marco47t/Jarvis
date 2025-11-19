# commands/tools/tool_models.py
from pydantic import BaseModel, Field
from typing import Optional, List

# This file defines the strict, typed argument schemas for every tool
# the agent can use. Using Pydantic ensures that arguments are validated
# before a tool is ever executed, preventing a major class of bugs.

# ===================================================================
#                          Helper Models
# ===================================================================

class NoArgs(BaseModel):
    """A special model for tools that take no arguments."""
    pass


# ===================================================================
#                      Tool Argument Models
# ===================================================================

# --- Backup Tools (backup_tools.py) ---
class CreateProjectBackupArgs(BaseModel):
    """Arguments for creating a timestamped zip backup of a folder."""
    source_path: Optional[str] = Field(None, description="The path to the folder to back up. Defaults to the current project directory if not provided.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

# --- Clipboard Tools (clipboard_tools.py) ---
class SetClipboardContentArgs(BaseModel):
    """Arguments for setting the system clipboard to the given text."""
    text: str = Field(..., description="The text to place in the clipboard.")

# --- Document Tools (document_tools.py) ---
class ReadPdfOrDocxContentArgs(BaseModel):
    """Arguments for reading content from a PDF or DOCX file."""
    file_path: str = Field(..., description="The absolute or relative path to the file.")

# --- File Organizer (file_organizer.py) ---
class MoveFileArgs(BaseModel):
    """Arguments for moving a file to a specific, user-defined location."""
    source_path: str = Field(..., description="The full path of the file to move.")
    destination_folder: str = Field(..., description="The full path of the folder to move the file into.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class RenameFileArgs(BaseModel):
    """Arguments for renaming a file."""
    current_path: str = Field(..., description="The full path of the file to rename.")
    new_name: str = Field(..., description="The new name for the file, including the extension.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class HandleInvoiceArgs(BaseModel):
    """Arguments for handling files classified as invoices."""
    file_path: str = Field(..., description="The full path of the invoice file to process.")
    company: str = Field(..., description="The name of the company that issued the invoice.")
    date: str = Field(..., description="The date of the invoice, preferably in YYYY-MM-DD format.")
    amount: Optional[str] = Field(None, description="The total amount of the invoice, if available.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class HandleScreenshotArgs(BaseModel):
    """Arguments for handling screenshots by renaming and moving them."""
    file_path: str = Field(..., description="The full path of the screenshot file.")
    subject: str = Field(..., description="A brief subject description for the screenshot's new name.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class HandleProjectAssetArgs(BaseModel):
    """Arguments for handling project-related assets like images, docs, or code."""
    file_path: str = Field(..., description="The full path of the asset file.")
    project_name: str = Field(..., description="The name of the project this asset belongs to.")
    asset_type: str = Field(..., description="The type of the asset (e.g., 'Image', 'Document', 'Code').")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class HandleGenericDocumentOrImageArgs(BaseModel):
    """Arguments for handling generic documents or images with a default action."""
    file_path: str = Field(..., description="The full path of the file to be organized.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

class DeleteJunkFileArgs(BaseModel):
    """Arguments for deleting a file that is classified as temporary or junk."""
    file_path: str = Field(..., description="The full path of the junk file to delete.")
    reason: str = Field(..., description="A brief reason why this file is considered junk.")
    dry_run: bool = Field(False, description="If True, describes the action without executing it.")

# --- GMail Tools (gmail_tools.py) ---
class SendGmailMessageArgs(BaseModel):
    """Arguments for sending an email via Gmail."""
    to_address: str = Field(..., description="The recipient's email address.")
    subject: str = Field(..., description="The subject line of the email.")
    body: str = Field(..., description="The plain text body of the email.")

# --- Image Tools (image_tools.py) ---
class AnalyzeImageContentArgs(BaseModel):
    """Arguments for analyzing an image to describe it or perform OCR."""
    file_path: str = Field(..., description="The local path to the image file to be analyzed.")
    analysis_type: str = Field(
        'describe',
        description="Type of analysis. Use 'describe' for a general description or 'ocr' for text extraction.",
        enum=['describe', 'ocr']
    )
    custom_prompt: Optional[str] = Field(None, description="An optional custom prompt to guide the analysis, overriding analysis_type.")

# --- System Info Tools (system_info_tools.py) ---
class GetProcessListArgs(BaseModel):
    """Arguments for retrieving a list of top running processes."""
    limit: int = Field(15, description="The number of top processes (sorted by memory) to return.")

# --- System Tools (system_tools.py) ---
class ExecuteShellCommandArgs(BaseModel):
    """Arguments for executing a shell command."""
    command: str = Field(..., description="The shell command to be executed.")

# --- Task Runner (task_runner.py) ---
class RunReportBuilderTaskArgs(BaseModel):
    """Arguments for executing the multi-step report builder task."""
    topic: str = Field(..., description="The topic for which to build the report.")

# --- Voice Tools (voice_tools.py) ---
class TranscribeAudioArgs(BaseModel):
    """Arguments for transcribing audio from a file."""
    audio_file_path: str = Field(..., description="The local path to the audio file to be transcribed.")

class TextToSpeechArgs(BaseModel):
    """Arguments for synthesizing text into an audio file."""
    text_to_synthesize: str = Field(..., description="The text content to be converted to speech.")
    output_directory: str = Field('audio_responses', description="The directory where the output MP3 file will be saved.")

# --- Web Tools (web_tools.py) ---
class BrowseWebPageArgs(BaseModel):
    """Arguments for fetching and parsing a single web page."""
    url: str = Field(..., description="The URL of the web page to fetch and parse.")

class SearchAndBrowseArgs(BaseModel):
    """Arguments for performing a Google search and browsing the results."""
    query: str = Field(..., description="The search query for Google.")
    num_results: int = Field(1, description="The number of top search results to browse.")
    follow_links: bool = Field(False, description="Whether to follow internal links on the browsed pages.")

# --- Python Script Tool (python_script_tool.py) ---
class ExecuteGeneratedPythonScriptArgs(BaseModel):
    """Arguments for executing an AI-generated Python script."""
    code: str = Field(..., description="A string containing the complete, valid Python code to execute.")
    reason: str = Field(..., description="A brief, one-sentence explanation of what the script does. This will be shown to the user for confirmation.")

# --- Memory Tools (memory_tools.py) ---
class SaveTaskSummaryArgs(BaseModel):
    """Arguments for saving a completed task summary to long-term memory."""
    task_summary: str = Field(..., description="A concise summary of the original user goal.")
    tools_used: List[str] = Field(..., description="A list of the tool names that were executed to complete the task.")
    final_result: str = Field(..., description="The final, user-facing answer that was provided.")

class SaveUserPreferenceArgs(BaseModel):
    """Arguments for saving a user preference."""
    preference_key: str = Field(..., description="The name of the preference to save (e.g., 'summary_format').")
    preference_value: str = Field(..., description="The value of the preference (e.g., 'bullet points').")


class CreateNewToolArgs(BaseModel):
    """Arguments for creating a new, session-specific tool from Python code."""
    tool_name: str = Field(..., description="The name for the new tool, must be a valid Python function name.")
    python_code: str = Field(..., description="A string containing the complete Python code for a single function.")
    description: str = Field(..., description="A clear, one-sentence description of what the tool does and what its arguments are.")


class GetTodaysTasksArgs(BaseModel):
    """Arguments for fetching tasks from Google Tasks for today."""
    max_results: int = Field(10, description="The maximum number of tasks to return.")

class CreateDocumentArgs(BaseModel):
    """Arguments for creating a new document."""
    filename: str = Field(..., description="The name for the new document, e.g., 'Meeting Notes.docx'.")
    content: str = Field(..., description="The initial text content for the document.")
    folder_path: str = Field("Desktop", description="The folder to save the document in, e.g., 'Desktop'.")

class TextToSpeechArgs(BaseModel):
    """Arguments for synthesizing text into an audio file."""
    text_to_synthesize: str = Field(..., description="The text content to be converted to speech.")
    output_directory: str = Field('temp', description="The directory where the output MP3 file will be saved.")

# in tool_models.py
class ListUpcomingEventsArgs(BaseModel):
    """Arguments for listing upcoming Google Calendar events."""
    max_results: int = Field(10, description="The maximum number of events to return.")

class SearchEmailsArgs(BaseModel):
    """Arguments for searching and fetching emails from the user's Gmail account."""
    query: str = Field(..., description="A valid Gmail search query. For example: 'is:unread', 'from:elonmusk', 'subject:receipt', or 'is:important'.")
    max_results: int = Field(5, description="The maximum number of emails to return.")

class GetTodaysTasksArgs(BaseModel):
    """Arguments for fetching tasks from Google Tasks for today."""
    max_results: int = Field(10, description="The maximum number of tasks to return.")

class CreateTaskArgs(BaseModel):
    """Arguments for creating a new task in the user's Google Tasks list."""
    title: str = Field(..., description="The title of the task to be created.")
    notes: Optional[str] = Field(None, description="Optional notes or a description for the task.")

class ArchiveEmailArgs(BaseModel):  # <-- ADD THIS NEW CLASS
    """Arguments for archiving an email (removing it from the inbox)."""
    email_id: str = Field(..., description="The unique ID of the email to be archived.")