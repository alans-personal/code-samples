import boto3
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES
from util.aws_util import get_ssm_parameter
from bud_helper_util import log_traceback_exception

SSM_PARAM_LDAP_USER_KEY = "GardenerLdapCheckerUser"
SSM_PARAM_LDAP_PASS_KEY = "GardenerLdapCheckerPass"

LDAP_HOST = '?'


def is_active_employee(roku_user_name):
    """
    Call LDAP server to determine if this is an active Roku employee.
    :param roku_user_name:
    :return: True if an active Roku user, otherwise False
    """
    # For active
    try:
        base_dn = 'OU=People,DC=corp,DC=roku'
        bool_found = is_employee_in_group(base_dn, roku_user_name)
    except ValueError as ve:
        print("{}".format(ve))
    except Exception as ex:
        print("{}".format(ex))
        log_traceback_exception(ex)

    return bool_found


def is_past_employee(roku_user_name):
    """
    Call LDAP server to determine if this is a past Roku employee.
    :param roku_user_name:
    :return: True if past Roku employee, otherwise False
    """
    try:
        base_dn = 'OU=Users,OU=Retired,DC=corp,DC=roku'
        bool_found = is_employee_in_group(base_dn, roku_user_name)
    except ValueError as ve:
        print("{}".format(ve))
    except Exception as ex:
        print("{}".format(ex))
        log_traceback_exception(ex)

    return bool_found


def is_employee_in_group(base_dn, roku_user_name, dry_run=False):
    """
    Check LDAP server for emplpoyee in base_dn group.
    :param base_dn: LDAP Group
    :param roku_user_name: Roku username like:  asnyder
    :return: True if found, otherwise False. Raise exception if error.
    """
    ldap_creds = get_ldap_cred_from_param_store()

    found_email = ''
    s = Server(LDAP_HOST, get_info=ALL)
    # Bind to the server
    c = Connection(s, user=ldap_creds['username'], password=ldap_creds['password'])
    if not c.bind():
        raise ValueError("Failed to connect to LDAP")

    if dry_run:
        print("Checking for user %s:" % roku_user_name)

    search_query = '(mailNickname=%s)' % roku_user_name
    c.search(search_base=base_dn, search_filter=search_query, attributes=['mail'])

    entries = c.entries
    if len(entries) == 0:
        #    if (dry_run == True):
        #        print("User not found or not termed.")
        return False

    for entry in entries:
        # print(entry.entry_to_json())
        found_email = str(entry['mail'])
        if dry_run:
            print("Terminated use found: %s" % found_email)

    c.unbind()
    return True


def get_ldap_cred_from_param_store():
    """
    Gets the encrypted credentials from the System Manager Parameter Store.
    :return: python dictionary with ldap 'username' and 'password'
    """
    ldap_creds = {}

    ldap_user = get_ssm_parameter(SSM_PARAM_LDAP_USER_KEY)
    ldap_pass = get_ssm_parameter(SSM_PARAM_LDAP_PASS_KEY)

    if ldap_user is None:
        print 'WARN, failed to find SSM Param: {}'.format(SSM_PARAM_LDAP_USER_KEY)
        raise ValueError('WARN, failed to find SSM Param: {}'.format(SSM_PARAM_LDAP_USER_KEY))
    if ldap_pass is None:
        print 'WARN, failed to find SSM Param: {}'.format(SSM_PARAM_LDAP_PASS_KEY)
        raise ValueError('WARN, failed to find SSM Param: {}'.format(SSM_PARAM_LDAP_PASS_KEY))

    ldap_creds['username'] = ldap_user
    ldap_creds['password'] = ldap_pass

    return ldap_creds


def get_ldap_cred_for_ldap_group_updates():
    return None


def add_user_to_group():
    return None


def create_new_one_login_role():
    return None


def convert_slack_id_to_ldap_name(slack_user_id, slack_user_name):
    """
    For users that are in the SlackUser's database look up what their LDAP name is.
    :param slack_user_name:
    :return:
    """
    dynamodb = boto3.resource('dynamodb')
    BUD_USERS_TABLE = dynamodb.Table('SlackBudUsers')

    response = BUD_USERS_TABLE.get_item(
        Key={
            'userid': slack_user_id
        }
    )

    item = response.get('Item')
    if item:
        corp_id = item.get('corpID')
        if corp_id:
            return corp_id

    print('WARN: Failed to find item for slack username: {} ({})'.format(slack_user_name, slack_user_id))
    print("response.get('Item') = {}".format(item))
    return slack_user_name
