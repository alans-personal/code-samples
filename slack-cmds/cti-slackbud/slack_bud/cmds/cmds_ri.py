"""Implements Ri command by asnyder"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface

import boto3


class CmdRi(CmdInterface):

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
            'sub_commands': ['info', 'report', 'summary', 'avail'],
            'help_title': 'AWS Reserved Instance information and reports',
            'permission_level': 'dev',
            'props_info': self.get_info_properties(),
            'props_report': self.get_report_properties(),
            'props_summary': self.get_summary_properties(),
            'props_avail': self.get_avail_properties()

        }

        return props


    def get_info_properties(self):
        """
        The properties for the "info" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`info`* _Prints out text on types of AWS Reserved Instances and details_',
            'help_examples': [
                '/run ri info'
            ],
            'switch-templates': []
        }
        return props

    def invoke_info(self, cmd_inputs):
        """
        Placeholder for "info" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_info")
        
            # Start Info code section #### output to "text" & "title".
            text = 'EC2:\nRDS:\nRedshift:\nElasticSearch:\nElasticache:\nDynamo:'
            # End Info code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Reserved Instance Types Info"
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
            'help_text': '*`report`* _Daily reports for RIs_',
            'help_examples': [
                '/run ri report -t coverage -r rds',
                '/run ri report -t utilization -r es',
                '/run ri report -t avail -r ec2'
            ],
            'switch-templates': [],
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Type values: coverage | utilization | avail'
            },
            'switch-r': {
                'aliases': ['r', 'resource'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Resource values: ec2 | rds | redshift | es | cache | dynamo'
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
            arg_type = cmd_inputs.get_by_key('type')
            arg_resource = cmd_inputs.get_by_key('resource')
            response_url = cmd_inputs.get_response_url()
        
            # Start Report code section #### output to "text" & "title".
            text = 'type = {}\n resource = {}\n\n'.format(arg_type, arg_resource)
            # End Report code section. ####

            # sts_client = boto3.client('sts')
            # session = sts_client.assume_role(
            #     RoleArn='arn:aws:iam::{}:role/ctipoke'.format('123456789012'), RoleSessionName='ctipoke')

            session = cti_helper_util.create_security_auditor_session('net-eng')
            ec2_client = aws_util.get_boto3_client_by_name('ec2', session, 'us-east-1')

            response = ec2_client.describe_reserved_instances(
                Filters=[
                    {'Name': 'state', 'Values': ['active']}
                ]
            )
            ri_map = {}
            ri_sort_list = []

            print('parsing response...')
            ri_list = response['ReservedInstances']
            for curr in ri_list:
                inst_type = curr['InstanceType']
                prod_desc = curr['ProductDescription']
                ri_id = curr['ReservedInstancesId']
                count = curr['InstanceCount']
                print('{}: {}-{}, #{}'.format(ri_id, inst_type, prod_desc, count))

                sort_str = '{}-{} | {}'.format(inst_type, prod_desc, ri_id)
                item_desc = '{}: `{}-{}`, #{}'.format(cti_helper_util.shorten_string(ri_id, 4), inst_type, prod_desc, count)
                ri_map[ri_id] = item_desc
                ri_sort_list.append(sort_str)

            ri_sort_list.sort()
            print('#RIs = {}'.format(len(ri_sort_list)))
            for sorted_item in ri_sort_list:
                split = sorted_item.split(' | ')
                key = split[1]
                sorted_desc = ri_map[key]

                print('sorted::: {}'.format(sorted_desc))
                text += ' {}\n'.format(sorted_desc)

            # Standard response below. Change title and text for output.
            title = "Report on coverage, utilization or avail types"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")


    def get_summary_properties(self):
        """
        The properties for the "summary" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`summary`* _List the current stats and next expiration times_',
            'help_examples': [
                '/run ri summary -r ec2',
                '/run ri summary -r cache'
            ],
            'switch-templates': [],
            'switch-r': {
                'aliases': ['r', 'resource'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Resource values: ec2 | rds | redshift | es | cache | dynamo'
            }
        }
        return props

    def invoke_summary(self, cmd_inputs):
        """
        Placeholder for "summary" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_summary")
            arg_resource = cmd_inputs.get_by_key('resource')
            response_url = cmd_inputs.get_response_url()
        
            # Start Summary code section #### output to "text" & "title".
            text = 'resource = {}\nToDo: List expire times'.format(arg_resource)
            # End Summary code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Summary of RI usage and expiration dates"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_avail_properties(self):
        """
        The properties for the "avail" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`avail`* _Quick summary of resource types that have available RIs._',
            'help_examples': [
                '/run ri avail -r es',
                '/run ri avail -r cache'
            ],
            'switch-templates': [],
            'switch-r': {
                'aliases': ['r', 'resource'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Resource values: ec2 | rds | redshift | es | cache | dynamo'
            }
        }
        return props

    def invoke_avail(self, cmd_inputs):
        """
        Placeholder for "avail" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_avail")
            arg_resource = cmd_inputs.get_by_key('resource')
            response_url = cmd_inputs.get_response_url()
        
            # Start Avail code section #### output to "text" & "title".
            text = 'resource = {}\nToDo: List expire times'.format(arg_resource)
            # End Avail code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Avail RIs"
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

# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_ri_main():
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