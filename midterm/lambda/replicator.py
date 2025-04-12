import os
import json
import boto3
from datetime import datetime

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

SRC_BUCKET = os.getenv("SRC_BUCKET")
DST_BUCKET = os.getenv("DST_BUCKET")
TABLE_NAME = os.getenv("TABLE_NAME")

table = dynamodb.Table(TABLE_NAME)


def handler(event, context):
    for record in event["Records"]:
        event_name = record["eventName"]
        object_key = record["s3"]["object"]["key"]

        if event_name.startswith("ObjectCreated:"):  # PUT event
            handle_put(object_key)
        elif event_name.startswith("ObjectRemoved:"):  # DELETE event
            handle_delete(object_key)


def handle_put(object_key):
    timestamp = int(datetime.utcnow().timestamp())
    copy_key = f"{object_key}_{timestamp}"

    # Copy object to destination bucket
    s3.copy_object(
        Bucket=DST_BUCKET,
        CopySource={"Bucket": SRC_BUCKET, "Key": object_key},
        Key=copy_key
    )

    # Fetch existing copies
    response = table.query(
        KeyConditionExpression="OriginalObj = :obj",
        ExpressionAttributeValues={":obj": object_key}
    )

    copies = sorted(response.get("Items", []), key=lambda x: x["CopyTimestamp"])

    # Delete oldest copy if more than 3 exist
    if len(copies) >= 3:
        oldest = copies[0]
        s3.delete_object(Bucket=DST_BUCKET, Key=oldest["CopyObj"])
        table.delete_item(
            Key={"OriginalObj": object_key, "CopyTimestamp": oldest["CopyTimestamp"]}
        )

    # Store new copy in DynamoDB
    table.put_item(
        Item={
            "OriginalObj": object_key,
            "CopyTimestamp": timestamp,
            "CopyObj": copy_key,
            "IsDisowned": "false"
        }
    )


def handle_delete(object_key):
    response = table.query(
        KeyConditionExpression="OriginalObj = :obj",
        ExpressionAttributeValues={":obj": object_key}
    )

    for item in response.get("Items", []):
        table.update_item(
            Key={"OriginalObj": item["OriginalObj"], "CopyTimestamp": item["CopyTimestamp"]},
            UpdateExpression="SET IsDisowned = :val, DeleteTime = :time",
            ExpressionAttributeValues={":val": "true", ":time": int(datetime.utcnow().timestamp())}
        )

