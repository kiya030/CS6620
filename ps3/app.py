from aws_cdk import App
from stacks.dynamodb_stack import DynamoDBStack
from stacks.s3_stack import S3Stack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import APIStack

app = App()

# 1) Create the table & bucket
dynamodb_stack = DynamoDBStack(app, "DynamoDBStack")
s3_stack = S3Stack(app, "S3Stack")

# 2) Create the Lambdas for size tracking & plotting
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    table=dynamodb_stack.table,
    bucket_arn=s3_stack.bucket_arn
)

# 3) Create the API and the Driver Lambda
#    This references the plotting lambda from LambdaStack
api_stack = APIStack(
    app,
    "APIStack",
    plotting_lambda=lambda_stack.plotting_lambda,
    bucket_arn=s3_stack.bucket_arn,
    table=dynamodb_stack.table
)

app.synth()
