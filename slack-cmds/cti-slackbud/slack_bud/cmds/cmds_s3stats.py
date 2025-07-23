"""Implements S3Stats command by asnyder"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface
import boto3


class CmdS3Stats(CmdInterface):

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
            'sub_commands': ['summary', 'details'],
            'help_title': 'Get AWS S3 bucket stats per account',
            'permission_level': 'dev',
            'props_summary': self.get_summary_properties(),
            'props_details': self.get_details_properties()

        }

        return props

    def get_summary_properties(self):
        """
        The properties for the "summary" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`summary`* _Get summary of S3 usage for account_',
            'help_examples': [
                '/run s3stats summary -a sr-dev'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Account name like net-eng, or dea'
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
            arg_account = cmd_inputs.get_by_key('account')
            response_url = cmd_inputs.get_response_url()
        
            # Start Summary code section #### output to "text" & "title".

            # Try to s3 download the file from image-server-bucket
            #  S3 copy this file into a bucket, or attach it to an e-mail.
            bucket_name = 'cti-image-server-bucket'
            s3_obj_key = 'forever/slack-s3-cmd/{}_s3_bucket_summary.txt'.format(arg_account)

            s3 = boto3.resource('s3')

            try:
                obj = s3.Object(bucket_name, s3_obj_key)
                file_contents = obj.get()['Body'].read().decode('utf-8')
                text = file_contents
            except Exception as e:
                text = 'Failed to find file. {}'.format(s3_obj_key)

            # End Summary code section. ####
        
            # Standard response below. Change title and text for output.
            title = "S3 summary stats: {}".format(arg_account)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_details_properties(self):
        """
        The properties for the "details" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`details`* _Get details of S3 usage for account_',
            'help_examples': [
                '/run s3stats details -a sr-dev'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Account name like net-eng, or dea'
            }
        }
        return props

    def invoke_details(self, cmd_inputs):
        """
        Placeholder for "details" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_details")
            arg_account = cmd_inputs.get_by_key('account')
            response_url = cmd_inputs.get_response_url()
        
            # Start Details code section #### output to "text" & "title".
            aws_account = arg_account

            link_path = 'forever/slack-s3-cmd/{}_s3_bucket_details.txt'.format(aws_account)
            link_to_report = 'http://internal-image-svc.eng.asnyder.com/static/{}'.format(link_path)
            text = 'S3 Bucket details link:\n ```{}```\n'.format(link_to_report)

            # End Details code section. ####
        
            # Standard response below. Change title and text for output.
            title = "S3 bucket usage details: {}".format(arg_account)
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

def test_cases_cmd_s3stats_main():
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