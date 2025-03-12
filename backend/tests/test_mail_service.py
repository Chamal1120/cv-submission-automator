import unittest
from unittest.mock import patch
from botocore.exceptions import ClientError
from utils.mail_service import send_review_email


class TestMailService(unittest.TestCase):

    @patch('utils.mail_service.ses_client')
    def test_send_review_email_success(self, mock_ses):
        mock_ses.send_email.return_value = {'MessageId': 'test_message_id'}

        send_review_email('test@example.com')

        mock_ses.send_email.assert_called_once()
        args, kwargs = mock_ses.send_email.call_args
        self.assertEqual(kwargs['Destination']['ToAddresses'], ['test@example.com'])

    @patch('utils.mail_service.ses_client')
    def test_send_review_email_ses_error(self, mock_ses):
        mock_ses.send_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email address is not verified'}},
            'SendEmail'
        )

        with self.assertRaises(ClientError):
            send_review_email('unverified@example.com')

