import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
BUCKET_NAME = "cv-parser-lambda-20250307112938506500000001"


def lambda_handler(event, context):
    try:
        # Parse the POST body
        body = json.loads(event.get("body", "{}"))
        file_name = body.get("fileName")

        # Check if fileName is provided
        if not file_name:
            logger.error("Missing required parameter: fileName")
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing required parameter: fileName"})
            }

        presigned_url = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": BUCKET_NAME, "Key": file_name, "ContentType": "application/pdf"},
            ExpiresIn=300  # 5 minutes
        )
        logger.info(f"Generated pre-signed URL for {file_name}")
        return {
            "statusCode": 200,
            "body": json.dumps({"url": presigned_url}),
            "headers": {"Content-Type": "application/json"}
        }
    except Exception as e:
        logger.error(f"Error generating URL: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
