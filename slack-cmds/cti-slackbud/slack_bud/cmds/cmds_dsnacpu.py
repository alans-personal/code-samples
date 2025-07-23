"""Implements Dsnacpu command by asnyder"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdDsnacpu(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'dsna-cpu',
            'sub_commands': ['start', 'stop', 'status', 'list', 'create'],
            'help_title': 'Jupyter command for only for CPUs',
            'permission_level': 'dev',
            'props_start': self.get_start_properties(),
            'props_stop': self.get_stop_properties(),
            'props_status': self.get_status_properties(),
            'props_list': self.get_list_properties(),
            'props_create': self.get_create_properties()

        }

        return props


    def get_start_properties(self):
        """
        The properties for the "start" sub-command
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
            'help_text': '*`start`* _description here_',
            'help_examples': [
                '/run dsnacpu start -e cti -r us-east-1 -s protoservice',
                '/run dsnacpu start -e cti -r us-west-2 -s protoservice'
            ],
            'switch-templates': ['env', 'service', 'region-optional']
        }
        return props

    def invoke_start(self, cmd_inputs):
        """
        Placeholder for "start" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_start")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Start code section #### output to "text" & "title".
            
            # End Start code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Start title"
            text = "Start response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_stop_properties(self):
        """
        The properties for the "stop" sub-command
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
            'help_text': '*`stop`* _description here_',
            'help_examples': [
                '/run dsnacpu stop -e sr-dev -r us-east-1 -s protoservice',
                '/run dsnacpu stop -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_stop(self, cmd_inputs):
        """
        Placeholder for "stop" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_stop")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Stop code section #### output to "text" & "title".
        
            # End Stop code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Stop title"
            text = "Stop response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_status_properties(self):
        """
        The properties for the "status" sub-command
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
            'help_text': '*`status`* _description here_',
            'help_examples': [
                '/run dsnacpu status -e sr-dev -r us-east-1 -s protoservice',
                '/run dsnacpu status -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_status(self, cmd_inputs):
        """
        Placeholder for "status" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_status")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Status code section #### output to "text" & "title".
        
            # End Status code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Status title"
            text = "Status response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_list_properties(self):
        """
        The properties for the "list" sub-command
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
            'help_text': '*`list`* _description here_',
            'help_examples': [
                '/run dsnacpu list -e sr-dev -r us-east-1 -s protoservice',
                '/run dsnacpu list -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_list(self, cmd_inputs):
        """
        Placeholder for "list" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_list")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start List code section #### output to "text" & "title".
        
            # End List code section. ####
        
            # Standard response below. Change title and text for output.
            title = "List title"
            text = "List response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_create_properties(self):
        """
        The properties for the "create" sub-command
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
            'help_text': '*`create`* _description here_',
            'help_examples': [
                '/run dsnacpu create -e sr-dev -r us-east-1 -s protoservice',
                '/run dsnacpu create -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_create(self, cmd_inputs):
        """
        Placeholder for "create" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_create")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Create code section #### output to "text" & "title".
        
            # End Create code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Create title"
            text = "Create response. Fill in here"
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

def test_cases_cmd_dsnacpu_main():
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