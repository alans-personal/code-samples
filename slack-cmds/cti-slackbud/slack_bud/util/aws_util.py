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

# DEPRECATED - Call AWS Account Info service
ENVIRONMENTS = {
    'adeng-admin': '123456789012',  # dataxu-admin
    'adeng-ae': '123456789012',  # dataxu-ae
    'adeng-prod': '123456789012', #dataxu-prod
    'adeng-rd': '123456789012', #dataxu-rd
    'adeng-sandbox': '123456789012', #dataxu-sandbox
    'adeng-shared': '123456789012',  # dataxu-shared
    'apps-prod': '123456789012',
    'apps-qa': '123456789012',
    'apps-stg': '123456789012',
    'aws-tools':  '123456789012',
    'bar':  '123456789012',  # build and release
    'cti':  '123456789012',
    'data-sci': '123456789012',
    'dea':  '123456789012',
    'delta-ml': '123456789012',
    'ent-eng-prod': '123456789012',
    'ent-eng-qa': '123456789012',
    'ent-eng-stg': '123456789012',
    'header-bidding': '123456789012',
    'it':  '123456789012',
    'mobile':  '123456789012',
    'mobile-dev': '123456789012',
    'msc-dev': '123456789012',
    'msc-prod': '123456789012',
    'net-eng':  '123456789012',
    'npi': '123456789012',
    'npi-audio': '123456789012',
    'pay-prod': '123456789012',
    'pay-qa': '123456789012',
    'pay-stg': '123456789012',
    'player-prod':  '123456789012',
    'player-stg':  '123456789012',
    'prog-ops': '123456789012',
    'sr-dev': '123456789012',
    'sr-infra': '123456789012',
    'sr-prod': '123456789012',
    'sr-qa': '123456789012',
    'trust':  '123456789012',
    'trust-prod': '123456789012',
    'unity-prod': '123456789012',
    'ux-eng': '123456789012',
    'web': '123456789012',
    'web-ads': '123456789012',
    'web-shop': '123456789012'
}

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
    if region:
        some_aws_client = boto3.client(
            name,
            aws_access_key_id=session['Credentials']['AccessKeyId'],
            aws_secret_access_key=session['Credentials']['SecretAccessKey'],
            aws_session_token=session['Credentials']['SessionToken'],
            region_name=region
        )
    else:
        some_aws_client = boto3.client(
            name,
            aws_access_key_id=session['Credentials']['AccessKeyId'],
            aws_secret_access_key=session['Credentials']['SecretAccessKey'],
            aws_session_token=session['Credentials']['SessionToken']
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


def get_route53_client(session):
    """Get a route53 client from a session"""
    return get_boto3_client_by_name('route53', session, '')


def get_elb_client(session, region):
    """Get a elb client from a session"""
    return get_boto3_client_by_name('elbv2', session, region)


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


def create_session(env):
    """Get a session from the environment assume roles."""
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::%s:role/SlackBudRole' % ENVIRONMENTS[env],
        RoleSessionName='SlackBudRole')
    return session


def get_prop_table_time_format():
    """Get timestamp in format used in prop dynamo tables.

    Example: January 19, 2018 - 09:55:48
    """
    time = pendulum.now('US/Pacific').strftime("%B %d, %Y - %H:%M:%S")
    return time


def get_dynamo_backup_name_time_format():
    """Get timestamp in format for dynamo table backups.
    The name is restricted to regular expression pattern: [a-zA-Z0-9_.-]+

    Will be in this format: 2018-jan-19-0955
    """
    time = pendulum.now('US/Pacific').strftime("%Y-%b-%d-%H%M")
    return time


def get_build_info_time_format():
    """Get timestamp in format for dynamo table builds.
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


def get_ssm_parameter(param_name):
    """
    Returns the value of the named SSM parameter
    :param param_name: name of the parameter in SSM to get
    :return: ssm_parameter_value
    """
    ssm_client = boto3.client('ssm')
    try:
        print('ssm_parameter_value = ssm_client.get_parameter({})'.format(param_name))
        ssm_parameter_value = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
        print('finished ssm_client.get_parameter')
    except ssm_client.exceptions.ParameterNotFound as e:
        print('no ssm parameter found named: {}'.format(param_name))
        print(e)
        return 'none'

    return ssm_parameter_value['Parameter']['Value']
