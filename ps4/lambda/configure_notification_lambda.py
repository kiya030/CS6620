import json
import boto3
import cfnresponse  # Make sure to include this in your zip

def lambda_handler(event, context):
    print("Event:", json.dumps(event))
    s3 = boto3.client("s3")
    
    try:
        props = event['ResourceProperties']
        bucket = props['BucketName']
        topic_arn = props['SnsTopicArn']

        config = {
            "TopicConfigurations": [
                {
                    "TopicArn": topic_arn,
                    "Events": ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
                }
            ]
        }

        if event["RequestType"] in ["Create", "Update"]:
            s3.put_bucket_notification_configuration(
                Bucket=bucket,
                NotificationConfiguration=config,
                SkipDestinationValidation=True  # ⛔ don't try to verify permissions
            )

        elif event["RequestType"] == "Delete":
            s3.put_bucket_notification_configuration(
                Bucket=bucket,
                NotificationConfiguration={}  # remove all notifications
            )

        cfnresponse.send(event, context, cfnresponse.SUCCESS, {})
    
    except Exception as e:
        print("Error:", str(e))
        cfnresponse.send(event, context, cfnresponse.FAILED, {"Message": str(e)})
