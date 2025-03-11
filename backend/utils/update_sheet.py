import os
import logging
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get the absolute path of the root dir
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Construct the full path to the google-credentials.json
credentials_path = os.path.join(root_dir, 'google-credentials.json')

# Google Sheets API setup
SERVICE_ACCOUNT_FILE = credentials_path
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '154hmgvVrNS9GxAjLRuYqC8axDdcbjygDG0rJ7GbGRwo'
SHEET_NAME = 'Sheet1'
RANGE_NAME = f'{SHEET_NAME}!A1'


def get_google_sheets_service():
    """Authenticate and create the Sheets API client."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service


def get_spreadsheet(service):
    """Retrieve the predefined Google Sheets file by ID or log an error if it doesn’t exist."""
    try:
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        logger.info(f"Spreadsheet found: {sheet_metadata['properties']['title']}")
        return SPREADSHEET_ID
    except Exception as e:
        logger.error(f"Failed to find spreadsheet with ID {SPREADSHEET_ID}: {str(e)}")
        raise  # Re-raise the exception to propagate it to the caller


def append_cv_details(service, spreadsheet_id, cv_data):
    """Append extracted CV data to the Google Sheets file."""
    sheet_values = [
        [
            cv_data["personal_info"].get("name", ""),
            cv_data["personal_info"].get("email", ""),
            "\n\n".join(cv_data.get("education", [])),
            "\n\n".join(cv_data.get("qualifications", [])),
            "\n\n".join(cv_data.get("projects", [])),
            cv_data.get("cv_public_link", ""),
            datetime.now(timezone.utc).isoformat()
        ]
    ]

    body = {'values': sheet_values}
    try:
        response = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=RANGE_NAME,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        logger.info(f"Appended data to sheet: {response}")
    except Exception as e:
        logger.error(f"Failed to append data to sheet: {str(e)}")
        raise
