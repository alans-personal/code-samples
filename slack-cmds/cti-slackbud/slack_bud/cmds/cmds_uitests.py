"""Implements Uitests command by redacted@email.com"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdUitests(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'unity',
            'sub_commands': ['test1', 'test2', 'test3'],
            'help_title': 'This command is for Slack UI testing. It is visible to only a small group of people',
            'permission_level': 'dev',
            'props_test1': self.get_test1_properties(),
            'props_test2': self.get_test2_properties(),
            'props_test3': self.get_test3_properties()

        }

        return props


    def get_test1_properties(self):
        """
        The properties for the "test1" sub-command
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
            'help_text': '*`test1`* _description here_',
            'help_examples': [
                '/run uitests test1 -e sr-dev -r us-east-1 -s protoservice',
                '/run uitests test1 -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_test1(self, cmd_inputs):
        """
        Placeholder for "test1" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_test1")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Test1 code section #### output to "text" & "title".
        
            # End Test1 code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Test1 title"
            text = "Test1 response. Fill in here"
            # return self.slack_ui_standard_response(title, text)

            return self.buildkit_test1_template()
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def buildkit_test1_template(self):
        return """{
	"blocks": [
		{
			"type": "divider"
		},
		{
			"type": "header",
			"text": {
				"type": "plain_text",
				"text": "Unattached EBS report",
				"emoji": true
			}
		},
		{
			"type": "divider"
		},
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "Download Report: *CTI* `us-east-1`"
			},
			"accessory": {
				"type": "button",
				"text": {
					"type": "plain_text",
					"text": "Download",
					"emoji": true
				},
				"value": "click_me_123",
				"url": "http://internal-image-svc.eng.asnyder.com/static/month/unattached-ebs-Test-File-Aug05-2245.csv",
				"action_id": "button-action"
			}
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "plain_text",
					"text": "20201-08-05 15:40 PST",
					"emoji": true
				}
			]
		}
	]
}"""

    def get_test2_properties(self):
        """
        The properties for the "test2" sub-command
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
            'help_text': '*`test2`* _description here_',
            'help_examples': [
                '/run uitests test2 -e sr-dev -r us-east-1 -s protoservice',
                '/run uitests test2 -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_test2(self, cmd_inputs):
        """
        Placeholder for "test2" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_test2")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Test2 code section #### output to "text" & "title".
        
            # End Test2 code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Test2 title"
            text = "Test2 response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_test3_properties(self):
        """
        The properties for the "test3" sub-command
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
            'help_text': '*`test3`* _description here_',
            'help_examples': [
                '/run uitests test3 -e sr-dev -r us-east-1 -s protoservice',
                '/run uitests test3 -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_test3(self, cmd_inputs):
        """
        Placeholder for "test3" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_test3")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Test3 code section #### output to "text" & "title".
        
            # End Test3 code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Test3 title"
            text = "Test3 response. Fill in here"
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

def test_cases_cmd_uitests_main():
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