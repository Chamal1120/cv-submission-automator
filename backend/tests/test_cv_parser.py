import unittest
from lambda_function import lambda_handler
from models.cv_parser import parse_cv_pdf
from unittest.mock import MagicMock, patch


class TestCVParser(unittest.TestCase):
    def setUp(self):
        """Set up fixtures before each test."""
        self.sample_text = (
            "Chamal Randika | chamal.randy@hisdomain.com | +9470-456-7890\n"
            "Education:\n Bachelor of Science in Software Engineering, SLTC Research University, 2026\n GCE A/L, Maliyadeva College, 2018\n"
            "Qualifications:\n Certified Python Developer - 2022 Certified\n Golang Developer\n"
            "Projects:\n Built a web app using Python and AWS.\n Built a mobile app with server driven UI components."
        )

        self.s3_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "my-bucket"},
                        "object": {"key": "Test-cv.pdf"},
                    }
                }
            ]
        }

        self.expected_output = {
            "personal_info": {
                "name": "Chamal Randika",
                "email": "chamal.randy@hisdomain.com",
                "phone": "+9470-456-7890",
            },
            "education": [
                "Bachelor of Science in Software Engineering, SLTC Research University, 2026",
                "GCE A/L, Maliyadeva College, 2018",
            ],
            "qualifications": [
                "Certified Python Developer - 2022",
                "Certified Golang Developer",
            ],
            "projects": [
                "Built a web app using Python and AWS.",
                "Built a mobile app with server driven UI components.",
            ],
            "cv_public_link": "https://my-bucket.s3.amazonaws.com/Test-cv.pdf"
        }

        self.expected_empty_output = {
            "personal_info": {"name": "", "email": "", "phone": ""},
            "education": [],
            "qualifications": [],
            "projects": [],
            "cv_public_link": "https://my-bucket.s3.amazonaws.com/Test-cv.pdf"
        }

    # Test parse_cv_pdf directly
    def test_parse_cv_pdf_success(self):
        """Test successful parsing of CV data."""
        self.maxDiff = None
        result = parse_cv_pdf(self.sample_text, "https://my-bucket.s3.amazonaws.com/Test-cv.pdf")
        self.assertEqual(result, self.expected_output)

    # Test lambda_handler
    @patch("requests.post")
    @patch("lambda_function.s3_client.get_object")
    @patch("pypdf.PdfReader")
    def test_lambda_handler_success(self, mock_reader, mock_s3_get, mock_post):
        """Test Lambda handler with valid S3 event."""
        self.maxDiff = None
        mock_page = MagicMock()
        mock_page.extract_text.return_value = self.sample_text
        mock_reader.return_value.pages = [mock_page]
        mock_s3_get.return_value = {"Body": "dummy file object"}
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None

        result = lambda_handler(self.s3_event, None)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], self.expected_output)

    def test_lambda_handler_invalid_format(self):
        """Test Lambda handler with non-PDF file."""
        invalid_event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "my-bucket"},
                        "object": {"key": "Test-cv.txt"},
                    }
                }
            ]
        }
        result = lambda_handler(invalid_event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"]["error"], "File must be in .pdf format")

    @patch("requests.post")
    @patch("lambda_function.s3_client.get_object")
    @patch("pypdf.PdfReader")
    def test_lambda_handler_multi_page(self, mock_reader, mock_s3_get, mock_post):
        """Test Lambda handler with multi-page PDF."""
        mock_reader.return_value.pages = [MagicMock(), MagicMock()]
        mock_s3_get.return_value = {"Body": "dummy file object"}
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None

        result = lambda_handler(self.s3_event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"]["error"], "PDF must be a single page only")

    @patch("requests.post")
    @patch("lambda_function.s3_client.get_object")
    @patch("pypdf.PdfReader")
    def test_lambda_handler_empty_pdf(self, mock_reader, mock_s3_get, mock_post):
        """Test Lambda handler with empty PDF."""
        self.maxDiff = None
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]
        mock_s3_get.return_value = {"Body": "dummy file object"}
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = lambda: None

        result = lambda_handler(self.s3_event, None)
        expected = {
            "personal_info": {"name": "", "email": "", "phone": ""},
            "education": [],
            "qualifications": [],
            "projects": [],
            "cv_public_link": "https://my-bucket.s3.amazonaws.com/Test-cv.pdf"
        }
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], expected)


if __name__ == "__main__":
    unittest.main()
