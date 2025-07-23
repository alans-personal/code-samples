"""Implements Awslogin command by asnyder"""
from __future__ import print_function

from util.slack_ui_util import ShowSlackError
import util.bud_helper_util as bud_helper_util
import util.jira_utils as jira_utils
import util.ldap_utils as ldap_utils
import boto3
from cmd_interface import CmdInterface


class CmdAwslogin(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'all',
            'sub_commands': ['request', 'params', 'roles', 'info', 'usage', 'deaparams', 'adengprodparams'],
            'help_title': 'Create JIRA ticket to request AWS Login access',
            'permission_level': 'dev',
            'props_request': self.get_request_properties(),
            'props_params': self.get_params_properties(),
            'props_roles': self.get_roles_properties(),
            'props_info': self.get_info_properties(),
            'props_usage': self.get_usage_properties(),
            'props_deaparams': self.get_deaparams_properties(),
            'props_adengprodparams': self.get_adengprodparams_properties(),
        }

        return props

    def get_request_properties(self):
        """
        The properties for the "request" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`request`* _Generate JIRA ticket requesting AWS access_',
            'help_examples': [
                '/run awslogin request -u batares -a CTI -r Admin',
                '/run awslogin request -u jpatel -a SrInfra -r Visitor --show'
            ],
            'switch-templates': [],
            'switch-u': {
                'aliases': ['u', 'user'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'User(s) needing access'
            },
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS account name'
            },
            'switch-r': {
                'aliases': ['r', 'role'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Role name'
            },
            'switch-d': {
                'aliases': ['d', 'debug'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Put in debug mode, to test JIRA workflow. Example: -d alantest'
            }
        }
        return props

    def invoke_request(self, cmd_inputs):
        """
        Make a request to DEA's pajar API

        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_request")
            arg_user = cmd_inputs.get_by_key('user')
            arg_account = cmd_inputs.get_by_key('account')
            arg_role = cmd_inputs.get_by_key('role')

            arg_slack_user_name = cmd_inputs.get_slack_user_name()
            arg_slack_user_id = cmd_inputs.get_slack_user_id()

            # Start Request code section #### output to "text" & "title".
            jira_server = jira_utils.get_jira_server(cmd_inputs)

            role_name = '{}-{}'.format(arg_account, arg_role)

            is_valid_account_name = jira_utils.verify_aws_account_name(arg_account)
            if not is_valid_account_name:
                msg = "Invalid account name: `{}`\n  See `/run awslogin params` for valid names".format(arg_account)
                print('Error: {}'.format(msg))
                raise ShowSlackError(msg)

            is_valid_role = jira_utils.verify_onelogin_role_exists(role_name)
            if not is_valid_role:
                msg = "The role: `{}` does not exist in account: `{}`".format(role_name, arg_account)
                print('Error: {}'.format(msg))
                raise ShowSlackError(msg)

            print('Creating SAM request for role: {}'.format(role_name))

            ldap_user_name = ldap_utils.convert_slack_id_to_ldap_name(arg_slack_user_id, arg_slack_user_name)

            new_issue = jira_utils.create_sam_aws_access_issue(jira_server, arg_user, role_name, ldap_user_name,
                                                               arg_account)
            jira_server_url = jira_utils.get_jira_server_url(cmd_inputs)
            jira_ticket_url = '{}/browse/{}'.format(jira_server_url, new_issue)

            text = "Access Request: *`{}`* for *{}*".format(new_issue, role_name)
            text += '\nJIRA ticket link:\n```{}```\n'.format(jira_ticket_url)

            # End Info code section. ####

            # Standard response below. Change title and text for output.
            title = '{}'.format(cmd_inputs.get_raw_inputs())
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError as sse:
            raise sse
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_params_properties(self):
        """
        The properties for the "params" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`params`* _Lists values needed by other commands_',
            'help_examples': [
                '/run awslogin params'
            ],
            'switch-templates': []
        }
        return props

    def invoke_params(self, cmd_inputs):
        """
        This command shows valid params for each account.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_params")

            # Start Params code section #### output to "text" & "title".

            text = '*`-r`*: *roles* _not case sensitive_\n'
            text += '```Admin\nDev\nReadOnly\nQA\nDevOps\nContractor\nVisitor```\n'
            text += '*`-a`*: *accounts* _not case sensitive_ \n'
            text += '```AdEngAdmin\nAdEngAE\nAdEngProd\nAdEngRd\nAdEngSandbox\nAdEngShared\n' \
                    'AdEngEmTechMADev\nAdEngEmTechMAGen\nAdEngEmTechMAProd\n' \
                    'AppsProd\nAppsQA\nAppsStg\n' \
                    'AwsTools\nBAR\nCTI\nDataSci\nDEA\nDeltaML\n' \
                    'EntEngProd\nEntEngQA\nEntEngStg\n' \
                    'HeaderBidding\nIT\nMscDev\nMscProd\n' \
                    'Mobile\nMobileDev\nNetEng\nNPI\nNpiAudio\n' \
                    'OsAdsProgArt\nOsAdsProgInt\n' \
                    'RokuPayProd\nRokuPayQA\nRokuPayStg\n' \
                    'PlayerProd\nPlayerStg\nProgOps\nRokuQuibiContent\n' \
                    'SparkEnhanceDev\n' \
                    'SrDev\nSrInfra\nSrProd\nSrQA\nTrustEng\nTrustProd\n' \
                    'UnityDev\nUnityProd\n' \
                    'UxEng\nWeb\nWebAds\nWebShop\nWink\nXprov```'
            text += '\n`/run awslogin request -u <user> -a <account> -r <role>`'
            text += '\n`/run awslogin roles -a <account>`'

            # End Params code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Params used by other commands"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_roles_properties(self):
        """
        The properties for the "roles" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`roles`* _List the roles available in this account_',
            'help_examples': [
                '/run awslogin roles -a SrDev',
                '/run awslogin roles -a cti'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of AWS account. See `params` for list.'
            }
        }
        return props

    def invoke_roles(self, cmd_inputs):
        """
        This command lists the roles for each account
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_roles")
            arg_account = cmd_inputs.get_by_key('account')

            onelogin_name, roles = jira_utils.list_aws_account_roles(arg_account)
            if not onelogin_name:
                msg = "Invalid account name: `{}`\n  See `/run awslogin params` for valid names".format(arg_account)
                print('Error: {}'.format(msg))
                raise ShowSlackError(msg)

            text = roles
            if len(text) == 0:
                text += 'No Roles in this account.'
            # End Roles code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Roles in *`{}`*".format(onelogin_name)

            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_info_properties(self):
        """
        The properties for the "info" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`info`* _Links for more documentation_',
            'help_examples': [
                '/run awslogin info'
            ],
            'switch-templates': []
        }
        return props

    def invoke_info(self, cmd_inputs):
        """
        This command shows where to get information on OneLogin
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_info")
        
            # Start Info code section #### output to "text" & "title".
            text = '  _Confluence Page:_\n ```https://confluence.portal.asnyder.com:8443/pages/viewpage.action?pageId=94225109```\n'
            # text += '\n  _Install AWS Keys:_\n ```https://awskeys-setup.eng.asnyder.com```\n'
            text += '\n  _Install AWS Keys:_\n ```https://gitlab.eng.asnyder.com/cti/getawskeys#installation```\n'
            text += '\n*Request access* _for someone else_:\n'
            text += '`/run awslogin request -u <user> -a <account> -r <role>`\n'
            text += '*Get valid parameters*:\n'
            text += '`/run awslogin params`'
            text += '\n\n'
            text += '*For Group Admins ==== *\n'
            text += '  _Permissions repo_\n ```https://gitlab.eng.asnyder.com/cloudtech/onelogin_sso_policies```'
            text += ''
            # End Info code section. ####
        
            # Standard response below. Change title and text for output.
            title = "AWS Access Information"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_usage_properties(self):
        """
        The properties for the "info" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`usage`* _Get latest Usage Report_',
            'help_examples': [
                '/run awslogin usage'
            ],
            'switch-templates': []
        }
        return props

    def invoke_usage(self, cmd_inputs):
        """
        This commands shows the usage report written into the S3 bucket
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_usage")

            # NOTE: For now the get the version 20190522 ...
            # Start Usage coe section
            text = '*OneLogin AWS Login Reports*: `2019-05-31 & past 7 days`\n'

            s3_client = boto3.client('s3')
            # arn:aws:s3:::cti-image-server-bucket
            # s3://cti-image-server-bucket/month/aws_onelogin_usage_20190513.csv
            text_usage = s3_client.get_object(
                Bucket='cti-image-server-bucket',
                Key='month/aws_onelogin_usage_20190531.csv'
            )['Body'].read()
            print('DEBUG: {}'.format(text_usage))

            text += '\n*Login Type by AWS Account Report*: \n'
            text += '```{}```'.format(text_usage)
            text += '\n'

            text_not_using = s3_client.get_object(
                Bucket='cti-image-server-bucket',
                Key='month/aws_onelogin_not_using_20190531.csv'
            )['Body'].read()

            text += '\n*Individuals Not Using OneLogin*: \n'
            text += '```{}```'.format(text_not_using)
            text += '\n'

            # Standard response below. Change title and text for output.
            title = "OneLogin Usage Report"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_deaparams_properties(self):
        """
        The properties for the "params" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`deaparams`* _Lists values needed by DEA account commands_',
            'help_examples': [
                '/run awslogin deaparams'
            ],
            'switch-templates': []
        }
        return props

    def invoke_deaparams(self, cmd_inputs):
        """
        This command shows valid params for each account.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_deaparams")

            # Start Params code section #### output to "text" & "title".

            text = '*`-r`*: *roles* _not case sensitive_\n'
            text += '```DEA-SuperAdmin    - Admin for all accounts\n' \
                    'DEA-AdCloudAdmin  - Advertising, Insights and Analytics Admin\n' \
                    'DEA-AdCloudDev    - Advertising, Insights and Analytics Developer\n' \
                    'DEA-DataAdmin     - Big Data and data pipelines Admin\n' \
                    'DEA-DataDev       - Big Data and data pipelines Developer\n' \
                    'DEA-DeltaAdmin    - Unify Data fom DataXu & Search Admin\n' \
                    'DEA-DeltaDev      - Unify Data fom DataXu & Search Developer\n' \
                    'DEA-DmpAdmin      - Data manipulation platform Admin\n' \
                    'DEA-DmpDev        - Data manipulation platform Developer\n' \
                    'DEA-PmpAdmin      - Private marketplace of ads Admin\n' \
                    'DEA-PmpDev        - Private marketplace of ads Developer\n' \
                    'DEA-RamsAdmin     - Roku Ad mediation Admin\n' \
                    'DEA-RamsDev       - Roku Ad mediation Admin\n' \
                    'DEA-Contractor    - non-Roku employees```\n'
            text += '*`-a`*: *accounts* _not case sensitive_ \n'
            text += '\n`/run awslogin request -u <user> -a DEA -r <role>`'
            text += '\n`/run awslogin roles -a DEA`'

            # End Params code section. ####

            # Standard response below. Change title and text for output.
            title = "Params used by other commands"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_adengprodparams_properties(self):
        """
        The properties for the "params" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`adengprodparams`* _Lists values needed by AdEngProd account commands_',
            'help_examples': [
                '/run awslogin adengprodparams'
            ],
            'switch-templates': []
        }
        return props

    def invoke_adengprodparams(self, cmd_inputs):
        """
        This command shows valid params for each account.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_adengprodparams")

            # Start Params code section #### output to "text" & "title".

            text = '*`-r`*: *roles* _not case sensitive_\n'
            text += '```AdEngProd-Admin           - Admin for all accounts\n' \
                    'AdEngProd-DevOps          - DevOps for all teams\n' \
                    'AdEngProd-AnalyticsDevOps - DevOps for Analytics team\n' \
                    'AdEngProd-DAPDevOps       - DevOps for DAP team\n' \
                    'AdEngProd-RTSDevOps       - DevOps for RTS team\n' \
                    'AdEngProd-CMSDevOps       - DevOps for CMS team\n' \
                    'AdEngProd-AppEngDevOps    - DevOps for AppEng team\n' \
                    'AdEngProd-PiiVisitor      - Roku employee with PII access\n' \
                    'AdEngProd-Dev             - Developer role\n' \
                    'AdEngProd-ReadOnly        - ReadOnly in the account```\n'
            text += '*`-a`*: *accounts* _not case sensitive_ \n'
            text += '\n`/run awslogin request -u <user> -a AdEngProd -r <role>`'
            text += '\n`/run awslogin roles -a AdEngProd`'

            # End Params code section. ####

            # Standard response below. Change title and text for output.
            title = "Params used by other commands"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    # End Command's Properties section
    # ###################################
    # Start Command's implemented interface method section

    def run_command(self):
        """
        DON'T change this method. It should only be changed but the
        create_command, add_sub_command, and remove_sub_command scripts.

        In this method we look up the sub-command being used, and then the
        properties for that sub-command. It parses and validates the arguments
        and deals with invalid arguments.

        If the arguments are good. It next determines if this sub command
        needs to be invoked via the longtask lambda, or can run in (this)
        shorttask lambda. It then packages the arguments up properly and
        runs that command.

        :return: SlackUI response.
        """
        return self.default_run_command()

    def build_cmd_specific_data(self):
        """
        If you need specific things common to many sub commands like
        dynamo db table names or sessions get it here.

        If nothing is needed return an empty dictionary.
        :return: dict, with cmd specific keys. default is empty dictionary
        """
        return {}

    def invoke_confirm_command(self):
        """
        Only fill out this section in the rare case your command might
        prompt the Slack UI with buttons ect. for responses.
        Most commands will leave this section blank.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print('invoke_confirm_command')
            cmd_inputs = self.get_cmd_input()
            params = cmd_inputs.get_confirmation_params()
            callback_id = cmd_inputs.get_callback_id()
            print('callback_id = {}'.format(callback_id))

            # Start confirmation code section.
            # Callback Id convention is callback_<sub-command-name>_<anything>

            # Replace_example below.
            # if callback_id == 'callback_mysubcommand_prompt_env':
            #     return some_method_to_handle_this_case(params)
            # if callback_id == 'callback_mysubcommand_prompt_region':
            #     return some_other_method_to_handle_region(params)


            # End confirmation code section.
            # Default return until this section customized.
            title = 'Default invoke_confirm_command'
            text = 'Need to customize, invoke_confirm_command'
            return self.slack_ui_standard_response(title, text)

        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

# End class functions
# ###################################
# Start static helper methods sections

# PUT STATIC METHODS HERE. AND REMOVE THIS COMMENT.


def select_one_approver_for_search_team(approvers, arg_approver):
    print('select_one_approver_for_search_team')
    print('approvers: {}, arg_approver: {}'.format(approvers, arg_approver))

    # default is not found.
    ret_val = 'gcuni'

    approver_text = make_search_group_approver_list(approvers)
    approvers_list = approver_text.split('\n')
    for item in approvers_list:
        if arg_approver in item:
            # pull out the name from this item.
            items = item.split(' ')
            ret_val = items[1]
            ret_val = ret_val.translate(None, '\n')

    # temp until figured out.
    print('ret_val = {}'.format(ret_val))
    return ret_val


def make_search_group_approver_list(approvers):
    print('make_search_group_approver_list')
    print('approvers: {}'.format(approvers))

    approver_list = approvers.split('|')
    print('approver_list: {}'.format(approver_list))

    is_first = True
    ret_val = ''
    for curr_approver in approver_list:
        initials = curr_approver[:2]
        curr_txt = '({}) {}'.format(initials, curr_approver)
        if not is_first:
            curr_txt = '\n{}'.format(curr_txt)
        is_first = False
        ret_val += curr_txt

    print('ret_val = {}'.format(ret_val))
    return ret_val

# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_awslogin_main():
    """
    Entry point for command unit tests.
    :return: True if tests pass False if they fail.
    """
    try:
        # Fill in any needed tests here.

        return True
    except Exception as ex:
        bud_helper_util.log_traceback_exception(ex)
        return False
