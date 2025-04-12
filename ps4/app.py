from aws_cdk import App
from stacks.dynamodb_stack import DynamoDBStack
from stacks.s3_stack import S3Stack
from stacks.lambda_stack import LambdaStack
from stacks.api_stack import APIStack
from stacks.messaging_stack import MessagingStack
from stacks.monitoring_stack import MonitoringStack 
from stacks.notification_config_stack import NotificationConfigStack

app = App()

# 1) Messaging first (SNS + SQS)
messaging_stack = MessagingStack(app, "MessagingStack")

# 2) DynamoDB
dynamodb_stack = DynamoDBStack(app, "DynamoDBStack")

# 3) S3 bucket with SNS notification
s3_stack = S3Stack(
    app,
    "S3Stack",
    sns_topic=messaging_stack.s3_event_topic
)


# 3.5) Configure S3 → SNS notifications via custom Lambda resource
notification_stack = NotificationConfigStack(
    app,
    "NotificationConfigStack",
    bucket=s3_stack.bucket,
    sns_topic=messaging_stack.s3_event_topic
)

# 4) Lambdas (including size tracking, logging, plotting, cleaner)
lambda_stack = LambdaStack(
    app,
    "LambdaStack",
    table=dynamodb_stack.table,
    bucket_arn=s3_stack.bucket_arn,
    size_queue=messaging_stack.size_tracking_queue,
    log_queue=messaging_stack.logging_queue,
    topic_arn=messaging_stack.s3_event_topic.topic_arn
)


# 5) API Gateway + Driver Lambda
api_stack = APIStack(
    app,
    "APIStack",
    plotting_lambda=lambda_stack.plotting_lambda,
    bucket=s3_stack.bucket,
    table=dynamodb_stack.table
)

# 6) Create CloudWatch metric filter and alarm
monitoring_stack = MonitoringStack(
    app,
    "MonitoringStack",
    # logging_lambda=lambda_stack.logging_lambda,
    logging_log_group_name=f"/aws/lambda/{lambda_stack.logging_lambda.function_name}",
    # cleaner_lambda=lambda_stack.cleaner_lambda
    cleaner_lambda_name=lambda_stack.cleaner_lambda.function_name
)

app.synth()
