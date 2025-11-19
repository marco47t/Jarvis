# commands/gmail_tools.py
import base64
import logging
import os
import re
from email.mime.text import MIMEText
from typing import List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import ENABLE_LOGGING

# --- Logger Setup ---
if ENABLE_LOGGING:
    logger = logging.getLogger(__name__)
else:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.CRITICAL + 1)
    logger.propagate = False

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.send']

def _get_gmail_service():
    """Authenticates with Gmail API and returns the service object."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}. Please re-authenticate.")
                creds = None
        if not creds:
            if not os.path.exists('credentials.json'):
                logger.error("credentials.json not found. Please download it from Google Cloud Console.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        service = build('gmail', 'v1', credentials=creds)
        logger.info("Gmail service successfully initialized.")
        return service
    except HttpError as error:
        logger.error(f"An HTTP error occurred with Gmail API: {error}")
        return None

def _parse_email_body(payload: Dict[str, Any]) -> str:
    """A helper function to recursively parse the email payload for the text body."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'multipart/alternative':
                # Recurse into multipart
                return _parse_email_body(part)
    elif 'body' in payload and 'data' in payload['body']:
         # For simple, non-multipart emails
        if payload.get('mimeType') == 'text/plain':
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return "" # Return empty string if no plain text part is found


def get_email_details(email_id: str) -> Dict:
    """
    Fetches the full details of a single email, including the body.
    """
    service = _get_gmail_service()
    if not service:
        return {"error": "Could not authenticate with Gmail."}
    try:
        message = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        
        body = _parse_email_body(payload)
        if not body:
            # Fallback to snippet if body parsing fails
            body = message.get('snippet', 'Could not load email body.')

        return {
            "from": from_header,
            "subject": subject,
            "body": body.strip()
        }

    except HttpError as error:
        logger.error(f"An HTTP error occurred while fetching email details: {error}")
        return {"error": f"Error fetching email: {error}"}
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching email details: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {e}"}


def search_and_fetch_emails(query: str, max_results: int = 25) -> List[Dict]:
    """
    Searches for emails using a query and fetches structured metadata for each.
    """
    service = _get_gmail_service()
    if not service: return []
    try:
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        email_list = []
        if not messages: return []
        for msg in messages:
            msg_id = msg['id']
            message = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject']).execute()
            headers = message['payload']['headers']
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
            from_header = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
            email_list.append({ "id": msg_id, "from_full": from_header, "subject": subject })
        return email_list
    except Exception: return []

def send_gmail_message(to_address: str, subject: str, body: str) -> str:
    """Sends an email via Gmail."""
    service = _get_gmail_service()
    if not service: return "Error: Could not authenticate with Gmail."
    try:
        message = MIMEText(body)
        message['to'] = to_address
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': raw_message}
        send_message = service.users().messages().send(userId='me', body=create_message).execute()
        return f"Email sent successfully to {to_address}."
    except HttpError as error:
        return f"Error sending email: {error}"