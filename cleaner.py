import os
import boto3
import time
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")
lambda_client = boto3.client("lambda")

DST_BUCKET = os.getenv("DST_BUCKET")
TABLE_NAME = os.getenv("TABLE_NAME")
SELF_INVOKE_ARN = os.getenv("SELF_INVOKE_ARN")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    now = int(datetime.utcnow().timestamp())

    # Query DynamoDB for disowned copies older than 10 seconds
    response = table.query(
        IndexName="DisownedIndex",
        KeyConditionExpression="IsDisowned = :d AND DeleteTime <= :t",
        ExpressionAttributeValues={":d": "true", ":t": now - 10}
    )

    for item in response.get("Items", []):
        s3.delete_object(Bucket=DST_BUCKET, Key=item["CopyObj"])
        table.delete_item(
            Key={"OriginalObj": item["OriginalObj"], "CopyTimestamp": item["CopyTimestamp"]}
        )

