# commands/tools/gcalendar_tools.py
import datetime
import logging
from .google_auth import get_google_api_service # This is correct
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

def list_upcoming_events(max_results: int = 10) -> list:
    """Lists the next upcoming events from the user's primary Google Calendar."""
    
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']    
    service = get_google_api_service('calendar', 'v3', scopes)
    if not service: return [{"error": "Authentication failed. Could not access Google Calendar."}]
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary', timeMin=now,
            maxResults=max_results, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])
        
        if not events:
            return [] # No events is a valid state

        event_list = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            event_list.append({'summary': event['summary'], 'start': start})
        return event_list
    except HttpError as error:
        logger.error(f"Google Calendar API Error: {error}")
        return [{"error": "Could not fetch calendar events. Please re-authenticate after deleting token.json and ensure calendar permission is granted."}]
    except Exception as e:
        logger.error(f"An unexpected error occurred fetching calendar events: {e}")
        return [{"error": f"An unexpected error occurred: {e}"}]