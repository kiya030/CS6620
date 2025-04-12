from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    CustomResource  # ✅ correct location
)
from constructs import Construct

class NotificationConfigStack(Stack):
    def __init__(self, scope: Construct, id: str, bucket, sns_topic, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Lambda function that will configure the S3 bucket notifications
        handler = _lambda.Function(
            self,
            "NotificationConfigurator",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="configure_notification_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            initial_policy=[
                iam.PolicyStatement(
                    actions=["s3:PutBucketNotification"],
                    resources=[bucket.bucket_arn]
                ),
                iam.PolicyStatement(
                    actions=["sns:Publish"],
                    resources=[sns_topic.topic_arn]
                )
            ]
        )

        # Create the custom resource that invokes the lambda at deploy time
        CustomResource(
            self,
            "ConfigureS3ToSNSNotifications",
            service_token=handler.function_arn,
            properties={
                "BucketName": bucket.bucket_name,
                "SnsTopicArn": sns_topic.topic_arn
            }
        )
