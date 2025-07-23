"""Utility class for Roku JIRA server."""

from __future__ import print_function
from jira import JIRA
import aws_util
import cti_helper_util
import bud_helper_util
import aws_account_info_util
import boto3
from slack_ui_util import ShowSlackError


def get_jira_server(cmd_inputs):
    """
    If in /rundev uses the Roku's devjira servers.
    If in /run use the Roku's production JIRA server.

    The credentials are stored in System Manager ParameterStore.

    :param cmd_inputs: to determine which server to connect with and get those credentials.
    :return: jira
    """
    # jira_info expected format: username | password | URL
    jira_info = None
    if cmd_inputs.get_slack_bud_env() == 'dev':
        jira_info = aws_util.get_ssm_parameter('jira_credentials_dev')
    else:
        # Get the production credentials.
        jira_info = aws_util.get_ssm_parameter('jira_credentials_prod')
    jira_parts = jira_info.split(' | ')

    n_parts = len(jira_parts)
    if n_parts != 3:
        raise ShowSlackError("Couldn't find valid credentials for ({})".format(cmd_inputs.get_slack_bud_env()))

    url = jira_parts[2]
    obscure_user = cti_helper_util.obscure_string(jira_parts[0])
    obscure_pwd = cti_helper_util.obscure_string(jira_parts[1])
    print('login url: {}, {}, {}'.format(url, obscure_user, obscure_pwd))

    options = {'server': jira_parts[2]}
    jira = JIRA(options, basic_auth=(jira_parts[0], jira_parts[1]))

    return jira


def get_jira_server_url(cmd_inputs):
    """
    Just return the URL for the JIRA server called.
    :param cmd_inputs:
    :return:
    """
    # jira_info expected format: username | password | URL
    jira_info = None
    if cmd_inputs.get_slack_bud_env() == 'dev':
        jira_info = aws_util.get_ssm_parameter('jira_credentials_dev')
    else:
        # Get the production credentials.
        jira_info = aws_util.get_ssm_parameter('jira_credentials_prod')
    jira_parts = jira_info.split(' | ')

    n_parts = len(jira_parts)
    if n_parts != 3:
        raise ShowSlackError("Couldn't find valid credentials for ({})".format(cmd_inputs.get_slack_bud_env()))

    jira_url = jira_parts[2]

    return jira_url


def get_component_name_from_aws_account_name(aws_account_name, role_name):
    """
    Look-up the component name based on lower case name of the aws account
    If the aws account is DEA also look-up based on the role name, since that account has two components.
    :param aws_account_name:
    :param role_name: Needed only for DEA account.
    :return:
    """
    print("get_component_name_from_aws_account_name({}, {})".format(aws_account_name, role_name))

    # lookup_name = aws_account_name
    # if role_name:
    #     lookup_name = '{}-{}'.format(aws_account_name, role_name)

    response = aws_account_info_util.get_jira_component_from_role_name(aws_account_name, role_name)
    if not response:
        raise ShowSlackError('No JIRA Component found for: {}-{}'.format(aws_account_name, role_name))

    print('aws_account_info_util.get_jira_component_from_role_name({}, {})'.format(aws_account_name, role_name))
    print('response = {}'.format(response))

    ret_val = response.get('JiraComponent')
    return ret_val


