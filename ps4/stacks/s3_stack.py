from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_iam as iam
)
from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, id: str, sns_topic, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Define the S3 Bucket
        self.bucket = s3.Bucket(
            self, "TestBucket",
            bucket_name="test-bucket-ps4-zz",
            removal_policy=RemovalPolicy.DESTROY
        )

        # Allow S3 to publish to the SNS topic
        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                principals=[iam.ServicePrincipal("s3.amazonaws.com")],
                resources=[sns_topic.topic_arn],
                conditions={
                    "ArnLike": {
                        "aws:SourceArn": self.bucket.bucket_arn
                    }
                }
            )
        )

        # # Add SNS notification for object created
        # self.bucket.add_event_notification(
        #     s3.EventType.OBJECT_CREATED,
        #     s3n.SnsDestination(sns_topic)
        # )

        # # Add SNS notification for object removed
        # self.bucket.add_event_notification(
        #     s3.EventType.OBJECT_REMOVED,
        #     s3n.SnsDestination(sns_topic)
        # )

        # Expose bucket and its ARN if needed in other stacks
        self.bucket_arn = self.bucket.bucket_arn
