from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_sns as sns, 
    aws_lambda_event_sources as sources
)

from aws_cdk.aws_s3_notifications import SnsDestination

from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, table, bucket_arn, size_queue, log_queue, topic_arn, **kwargs):
        super().__init__(scope, id, **kwargs)

        # self.topic = sns.Topic(self, "MyTopic")

        sns_topic = sns.Topic.from_topic_arn(self, "ImportedTopic", topic_arn)


        # 🔐 Allow S3 to publish to the topic (this is the missing part)
        sns_topic.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["sns:Publish"],
                principals=[iam.ServicePrincipal("s3.amazonaws.com")],
                resources=[sns_topic.topic_arn],
                conditions={
                    "ArnLike": {
                        "aws:SourceArn": bucket_arn
                    }
                }
            )
        )

        bucket = s3.Bucket.from_bucket_arn(self,'ImportedBucket', bucket_arn)

        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SnsDestination(sns_topic)
        )

        # bucket.add_event_notification(
        #     s3.EventType.OBJECT_REMOVED,
        #     s3n.SnsDestination(self.topic)
        # )
        bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.SnsDestination(sns_topic),
            s3.NotificationKeyFilter(prefix="removed/")
        )

        # Size-Tracking Lambda
        self.size_tracking_lambda = _lambda.Function(
            self,
            "SizeTrackingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="size_tracking_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "DYNAMODB_TABLE_NAME": table.table_name,
                "BUCKET_ARN": bucket.bucket_arn
            }
        )

        size_queue.grant_consume_messages(self.size_tracking_lambda)
        self.size_tracking_lambda.add_event_source(sources.SqsEventSource(size_queue))

        # Cleaner Lambda
        self.cleaner_lambda = _lambda.Function(
            self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="cleaner_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "BUCKET_NAME": "test-bucket-ps4-zz"
            }
        )
        
        # s3:ListBucket applies to bucket ARN only
        self.cleaner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:ListBucket"],
                resources=[bucket.bucket_arn]
            )
        )
        # s3:DeleteObject applies to object ARNs
        self.cleaner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:DeleteObject"],
                resources=[f"{bucket.bucket_arn}/*"]
            )
        )

        self.logging_lambda = _lambda.Function(
            self, "LoggingLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="logging_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
        )

        log_queue.grant_consume_messages(self.logging_lambda)
        self.logging_lambda.add_event_source(sources.SqsEventSource(log_queue))

        self.logging_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["logs:FilterLogEvents"],
                resources=["*"]  # Optionally restrict to your own log group
            )
        )

        table.grant_write_data(self.size_tracking_lambda)

        self.size_tracking_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=[bucket.bucket_arn, f"{bucket.bucket_arn}/*"]
            )
        )

        # Plotting Lambda
        matplotlib_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "Klayers-p311-matplotlib",
            "arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p311-matplotlib:15"
        )
        numpy_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "Klayers-p311-numpy",
            "arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p311-numpy:14"
        )

        self.plotting_lambda = _lambda.Function(
            self,
            "PlottingLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="plotting_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            environment={
                "DYNAMODB_TABLE_NAME": table.table_name,
                "BUCKET_NAME": "test-bucket-ps4-zz"
            },
            layers=[matplotlib_layer, numpy_layer]
        )
        table.grant_read_data(self.plotting_lambda)
        self.plotting_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:Query"],
                resources=[table.table_arn]
            )
        )

        self.plotting_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObject"],
                resources=[f"{bucket.bucket_arn}/*"]  # Allows PutObject on any file inside the bucket
            )
        )

