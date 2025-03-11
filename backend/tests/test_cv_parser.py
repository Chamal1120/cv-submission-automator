import unittest
from models.cv_parser import parse_cv_pdf, _normalize_text, _get_personal_info, _get_education, _get_qualifications, _get_projects


class TestCVParser(unittest.TestCase):

    def test_normalize_text(self):
        input_text = "Test\r\nText  with  extra  spaces"
        expected_output = "Test Text with extra spaces"
        self.assertEqual(_normalize_text(input_text), expected_output)

    def test_get_personal_info(self):
        test_text = "John Doe | john.doe@example.com\n+94 123 456 789"
        result = _get_personal_info(test_text)
        self.assertEqual(result['name'], "John Doe")
        self.assertEqual(result['email'], "john.doe@example.com")
        self.assertEqual(result['phone'], "+94 123 456 789")

    def test_get_education(self):
        test_text = """
        Education:
        Bachelor of Science, University of Test 2015-2019
        Master of Arts, Test College 2020-2022
        Qualifications:
        """
        result = _get_education(test_text)
        self.assertEqual(len(result), 2)
        self.assertIn("Bachelor of Science, University of Test 2015-2019", result)
        self.assertIn("Master of Arts, Test College 2020-2022", result)

    def test_get_qualifications(self):
        test_text = """
        Qualifications:
        Certified Python Developer, 2020
        Certified Solutions Architect, 2021

        Projects:
        """
        result = _get_qualifications(test_text)
        self.assertEqual(len(result), 2)
        self.assertIn("Certified Python Developer, 2020", result)
        self.assertIn("Certified Solutions Architect, 2021", result)

    def test_get_projects(self):
        test_text = """
        Projects:
        Developed a machine learning model for image recognition.
        Created a web application using Django and React.
        """
        result = _get_projects(test_text)
        self.assertEqual(len(result), 2)
        self.assertIn("Developed a machine learning model for image recognition.", result)
        self.assertIn("Created a web application using Django and React.", result)

    def test_parse_cv_pdf(self):
        test_text = """John Doe | john.doe@example.com
        +94 123 456 789

        Education:
        Bachelor of Science, University of Test 2015-2019

        Qualifications:
        Certified Python Developer, 2020

        Projects:
        Developed a machine learning model for image recognition."""

        result = parse_cv_pdf(test_text, "test_file_path")

        self.assertEqual(result['personal_info']['name'], "John Doe")
        self.assertEqual(result['personal_info']['email'], "john.doe@example.com")
        self.assertEqual(result['education'][0], "Bachelor of Science, University of Test 2015-2019")
        self.assertEqual(result['qualifications'][0], "Certified Python Developer, 2020")
        self.assertEqual(result['projects'][0], "Developed a machine learning model for image recognition.")
        self.assertEqual(result['cv_public_link'], "test_file_path")


