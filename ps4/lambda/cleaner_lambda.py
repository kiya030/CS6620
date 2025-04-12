import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["BUCKET_NAME"]

def lambda_handler(event, context):
    try:
        logger.info(f"Cleaner triggered by CloudWatch alarm. Bucket: {BUCKET_NAME}")

        # 1. List all objects in the bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if "Contents" not in response or not response["Contents"]:
            logger.info("No objects in bucket.")
            return

        objects = response["Contents"]

        # 2. Find the largest file
        largest = max(objects, key=lambda obj: obj["Size"])
        key = largest["Key"]
        size = largest["Size"]

        logger.info(f"Deleting largest file: {key} ({size} bytes)")

        # 3. Delete it
        s3.delete_object(Bucket=BUCKET_NAME, Key=key)
        logger.info(f"Deleted: {key}")

    except Exception as e:
        logger.error(f"Error in cleaner lambda: {e}")
