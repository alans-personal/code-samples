"""
The entry point for the Refresh JWT Token lambda function.
"""
from __future__ import print_function
import boto3

import botocore.session
import json
import base64
import hvac
from urlparse import urlparse


def handler(event, context):
    """
    Get an update the build number for a service and write to history table
    :param event:
    :param context:
    :return: build number on success or ERROR: ... on failure
    """

    print('event: {}'.format(event))

    try:
        detail_type = event.get('detail-type')
        source = event.get('source')
        print('Event: {}, source: {}'.format(detail_type, source))

        # Refresh the JWT Token
        refresh_jwt_token()

    except Exception as e:
        print('ERROR: {}'.format(e.message))

    return 'Done'


def refresh_jwt_token():
    """
    Call invoke on a specific lambda function. Record errors.
    :return: None
    """
    try:
        # Fetch a new JWT token
        print('Fetching a new JWT token')
        new_jwt_token = fetch('cti-common', 'https://ss.cti.asnyder.com:8443', 'secret/cti/common/jwt')

        # Log last few characters of token to verify.
        log_token_snippet(new_jwt_token)

        # Store in AWS Parameter Store.
        store_in_aws_parameter_store(new_jwt_token)

    except Exception as e:
        print('ERROR: message: {}'.format(e.message))


def log_token_snippet(new_jwt_token):
    """
    Log token snippet
    :param new_jwt_token:
    :return: None
    """
    first_part = new_jwt_token[0:8]
    token_len = len(new_jwt_token)
    last_part = new_jwt_token[-16:]
    print('new jwt token: {}..len({})..{}'.format(first_part, token_len, last_part))


def store_in_aws_parameter_store(new_jwt_token):
    """
    Store this in Parameter Store with name 'slackbud_jwt_token'
    :param new_jwt_token:
    :return: None
    """
    ssm_client = boto3.client('ssm')

    ssm_client.put_parameter(
        Name='slack_bud_jwt_token',
        Value=new_jwt_token,
        Type='SecureString',
        KeyId='alias/aws/ssm',
        Overwrite=True
    )


def headers_to_go_style(headers):
    retval = {}
    for k, v in headers.iteritems():
        retval[k] = [v]
    return retval


def get_vault_netloc(vault_url):
    o = urlparse(vault_url)
    return o.netloc


def generate_vault_request(role_name="", vault_url="https://ss.cti.asnyder.com"):
    session = botocore.session.get_session()
    # if you have credentials from non-default sources, call
    # session.set_credentials here, before calling session.create_client

    # Try to assume role here.
    cti_session = create_cti_common_aws_iam_role_session()

    session.set_credentials(
        access_key=cti_session['Credentials']['AccessKeyId'],
        secret_key=cti_session['Credentials']['SecretAccessKey'],
        token=cti_session['Credentials']['SessionToken']
    )

    client = session.create_client('sts', region_name='us-east-1')
    endpoint = client._endpoint
    operation_model = client._service_model.operation_model('GetCallerIdentity')
    request_dict = client._convert_to_request_dict({}, operation_model)

    awsIamServerId = get_vault_netloc(vault_url)
    request_dict['headers']['X-Vault-AWS-IAM-Server-ID'] = awsIamServerId

    request = endpoint.create_request(request_dict, operation_model)

    # It's now signed...
    return {
        'iam_http_request_method': request.method,
        'iam_request_url': base64.b64encode(request.url),
        'iam_request_body': base64.b64encode(request.body),
        'iam_request_headers': base64.b64encode(json.dumps(headers_to_go_style(dict(request.headers)))),
    # It's a CaseInsensitiveDict, which is not JSON-serializable
        'role': role_name,
    }


def fetch(vault_role, vault_url, secret):
    params = generate_vault_request(vault_role, vault_url)
    client = hvac.Client(url=vault_url)
    result = client.auth('v1/auth/aws/login', json=params)
    jwt_token_data = client.read(secret)
    print('got token')
    return jwt_token_data['data']['key']


def create_cti_common_aws_iam_role_session():
    """
    Create a session for cti_common_aws_iam_role
    :return:
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::123456789012:role/cti_common_aws_iam_role',
        RoleSessionName='CitCommonAwsIamRoleSession')
    return session