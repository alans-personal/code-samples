"""Implements Cmd command by asnyder@roku.com"""
from __future__ import print_function
import boto3
from boto3.dynamodb.conditions import Key, Attr
import time

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdCmd(CmdInterface):

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
            'sub_commands': ['history'],
            'help_title': 'Framework command to get history of commands typed',
            'permission_level': 'dev',
            'props_history': self.get_history_properties()

        }

        return props


    def get_history_properties(self):
        """
        The properties for the "history" sub-command
        Modify the values as needed, but leave keys alone.

        When done reduce the DocString to a description of the 
            sub-commands properties.
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`history`* _Get the last commands typed_',
            'help_examples': [
                '/run cmd history',
                '/run cmd history -n 30',
                '/run cmd history -g farm',
                '/run cmd history -n 100 -g deploy'
            ],
            'switch-templates': [],
            'switch-n': {
                'aliases': ['n', 'num'],
                'type': 'int',
                'required': False,
                'lower_case': True,
                'help_text': 'Number to display. Default is 10.'
            },
            'switch-g': {
                'aliases': ['g', 'grep'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'grep-like filter for command output'
            }
        }
        return props

    def invoke_history(self, cmd_inputs):
        """
        Placeholder for "history" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_history")
            arg_num = cmd_inputs.get_by_key('num')
            if not arg_num:
                arg_num = 10
            user_id = cmd_inputs.get_slack_user_id()
            time_str = time.strftime('%y%m%d%H%M%S')

            arg_grep = cmd_inputs.get_by_key('grep')
            if not arg_grep:
                arg_grep = ''
            else:
                print('Using grep filter: {}'.format(arg_grep))
        
            # Start History code section #### output to "text" & "title".
            text = ''

            # Need to look up the user's id.
            dynamobd = boto3.resource('dynamodb')
            slack_cmd_table = dynamobd.Table('SlackBudCmds')

            # Call the DynamoDB table to get and filter out the last (n) elements.
            response = slack_cmd_table.query(
                Limit=int(arg_num),
                ScanIndexForward=False,
                KeyConditionExpression=Key('userid').eq(user_id) & Key('timestamp').lte(time_str)
            )

            # display the commands.
            duplicate_set = set()
            duplicate_count = 0
            grep_filter_count = 0
            if 'Items' in response:
                items = response['Items']
                print('(DEBUG) SlackCmd Items = {}'.format(items))
                for curr_item in items:
                    cmdline = curr_item['cmdline']
                    if len(arg_grep) > 0:
                        if arg_grep not in cmdline:
                            grep_filter_count += 1
                            continue
                    if cmdline in duplicate_set:
                        duplicate_count += 1
                    else:
                        text += '/run {}\n'.format(cmdline)
                        duplicate_set.add(cmdline)
                if duplicate_count > 0:
                    text += 'Removed {} duplicate commands\n'.format(duplicate_count)
                if grep_filter_count > 0:
                    text += 'Removed {} items not containing "{}"\n'\
                        .format(grep_filter_count, arg_grep)
            else:
                print('No Item in response')
                print('(DEBUG) response={}'.format(response))

            # End History code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Command History ({})".format(arg_num)
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

def test_cases_cmd_cmd_main():
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