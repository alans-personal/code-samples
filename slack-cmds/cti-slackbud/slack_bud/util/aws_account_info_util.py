from __future__ import print_function

import json
import boto3
import sys
import aws_util
import bud_helper_util

MSC_DEV_ACCOUNT_ID = '123456789012'  # TODO: Replace with actual account ID

# Cache keys, since the don't change often
LAST_UPDATE = None
ACCOUNT_ID_CACHE = {}   # key = AccountId, value = OneLogin name
ACCOUNT_NAME_CACHE = {}  # key = OneLogin name, value= AccountId
ALIAS_NAME_CACHE = {}  # key = alias name, value = OneLogin name


def get_account_list(arg_grep):
    """
    Display a list with OneLogin names and AWS Account Ids listed. The list can be shorted by
    only displaying the strings that match arg_grep
    :param arg_grep: String used to filter down the list.
    :return: dictionary with key(name) and value(account_id)
    """

    # Do we have a cache?
    if ACCOUNT_NAME_CACHE:
        # Check to see if the cache is current.
        last_update_time = get_last_update_time()
        if LAST_UPDATE == last_update_time:
            # return what is in the cache.
            return filtered_dictionary(ACCOUNT_NAME_CACHE, arg_grep)

    # update the cache
    scan_all_accounts()
    return ACCOUNT_NAME_CACHE


def filtered_dictionary(dictionary, filter_string):
    """
    If filter string is not None use it to return only elements that that are substrings.
    :param dictionary:
    :param filter_string:
    :return: dictionary
    """
    if not filter_string:
        return dictionary
    else:
        filter_lc = filter_string.lower()
        ret_val = {}
        keys = dictionary.keys()
        for curr_key in keys:
            curr_value = dictionary.get(curr_key)
            key_lc = curr_key.lower()
            value_lc = curr_value.lower()
            if filter_lc in key_lc:
                ret_val[curr_key] = curr_value
            if filter_lc in value_lc:
                ret_val[curr_key] = curr_value
        return ret_val


def get_account_info(account):
    """
    Invoke a lambda function to
    :return: JSON string(confirm?) with response from database.
    """

    # get location.
    sts_client = boto3.client("sts")
    sts_response = sts_client.get_caller_identity()
    user_id = sts_response.get('UserId')
    local_account = sts_response.get('Account')
    arn = sts_response.get('Arn')

    # get region
    region_name = sts_client.meta.region_name

    print('Call is being made from:\n user_id={}\n from_account={}\n arn={}\n region={}'.format(
        user_id, local_account, arn, region_name))

    payload = {
        "cmd": "get_account_info",
        "account": account
    }

    session = None
    region = None
    # if not in same account get session needed.
    if local_account != MSC_DEV_ACCOUNT_ID:
        session = get_aws_account_session()
        region = 'us-east-1'

    lambda_func_arn = 'arn:aws:lambda:us-east-1:123456789012:function:aws-account-info-service'
    response = invoke_lambda_function(lambda_func_arn, payload, session, region)

    # If this was an alias to the account, get the key and make the call again.
    if response.get("AccountKey"):
        key = response.get("AccountKey")
        payload = {
            "cmd": "get_account_info",
            "account": key
        }
        response = invoke_lambda_function(lambda_func_arn, payload, session, region)

    return response


def add_new_account(new_account_id, new_account_name, alias_names, roles, jira_component):
    """
    Add the rows needed for a new AWS Account.

    :param new_account_id: string, id like: 123456789012
    :param new_account_name: string, like: UnityDev
    :param alias_names: string, like: unity-dev
    :param roles: comma separated string, like: Admin,Dev,ReadOnly
    :param jira_component: string, like: AWS UnityDev (123456789012)
    :return:
    """

    payload = {
        "cmd": "add_new_account",
        "new_account_id": new_account_id,
        "new_account_name": new_account_name,
        "alias_names": alias_names,
        "roles": roles,
        "jira_component": jira_component
    }

    response = invoke_account_info_lambda_from_any_where(payload)

    # The response is a dictionary with the following keys
    # { "status", "message" }

    if response.get("status") == "200":
        return response.get("message")
    else:
        print("WARN: Failed to insert new AWS Account. message: {}".format(response.get("message")))
        return None


def get_last_update_time():
    """
    Get the last update time
    :return:
    """
    payload = {
        "cmd": "get_last_update"
    }

    response = invoke_account_info_lambda_from_any_where(payload)

    # The response is a dictionary with the following keys.
    # { "status", "message", "last_update" }

    if response.get("status") == "200":
        return response.get("last_update")
    else:
        print("WARN: Failed to get last_update from AWS Account Info. message: {}".format(response.get("message")))
        return None


