# commands/tools/gmail_tools.py
import base64
import logging
from email.mime.text import MIMEText
from typing import List, Dict, Any

from .google_auth import get_google_api_service # <-- Use the new central auth
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def _parse_email_body(payload: Dict[str, Any]) -> str:
    """A helper function to recursively parse the email payload for the text body."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                if 'data' in part['body']:
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            elif part['mimeType'] == 'multipart/alternative':
                return _parse_email_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        if payload.get('mimeType') == 'text/plain':
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return ""


def get_email_details(email_id: str) -> Dict:
    """Fetches the full details of a single email, including the body and a direct web link."""
    # FIX: Call the central auth function with the correct readonly scope
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    service = get_google_api_service('gmail', 'v1', scopes)
    
    if not service:
        return {"error": "Could not authenticate with Gmail."}
    try:
        message = service.users().messages().get(userId='me', id=email_id, format='full').execute()
        payload = message.get('payload', {})
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
        from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
        body = _parse_email_body(payload) or message.get('snippet', 'Could not load email body.')
        web_link = f"https://mail.google.com/mail/u/0/#inbox/{email_id}"

        return {
            "from": from_header,
            "subject": subject,
            "body": body.strip(),
            "web_link": web_link
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching email details: {e}", exc_info=True)
        return {"error": f"An unexpected error occurred: {e}"}


def search_and_fetch_emails(query: str, max_results: int = 25) -> List[Dict]:
    """Searches for emails using a query and fetches structured metadata for each."""
    # FIX: Call the central auth function with the correct readonly scope
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    service = get_google_api_service('gmail', 'v1', scopes)

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
    except Exception as e:
        logger.error(f"Error during email search: {e}", exc_info=True)
        return []

def send_gmail_message(to_address: str, subject: str, body: str) -> str:
    """Sends an email via Gmail."""
    # FIX: Call the central auth function with the correct send scope
    scopes = ['https://www.googleapis.com/auth/gmail.send']
    service = get_google_api_service('gmail', 'v1', scopes)
    
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
    

def archive_email(email_id: str) -> str:
    """
    Archives an email by removing it from the inbox.

    Args:
        email_id (str): The ID of the email to archive.

    Returns:
        str: A confirmation message.
    """
    scopes = ['https://www.googleapis.com/auth/gmail.modify']
    service = get_google_api_service('gmail', 'v1', scopes)
    if not service:
        return "Error: Could not authenticate with Gmail to modify emails."
    
    try:
        # The body for the modify request to remove the 'INBOX' label
        body = {'removeLabelIds': ['INBOX']}
        service.users().messages().modify(userId='me', id=email_id, body=body).execute()
        logger.info(f"Successfully archived email with ID: {email_id}")
        return f"Successfully archived email (ID: {email_id})."
    except HttpError as error:
        logger.error(f"Failed to archive email {email_id}: {error}")
        return f"Error: Could not archive email. API Error: {error}"
    except Exception as e:
        logger.error(f"An unexpected error occurred while archiving email {email_id}: {e}", exc_info=True)
        return f"An unexpected error occurred: {e}"