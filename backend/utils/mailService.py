import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses_client = boto3.client("ses")

# AWS SES verified email for sending responses
SENDER_EMAIL = "chamal.randika.mcr@gmail.com"


def send_review_email(candidate_email):
    """Function to send a response email.

    Args:
        candidate_email (str): The candidate_email addresss where the mail will be sento
    Raises:
        ClientError: If SES fails (e.g., unverified email, quota exceeded).
        ValueError: If the email address is invalid.
    """
    subject = "Your CV is Under Review"
    body_text = (
        "Dear Candidate,\n\n"
        "Thank you for submitting your CV. It is currently under review by our team. "
        "We will contact you soon with next steps.\n\n"
        "Best regards,\nRecruitment Team"
    )
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [candidate_email]},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": body_text}}
            }
        )
        logger.info(f"Email sent to {candidate_email}: {response['MessageId']}")

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(f"SES ClientError sending email to {candidate_email}: {error_code} - {error_message}")

        # Handle specific SES errors
        if error_code == "MessageRejected":
            if "Email address is not verified" in error_message:
                raise ClientError(
                    e.response,
                    f"Email address not verified: {candidate_email} (SES sandbox restriction)"
                )
            elif "quota" in error_message.lower():
                raise ClientError(e.response, "SES sending quota exceeded")
        elif error_code == "InvalidParameterValue":
            raise ClientError(e.response, f"Invalid email parameter: {candidate_email}")
        elif error_code == "Throttling":
            logger.warning("SES throttling detected, consider retrying")
            raise ClientError(e.response, "SES throttling - temporary failure")

        # Generic SES error
        raise ClientError(e.response, f"Failed to send email to {candidate_email}")

    except Exception as e:
        logger.error(f"Failed to send email to {candidate_email}: {str(e)}")
        raise Exception(f"Unexpected error sending email: {str(e)}")
