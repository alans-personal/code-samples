"""Implements Rtbproto command by asnyder"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdRtbproto(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'cti',
            'sub_commands': ['build', 'deploy', 'params', 'lb', 'graph', 'awslogin', 'newhelp'],
            'help_title': 'build,deploy,params,lb,graph,awslogin,newhelp',
            'permission_level': 'dev',
            'props_build': self.get_build_properties(),
            'props_deploy': self.get_deploy_properties(),
            'props_params': self.get_params_properties(),
            'props_lb': self.get_lb_properties(),
            'props_graph': self.get_graph_properties(),
            'props_awslogin': self.get_awslogin_properties(),
            'props_newhelp': self.get_newhelp_properties()

        }

        return props


    def get_build_properties(self):
        """
        The properties for the "build" sub-command
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
            'help_text': '*`build`* _description here_',
            'help_examples': [
                '/run rtbproto build -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto build -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_build(self, cmd_inputs):
        """
        Placeholder for "build" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_build")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Build code section #### output to "text" & "title".
        
            # End Build code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Build title"
            text = "Build response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_deploy_properties(self):
        """
        The properties for the "deploy" sub-command
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
            'help_text': '*`deploy`* _Trying raw modal response_',
            'help_examples': [
                '/run rtbproto deploy -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto deploy -e sr-dev -r us-west-2 -s protoservice -c changeme'
            ],
            'switch-templates': [],
            'switch-c': {
                'aliases': ['c', 'changeme'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Is a param for testing later'
            }
        }
        return props

    def invoke_deploy(self, cmd_inputs):
        """
        Placeholder for "deploy" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_deploy")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Deploy code section #### output to "text" & "title".
        
            # End Deploy code section. ####
        
            # Standard response below. Change title and text for output.
            # title = "Deploy title"
            # text = "Deploy response. Fill in here"
            # return self.slack_ui_standard_response(title, text)

            raw_response = """{
	"type": "modal",
	"title": {
		"type": "plain_text",
		"text": "My App",
		"emoji": true
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit",
		"emoji": true
	},
	"close": {
		"type": "plain_text",
		"text": "Cancel",
		"emoji": true
	},
	"blocks": [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": "This is a mrkdwn section block :ghost: *this is bold*, and ~this is crossed out~, and <https://google.com|this is a link>"
			}
		},
		{
			"type": "context",
			"elements": [
				{
					"type": "mrkdwn",
					"text": "*Deployer:* Alan Snyder"
				}
			]
		},
		{
			"type": "divider"
		},
		{
			"type": "actions",
			"elements": [
				{
					"type": "conversations_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select a conversation",
						"emoji": true
					}
				},
				{
					"type": "channels_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select a channel",
						"emoji": true
					}
				},
				{
					"type": "users_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select a user",
						"emoji": true
					}
				},
				{
					"type": "static_select",
					"placeholder": {
						"type": "plain_text",
						"text": "Select an item",
						"emoji": true
					},
					"options": [
						{
							"text": {
								"type": "plain_text",
								"text": "Excellent item 1",
								"emoji": true
							},
							"value": "value-0"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "Fantastic item 2",
								"emoji": true
							},
							"value": "value-1"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "Nifty item 3",
								"emoji": true
							},
							"value": "value-2"
						},
						{
							"text": {
								"type": "plain_text",
								"text": "Pretty good item 4",
								"emoji": true
							},
							"value": "value-3"
						}
					]
				}
			]
		}
	]
}"""
            return raw_response

        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_params_properties(self):
        """
        The properties for the "params" sub-command
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
            'help_text': '*`params`* _description here_',
            'help_examples': [
                '/run rtbproto params -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto params -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_params(self, cmd_inputs):
        """
        Placeholder for "params" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_params")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
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

    def get_lb_properties(self):
        """
        The properties for the "lb" sub-command
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
            'help_text': '*`lb`* _description here_',
            'help_examples': [
                '/run rtbproto lb -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto lb -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_lb(self, cmd_inputs):
        """
        Placeholder for "lb" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_lb")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Lb code section #### output to "text" & "title".
        
            # End Lb code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Lb title"
            text = "Lb response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_graph_properties(self):
        """
        The properties for the "graph" sub-command
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
            'help_text': '*`graph`* _description here_',
            'help_examples': [
                '/run rtbproto graph -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto graph -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_graph(self, cmd_inputs):
        """
        Placeholder for "graph" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_graph")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Graph code section #### output to "text" & "title".
        
            # End Graph code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Graph title"
            text = "Graph response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_awslogin_properties(self):
        """
        The properties for the "awslogin" sub-command
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
            'help_text': '*`awslogin`* _description here_',
            'help_examples': [
                '/run rtbproto awslogin -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto awslogin -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_awslogin(self, cmd_inputs):
        """
        Placeholder for "awslogin" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_awslogin")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Awslogin code section #### output to "text" & "title".
        
            # End Awslogin code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Awslogin title"
            text = "Awslogin response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_newhelp_properties(self):
        """
        The properties for the "newhelp" sub-command
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
            'help_text': '*`newhelp`* _description here_',
            'help_examples': [
                '/run rtbproto newhelp -e sr-dev -r us-east-1 -s protoservice',
                '/run rtbproto newhelp -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_newhelp(self, cmd_inputs):
        """
        Placeholder for "newhelp" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_newhelp")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Newhelp code section #### output to "text" & "title".
        
            # End Newhelp code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Newhelp title"
            text = "Newhelp response. Fill in here"
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

def test_cases_cmd_rtbproto_main():
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