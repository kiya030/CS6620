from aws_cdk import Stack, RemovalPolicy, aws_s3 as s3
from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ✅ Define the S3 Bucket
        self.bucket = s3.Bucket(
            self, "TestBucket",
            bucket_name="test-bucket-ps3-zz",
            removal_policy=RemovalPolicy.DESTROY
        )

        # ✅ Expose only the ARN to avoid cyclic dependency
        self.bucket_arn = self.bucket.bucket_arn