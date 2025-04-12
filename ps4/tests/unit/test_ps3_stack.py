import aws_cdk as core
import aws_cdk.assertions as assertions

from ps3.ps3_stack import Ps3Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in ps3/ps3_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Ps3Stack(app, "ps3")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
