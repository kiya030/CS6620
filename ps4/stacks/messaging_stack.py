from aws_cdk import (
    Stack,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as subscriptions
)
from constructs import Construct

class MessagingStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 1. Create SNS Topic
        self.s3_event_topic = sns.Topic(self, "S3EventTopic")

        # 2. Create Two SQS Queues
        self.size_tracking_queue = sqs.Queue(self, "SizeTrackingQueue")
        self.logging_queue = sqs.Queue(self, "LoggingQueue")

        # 3. Subscribe Queues to SNS
        self.s3_event_topic.add_subscription(subscriptions.SqsSubscription(self.size_tracking_queue))
        self.s3_event_topic.add_subscription(subscriptions.SqsSubscription(self.logging_queue))