def scan_all_accounts():
    """
    Scan all the AWS Accounts if needed. Cache the result.
    :return:
    """
    global LAST_UPDATE
    global ACCOUNT_ID_CACHE
    global ACCOUNT_NAME_CACHE
    global ALIAS_NAME_CACHE

    is_cache_current = False
    # Do we have a cache?
    if len(ACCOUNT_ID_CACHE) > 0:
        # Is it up to date?
        last_update_time = get_last_update_time()
        if last_update_time == LAST_UPDATE:
            is_cache_current = True

    if is_cache_current:
        print('AWS Account Info cache is current')
    else:
        # scan the database and get the results.
        payload = {
            "cmd": "scan"
        }

        response = invoke_account_info_lambda_from_any_where(payload)

        # The response is a dictionary constructed by the lambda function with the following keys.
        # { "status", "message", "last_update", "accounts_dictionary", "alias_dictionary"}
        # The accounts-dictionary is a dictionary of name(key): id(value) constructed by the lambda function
        # to handle paging and corner-cases like DEA account in the database.

        if response:
            LAST_UPDATE = response.get("last_update")
            accounts_dictionary = response.get("accounts_dictionary")
            ALIAS_NAME_CACHE = response.get("alias_dictionary")
            # walk all the keys.
            ACCOUNT_ID_CACHE = {}
            ACCOUNT_NAME_CACHE = {}
            keys = accounts_dictionary.keys()
            for curr_key in keys:
                curr_value = accounts_dictionary.get(curr_key)
                ACCOUNT_ID_CACHE[curr_value] = curr_key
                ACCOUNT_NAME_CACHE[curr_key] = curr_value

        else:
            print("WARN: Failed AWS Account Info scan failed: {}".format(response.get("message")))


def fix_dea_role_name_case(role_name):
    """
    Fix the case of dea role names.
    superadmin => SuperAdmin
    ramsadmin => RamsAdmin

    :param role_name:
    :return: DEA-specific case corrected Role name
    """
    ret_val = role_name

    ret_val = ret_val.replace('infraadmin', 'InfraAdmin')
    ret_val = ret_val.replace('delta', 'Delta')
    ret_val = ret_val.replace('dmp', 'Dmp')
    ret_val = ret_val.replace('pmp', 'Pmp')
    ret_val = ret_val.replace('rams', 'Rams')
    ret_val = ret_val.replace('data', 'Data')
    ret_val = ret_val.replace('adcloud', 'AdCloud')
    ret_val = ret_val.replace('adeng', 'AdEng')
    ret_val = ret_val.replace('super', 'Super')
    ret_val = ret_val.replace('admin', 'Admin')
    ret_val = ret_val.replace('dev', 'Dev')
    ret_val = ret_val.replace('contractor', 'Contractor')

    return ret_val


def get_account_id_from_name(arg_account):
    """
    Look for an AWS Account ID give an name, including aliases.
    :param arg_account:
    :return: AWS Account ID or the None
    """
    try:
        response = get_account_info(arg_account)
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


def get_jira_component_from_role_name(account_name, role_name):
    """

    :param account_name: The account name. Ex. DEA, AdEngPro, SrProd, CTI, etc...
    :param role_name: role name (for DEA) or account or optionally role name of anything else.
    :return: The name of the Component in the JIRA server needed for SAM ticket.
    """

    # Where is the call being made from? This determines if a session is needed to make call.
    sts_client = boto3.client("sts")
    sts_response = sts_client.get_caller_identity()
    user_id = sts_response.get('UserId')
    local_account = sts_response.get('Account')
    arn = sts_response.get('Arn')

    # get region
    region_name = sts_client.meta.region_name

    print('Call is being made from:\n user_id={}\n from_account={}\n arn={}\n region={}'.format(
        user_id, local_account, arn, region_name))

    # Construct the payload
    dynamodb_key = account_name
    # if account_name.startswith('DEA') or account_name.startswith('dea'):
    is_dea_account = False
    is_ae_part_of_dea = False
    is_de_part_of_dea = False
    if 'dea' in account_name.lower():
        is_dea_account = True
    elif account_name.startswith('AE') or account_name.startswith('ae'):
        is_dea_account = True
        is_ae_part_of_dea = True
    elif account_name.lower() == 'de':
        is_dea_account = True
        is_de_part_of_dea = True

    if is_dea_account:
        # DEA account is the exception and is different approves depending on the role.
        if '-' in role_name:
            parts = role_name.split('-')
            role_name = parts[1]

        role_name = fix_dea_role_name_case(role_name)
        dea_sub_account_name = 'DEA'
        # Needed for DE-InfraAdmin & AE-InfraAdmin roles which have different JIRA Components
        if is_ae_part_of_dea:
            dea_sub_account_name = 'AE'
        if is_de_part_of_dea:
            dea_sub_account_name = 'DE'
        dynamodb_key = '{}-{}'.format(dea_sub_account_name, role_name)
    else:
        # This offers a little more robustness for account name.
        response = get_account_info(dynamodb_key)
        dynamodb_key = response.get('OneLoginName')

    print('Looking JIRA Component with DynamoDB key = {}'.format(dynamodb_key))
    payload = {
        "cmd": "get_jira",
        "key": dynamodb_key
    }

    session = None
    region = None
    # if not in same account get session needed.
    if local_account != MSC_DEV_ACCOUNT_ID:
        session = get_aws_account_session()
        region = 'us-east-1'

    lambda_func_arn = 'arn:aws:lambda:us-east-1:123456789012:function:aws-account-info-service'
    response = invoke_lambda_function(lambda_func_arn, payload, session, region)

    return response


