from datetime import datetime, timezone
import boto3
import pypdf
import requests
import json
import logging
from io import BytesIO
from models.cv_parser import parse_cv_pdf
from utils.mail_service import send_review_email
from utils.update_sheet import (
    get_google_sheets_service,
    get_spreadsheet,
    append_cv_details
)

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initiate s3 client
s3_client = boto3.client("s3")


# Webhook endpoint
WEBHOOK_URL = "https://rnd-assignment.automations-3d6.workers.dev/"
# My Candidate email for assignment verification
CANDIDATE_EMAIL = "chamal.randika.mcr@gmail.com"


def lambda_handler(event, context):
    """AWS Lambda handler to process the CV PDF from an S3 trigger.

    Args:
        event (dict): The event data from S3 (e.g., bucket and key).
        context (object): Lambda context object (unused here).

    Returns:
        dict: Parsed CV data or error response.
    """
    try:
        # Extract S3 bucket and key from event
        s3_record = event["Records"][0]["s3"]
        bucket = s3_record["bucket"]["name"]
        key = s3_record["object"]["key"]
        logger.info(f"Processing S3 object: s3://{bucket}/{key}")

        # Validate file extension
        if not key.lower().endswith(".pdf"):
            logger.error("File is not a PDF")
            return {"statusCode": 400, "body": {"error": "File must be in .pdf format"}}

        # Download the PDF from S3 to memory
        response = s3_client.get_object(Bucket=bucket, Key=key)
        pdf_file = BytesIO(response["Body"].read())
        logger.info("Downloaded PDF from S3")

        # Read PDF content
        reader = pypdf.PdfReader(pdf_file)
        if len(reader.pages) > 1:
            logger.error("PDF has more than one page")
            return {
                "statusCode": 400,
                "body": {"error": "PDF must be a single page only"},
            }
        pdf_text = reader.pages[0].extract_text() or ""
        logger.info("Extracted PDF text successfully")

        # Format s3 url and parse CV data
        public_url = f"https://{bucket}.s3.amazonaws.com/{key}"
        cv_data = parse_cv_pdf(pdf_text, public_url)
        candidate_email = cv_data.get("personal_info", {}).get("email")
        logger.info(f"Parsed CV data: {json.dumps(cv_data)}")

        # Initialize Google Sheets service
        sheets_service = get_google_sheets_service()

        # Get or create the Google Sheets file
        spreadsheet_id = get_spreadsheet(sheets_service)

        # Append the CV data to the sheet
        append_cv_details(sheets_service, spreadsheet_id, cv_data)

        webhook_payload = {
            "cv_data": cv_data,
            "metadata": {
                "applicant_name": cv_data["personal_info"]["name"] or "Unknown",
                "email": cv_data["personal_info"]["email"] or "unkown@email.com",
                "status": "prod",
                "cv_processed": True,
                "processed_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }
        logger.info(f"Webhook payload: {json.dumps(webhook_payload)}")

        # Send webhook request
        headers = {
            "X-Candidate-Email": CANDIDATE_EMAIL,
            "Content-Type": "application/json",
        }
        response = requests.post(
            WEBHOOK_URL, headers=headers, data=json.dumps(webhook_payload)
        )
        response.raise_for_status()
        logger.info(f"Webhook sent successfully. Response: {response.status_code} - {response.text}")

        # Send review email if email is present and valid
        candidate_email = cv_data["personal_info"]["email"]
        if candidate_email and "@" in candidate_email:
            send_review_email(candidate_email)
        else:
            logger.info("No valid email found; skipping follow up email")

        logger.info("CV processing completed successfully")
        return {"statusCode": 200, "body": cv_data}

    except requests.RequestException as re:

        # Log webhook failure but don't fail the lambda
        print(f"webhook failed: {str(re)}")
        logger.error(f"Webhook failed: {str(re)}")
        return {
            "statusCode": 200,
            "body": (
                cv_data
                if "cv_data" in locals()
                else {"errors": "Processed but webhook failed"}
            ),
        }

    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {"statusCode": 500, "body": {"error": str(e)}}

