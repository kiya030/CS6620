import json
import logging
import os
import boto3
from datetime import datetime, timedelta

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logs = boto3.client("logs")

LOG_GROUP = f"/aws/lambda/{os.environ['AWS_LAMBDA_FUNCTION_NAME']}"

def get_previous_size(object_name):
    try:
        now = datetime.utcnow()
        start_time = int((now - timedelta(days=1)).timestamp() * 1000)
        end_time = int(now.timestamp() * 1000)

        response = logs.filter_log_events(
            logGroupName=LOG_GROUP,
            startTime=start_time,
            endTime=end_time,
            filterPattern=f'"{object_name}" "size_delta"',
            limit=50
        )

        for event in response.get("events", []):
            try:
                data = json.loads(event["message"])
                if data.get("object_name") == object_name and data.get("size_delta", 0) > 0:
                    return data["size_delta"]
            except Exception:
                continue
    except Exception as e:
        logger.error(f"Log lookup failed: {e}")
    return -1  # fallback

def lambda_handler(event, context):
    for record in event["Records"]:
        try:
            sns_message = json.loads(record["body"])
            s3_event = json.loads(sns_message["Message"])

            for s3_record in s3_event["Records"]:
                event_name = s3_record["eventName"]
                object_key = s3_record["s3"]["object"]["key"]
                object_size = s3_record["s3"]["object"]["size"]

                if event_name.startswith("ObjectCreated"):
                    log_data = {
                        "object_name": object_key,
                        "size_delta": object_size
                    }

                elif event_name.startswith("ObjectRemoved"):
                    # prev_size = get_previous_size(object_key)
                    log_data = {
                        "object_name": object_key,
                        "size_delta": -object_size
                    }
                else:
                    continue

                logger.info(json.dumps(log_data))

        except Exception as e:
            logger.info(record)
            logger.error(f"Failed to parse record: {e}")
