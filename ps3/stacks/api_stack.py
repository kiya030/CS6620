from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as _lambda,
    aws_iam as iam,
    Duration
)
from constructs import Construct

class APIStack(Stack):
    def __init__(self, scope: Construct, id: str, plotting_lambda, bucket_arn, table, **kwargs):
        super().__init__(scope, id, **kwargs)

        # ------------------------------------------------
        # 1) Create API Gateway for the Plotting Lambda
        # ------------------------------------------------
        self.api = apigateway.RestApi(
            self,
            "PlottingAPI",
            rest_api_name="PlottingAPI",
            description="API to trigger the Plotting Lambda"
        )

        # ✅ Explicitly add a /plot GET route
        plot_resource = self.api.root.add_resource("plot")

        plot_resource.add_method(
            "GET",  # <-- This explicitly enables GET requests
            apigateway.LambdaIntegration(plotting_lambda),
            authorization_type=apigateway.AuthorizationType.NONE  # Open API for now
        )

        # ------------------------------------------------
        # 2) Create the Driver Lambda INSIDE APIStack
        #    so we can pass self.api.url without cyclic dependencies
        # ------------------------------------------------
        self.driver_lambda = _lambda.Function(
            self,
            "DriverLambda",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="driver_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(60),
            environment={
                "BUCKET_NAME": "test-bucket-ps3-zz",
                "PLOTTING_LAMBDA_API": f"{self.api.url}/plot"  # <-- Updated URL
            }
        )

        # Attach requests layer
        requests_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "Klayers-p311-requests",
            "arn:aws:lambda:us-west-1:770693421928:layer:Klayers-p311-requests:15"
        )
        self.driver_lambda.add_layers(requests_layer)

        # Grant wide S3 & API access to the driver lambda
        self.driver_lambda.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        self.driver_lambda.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonAPIGatewayInvokeFullAccess")
        )
