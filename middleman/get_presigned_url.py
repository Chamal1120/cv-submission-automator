import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]


def lambda_handler(event, context):
    # Define CORS headers for all responses
    headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "https://wyspfmmxrk.execute-api.us-east-1.amazonaws.com/prod/get-presigned-url",
        "Access-Control-Allow-Methods": "POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
    }

    try:
        # Handle OPTIONS preflight directly in Lambda
        if event.get("httpMethod") == "OPTIONS":
            logger.info("Handling OPTIONS preflight request")
            return {
                "statusCode": 200,
                "headers": headers,
                "body": json.dumps({"message": "CORS preflight successful"}),
            }

        # Parse the POST body
        body = json.loads(event.get("body", "{}"))
        file_name = body.get("fileName")

        # Check if fileName is provided
        if not file_name:
            logger.error("Missing required parameter: fileName")
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"error": "Missing required parameter: fileName"}),
            }

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET_NAME,
                "Key": file_name,
                "ContentType": "application/pdf",
            },
            ExpiresIn=300,  # 5 minutes
        )
        logger.info(f"Generated pre-signed URL for {file_name}")
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({"url": presigned_url}),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({"error": "Invalid JSON in request body"}),
        }
    except Exception as e:
        logger.error(f"Error generating URL: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"error": str(e)}),
        }
