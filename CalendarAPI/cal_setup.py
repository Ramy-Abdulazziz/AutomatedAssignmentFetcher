import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/calendar']

CREDENTIALS = 'AssignmentFetcher/Credentials/credentials.json'

def get_calendar_service():
    creds = None
    
    if os.path.exists('AssignmentFetcher/Credentials/token.pickle'):
        with open('AssignmentFetcher/Credentials/token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)

        with open('AssignmentFetcher/Credentials/token.pickle', 'wb') as token:
            pickle.dump(creds,token)

    service = build('calendar', 'v3', credentials = creds)

    return service