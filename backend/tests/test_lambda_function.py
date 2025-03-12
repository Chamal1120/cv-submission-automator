import unittest
from unittest.mock import patch, MagicMock
from io import BytesIO
from lambda_function import lambda_handler


class TestLambdaFunction(unittest.TestCase):

    @patch('lambda_function.s3_client')
    @patch('lambda_function.pypdf.PdfReader')
    @patch('lambda_function.parse_cv_pdf')
    @patch('lambda_function.get_google_sheets_service')
    @patch('lambda_function.get_spreadsheet')
    @patch('lambda_function.append_cv_details')
    @patch('lambda_function.requests.post')
    @patch('lambda_function.send_review_email')
    def test_lambda_handler_success(self, mock_send_email, mock_post, mock_append,
                                    mock_get_spreadsheet, mock_get_service,
                                    mock_parse_cv, mock_pdf_reader, mock_s3):
        # Mock S3 event
        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "test.pdf"}
                }
            }]
        }

        # Mock S3 client response
        mock_s3.get_object.return_value = {'Body': BytesIO(b'pdf content')}

        # Mock PDF reader
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Test CV content"
        mock_pdf_reader.return_value.pages = [mock_page]

        # Mock CV parsing
        mock_parse_cv.return_value = {
            "personal_info": {"name": "Test User", "email": "test@example.com"},
            "education": ["Test University"],
            "qualifications": ["Test Qualification"],
            "projects": ["Test Project"],
            "cv_public_link": "https://test-bucket.s3.amazonaws.com/test.pdf"
        }

        # Mock Google Sheets service
        mock_get_service.return_value = MagicMock()
        mock_get_spreadsheet.return_value = "test_spreadsheet_id"

        # Mock webhook response
        mock_post.return_value.status_code = 200

        # Call lambda handler
        response = lambda_handler(event, None)

        # Assertions
        self.assertEqual(response['statusCode'], 200)
        mock_s3.get_object.assert_called_once_with(Bucket='test-bucket', Key='test.pdf')
        mock_parse_cv.assert_called_once()
        mock_get_service.assert_called_once()
        mock_get_spreadsheet.assert_called_once()
        mock_append.assert_called_once()
        mock_post.assert_called_once()
        mock_send_email.assert_called_once_with('test@example.com')

    @patch('lambda_function.s3_client')
    def test_lambda_handler_invalid_format(self, mock_s3):
        event = {
            "Records": [{
                "s3": {
                    "bucket": {"name": "test-bucket"},
                    "object": {"key": "test.txt"}
                }
            }]
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['body'], {"error": "File must be in .pdf format"})