def invoke_account_info_lambda_from_any_where(payload):
    """
    Invoke aws_account_info lambda function from any location
    :param payload:
    :return: response
    """
    # get location.
    sts_client = boto3.client("sts")
    sts_response = sts_client.get_caller_identity()
    user_id = sts_response.get('UserId')
    local_account = sts_response.get('Account')
    arn = sts_response.get('Arn')

    # get region
    region_name = sts_client.meta.region_name

    print('Call is being made from:\n user_id={}\n from_account={}\n arn={}\n region={}'.format(
        user_id, local_account, arn, region_name))

    session = None
    region = None
    # if not in same account get session needed.
    if local_account != MSC_DEV_ACCOUNT_ID:
        session = get_aws_account_session()
        region = 'us-east-1'

    lambda_func_arn = 'arn:aws:lambda:us-east-1:123456789012:function:aws-account-info-service'
    response = invoke_lambda_function(lambda_func_arn, payload, session, region)

    print('invoke_..._from_any_where  response: {}'.format(response))

    return response


def invoke_lambda_function(func_name, payload, session=None, region=None):
    """
    Generic invoke lambda function that handles local or remote lambda functions.
    :param func_name: Name of lambda function
    :param payload:
    :param session: None if same account and region
    :param region: None if session is None
    :return:
    """
    if func_name is None:
        raise Exception('ERROR no lambda function name')

    payload_str = json.dumps(payload)
    # payload_bytes = bytes(payload_str, encoding='utf8')
    payload_bytes = bytes(payload_str)

    lambda_client = None
    if session:
        print('using session with region = {}'.format(region))
        lambda_client = aws_util.get_boto3_client_by_name('lambda', session, region)
    else:
        lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=func_name,
        InvocationType='RequestResponse',
        Payload=payload_bytes
    )

    resp_payload = json.loads(response['Payload'].read())

    print('invoke_lambda_function() response: {}'.format(resp_payload))

    return resp_payload


def get_aws_account_session():
    """
    Get the session needed to access the lambda function.
    :return:
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::123456789012:role/AWSInfoCrossAccountRole',
        RoleSessionName='AWSInfoCrossAccountRole')
    return session


# do some testing

def test_get_account_info():
    """Use for testing"""

    print('#################################')
    print('##  test_get_account_info')
    print('#################################')

    # verify we are going python 3.
    print(sys.version_info)

    # Test call from the same region.
    boto3.setup_default_session(profile_name='redacted_mscdev-admin', region_name='us-east-1')

    r0 = get_account_info('123456789012')
    print('--\nr0={}'.format(r0))

    r1 = get_account_info('NetEng')
    print('r1={}\n--'.format(r1))

    r2 = get_account_info('net-eng')
    print('r2={}\n--'.format(r2))

    r3 = get_account_info('DEA')
    print('r3={}\n--'.format(r3))

    r4 = get_account_info('CTI')
    print('r4={}\n--'.format(r4))

    r5 = get_account_info('AdEngProd')
    print('r5={}\n--'.format(r5))

    r6 = get_account_info('NPI')
    print('r6={}\n--'.format(r6))


def test_get_jira_component():
    """

    :return:
    """
    print('#################################')
    print('##  test_get_jira_component')
    print('#################################')

    boto3.setup_default_session(profile_name='roku-msc-dev_mscdev-admin', region_name='us-east-1')

    test_list = [['CTI', 'Admin'], ['DEA', 'SuperAdmin'], ['SrDev','Dev'], ['DEA','AdCloudAdmin']]
    for cur_test in test_list:
        print('{}'.format(cur_test))

    c1 = get_jira_component_from_role_name('CTI', 'Admin')
    print('c1={}'.format(c1))

    c2 = get_jira_component_from_role_name('DEA', 'SuperAdmin')
    print('c2={}'.format(c2))

    c3 = get_jira_component_from_role_name('SrDev','Dev')
    print('c3={}'.format(c3))

    c4 = get_jira_component_from_role_name('DEA','AdCloudAdmin')
    print('c4={}'.format(c4))

    c5 = get_jira_component_from_role_name('dea','adcloudadmin')
    print('c5={}'.format(c5))


def test_filter_dictionary():
    """
    Tests the filter dictionary method.
    :return:
    """
    test_dict = {}
    test_dict['AccountOne'] = "111111"
    test_dict['AccountTwo'] = "222222"
    test_dict['AccountThree'] = "3333333"

    r1 = filtered_dictionary(test_dict, None)
    print('r1: {}'.format(r1))

    r2 = filtered_dictionary(test_dict, "Two")
    print('r2: {}'.format(r2))

    r3 = filtered_dictionary(test_dict, "3")
    print('r3: {}'.format(r3))

    r4 = filtered_dictionary(test_dict, "Account")
    print('r4: {}'.format(r4))


if __name__ == '__main__':
    # test_get_account_info()
    test_get_jira_component()
    test_filter_dictionary()