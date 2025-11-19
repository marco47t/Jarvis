# commands/tools/gtasks_tools.py
import datetime
import logging
from .google_auth import get_google_api_service
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

def get_todays_tasks(max_results: int = 20) -> list:
    """Fetches tasks from the user's specified Google Tasks list that are due today."""
    scopes = ['https://www.googleapis.com/auth/tasks.readonly']
    service = get_google_api_service('tasks', 'v1', scopes)
    if not service: return [{"error": "Could not authenticate with Tasks API."}]
    
    try:
        now = datetime.datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        end_of_day = now.replace(hour=23, minute=59, second=59).isoformat() + 'Z'
        
        # --- MODIFIED LINE ---
        # Using your specific Task List ID instead of the default.
        results = service.tasks().list(
            tasklist='MTU0ODMxODY2ODc3NTc0NTQ2Mzc6MDow', 
            maxResults=max_results, 
            dueMin=start_of_day, 
            dueMax=end_of_day, 
            showCompleted=False
        ).execute()

        items = results.get('items', [])
        if not items:
            return []
            
        return [{"title": item['title'], "notes": item.get('notes', ''), "id": item['id']} for item in items]
    except HttpError as error:
        logger.error(f"Google Tasks API Error: {error}")
        return [{"error": "Could not fetch tasks. Please re-authenticate after deleting token.json and ensure tasks permission is granted."}]
    except Exception as e:
        logger.error(f"Error fetching Google Tasks: {e}", exc_info=True)
        return [{"error": f"An error occurred fetching tasks: {e}"}]

def create_task(title: str, notes: str = None) -> dict:
    """Creates a new task in the user's specified Google Tasks list."""
    scopes = ['https://www.googleapis.com/auth/tasks']
    service = get_google_api_service('tasks', 'v1', scopes)
    if not service: return {"error": "Could not authenticate with Tasks API."}
    
    try:
        task_body = {'title': title}
        if notes:
            task_body['notes'] = notes

        # --- MODIFIED LINE ---
        # Using your specific Task List ID for creating new tasks.
        result = service.tasks().insert(tasklist='MTU0ODMxODY2ODc3NTc0NTQ2Mzc6MDow', body=task_body).execute()

        return {"success": True, "title": result['title'], "id": result['id']}
    except HttpError as error:
        logger.error(f"Google Tasks API Error: {error}")
        return {"error": "Could not create task. Please ensure you have granted read/write tasks permission."}
    except Exception as e:
        logger.error(f"Error creating Google Task: {e}", exc_info=True)
        return {"error": f"An error occurred creating the task: {e}"}