"""Implements Patch command by asnyder"""
from __future__ import print_function
import traceback
import operator

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface


class CmdPatch(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'trust',
            'sub_commands': ['list', 'report', 'roles'],
            'help_title': 'Command for AWS Patch Manager. Get list of tagged EC2 Instances or create a report for an account',
            'permission_level': 'dev',
            'props_list': self.get_list_properties(),
            'props_report': self.get_report_properties(),
            'props_roles': self.get_roles_properties()
        }

        return props


    def get_list_properties(self):
        """
        The properties for the "list" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`list`* _List instances tagged by security_',
            'help_examples': [
                '/run patch list -a sr-dev -r us-east-1 -k is_managed -v false',
                '/run patch list -a sr-dev -r us-west-2 -k is_patched'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Region, default us-east-1'
            },
            'switch-k': {
                'aliases': ['k', 'key'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'key part of roku:security:<key>'
            },
            'switch-v': {
                'aliases': ['v', 'value'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Optional value of key'
            }
        }
        return props

    def invoke_list(self, cmd_inputs):
        """
        Placeholder for "list" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_list")
            arg_account = cmd_inputs.get_by_key('account')
            arg_region = cmd_inputs.get_by_key('region')
            arg_key = cmd_inputs.get_by_key('key')
            arg_value = cmd_inputs.get_by_key('value')
            response_url = cmd_inputs.get_response_url()
        
            # Start List code section #### output to "text" & "title".
            session = cti_helper_util.create_security_auditor_session(arg_account)
            arn_list = get_resource_arns_for_tag(session, arg_region, arg_key, arg_value)

            title = 'List `{}` in *{}* {}'.format(arg_key, arg_account, arg_region)
            text = ''
            if len(arn_list) < 1:
                text = 'No Resources found'
            if len(arn_list) < 30:
                # Print out all ARNs
                for curr_arn in arn_list:
                    text += '   {}\n'.format(curr_arn)
            else:
                # Print out first 30 followed by ...
                size = len(arn_list)
                text += 'Found {} ARNs. listing first 30'.format(size)
                index = 0
                for curr_arn in arn_list:
                    index += 1
                    curr_arn
                    if index > 30:
                        text += '... more\n'
                        break
                    else:
                        text += '   {}\n'.format(curr_arn)

            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_report_properties(self):
        """
        The properties for the "report" sub-command
        Modify the values as needed, but leave keys alone.
        Valid 'run-type' values are ['shorttask, 'longtask, 'docker']
        The 'confirmation' section is and advanced feature and commented out.
        Remove it unless you plan on using confirmation responses.
        'help_text' needs a short one line description
        'help_examples' is a python list.
              Modify add remove examples (one per line) as needed.
        'switch-templates' contains common switchs (-e, -d, -s)
              remove the ones not need. Leave an empty list if needed.
              use 'region-optional' and 'service-optional' if param not required.        See 'switch-z' as an example custom parameter definition.
            valid 'types' are string | int | property
        Copy-paste that section as needed.
        Then delete the 'switch-z' section.
        
        When done reduce the DocString to a description of the 
            sub-commands properties.
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`report`* _description here_',
            'help_examples': [
                '/run patch report -e sr-dev -r us-east-1 -s protoservice',
                '/run patch report -e sr-dev -r us-west-2 -s protoservice -c changeme'
            ],
            'switch-templates': ['env', 'service', 'region-optional'],
            'switch-c': {
                'aliases': ['c', 'changeme'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Change this help string for switch'
            }
        }
        return props

    def invoke_report(self, cmd_inputs):
        """
        Placeholder for "report" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_report")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Report code section #### output to "text" & "title".
        
            # End Report code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Report title"
            text = "Report response. Fill in here"
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
            'help_text': '*`roles`* _Find Roles that need updates for patching_',
            'help_examples': [
                '/run patch roles -a MscDev -r us-east-1'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Region, default us-east-1'
            }
        }
        return props

    def invoke_roles(self, cmd_inputs):
        """
        Placeholder for "roles" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_roles")
            arg_account = cmd_inputs.get_by_key('account')
            arg_region = cmd_inputs.get_by_key('region')
            response_url = cmd_inputs.get_response_url()
        
            # Start Inactive code section #### output to "text" & "title".
            session = cti_helper_util.create_security_auditor_session(arg_account)
            arn_list = get_resource_arns_for_tag(session, arg_region, 'roku:security:is_managed', 'false')

            # Report back the number of EC2 Instances found, via response URL
            num_instances = len(arn_list)
            text = 'Found: {} unmanaged instances in *{}*. Looking up roles...\n'.format(num_instances, arg_region)
            title = 'Unmanaged Patch Roles: `{}`'.format(arg_account)
            slack_ui_util.text_command_response(
                title, text, post=True, response_url=response_url)

            # Go through the list accumulation the roles and the number of times seen.
            role_map = create_role_map(session, arg_region, arn_list)

            # sort role maps
            sorted_role_list = convert_count_map_to_sorted_list(role_map)

            #list the top 30 items.
            total_lines = len(sorted_role_list)
            text = 'Found {} distinct roles\n'.format(total_lines)
            index = 0
            for curr_line in sorted_role_list:
                index += 1
                if index > 30:
                    text += '\n  more ...'
                    break
                else:
                    text += '\n  {}'.format(curr_line)

            # End Inactive code section. ####
        
            # Standard response below. Change title and text for output.
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


def convert_count_map_to_sorted_list(dict_with_count_values):
    """
    Convert a dictionary with values as a counter, into a sorted list.
    :param role_map:
    :return: sorted list of strings for output.
    """
    temp_map = {}
    sort_list = []
    key_list = dict_with_count_values.keys()
    for curr_key in key_list:
        value = dict_with_count_values[curr_key]
        sort_value = 10000 + value
        sort_key = '{}-{}'.format(sort_value, curr_key)
        parts = curr_key.split('/')
        if len(parts) == 2:
            curr_key = parts[1]
        str_value = ' {} instances with role: `{}`'.format(value, curr_key)
        temp_map[sort_key] = str_value
        sort_list.append(sort_key)

    sort_list.sort(reverse=True)

    ret_val = []
    for curr_s_key in sort_list:
        v = temp_map[curr_s_key]
        ret_val.append(v)

    return ret_val


def get_roles_from_ec2_id_list(session, arg_region, ec2_id_list):
    """
    Find the distinct roles attached to EC2 Instances and count them.
    :param session:
    :param arg_region:
    :param ec2_id_list:
    :return:
    """
    ret_val = {}

    ec2_client = aws_util.get_boto3_client_by_name('ec2', session, arg_region)
    response = ec2_client.describe_instances(
        InstanceIds=ec2_id_list
    )

    reservations = response.get('Reservations')
    if reservations is None:
        return ret_val
    for curr_res in reservations:
        instances = curr_res.get('Instances')
        if instances is None:
            continue
        for curr_inst in instances:
            inst_profile_arn = 'None'
            inst_profile_obj = curr_inst.get('IamInstanceProfile')
            if inst_profile_obj is not None:
                inst_profile_arn = inst_profile_obj.get('Arn')
                if inst_profile_arn not in ret_val:
                    ret_val[inst_profile_arn] = 1
                else:
                    value = ret_val[inst_profile_arn]
                    ret_val[inst_profile_arn] = value + 1

    return ret_val


def create_role_map(session, arg_region, arn_list):
    """
    Go through the arn_list and find a unique set of roles, and count number of instances with them.
    :param session:
    :param arg_region:
    :param arn_list:
    :return:
    """
    # turn arn_list into EC2_ID
    ec2_id_list = []
    for curr_arn in arn_list:
        part = curr_arn.split('/')
        if len(part) == 2:
            ec2_id_list.append(part[1])

    # Call boto3 to get roles.
    ret_val = get_roles_from_ec2_id_list(session, arg_region, ec2_id_list)
    return ret_val


def get_resource_arns_for_tag(session, arg_region, arg_key, arg_value):
    """
    Return a list of ARNs tagged with a specific value.
    :return: List of ARNs
    """
    tag_client = aws_util.get_tagging_client(session, arg_region)
    response = tag_client.get_resources(
        TagFilters=[
            {
                'Key': arg_key,
                'Values': [
                    arg_value,
                ]
            }
        ],
        ResourcesPerPage=100,
        ResourceTypeFilters=[
            'ec2:instance'
        ]
    )
    arn_list = parse_get_resources_response(response)
    return arn_list


def parse_get_resources_response(response):
    """
    Return the ARN list.
    :param response: JSON from the boto3 API.
    :return: list of strings which are ARNs.
    """
    ret_val = []
    resource_list = response.get('ResourceTagMappingList')
    for curr_resource in resource_list:
        arn = curr_resource.get('ResourceARN')
        ret_val.append(arn)
    return ret_val


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_patch_main():
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