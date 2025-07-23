"""Utility class for getting AWS resources."""
from __future__ import print_function

import json
import boto3
import pendulum

AWS_REGIONS = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'ca-central-1',
    'eu-west-1',
    'eu-west-2',
    'eu-central-1',
    'sa-east-1',
    'ap-south-1',
    'ap-northeast-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2']

# TODO: Replace with actual account IDs
ENVIRONMENTS = {
    "sr-dev": '123456789012',
    "sr-qa": '223456789012',
    "sr-prod": '323456789012'}


class CodePipelineStageError(Exception):
    """Raise this exception when you want to fail a stage in code-pipeline"""
    def __init__(self, *args):
        Exception.__init__(self, *args)


def region_is_valid(region):
    """Check if the region is valid."""
    if region not in AWS_REGIONS:
        return False
    return True


def env_is_valid(env):
    """Check if the env is valid."""
    if env not in ENVIRONMENTS:
        return False
    return True


def get_boto3_client_by_name(name, session, region):
    """
    Get a boto3 client by the name string.
    :param name: string like:  ec2, dynamodb, cloudformation, ...
    :param session: session has temp credentials from AWS.
    :param region: AWS region like: us-east-1, us-west-2, etc...
    :return:
    """
    print('Getting boto3 client: {}'.format(name))
    some_aws_client = boto3.client(
        name,
        aws_access_key_id=session['Credentials']['AccessKeyId'],
        aws_secret_access_key=session['Credentials']['SecretAccessKey'],
        aws_session_token=session['Credentials']['SessionToken'],
        region_name=region
    )
    return some_aws_client


def get_boto3_resource_by_name(name, session, region):
    """

    :param name:
    :param session:
    :param region:
    :return:
    """
    print('Getting boto3 resource: {}'.format(name))
    some_aws_resource = boto3.resource(
        name,
        aws_access_key_id=session['Credentials']['AccessKeyId'],
        aws_secret_access_key=session['Credentials']['SecretAccessKey'],
        aws_session_token=session['Credentials']['SessionToken'],
        region_name=region
    )
    return some_aws_resource


def get_dynamo_resource(session, region, client=False):
    """Get a dynamodb client from a session."""
    if not client:
        dynamodb = get_boto3_resource_by_name('dynamodb', session, region)
    else:
        dynamodb = get_boto3_client_by_name('dynamodb', session, region)
    return dynamodb


def get_cloudformation_client(session, region):
    """Get a cloundformation client from a session"""
    return get_boto3_client_by_name('cloudformation', session, region)


def get_s3_client(session, region):
    """
    Get S3 client from boto3
    :param session:
    :param region:
    :return:
    """
    return get_boto3_client_by_name('s3', session, region)


def get_tagging_client(session, region):
    """Get a AWS Tagging client from a session"""
    return get_boto3_client_by_name('resourcegroupstaggingapi', session, region)


def get_ecr_client(session, region):
    """Get a ecr client from a session"""
    return get_boto3_client_by_name('ecr', session, region)


def get_ec2_resource(session, region, client=False):
    """Get a ec2 client from a session."""

    if not client:
        ec2 = get_boto3_resource_by_name('ec2', session, region)
    else:
        ec2 = get_boto3_client_by_name('ec2', session, region)
    return ec2


def get_dynamo_backup_name_time_format():
    """Get timestamp in format for dynamo table backups.
    The name is restricted to regular expression pattern: [a-zA-Z0-9_.-]+

    Will be in this format: 2018-jan-19-0955
    """
    time = pendulum.now('US/Pacific').strftime("%Y-%b-%d-%H%M")
    return time


def get_build_info_time_format():
    """Get timestamp in format for dynamo table backups.
    The name is restricted to regular expression pattern: [a-zA-Z0-9_.-]+

    Will be in this format: 2018-jan-19-0955
    """
    time = pendulum.now('US/Pacific').strftime("%Y%m%d")
    return time


def invoke_remote_lambda(lambda_function_name, payload):
    """
    Invoke a remote lambda and return the response.
    No attempt is made to verify inputs, so this could
    throw an exception from boto3.

    :param lambda_function_name: Name of lambda function like: 'longtask-lambda'
    :param payload: python dictionary.
    :return: boto3 response
    """
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=lambda_function_name,
        InvocationType="Event",
        Payload=json.dumps(dict(payload))
    )
    return response
