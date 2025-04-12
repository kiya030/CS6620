import aws_cdk as cdk
from constructs import Construct
from aws_cdk import aws_s3 as s3, aws_dynamodb as dynamodb, aws_lambda as _lambda, aws_s3_notifications as s3_notifications

class StorageReplicatorStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Create S3 Buckets
        self.src_bucket = s3.Bucket(self, "BucketSrc", removal_policy=cdk.RemovalPolicy.DESTROY)
        self.dst_bucket = s3.Bucket(self, "BucketDst", removal_policy=cdk.RemovalPolicy.DESTROY)

        # Create DynamoDB Table
        self.table = dynamodb.Table(
            self, "TableT",
            table_name="TableT",
            partition_key=dynamodb.Attribute(name="OriginalObj", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="CopyTimestamp", type=dynamodb.AttributeType.NUMBER),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Add Global Secondary Index
        self.table.add_global_secondary_index(
            index_name="DisownedIndex",
            partition_key=dynamodb.Attribute(name="IsDisowned", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="DeleteTime", type=dynamodb.AttributeType.NUMBER)
        )

        # Create Replicator Lambda
        self.replicator_fn = _lambda.Function(
            self, "ReplicatorLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="replicator.handler",
            code=_lambda.Code.from_asset("lambda/"),
            environment={
                "SRC_BUCKET": self.src_bucket.bucket_name,
                "DST_BUCKET": self.dst_bucket.bucket_name,
                "TABLE_NAME": "TableT",
            },
        )

        # Configure S3 event notifications **inside the same stack**
        self.src_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(self.replicator_fn)
        )

        self.src_bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3_notifications.LambdaDestination(self.replicator_fn)
        )

        # Grant permissions
        self.src_bucket.grant_read(self.replicator_fn)
        self.dst_bucket.grant_write(self.replicator_fn)
        self.table.grant_full_access(self.replicator_fn)