def create_sam_aws_access_issue(jira, users, role_name, reporter_name, aws_account_name=None):
    """
    A new workflow was created in October. This method works with that new workflow

    :param jira: valid jira server. Either Roku's dev or production JIRA server.
    :param users: String comma delimited, list of LDAP user names.
    :param role_name: Role name like: CTI-VISITOR
    :param reporter_name: String name of requester
    :param aws_account_name: String like CTI | WebShop
    :return: boolean True if accepted.
    """
    try:
        print('New workflow SAM ticket')

        user_list = users.split(',')
        clean_user_list = [x.strip(' ') for x in user_list]
        num_users = len(clean_user_list)
        users_text = ''
        if num_users != 1:
            raise ShowSlackError('Only one user allow per SAM ticket.  Was: {}'.format(clean_user_list))
        users_text = clean_user_list[0]
        summary_text = 'AWS access request for: {}, Role: {}'.format(users_text, role_name)

        aws_account_id = get_account_id_from_name(aws_account_name)
        if aws_account_id:
            summary_text += ', AWS account: ({}) {}'.format(aws_account_id, aws_account_name)

        desc_text = ' *Role:* {}\n\n'.format(role_name)
        desc_text += ' *User(s):* '
        is_first = True
        for curr_user in clean_user_list:
            if not is_first:
                desc_text += ', '
            is_first = False
            desc_text += '{}'.format(curr_user)
        desc_text += '\n\n'
        desc_text += ' *Reporter:* {}\n\n'.format(reporter_name)
        desc_text += ' ------------\n\n'

        print('Create JIRA. summary: {}'.format(summary_text))
        print('Description: {}'.format(desc_text))

        issue_type_list = jira.issue_types()
        print('Issue types: {}'.format(issue_type_list))

        component_name = get_component_name_from_aws_account_name(aws_account_name, role_name)
        new_issue = jira.create_issue(project='SAM',
                            issuetype={'name': 'Account Access Request'},
                            components=[{'name': component_name}],
                            reporter={'name': users_text},
                            summary=summary_text, description=desc_text)

        print('type(new_issue)...')
        print(type(new_issue))
        print('create_response: {}'.format(new_issue))
        return new_issue

    except ShowSlackError as sse:
        raise sse
    except Exception as ex:
        print('Failed to create JIRA SAM ticket. Reason: {}'.format(ex))
        bud_helper_util.log_traceback_exception(ex)
        raise ShowSlackError('Failed to create JIRA ticket for access request')


#
# DEPRECATED Use:: aws_account_info_util.get_account_id_from_name(arg_account)
#
def get_account_id_from_name(arg_account):
    """
    Look for an AWS Account ID give an name, including aliases.
    :param arg_account:
    :return: AWS Account ID or the None
    """
    try:
        response = aws_account_info_util.get_account_info(arg_account)
        account_key = response.get('AccountKey')
        if account_key:
            return account_key

        key = response.get('Key')
        if key:
            return key

        # If someone uses the AWS account id, look for a OneLoginName
        onelogin_name = response.get('OneLoginName')
        if onelogin_name:
            return arg_account

        print('WARN: No AWS Account Id found for name _{}_'.format(arg_account))
        return None
    except Exception as ex:
        print('ERROR: {}'.format(ex))
        bud_helper_util.log_traceback_exception(ex)
        print('arg_account = {}'.format(arg_account))
        return None


def verify_aws_account_name(arg_account):
    """
    Replace
    :param arg_account:
    :return:
    """
    if not arg_account:
        print('WARN: None passed in as account name.')
        return False

    try:
        response = aws_account_info_util.get_account_info(arg_account)
        oln = response.get("OneLoginName")
        if oln:
            return True

        # try again with an all lower-case version
        arg_account_lower_case = arg_account.lower()
        response = aws_account_info_util.get_account_info(arg_account_lower_case)
        oln = response.get("OneLoginName")
        if oln:
            return True

        return False

    except ShowSlackError:
        raise
    except Exception as ex:
        print('Error in verify_aws_account_name_v2({})'.format(arg_account))
        bud_helper_util.log_traceback_exception(ex)
        return False


def verify_onelogin_role_exists(onelogin_role_name):
    """
    Accept a role name as either camel case or lower case and see if they exist.

    :param onelogin_role_name: String with expected value <OneLoginName>-<Role>
    :return:
    """
    try:
        parts = onelogin_role_name.split('-')

        if len(parts) != 2:
            raise ShowSlackError('Invalid role name: {}. Expected format <Account>-<Role>'.format(onelogin_role_name))

        account = parts[0]
        role = parts[1]

        response = aws_account_info_util.get_account_info(account)
        oln = response.get("OneLoginName")
        if not oln:
            raise ShowSlackError('No Role called {} found for: {}'.format(role, account))

        roles = response.get("Roles")
        role_list = roles.split(",")
        for curr_role in role_list:
            if role == curr_role:
                return True
            curr_role_lower = curr_role.lower()
            role_lower = role.lower()
            if role_lower == curr_role_lower:
                return True
        return False

    except ShowSlackError:
        raise
    except Exception as ex:
        print('Error in verify_onelogin_role_exists_v2({})'.format(onelogin_role_name))
        bud_helper_util.log_traceback_exception(ex)
        return False


