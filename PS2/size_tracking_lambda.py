import boto3
import json
import time
from datetime import datetime

# AWS Clients
s3_client = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

# DynamoDB Table Name
TABLE_NAME = "S3-object-size-history"

def calculate_bucket_size(bucket_name):
    """
    Calculate total size and object count of all objects in the given S3 bucket.
    """
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    object_list = response.get("Contents", [])

    total_size = sum(obj["Size"] for obj in object_list)
    object_count = len(object_list)

    return total_size, object_count

def lambda_handler(event, context):
    """
    AWS Lambda function triggered by S3 events (PUT, POST, DELETE).
    Computes total bucket size and writes to DynamoDB.
    """
    print(f"Received event: {json.dumps(event)}")

    # Extract bucket name from event
    try:
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    except KeyError:
        print("Error: Unable to retrieve bucket name from event.")
        return {"statusCode": 400, "body": "Invalid event structure"}

    # Compute bucket size
    total_size, object_count = calculate_bucket_size(bucket_name)
    timestamp = int(time.time())  # Unix timestamp

    # Store data in DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    response = table.put_item(
        Item={
            "bucket_name": bucket_name,
            "timestamp": timestamp,
            "total_size": total_size,
            "object_count": object_count
        }
    )


    print(f"DynamoDB Response: {response}")  # <-- Add this to debug

    print(f"Updated DynamoDB: {bucket_name} - Size: {total_size} bytes, Objects: {object_count}")
    
    return {"statusCode": 200, "body": "Bucket size updated"}
