from aws_cdk import (
    Stack,
    Duration,
    aws_logs as logs,
    aws_cloudwatch as cloudwatch,
)
from aws_cdk.aws_cloudwatch_actions import LambdaAction
from aws_cdk.aws_lambda import Function
from constructs import Construct

class MonitoringStack(Stack):
    def __init__(self, scope: Construct, id: str, logging_log_group_name: str, cleaner_lambda_name: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 1. Import log group from Logging Lambda
        # log_group = logs.LogGroup.from_log_group_name(
        #     self,
        #     "ImportedLoggingLogGroup",
        #     f"/aws/lambda/{logging_lambda.function_name}"
        # )

        log_group = logs.LogGroup.from_log_group_name(
            self,
            "ImportedLoggingLogGroup",
            logging_log_group_name
        )


        # 2. Define metric filter to extract "size_delta"
        metric_filter = logs.MetricFilter(
            self,
            "SizeDeltaMetricFilter",
            log_group=log_group,
            metric_namespace="Assignment4App",
            metric_name="TotalObjectSize",
            filter_pattern=logs.FilterPattern.exists("$.size_delta"),
            metric_value="$.size_delta",
        )

        # 3. Construct metric with Sum statistic over 5-minute window
        metric = metric_filter.metric(
            statistic="Sum",
            period=Duration.seconds(10)
        )

        # 4. Create CloudWatch alarm that fires when sum > 20
        alarm = cloudwatch.Alarm(
            self,
            "SizeAlarm",
            metric=metric,
            threshold=20,
            evaluation_periods=1,
            alarm_description="Triggers when total size_delta exceeds 20 bytes"
        )

        # 5. Trigger Cleaner Lambda when alarm fires
        cleaner = Function.from_function_name(self, "ImportedCleanerFn", cleaner_lambda_name)
        alarm.add_alarm_action(LambdaAction(cleaner))
