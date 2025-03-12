import unittest
from unittest.mock import patch
from utils.mail_service_sg import send_review_email


class TestSendReviewEmail(unittest.TestCase):

    @patch("utils.mail_service_sg.SendGridAPIClient")
    def test_send_review_email_success(self, MockSendGridAPIClient):

        # Mock SendGrid client and its response
        mock_client = MockSendGridAPIClient.return_value
        mock_client.send.return_value.status_code = 202

        try:
            send_review_email("test@example.com")
        except Exception as e:
            self.fail(f"send_review_email raised an exception unexpectedly: {e}")

        # Assert that send was called
        mock_client.send.assert_called_once()

    @patch("utils.mail_service_sg.SendGridAPIClient")
    def test_send_review_email_failure(self, MockSendGridAPIClient):
        # Mock SendGrid client to simulate a failure
        mock_client = MockSendGridAPIClient.return_value
        mock_client.send.return_value.status_code = 400

        with self.assertRaises(Exception) as context:
            send_review_email("test@example.com")

        self.assertIn("Failed to send email", str(context.exception))


if __name__ == "__main__":
    unittest.main()
