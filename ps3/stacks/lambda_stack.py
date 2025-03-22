from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration,
    aws_s3 as s3,
    aws_s3_notifications as s3n
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, table, bucket_arn, **kwargs):
        super().__init__(scope, id, **kwargs)

        bucket = s3.Bucket.from_bucket_arn(
            self,
            "ImportedBucket",
            bucket_arn
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
                "BUCKET_ARN": bucket_arn
            }
        )
        table.grant_write_data(self.size_tracking_lambda)

        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.size_tracking_lambda)
        )
        bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.LambdaDestination(self.size_tracking_lambda)
        )
        self.size_tracking_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:*"],
                resources=[bucket_arn, f"{bucket_arn}/*"]
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
                "BUCKET_NAME": "test-bucket-ps3-zz"
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
                resources=[f"{bucket_arn}/*"]  # Allows PutObject on any file inside the bucket
            )
        )