def list_aws_account_roles(arg_account):
    """
    NOTE: Run this in parallel for a while with v1.
    :param arg_account:
    :return:
    """
    print('list_aws_account_roles_v2: arg_account={}'.format(arg_account))
    account_info = aws_account_info_util.get_account_info(arg_account)
    onelogin_name = account_info.get('OneLoginName')
    if not onelogin_name:
        print('Account not found')
        return "Not Found", ""

    roles = account_info.get('Roles')
    print('{}, {}'.format(onelogin_name, roles))
    return onelogin_name, roles


def debug_project(jira_server, project_id):
    """
    Just for debugging.
    :param project_id:
    :return: None
    """
    try:
        print('debug_project')
        project_object = jira_server.project('SAM')
        debug_object(project_object, comment="SAM Project")

    except Exception as ex:
        print('Error: debug_project. ex={}'.format(ex))
        bud_helper_util.log_traceback_exception(ex)


def debug_object(obj, comment=None):
    """
    Debug an object
    :param obj:
    :param comment: Optional command to include with debug statements
    :return: None, just do throw a exception
    """
    try:
        if comment:
            print('Debug object: {}\n'.format(comment))

        for attr in dir(obj):
            if hasattr(obj, attr):
                print("obj.%s = %s" % (attr, getattr(obj, attr)))
            else:
                print('obj missing {}'.format(attr))
        print('\n')
    except Exception as ex:
        print('Error: debug_object: {}'.format(ex))
        bud_helper_util.log_traceback_exception(ex)


# Test methods below
def test_get_account_id_from_name():
    """

    :return:
    """
    # test different aliases.
    r1 = get_account_id_from_name('SrProd')
    print('"SrProd" ID = {}\n'.format(r1))
    r2 = get_account_id_from_name('srprod')
    print('"srprod" ID = {}\n'.format(r2))
    r3 = get_account_id_from_name('sr-prod')
    print('"sr-prod" ID = {}\n'.format(r3))

    # test the negative value.
    r4 = get_account_id_from_name('NotRealAccount')
    print('"NotRealAccount" ID = {}\n'.format(r4))


def test_verify_onelogin_role_exists():
    # Test VERIFY_ONELOGIN_ROLE exists.
    test_list = ["SrProd-Admin", "DEA-Admin", "SrProd-Contractor", "srprod-Admin", 'cti-admin']
    for curr_test in test_list:
        print('\n-- verify_onelogin_role_exists -- {}'.format(curr_test))
        r_vr = verify_onelogin_role_exists(curr_test)
        print('{} is {}'.format(curr_test, r_vr))


def test_list_account_roles():
    # Test list account roles
    test_list = ['SrProd', 'CTI', 'DEA', 'NPIAudio', 'NpiAudio', 'DoesNotExist']
    for curr_test in test_list:
        print('\n-- verify_aws_account_name_v2 -- {}'.format(curr_test))
        r_e = verify_aws_account_name(curr_test)
        print('{} is {}'.format(curr_test, r_e))


def test_get_jira_component_name_from_account():
    # Test JIRA component look-up
    print('Testing component name')

    test_list = ['CTI-Admin', 'DEA-SuperAdmin', 'AdEngProd-Something']
    for curr_test in test_list:
        parts = curr_test.split('-')
        try:
            jira = get_component_name_from_aws_account_name(parts[0], parts[1])
            print('\n{}: {}\n'.format(curr_test, jira))
        except ShowSlackError as sse:
            print('\n{} had {}\n'.format(curr_test, sse))
        except Exception as ex:
            print('\n{} had {}\n'.format(curr_test, ex))


if __name__ == '__main__':

    # Test call from the same region.
    boto3.setup_default_session(profile_name='redacted_mscdev-admin', region_name='us-east-1')

    test_get_account_id_from_name()
    test_verify_onelogin_role_exists()
    test_list_account_roles()
    test_get_jira_component_name_from_account()
