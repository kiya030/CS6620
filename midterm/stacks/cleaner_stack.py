import aws_cdk as cdk
from aws_cdk import aws_lambda as _lambda, aws_events as events, aws_events_targets as targets
import aws_cdk.aws_s3 as s3
from constructs import Construct
import aws_cdk.aws_dynamodb as dynamodb

class CleanerStack(cdk.Stack):
    def __init__(self, scope: Construct, id: str, storage, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.cleaner_fn = _lambda.Function(
            self, "CleanerLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="cleaner.handler",
            code=_lambda.Code.from_asset("lambda/"),
            environment={
                "DST_BUCKET": storage.dst_bucket.bucket_name,
                "TABLE_NAME": storage.table.table_name,
            },
        )

        storage.dst_bucket.grant_read_write(self.cleaner_fn)
        storage.table.grant_full_access(self.cleaner_fn)

        events.Rule(
            self, "CleanerSchedule",
            schedule=cdk.aws_events.Schedule.rate(cdk.Duration.minutes(1)),
            targets=[targets.LambdaFunction(self.cleaner_fn)]
        )

