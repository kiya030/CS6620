from aws_cdk import Stack, aws_dynamodb as dynamodb
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Let CloudFormation generate an actual table name
        self.table = dynamodb.Table(
            self, "S3ObjectSizeHistory",
            partition_key=dynamodb.Attribute(
                name="bucket_name", 
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", 
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

