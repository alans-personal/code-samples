"""Implements Unity command by asnyder"""
from __future__ import print_function
import traceback
import boto3

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface


class CmdUnity(CmdInterface):

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
            'sub_commands': ['build', 'deploy', 'metrics', 'promote'],
            'help_title': 'Commands to manage Unity builds through QA pipeline',
            'permission_level': 'dev',
            'props_build': self.get_build_properties(),
            'props_deploy': self.get_deploy_properties(),
            'props_metrics': self.get_metrics_properties(),
            'props_promote': self.get_promote_properties()

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
            'run-type': 'longtask',
            'help_text': '*`build`* _description here_',
            'help_examples': [
                '/run unity build',
                '/run unity build -c changeme'
            ],
            'switch-templates': [],
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

            session = create_session_for_unity_dev_pipeline()
            region = 'us-west-2'
            ecr_client = aws_util.get_boto3_client_by_name('ecr', session, region)

            text = '```\n'
            response = ecr_client.describe_repositories()
            repos = response.get('repositories')
            for curr_repo in repos:
                reg_id = curr_repo.get('registryId') # seems to be the same as the account id.
                reg_name = curr_repo.get('repositoryName')
                reg_uri = curr_repo.get('repositoryUri')
                text += 'URI: {}'.format(reg_uri)
                text += get_images_from_repo(ecr_client, reg_id, reg_name)

            text += '```'
            # End Build code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Unity Builds"
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
            'run-type': 'longtask',
            'help_text': '*`deploy`* _description here_',
            'help_examples': [
                '/run unity deploy -e sr-dev -r us-east-1 -s protoservice',
                '/run unity deploy -e sr-dev -r us-west-2 -s protoservice -c changeme'
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
            title = "Deploy title"
            text = "Deploy response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_metrics_properties(self):
        """
        The properties for the "metrics" sub-command
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
            'run-type': 'longtask',
            'help_text': '*`metrics`* _description here_',
            'help_examples': [
                '/run unity metrics -e sr-dev -r us-east-1 -s protoservice',
                '/run unity metrics -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_metrics(self, cmd_inputs):
        """
        Placeholder for "metrics" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_metrics")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Metrics code section #### output to "text" & "title".
        
            # End Metrics code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Metrics title"
            text = "Metrics response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_promote_properties(self):
        """
        The properties for the "promote" sub-command
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
            'help_text': '*`promote`* _description here_',
            'help_examples': [
                '/run unity promote -e sr-dev -r us-east-1 -s protoservice',
                '/run unity promote -e sr-dev -r us-west-2 -s protoservice -c changeme'
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

    def invoke_promote(self, cmd_inputs):
        """
        Placeholder for "promote" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_promote")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Promote code section #### output to "text" & "title".
        
            # End Promote code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Promote title"
            text = "Promote response. Fill in here"
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


def get_first_item_in_list(items_list):
    return next(iter(items_list or []), None)


def get_images_from_repo(ecr_client, reg_id, reg_name):
    """

    :param ecr_client:
    :param reg_id:
    :param reg_name:
    :return: text
    """
    response = ecr_client.describe_images(
        registryId=reg_id,
        repositoryName=reg_name)

    print('get_images_from_repo( id={}, name={} )'.format(reg_id, reg_name))
    print('{}'.format(response))

    text = ''
    image_list = response.get('imageDetails')
    for curr_image in image_list:
        sha = curr_image.get('imageDigest')
        size = curr_image.get('imageSizeInBytes')
        push_time = curr_image.get('imagePushedAt')
        image_tag_list = curr_image.get('imageTags')

        short_sha = cti_helper_util.shorten_string(sha, 9)
        end_of_sha = sha[-4:]

        push_time_size = len(push_time)
        short_push_time = push_time[5:]
        short_push_time = short_push_time[:-6]

        first_tag = get_first_item_in_list(image_tag_list)

        text += ' sha256:..{}, {}, {} bytes\n      {}\n'.format(end_of_sha, short_push_time, size, first_tag)

    text += '---\n'

    return text


def create_session_for_unity_dev_pipeline():
    """
    The ... role needs to be in place
    :return:
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::0123456789012:role/UnityPipelineCmdRole',  # TODO: Replace with actual role ARN
        RoleSessionName='UnityPipelineCmdRole')
    return session

# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."


def test_cases_cmd_unity_main():
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