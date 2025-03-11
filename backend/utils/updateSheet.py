import logging
from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Google Sheets api setup
SERVICE_ACCOUNT_FILE = 'google-credentials.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '154hmgvVrNS9GxAjLRuYqC8axDdcbjygDG0rJ7GbGRwo'
SHEET_NAME = 'Sheet1'
RANGE_NAME = f'{SHEET_NAME}!A1'


def get_google_sheets_service():
    """Authenticate and create the Sheets API client."""
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=credentials)


def create_or_get_spreadsheet(service):
    """Create a new Google Sheets file named 'cv-details-extracted' if it doesn't exist."""
    try:
        # Try to access the spreadsheet
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        logger.info(f"Spreadsheet found: {sheet_metadata['properties']['title']}")
        return SPREADSHEET_ID
    except Exception as e:
        logger.warning("Spreadsheet not found. Creating a new one...", e)

        # Create new If it doesn't exist
        spreadsheet_body = {
            'properties': {'title': 'cv-details-extracted'}
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId').execute()
        new_spreadsheet_id = spreadsheet.get('spreadsheetId')

        # Log and return the new spreadsheet ID
        logger.info(f"New Spreadsheet created with ID: {new_spreadsheet_id}")
        return new_spreadsheet_id


def append_cv_details(service, spreadsheet_id, cv_data):
    """Append extracted CV data to the Google Sheets file."""
    sheet_values = [
        [
            cv_data["personal_info"].get("name", ""),
            cv_data["personal_info"].get("email", ""),
            cv_data.get("education", ""),
            cv_data.get("experience", ""),
            cv_data.get("skills", ""),
            cv_data.get("public_url", ""),
            datetime.now(timezone.utc).isoformat()
        ]
    ]

    body = {
        'values': sheet_values
    }
    response = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=RANGE_NAME,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()

    logger.info(f"Appended data to sheet: {response}")


