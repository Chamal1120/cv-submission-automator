import unittest
from unittest.mock import patch, MagicMock
from utils.update_sheet import get_google_sheets_service, get_spreadsheet, append_cv_details


class UpdateSheetTests(unittest.TestCase):
    @patch("utils.update_sheet.service_account.Credentials.from_service_account_file")
    @patch("utils.update_sheet.build")
    def test_get_google_sheets_service(self, mock_build, mock_credentials):
        mock_creds = MagicMock()
        mock_credentials.return_value = mock_creds
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        result = get_google_sheets_service()
        mock_credentials.assert_called_once()
        mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_creds)
        self.assertEqual(result, mock_service)

    @patch("utils.update_sheet.get_google_sheets_service")
    def test_get_spreadsheet_existing(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_spreadsheet = MagicMock()
        mock_service.spreadsheets().get().execute.return_value = mock_spreadsheet
        result = get_spreadsheet(mock_service)
        self.assertEqual(result, "154hmgvVrNS9GxAjLRuYqC8axDdcbjygDG0rJ7GbGRwo")

    @patch("utils.update_sheet.get_google_sheets_service")
    def test_get_spreadsheet_not_found(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_service.spreadsheets().get().execute.side_effect = Exception("Spreadsheet not found")
        with self.assertRaises(Exception):
            get_spreadsheet(mock_service)

    @patch("utils.update_sheet.datetime")
    def test_append_cv_details(self, mock_datetime):
        mock_service = MagicMock()
        mock_spreadsheets = MagicMock()
        mock_values = MagicMock()
        mock_append = MagicMock()
        mock_service.spreadsheets.return_value = mock_spreadsheets
        mock_spreadsheets.values.return_value = mock_values
        mock_values.append.return_value = mock_append
        mock_datetime.now.return_value.isoformat.return_value = "2025-03-11T12:00:00Z"
        cv_data = {
            "personal_info": {"name": "Test", "email": "test@example.com"},
            "education": ["Edu1"],
            "qualifications": ["Qual1"],
            "projects": ["Proj1"],
            "cv_public_link": "http://example.com"
        }
        append_cv_details(mock_service, "mock_spreadsheet_id", cv_data)
        mock_service.spreadsheets.assert_called_once()
        mock_spreadsheets.values.assert_called_once()
        mock_values.append.assert_called_once_with(
            spreadsheetId="mock_spreadsheet_id",
            range="Sheet1!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={
                "values": [
                    [
                        "Test",
                        "test@example.com",
                        "Edu1",
                        "Qual1",
                        "Proj1",
                        "http://example.com",
                        "2025-03-11T12:00:00Z"
                    ]
                ]
            }
        )
        mock_append.execute.assert_called_once()


