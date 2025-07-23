"""Utility class with helper methods for CTI group specific commands.

This class depends on aws_util, but it agnostic of the UI.
Exceptions caught need to be converted into UI format and
passed back to the user.
"""
from __future__ import print_function
import json
import os
import boto3
import aws_util
import jira_utils
from slack_ui_util import ShowSlackError

ENVIRONMENTS = aws_util.ENVIRONMENTS


def list_aws_account_names():
    """
    List the ASW account names.
    :return: list of Roku's AWS account names.
    """
    return ENVIRONMENTS.keys()


def create_cloudtech_session():
    """
    This method should be made obsolete in the future when we need to reach into different AWS
    accounts. This will work only in tasks are within the cloudtech AWS Account.
    :return:
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::141602222194:role/serverless-slackbud-dev-us-east-1-lambdaRole',
        RoleSessionName='CloudTechSession')
    return session


def create_security_auditor_session(aws_account_name):
    """
    Create a session with read access to AWS accounts.
    :param aws_account_name: Same as ENVIRONMENT above.
    :return: session.
    """

    # Get AWS account-id from the name or an alias.
    account_id = jira_utils.get_account_id_from_name(aws_account_name)
    if not account_id:
        raise ShowSlackError("No account id for: {}".format(aws_account_name))

    print('Name: {}, Id: {}'.format(aws_account_name, account_id))

    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::{}:role/SecurityAuditor'.format(account_id),
        RoleSessionName='SecurityAuditor')
    return session


# DEPRECATED
# def create_cti_poke_session(aws_account_name):
#     """
#     Create a session with read access to AWS accounts.
#     :param aws_account_name: Same as ENVIRONMENT above.
#     :return: session.
#     """
#     sts = boto3.client('sts')
#     session = sts.assume_role(
#         RoleArn='arn:aws:iam::{}:role/ctipoke'.format(ENVIRONMENTS[aws_account_name]),
#         RoleSessionName='ctipoke')
#     return session


def get_tag_value_from_list(tags, key_name):
    """
    Tags from EC2 describe_instances look like the following:

    tags=[
        {u'Value': 'sriise[AROAIJG4ICM2P2NPHE466:sriise]', u'Key': 'Owner'},
        {u'Value': 'soren-ml-box', u'Key': 'Name'}
    ]

    This method parse that format and returns the value for the specified Name.
    If the name isn't found, None is returned.

    :param tags: List of tags from boto3 calls like ec2 describe
    :param key_name:
    :return: value tag for the 'key_name', if the key_name isn't found return None
    """
    for curr_tag in tags:
        key = curr_tag['Key']
        if key == key_name:
            value = curr_tag['Value']
            return value

    return None


def obscure_string(value, num_chars=3):
    """
    Obscure a string so the full value doesn't appear in the log, but
    the start and end are correct so you can validate it is correct value.

    If long:
    Th!s!s4P4ssword
    Th!***(15)***ord

    If short:
    ASh0rtStr
    AS**(9)**tr

    The result will be the first three and last three characters, and something in the middle to indicate
    the length. If the len is less than 10 characters it will be shorter.

    :param value: Some string the needs to be obscured, but logged partially to verify.
    :param num_chars: Number of characters to put at start and end of string
    :return: String like
    """
    if value is None:
        return 'None'

    str_len = len(value)

    ret_val = ''
    if str_len > 10:
        ret_val += value[0:3]
        ret_val += '***({})***'.format(str_len)
        ret_val += value[-3:]
    else:
        ret_val += value[0:2]
        ret_val += '**({})**'.format(str_len)
        ret_val += value[-2:]

    return ret_val


def shorten_string(value, num_char):
    """

    :param value:
    :param num_char:
    :return:
    """
    if value is None:
        return 'None'

    str_len = len(value)

    ret_val = ''
    if str_len > 10:
        ret_val += value[0:num_char]
        ret_val += '***({})***'.format(str_len)
        ret_val += value[-1*num_char:]
    else:
        ret_val += value[0:2]
        ret_val += '**({})**'.format(str_len)
        ret_val += value[-2:]

    return ret_val

