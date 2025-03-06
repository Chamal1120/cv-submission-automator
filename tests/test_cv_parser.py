import unittest
from unittest.mock import MagicMock, patch, mock_open
from models.cv_parser import CVParser


class TestCVParser(unittest.TestCase):
    def setUp(self):
        """Set up fixtures before each test"""

        self.sample_text = (
            "Chamal Randika |  chamal.randy@hisdomain.com | +9470-456-7890\n"
            "Education:\n Bachelor of Science in Software Engineering, SLTC Research University,  2026\n GCE A/L, Maliyadeva College, 2018\n"
            "Qualifications:\n Certified Python Developer - 2022 Certified\n Golang Developer\n"
            "Projects:\n Built a web app using Python and AWS.\n Built a mobile app with server driven UI components."
        )

        self.expected_output = {
            "personal_info": {
                "name": "Chamal Randika",
                "email": "chamal.randy@hisdomain.com",
                "phone": "+9470-456-7890",
            },
            "education": [
                "Bachelor of Science in Software Engineering, SLTC Research University, 2026",
                "GCE A/L, Maliyadeva College, 2018"
            ],
            "qualifications": [
                "Certified Python Developer - 2022",
                "Certified Golang Developer",
            ],
            "projects": [
                "Built a web app using Python and AWS.",
                "Built a mobile app with server driven UI components.",
            ],
            "cv_public_link": "file://Test-cv.pdf",
        }

    @patch("pypdf.PdfReader")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    def test_get_cv_data_success(self, mock_file, mock_reader):
        """Test successful  extraction of CV data with valid"""
        self.maxDiff = None
        mock_page = MagicMock()
        mock_page.extract_text.return_value = self.sample_text
        mock_reader.return_value.pages = [mock_page]

        parser = CVParser("Test-cv.pdf")
        result = parser.get_cv_data()

        self.assertEqual(result, self.expected_output)

    def test_invalid_file_format(self):
        """Test that a non-PDF file raises ValueError"""
        with self.assertRaises(ValueError) as context:
            CVParser("Test-cv.txt")
        self.assertEqual(str(context.exception), "File must be in .pdf format.")

    @patch("pypdf.PdfReader")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    def test_multi_page_pdf(self, mock_file, mock_reader):
        """Test that a multi-page PDF raises ValueError"""
        mock_reader.return_value.pages = [MagicMock(), MagicMock()]

        with self.assertRaises(ValueError) as context:
            CVParser("Test-cv.pdf")
        self.assertEqual(str(context.exception), "PDF must be a single page only.")

    @patch("pypdf.PdfReader")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    def test_empty_pdf(self, mock_file, mock_reader):
        """Test extraction with an empty PDF."""
        self.maxDiff = None
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]

        parser = CVParser("Test-cv.pdf")
        result = parser.get_cv_data()

        expected = {
            "personal_info": {"name": "", "email": "", "phone": ""},
            "education": [],
            "qualifications": [],
            "projects": [],
            "cv_public_link": "file://Test-cv.pdf",
        }

        self.assertEqual(result, expected)

    @patch("pypdf.PdfReader")
    @patch("builtins.open", new_callable=mock_open, read_data="dummy data")
    def test_missing_sections(self, mock_file, mock_reader):
        """Test extraction when some sections are missing."""

        partial_text = "Chamal Randika |  chamal.randy@hisdomain.com | +9470-456-7890"
        mock_page = MagicMock()
        mock_page.extract_text.return_value = partial_text
        mock_reader.return_value.pages = [mock_page]

        parser = CVParser("Test-cv.pdf")
        result = parser.get_cv_data()

        expected = {
            "personal_info": {
                "name": "Chamal Randika",
                "email": "chamal.randy@hisdomain.com",
                "phone": "+9470-456-7890",
            },
            "education": [],
            "qualifications": [],
            "projects": [],
            "cv_public_link": "file://Test-cv.pdf",
        }
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
