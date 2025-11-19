# commands/tools/google_auth.py
import os
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# --- DEFINE ALL REQUIRED SCOPES IN ONE PLACE ---
# This list is now the single source of truth for all permissions.
ALL_APP_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/tasks',          # Read/Write for creating tasks
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
]

TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'

def get_google_api_service(api_name: str, api_version: str, requested_scopes: list):
    """
    Centralized function to authenticate and get a Google API service object.
    It manages a single token.json with all required scopes.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, ALL_APP_SCOPES)
        if not all(scope in creds.scopes for scope in requested_scopes):
             print(f"--- DEBUG: Token missing required scopes for {api_name}. Re-authenticating. ---")
             creds = None #

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("--- DEBUG: Refreshing expired Google token... ---")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}. Deleting token and re-authenticating.")
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None
        
        if not creds:
            existing_scopes = set()
            if os.path.exists(TOKEN_FILE):
                 try:
                    # Temporarily load just to get scopes
                    temp_creds = Credentials.from_authorized_user_file(TOKEN_FILE, ALL_APP_SCOPES)
                    existing_scopes = set(temp_creds.scopes)
                 except Exception:
                    pass # Ignore if token is invalid

            # Combine existing scopes with newly requested ones
            scopes_for_auth = list(existing_scopes.union(set(requested_scopes)))
            
            print(f"--- DEBUG: Requesting Google auth with scopes: {scopes_for_auth} ---")
            
            # Use the combined list, not ALL_APP_SCOPES
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes_for_auth) 
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            
    try:
        service = build(api_name, api_version, credentials=creds)
        logger.info(f"Google API service '{api_name}' initialized successfully.")
        return service
    except HttpError as error:
        logger.error(f"An HTTP error occurred building service '{api_name}': {error}")
        return None