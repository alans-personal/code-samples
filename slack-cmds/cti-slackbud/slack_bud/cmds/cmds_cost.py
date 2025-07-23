"""Implements Cost command by asnyder"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface


class CmdCost(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'bill',
            'sub_commands': ['ebs', 'report', 'params'],
            'help_title': 'Commands to help monitor AWS Cost',
            'permission_level': 'dev',
            'props_ebs': self.get_ebs_properties(),
            'props_report': self.get_report_properties(),
            'props_params': self.get_params_properties()

        }

        return props

    def get_ebs_properties(self):
        """
        The properties for the "ebs" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`ebs`* _List unattached EBS volumes in an AWS Account_',
            'help_examples': [
                '/run cost ebs -a sr-dev -r us-east-1'
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
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Region'
            }
        }
        return props

    def invoke_ebs(self, cmd_inputs):
        """
        Placeholder for "ebs" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_ebs")
            arg_region = cmd_inputs.get_by_key('region')
            arg_account = cmd_inputs.get_by_key('account')
            response_url = cmd_inputs.get_response_url()

            # Start Ebs code section #### output to "text" & "title".
            print('Account: {} Region: {}'.format(arg_account, arg_region))
            text = 'Account: *{}* Region: *{}*\n'.format(arg_account, arg_region)

            session = cti_helper_util.create_security_auditor_session(arg_account)
            ec2_client = aws_util.get_boto3_client_by_name('ec2', session, arg_region)

            list_volumes = get_all_unattached_volumes(ec2_client)

            data = ''
            for curr_line in list_volumes:
                # remove the first column
                split_str = curr_line.strip('\n').split(',')
                out = ' '.join(split_str[1:]) + '\n'
                data += out

            data = "```{}```".format(data)
            text = text + data

            # End Ebs code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Unattached EBS Volumes"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_report_properties(self):
        """
        The properties for the "report" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`report`* _description here_',
            'help_examples': [
                '/run cost report -a sr-dev -t storage',
                '/run cost report -a sr-dev -r us-west-2 -t ec2'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Region'
            },
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Report type. See params command for list'
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
            arg_account = cmd_inputs.get_by_key('account')
            arg_region = cmd_inputs.get_by_key('region')
            arg_type = cmd_inputs.get_by_key('type')
            response_url = cmd_inputs.get_response_url()
        
            # Start Report code section #### output to "text" & "title".
            text = 'Account: {}\nRegion: {}\nType: {}'.format(arg_account, arg_region, arg_type)


            # End Report code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Report title"

            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
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
            'help_text': '*`params`* _List of Cost Explorer report types_',
            'help_examples': [
                '/run cost params',
            ],
            'switch-templates': [],
            'switch-c': {
                'aliases': [],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Change this help string for switch'
            }
        }
        return props

    def invoke_params(self, cmd_inputs):
        """
        Placeholder for "params" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_params")

            # Start Params code section #### output to "text" & "title".
        
            # End Params code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Params title"
            text = "Params response. Fill in here"
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


def format_data_row(columns):
    """
    Make a fixed column table that is 73 columns wide, and limit the max size of certain columns.

    NOTE: from the input we remove column zero which was the sort id originally.

    1: volume_id -  vol-00895704d998e70c6 - always 22 wide
    2: name - use the remaining available space. - 16 wide seems available.
    3: state - available  shrink to - max 6 wide
    4: size - 4000  -  max 6 wide
    5: date created - 2017-12-05 - always 11 wide
    6: snapshot_id - max 12 wide

    :param columns:
    :return:
    """
    try:
        print('formatting: {}'.format(columns))

        vol_id = columns.get(1)
        name = columns.get(2)

        ret_val = ''.format()

    except Exception as ex:
        print('FORMATTING ERROR: {}'.format(ex))


def get_volume_name_from_tag(desc_volume_response):
    """
    Pull the Name from the tags on the EBS Volume if it exists.
    If no name is found or an error occurs then return a space since CSV column is output.
    """
    ret_val = ' '
    try:
        tags = desc_volume_response.get('Tags')
        if tags:
            for curr_tag in tags:
                kv = curr_tag.get('Key')
                if kv == 'Name':
                    ret_val = curr_tag.get('Value')
                    print('Volume Name: _{}_'.format(ret_val))

    except Exception as ex:
        print('get_volume_name_from_tag had error: {}'.format(ex))
    return ret_val


def parse_ebs_volume_response(response):
    """
    Parse the response of a describe_volumes call and retrun list string with results.
    """
    # resp_len = len(str(response)
    # print('resp_len = {}'.format(resp_len))
    # if resp_len < 10:
    #    print('response={}'.format(response))

    print('parse_ebs_volume_response')
    ret_val = ['sort_key,volume_id,name,state,size,created,snapshot']
    error_count = 0

    volumes = response['Volumes']
    for curr_volume in volumes:
        try:
            if len(curr_volume['Attachments']) == 0:
                volume_id = curr_volume['VolumeId']
                state = curr_volume['State']
                snapshot_id = curr_volume['SnapshotId']
                create_time = curr_volume['CreateTime']
                size = curr_volume['Size']

                if snapshot_id is '':
                    snapshot_id = 'no'
                else:
                    snapshot_id = 'yes'

                volume_name = get_volume_name_from_tag(curr_volume)

                value = '{},{},{},{},{},{}'.format(volume_id, volume_name, state, size, create_time.date(),
                                                      snapshot_id)

                # create the sort key, so oldest and largest are first.
                digits_in_size = len(str(size))
                create_time_str = str(create_time.date())
                year_in_create_time = create_time_str.split('-')[0]
                sort_key = '{}-{}-{}-{}'.format(digits_in_size, size, year_in_create_time, create_time)

                item = '{}, {}'.format(sort_key, value)
                # print('{}'.format(item))

                ret_val.append(item)

        except Exception as ex:
            error_count += 1
            print('Error: {}'.format(ex))

    print('num errors: {}'.format(error_count))
    print('list size: {}'.format(len(ret_val)))

    return ret_val


def get_all_unattached_volumes(ec2_client):
    """
    Get all unattached volumes even if need to pageinate.
    Sort them by size and age. 4 diget sizes first, the 3 digit sizes then 2 digit sizes.
    Return list with oldest and largest at top.

    The ec2_client will be for the specific account and region
    """
    unsorted_list = []

    keep_going = True
    loop_count = 0
    next_token = None
    while keep_going:
        if not next_token:
            response = ec2_client.describe_volumes(Filters=[], )
            keep_going = False
        else:
            response = ec2_client.describe_volumes(Filters=[], NextToken=next_token)

        print('parse_ebs_volume_response')
        list = parse_ebs_volume_response(response)
        unsorted_list = unsorted_list + list

        loop_count += 1
        print('iteration #{}'.format(loop_count))
        print('list size = {}'.format(len(list)))
        if loop_count > 10:
            keep_going = False

    unsorted_list.sort(reverse=True)

    print('# EBS volumes: {}'.format(len(unsorted_list)))
    return unsorted_list

# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_cost_main():
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