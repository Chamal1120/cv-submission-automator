import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    pass

# Initialize logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER_EMAIL = "chamal.randika.mcr@gmail.com"

if not SENDGRID_API_KEY:
    raise ValueError("SENDGRID_API_KEY environment variable is not set")


def send_review_email(candidate_email):
    """Function to send a response email using SendGrid.

    Args:
        candidate_email (str): The candidate's email address where the mail will be sent.

    Raises:
        Exception: If the email sending fails.
    """
    subject = "Your CV is Under Review"
    body_text = (
        "Dear Candidate,\n\n"
        "Thank you for submitting your CV. It is currently under review by our team. "
        "We will contact you soon with next steps.\n\n"
        "Best regards,\nRecruitment Team"
    )

    message = Mail(
        from_email=SENDER_EMAIL,
        to_emails=candidate_email,
        subject=subject,
        plain_text_content=body_text,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        logger.info(
            f"Email sent to {candidate_email}: Status Code {response.status_code}"
        )

        if response.status_code != 202:
            raise Exception(
                f"Failed to send email. Status Code: {response.status_code}"
            )

    except Exception as e:
        logger.error(f"Failed to send email to {candidate_email}: {str(e)}")
        raise Exception(f"Error sending email: {str(e)}")
