"""Implements Uxeng command by asnyder"""
from __future__ import print_function
import traceback
import time

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.cti_helper_util as cti_helper_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdUxeng(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'uxeng',
            'sub_commands': ['list', 'remove', 'add'],
            'help_title': 'Commands to deploy web-sites for UxEng team',
            'permission_level': 'dev',
            'props_list': self.get_list_properties(),
            'props_remove': self.get_remove_properties(),
            'props_add': self.get_add_properties()

        }

        return props


    def get_list_properties(self):
        """
        The properties for the "list" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`list`* _List the deployed UI demos_',
            'help_examples': [
                '/run uxeng list',
                '/run uxeng list -e external -t prototypes '
            ],
            'switch-templates': [],
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*type* valid values are: < pending | prototypes>'
            },
            'switch-e': {
                'aliases': ['e', 'env'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*env* Environment. < internal | external >'
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
            arg_type = cmd_inputs.get_by_key('type')
            arg_env = cmd_inputs.get_by_key('env')

            # validate inputs
            if not arg_type:
                arg_type = 'prototypes'
            if arg_type not in ['pending', 'prototypes']:
                raise ShowSlackError('Invalid -t switch. Should be < pending | prototypes >')

            if not arg_env:
                arg_env = 'internal'
            if arg_env not in ['internal', 'external']:
                raise ShowSlackError('Invalid -e switch. Should be < internal | external >')
            if arg_env == 'external':
                if arg_type == 'pending':
                    raise ShowSlackError('For external machine only type allowed is "prototypes"')

            response_url = cmd_inputs.get_response_url()

            region = 'us-west-2'
            session = aws_util.create_session('ux-eng')

            instance_run_list = get_instance_for_env(arg_env)

            # Send the command
            ssm_client = aws_util.get_boto3_client_by_name('ssm', session, region)
            cmd_line = "sh uxeng-list.sh {}".format(arg_type)
            print('command is: {}'.format(cmd_line))

            send_response = ssm_client.send_command(
                InstanceIds=instance_run_list,
                DocumentName='AWS-RunRemoteScript',
                Parameters={
                    'sourceType':["S3"],
                    'sourceInfo':["{\"path\": \"https://roku-uxeng-ssm-script.s3-us-west-2.amazonaws.com/uxeng-list.sh\"}"],
                    'commandLine':[cmd_line],
                    'workingDirectory':[""],
                    'executionTimeout':["60"]
                },
                TimeoutSeconds=180
            )

            # Wait for the response.
            print('UxEng List response: {}'.format(send_response))
            cmd = send_response.get('Command')
            cmd_id = cmd.get('CommandId')
            doc_name = cmd.get('DocumentName')
            status = cmd.get('Status')

            time.sleep(5)
            title = 'UxEng List command'
            text = 'response id: {}'.format(cmd_id)
            slack_ui_util.text_command_response(
                title, text, post=True, response_url=response_url)

            run_time_in_sec = 30
            wait_time_in_sec = 0
            SLEEP_INTERVAL = 3  # seconds
            while wait_time_in_sec < run_time_in_sec + 10:
                time.sleep(SLEEP_INTERVAL)
                wait_time_in_sec += SLEEP_INTERVAL
                # Get the output from the command invocation
                instance_id = str(instance_run_list[0])
                print('Getting result for id: {}, instance: {}'.format(cmd_id, instance_id))
                invocation_response = ssm_client.get_command_invocation(
                    CommandId=cmd_id,
                    InstanceId=instance_id,
                    PluginName='runShellScript'
                )

                print('SSM: invocation took ({}) seconds. response: {}'
                      .format(wait_time_in_sec, invocation_response))
                status = invocation_response['Status']
                print("Status = {}".format(status))
                if 'Success' == status:
                    print("Success list call took {} sec.".format(wait_time_in_sec))
                    std_out = invocation_response.get('StandardOutputContent')
                    std_err = invocation_response.get('StandardErrorContent')
                    break

                if 'Failed' == status:
                    print('Failed after {} sec.'.format(wait_time_in_sec))
                    std_out = invocation_response.get('StandardOutputContent')
                    std_err = invocation_response.get('StandardErrorContent')
                    break

            if std_out:
                text = std_out
            elif std_err:
                text = 'Error: {}'.format(std_err)

            # End List code section. ####
        
            # Standard response below. Change title and text for output.
            title = "List deployed demos"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")


    def get_remove_properties(self):
        """
        The properties for the "remove" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`remove`* _Remove a UI demo from server_',
            'help_examples': [
                '/run uxeng remove -d EPG -e external -t prototypes',
                '/run uxeng remove -d concept_steps.framer -e internal -t pending'
            ],
            'switch-templates': [],
            'switch-d': {
                'aliases': ['d', 'dir'],
                'type': 'string',
                'required': True,
                'lower_case': False,
                'help_text': '*dir* directory name of UI demo'
            },
            'switch-e': {
                'aliases': ['e', 'env'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*env* Environment. < internal | external >'
            },
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*type* Type. < pending | prototypes >'
            }
        }
        return props

    def invoke_remove(self, cmd_inputs):
        """
        Placeholder for "remove" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_remove")
            arg_dir = cmd_inputs.get_by_key('dir')
            arg_env = cmd_inputs.get_by_key('env')
            if not arg_env:
                arg_env = 'internal'

            arg_type = cmd_inputs.get_by_key('type')
            if not arg_type:
                arg_type = 'prototypes'

            # validate the inputs.
            if arg_env not in ['internal', 'external']:
                raise ShowSlackError('Invalid -e switch. Should be < internal | external >')
            if arg_type not in ['pending', 'prototypes']:
                raise ShowSlackError('Invalid -t switch. Should be < pending | prototypes >')
            if arg_env == 'external':
                if arg_type == 'pending':
                    raise ShowSlackError('For external machine only type allowed is "prototypes"')

            response_url = cmd_inputs.get_response_url()
        
            # Start Remove code section #### output to "text" & "title".
            text = 'dir: {}\nenv: {}\ntype: {}\n'.format(arg_dir, arg_env, arg_type)

            instance_run_list = get_instance_for_env(arg_env)

            # Send the command
            region = 'us-west-2'
            session = aws_util.create_session('ux-eng')
            ssm_client = aws_util.get_boto3_client_by_name('ssm', session, region)
            command_line = 'sh uxeng-remove.sh {} {}'.format(arg_type, arg_dir)
            send_response = ssm_client.send_command(
                InstanceIds=instance_run_list,
                DocumentName='AWS-RunRemoteScript',
                Parameters={
                    'sourceType': ["S3"],
                    'sourceInfo': [
                        "{\"path\": \"https://roku-uxeng-ssm-script.s3-us-west-2.amazonaws.com/uxeng-remove.sh\"}"],
                    'commandLine': [command_line],
                    'workingDirectory': [""],
                    'executionTimeout': ["60"]
                },
                TimeoutSeconds=180
            )

            print('UxEng Add response: {}'.format(send_response))
            cmd = send_response.get('Command')
            cmd_id = cmd.get('CommandId')

            text += 'response id: {}'.format(cmd_id)



            # End Remove code section. ####



            # Standard response below. Change title and text for output.
            title = "Remove directory"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_add_properties(self):
        """
        The properties for the "add" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`add`* _Add a UI demo from server_',
            'help_examples': [
                '/run uxeng add -d EPG -e external -t pending',
                '/run uxeng add -d voice-email'
            ],
            'switch-templates': [],
            'switch-d': {
                'aliases': ['d', 'dir'],
                'type': 'string',
                'required': True,
                'lower_case': False,
                'help_text': '*dir* directory of demo'
            },
            'switch-e': {
                'aliases': ['e', 'env'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*env* Environment. < internal | external >'
            },
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': '*type* Type. < pending | prototypes >'
            }
        }
        return props

    def invoke_add(self, cmd_inputs):
        """
        Placeholder for "add" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_add")
            arg_dir = cmd_inputs.get_by_key('dir')
            arg_env = cmd_inputs.get_by_key('env')
            if not arg_env:
                arg_env = 'internal'

            arg_type = cmd_inputs.get_by_key('type')
            if not arg_type:
                arg_type = 'prototypes'

            # validate the inputs.
            if arg_env not in ['internal', 'external']:
                raise ShowSlackError('Invalid -e switch. Should be < internal | external >')
            if arg_type not in ['pending', 'prototypes']:
                raise ShowSlackError('Invalid -t switch. Should be < pending | prototypes >')
            if arg_env == 'external':
                if arg_type == 'pending':
                    raise ShowSlackError('For external machine only type allowed is "prototypes"')

            response_url = cmd_inputs.get_response_url()
        
            # Start Add code section #### output to "text" & "title".
            text = 'dir: {}\nenv: {}\ntype: {}\n'.format(arg_dir, arg_env, arg_type)

            instance_run_list = get_instance_for_env(arg_env)

            # Send the command
            region = 'us-west-2'
            session = aws_util.create_session('ux-eng')
            ssm_client = aws_util.get_boto3_client_by_name('ssm', session, region)
            command_line = 'sh uxeng-add.sh {} {}'.format(arg_type, arg_dir)
            send_response = ssm_client.send_command(
                InstanceIds=instance_run_list,
                DocumentName='AWS-RunRemoteScript',
                Parameters={
                    'sourceType': ["S3"],
                    'sourceInfo': [
                        "{\"path\": \"https://roku-uxeng-ssm-script.s3-us-west-2.amazonaws.com/uxeng-add.sh\"}"],
                    'commandLine': [command_line],
                    'workingDirectory': [""],
                    'executionTimeout': ["180"]
                },
                TimeoutSeconds=360
            )

            print('UxEng Add response: {}'.format(send_response))
            cmd = send_response.get('Command')
            cmd_id = cmd.get('CommandId')

            text += 'response id: {}'.format(cmd_id)
            title = "Add directory"
            slack_ui_util.text_command_response(
                title, text, post=True, response_url=response_url)

            text = ''
            run_time_in_sec = 30
            wait_time_in_sec = 0
            SLEEP_INTERVAL = 3  # seconds
            while wait_time_in_sec < run_time_in_sec + 10:
                time.sleep(SLEEP_INTERVAL)
                wait_time_in_sec += SLEEP_INTERVAL
                # Get the output from the command invocation
                instance_id = str(instance_run_list[0])
                print('Getting result for id: {}, instance: {}'.format(cmd_id, instance_id))
                list_response = ssm_client.list_commands(
                    CommandId=cmd_id,
                )

                print('SSM: invocation took ({}) seconds. response: {}'
                      .format(wait_time_in_sec, list_response))
                status = list_response['Commands'][0]['Status']
                print("Status = {}".format(status))
                if status == 'InProgress' or status == 'Pending':
                    print('keep waiting')
                else:
                    print('done waiting')
                    break

            # Do the call again with the plugin.
            invocation_response = ssm_client.get_command_invocation(
                CommandId=cmd_id,
                InstanceId=instance_id,
                PluginName='runShellScript'
            )
            status = invocation_response['Status']
            print("Status = {}".format(status))
            if 'Success' == status:
                print("Success list call took {} sec.".format(wait_time_in_sec))
                std_out = invocation_response.get('StandardOutputContent')
                std_err = invocation_response.get('StandardErrorContent')
            elif 'Failed' == status:
                print('Failed after {} sec.'.format(wait_time_in_sec))
                std_out = invocation_response.get('StandardOutputContent')
                std_err = invocation_response.get('StandardErrorContent')

            if std_out:
                text = std_out
            elif std_err:
                text = 'Error: {}'.format(std_err)

            # End Add code section. ####
        
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


def get_instance_for_env(arg_env):
    """
    Look for tag  ruku.uxeng.type to select the instance id needed.
    If more than one found, or zero found raise an excetion.
    :param arg_env:
    :return:
    """
    print('get_instance_for_env( {} )'.format(arg_env))

    # Get instance by looking for tag.
    region = 'us-west-2'
    session = aws_util.create_session('ux-eng')
    ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)

    tag_value = 'internal'
    if arg_env == 'external':
        tag_value = 'internet-facing'

    instance_id = None
    try:
        response = ec2_client.describe_instances(
            Filters=[
                {
                    'Name': 'tag:roku:uxeng:type',
                    'Values': [
                        tag_value
                    ]
                }
            ]
        )
        print('DEBUG: describe_instance response = {}'.format(response))

        res = response.get('Reservations')

        if res:
            for curr_res in res:
                instances = curr_res.get('Instances')
                for curr_inst in instances:
                    state = curr_inst.get('State')
                    state_name = state.get('Name')
                    instance_id = curr_inst.get('InstanceId')

                    print('Checking: {} in state {}'.format(instance_id, state_name))

                    if state_name is 'running':
                        break

        if instance_id:
            print('Found {} by tag value: {}'.format(instance_id, tag_value))
            ret_val = [instance_id]
            return ret_val

    except Exception as ex:
        bud_helper_util.log_traceback_exception(ex)
        
    print("WARNING: Didn't find EC instance with tag value = {}. Using hard-coded backup.".format(tag_value))

    instance_run_list = ['i-03548a9a31537eb84']
    if arg_env == 'external':
        instance_run_list = ['i-054c366ed0bb77bc5']

    print('WARNING: ... Using EC2 Instance Id: {}'.format(instance_run_list))
    return instance_run_list


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_uxeng_main():
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