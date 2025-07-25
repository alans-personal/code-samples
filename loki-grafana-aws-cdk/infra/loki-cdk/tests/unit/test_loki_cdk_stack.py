import aws_cdk as core
import aws_cdk.assertions as assertions

from loki_cdk.loki_cdk_stack import LokiCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in loki_cdk/loki_cdk_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LokiCdkStack(app, "loki-cdk")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
