"""Implements Jupyter command by asnyder@roku.com"""
from __future__ import print_function
import traceback
from time import sleep

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface


class CmdJupyter(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'data,dsna-gpu',
            'sub_commands': ['start', 'stop', 'status', 'list'],
            'help_title': 'Control Data Science EC2 Instances',
            'permission_level': 'dev',
            'props_start': self.get_start_properties(),
            'props_stop': self.get_stop_properties(),
            'props_status': self.get_status_properties(),
            'props_list': self.get_list_properties()
        }

        return props

    def get_start_properties(self):
        """
        The properties for the "start" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`start`* _Data-Science group instance_',
            'help_examples': [
                '/run jupyter start -n dsna-asnyder'
            ],
            'switch-templates': [],
            'switch-n': {
                'aliases': ['n', 'name'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Instance to start'
            },
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
            slack_user_name = cmd_inputs.get_slack_user_name()
            arg_name = cmd_inputs.get_by_key('name')
        
            # Start Start code section #### output to "text" & "title".
            print('User: {} is trying to START instance: {}'.format(slack_user_name, arg_name))

            session = cti_helper_util.create_cloudtech_session()
            region = 'us-east-1'
            ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)
            ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)

            # Get Instance-Id and verify tagged with LightSwitch_Group = Jupyter tag.
            ec2_inst_id = get_ec2_instance_id_for_name(arg_name, session, region)
            text = ''
            status = get_simple_status_for_ec2_inst_id(ec2_inst_id, session, region)

            if status == 'running':
                text = '*Cannot start!* *`{}`* is already running.\n--'.format(arg_name)
                status_text = get_status_info_for_ec2_instance(ec2_inst_id, ec2_client)
                text += '\n{}'.format(status_text)

            elif status != 'stopped':
                text = 'Cannot start until *`{}`* is in stopped status.  Status: *{}*'.format(arg_name, status)
            else:
                ec2_resource_instance = ec2_resource.Instance(ec2_inst_id)
                ec2_resource_instance.start()

                # Make the System's Manager call. This command needs to be delay by about one minute.
                ssm_client = aws_util.get_boto3_client_by_name('ssm', session, region)

                ssm_document_name = 'LightSwitch_Jupyter_StartJupyterLabs'
                found_ssm_doc = debug_find_ssm_document(ssm_client, ssm_document_name)

                # Delay command by a few (45) seconds. hack.
                sleep(45)

                if found_ssm_doc:
                    print('Send command to machine: {}, id={}'.format(arg_name, ec2_inst_id))
                    response_cmd_send = ssm_client.send_command(
                        InstanceIds=[ec2_inst_id],
                        DocumentName=ssm_document_name,
                        TimeoutSeconds=300,
                        OutputS3BucketName='dsna-data',
                        OutputS3KeyPrefix='LightSwitch')
                    print('response_cmd_send = {}'.format(response_cmd_send))

                # Add the needed tags.
                time = aws_util.get_prop_table_time_format()
                time_string = '{}'.format(time)

                tag_list = []
                owner_tag = {
                    'Key': 'Jupyter_Owner',
                    'Value': slack_user_name
                }
                last_change_tag = {
                    'Key': 'Jupyter_Last_Change',
                    'Value': time_string
                }
                # Automatic shutdown tag.

                # Delayed Start tag.

                tag_list.append(owner_tag)
                tag_list.append(last_change_tag)

                ec2_resource_instance.create_tags(
                    Tags=tag_list
                )

                text = '*Starting* *`{}`*... should take a minute.\n'.format(arg_name)
                text += 'Verify with `/run jupyter status` command.'
            # End Start code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Start GPU {} machine".format(arg_name)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_stop_properties(self):
        """
        The properties for the "stop" sub-command

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`stop`* _Data Science group instance_',
            'help_examples': [
                '/run jupyter stop -n dsna-gpu'
            ],
            'switch-templates': [],
            'switch-n': {
                'aliases': ['n', 'name'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Instance to stop'
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
            slack_user_name = cmd_inputs.get_slack_user_name()
            arg_name = cmd_inputs.get_by_key('name')
        
            # Start Stop code section #### output to "text" & "title".
            print('User: {} is trying to STOP instance: {}'.format(slack_user_name, arg_name))

            session = cti_helper_util.create_cloudtech_session()
            region = 'us-east-1'
            ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)

            # New logic here.
            # Get Instance-Id and verify tagged with LightSwitch_Group = Jupyter tag.
            ec2_inst_id = get_ec2_instance_id_for_name(arg_name, session, region)
            text = ''
            status = get_simple_status_for_ec2_inst_id(ec2_inst_id, session, region)

            if status != 'running':
                text = '*Cannot stop!*\n'
                text += '*`{}`* is not running. Current status: *{}*'.format(arg_name, status)
            else:
                ec2_resource_instance = ec2_resource.Instance(ec2_inst_id)
                ec2_resource_instance.stop()

                # Update the Jupyter_Last_Change tag.
                time = aws_util.get_prop_table_time_format()
                time_string = '{}'.format(time)
                ec2_resource_instance.create_tags(
                    Tags=[
                        {
                            'Key': 'Jupyter_Last_Change',
                            'Value': time_string
                         }
                    ]
                )
                text += '*Stopping* ... should take a minute.\n'
                text += 'Verify with `/run jupyter status` command.'

            # End Stop code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Stop {} machine".format(arg_name)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_status_properties(self):
        """
        The properties for the "status" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`status`* _for Data Science group machines_',
            'help_examples': [
                '/run jupyter status'
            ],
            'switch-templates': []
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
            response_url = cmd_inputs.get_response_url()
        
            # Start Status code section #### output to "text" & "title".
            session = cti_helper_util.create_cloudtech_session()
            region = 'us-east-1'
            ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)
            ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)

            list_ec2_inst_ids = []
            # Get the tagging client.
            filters = [{'Name': 'tag:LightSwitch_Group', 'Values': ['Jupyter']}]
            for curr_instance in ec2_resource.instances.filter(Filters=filters):
                curr_instance.instance_id
                list_ec2_inst_ids.append(curr_instance.instance_id)

            # NOTE: Alternative to above is:
            # ec2_instance_ids_for_light_switch_group

            text = ''
            count = 0
            for curr_id in list_ec2_inst_ids:
                if count > 0:
                    text += '---\n'
                count += 1
                text += get_status_info_for_ec2_instance(curr_id, ec2_client)

            if count == 0:
                text = 'No machines found.'

            # End Status code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Status Juputer machines"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_list_properties(self):
        """
        The properties for the "status" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`list`* _for instances tagged for jupyter project_',
            'help_examples': [
                '/run jupyter list'
            ],
            'switch-templates': []
        }
        return props

    def invoke_list(self, cmd_inputs):
        """
        This is the list sub-command. It looks for all EC2 Instances tagged with
        "LightSwitch_Group: Jupyter". It then collects all the names.
        "LightSwitch_Instance: <name>" and displays those.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_list")
            response_url = cmd_inputs.get_response_url()

            # Start Status code section #### output to "text" & "title".
            session = cti_helper_util.create_cloudtech_session()
            region = 'us-east-1'
            # ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)

            ec2_id_list = ec2_instance_ids_for_light_switch_group('Jupyter', session, region)
            name_list = get_ec2_instance_names(ec2_id_list, session, region)

            text = ''
            count = 0
            for curr_name in name_list:
                if count > 0:
                    text += '\n'
                count += 1
                text += '{}'.format(curr_name)

            if count == 0:
                text = 'No machines found.'

            # End Status code section. ####

            # Standard response below. Change title and text for output.
            title = "List Light-Switch names"
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


def get_status_info_for_ec2_instance(curr_id, ec2_client):
    """
    Print out in text format the status of an EC2 Instance.
    :param curr_id:
    :param ec2_client:
    :return: multi-lines of Slack-UI formatted text.
    """
    try:
        response = ec2_client.describe_instances(
            InstanceIds=[curr_id]
        )

        text = ''

        if response:
            reservations = response.get('Reservations')
            for curr_res in reservations:
                instances = curr_res.get('Instances')
                for curr_inst in instances:
                    state_dict = curr_inst.get('State')
                    state_name = state_dict.get('Name')
                    state_reason_dict = curr_inst.get('StateReason')
                    if state_reason_dict:
                        state_reason_msg = state_reason_dict.get('Message')
                    else:
                        state_reason_msg = '.'
                    private_ip = curr_inst.get('PrivateIpAddress')
                    instance_type = curr_inst.get('InstanceType')

                    tag_list = curr_inst.get('Tags')
                    jupyter_owner_tag = None
                    jupyter_last_change = None
                    instance_name = None
                    for curr_tag in tag_list:
                        tag_key = curr_tag.get('Key')
                        if tag_key == 'Jupyter_Owner':
                            jupyter_owner_tag = curr_tag.get('Value')
                        elif tag_key == 'Jupyter_Last_Change':
                            jupyter_last_change = curr_tag.get('Value')
                        elif tag_key == 'Name':
                            instance_name = curr_tag.get('Value')

                    if instance_name:
                        text += '*`{}`* {} - *{}*\n'.format(instance_name, instance_type, state_name.upper())
                    else:
                        text += '*`???`* {} - *{}*\n'.format(instance_type, state_name.upper())
                    if state_name != 'running' and state_reason_msg != '.':
                        text += '_Reason: {}_\n'.format(state_reason_msg)
                    text += '{} - {}\n'.format(curr_id, private_ip)
                    if jupyter_last_change:
                        text += '_Last Change: {}_\n'.format(jupyter_last_change)
                    if jupyter_owner_tag:
                        text += '_Owner: {}_\n'.format(jupyter_owner_tag)

        return text

    except Exception as ex:
        bud_helper_util.log_traceback_exception(ex)
        print('Error for {}. Reason: {}'.format(curr_id, ex.message))
        return 'Error {}? Reason: {}\n'.format(curr_id, ex.message)


def get_ec2_instance_ids_by_name_tag(ec2_instance_name, session, region):
    """

    :param ec2_instance_name:
    :param session:
    :param region:
    :return: List of EC2 Instance Ids with this name.
    """
    ret_val = []

    tag_client = aws_util.get_boto3_client_by_name('resourcegroupstaggingapi', session, region)

    response = tag_client.get_resources(
        TagFilters=[
            {
                'Key': 'Name',
                'Values': [ec2_instance_name]
            },
        ],
        ResourceTypeFilters=['ec2']
    )

    tag_map_list = response.get('ResourceTagMappingList')
    if tag_map_list:
        for curr_tag_map in tag_map_list:
            arn = curr_tag_map.get('ResourceARN')

            # arn:aws:ec2:us-east-1:141602222194:instance/i-01ed7a780b7ee05bd
            # to
            # i-01ed7a780b7ee05bd
            parts = arn.split(':instance/')
            ec2_instance_id = parts[1]

            ret_val.append(ec2_instance_id)

    return ret_val


def is_ec2_tagged_with(curr_ec2_id, session, region, tag_key_name, tag_value=None):
    """
    Check that this instance is tagged.
    :param curr_ec2_id:
    :param session:
    :param region:
    :param tag_key_name:
    :param tag_value:
    :return: True | False.  True if this isn't is tagged.
    """
    print('Checking {} for tag {}'.format(curr_ec2_id, tag_key_name))
    tag_client = aws_util.get_boto3_client_by_name('resourcegroupstaggingapi', session, region)
    tag_filter = {}
    tag_filter['Key'] = tag_key_name
    if tag_value:
        tag_filter['Values'] = [tag_value]

    response = tag_client.get_resources(
        TagFilters=[tag_filter],
        ResourceTypeFilters=['ec2']
    )

    tag_map_list = response.get('ResourceTagMappingList')
    if tag_map_list:
        for curr_tag_map in tag_map_list:
            arn = curr_tag_map.get('ResourceARN')

            # arn:aws:ec2:us-east-1:141602222194:instance/i-01ed7a780b7ee05bd
            # to
            # i-01ed7a780b7ee05bd
            parts = arn.split(':instance/')
            ec2_instance_id = parts[1]

            if ec2_instance_id == curr_ec2_id:
                return True

    print("Didn't find {}, with filter: {}".format(curr_ec2_id, tag_filter))
    return False


def get_ec2_instance_id_for_name(arg_name, session, region):
    """
    Looks for a single instance with this name and the proper LightSwitch_Group tag.

    If it doesn't find any instances that match the name and is tagged throw an error.
    If it finds too many also throw an error.

    :param arg_name:
    :param session:
    :param region:
    :return:
    """
    tagged_id_list = []
    raw_id_list = get_ec2_instance_ids_by_name_tag(arg_name, session, region)
    print('{} ... raw_id_list={}'.format(arg_name,raw_id_list))
    print('Remove untagged (LightSwitch_Group: Jupyter)instances.')

    for curr_ec2_id in raw_id_list:
        if is_ec2_tagged_with(curr_ec2_id, session, region, 'LightSwitch_Group', 'Jupyter'):
            tagged_id_list.append(curr_ec2_id)

    if len(tagged_id_list) == 0:
        print('ShowSlackError: too few instances.')
        raise ShowSlackError('Could not find tagged EC2 Instance named: *{}*'.format(arg_name))
    if len(tagged_id_list) > 1:
        print('ShowSlackError: too many instances.')
        raise ShowSlackError('Found multiple EC2 Instances named: *{}*'.format(arg_name))

    ec2_inst_id = tagged_id_list[0]

    print('{} ec2_instance_id = {}'.format(arg_name, ec2_inst_id))
    return ec2_inst_id


def get_jupyter_ec2_instance_id(session, region):
    """

    :param session:
    :param region:
    :return:
    """
    id_list = get_ec2_instance_ids_by_name_tag('Tensorflow', session, region)
    if len(id_list) == 0:
        raise ShowSlackError('Could not find "Tensorflow" EC2 Instance')
    if len(id_list) > 1:
        raise ShowSlackError('Found multiple "Tensorflow" EC2 Instances')
    print('Tensorflow ... id_list={}'.format(id_list))
    jupyter_ec2_inst_id = id_list[0]

    print('Tensorflow ec2_instance_id = {}'.format(jupyter_ec2_inst_id))
    return jupyter_ec2_inst_id


def get_simple_status_for_ec2_inst_id(ec2_inst_id, session, region):
    """
    Get just one line <running | stopping | stopped> status for
    ec2 instance, which is needed by both the start and stop commands.
    :param ec2_inst_id:
    :param session:
    :param region:
    :return: <running | stopping | stopped>
    """
    ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)
    ec2_instance = ec2_resource.Instance(ec2_inst_id)

    state_name = ec2_instance.state.get('Name')
    return state_name


def get_simple_status_jupyter(session, region):
    """
    Get just one line <running | stopping | stopped> status for
    jupyter instance, which is needed by both the start and stop commands.
    :param session:
    :param region:
    :return: True if tests pass False if they fail.
    """
    jupyter_ec2_inst_id = get_jupyter_ec2_instance_id(session, region)
    ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)
    jupyter_instance = ec2_resource.Instance(jupyter_ec2_inst_id)

    state_name = jupyter_instance.state.get('Name')
    return state_name

# #### This section contains tags for LightSwitch tags. ###


def ec2_instance_ids_for_light_switch_group(group_name, session, region):
    """
    Returns a list of ec2_instance ids that have the "LightSwitch_Group" tag with a certain value.
    :param group_name:
    :param session:
    :param region:
    :return: list of ec2_instance ids.
    """
    ret_val = []
    tag_client = aws_util.get_boto3_client_by_name('resourcegroupstaggingapi', session, region)

    response = tag_client.get_resources(
        TagFilters=[
            {
                'Key': 'LightSwitch_Group',
                'Values': [group_name]
            },
        ],
        ResourceTypeFilters=['ec2']
    )

    tag_map_list = response.get('ResourceTagMappingList')
    if tag_map_list:
        for curr_tag_map in tag_map_list:
            arn = curr_tag_map.get('ResourceARN')

            # arn:aws:ec2:us-east-1:141602222194:instance/i-01ed7a780b7ee05bd
            # to
            # i-01ed7a780b7ee05bd
            parts = arn.split(':instance/')
            ec2_instance_id = parts[1]

            ret_val.append(ec2_instance_id)

    return ret_val


def get_ec2_instance_names(ec2_id_list, session, region):
    """
    Get all the values on "LightSwitch_Instance" for the list of ec2_instance ids.
    :param ec2_id_list:
    :param session:
    :param region:
    :return: list of string with names from "LightSwitch_Instance" tag.
    """
    ec2_resource = aws_util.get_boto3_resource_by_name('ec2', session, region)

    ret_val = []

    for curr_ec2_id in ec2_id_list:
        curr_instance = ec2_resource.Instance(curr_ec2_id)
        tag_list = curr_instance.tags
        for curr_tag in tag_list:
            curr_key = curr_tag.get('Key')
            if curr_key == 'Name':
                curr_value = curr_tag.get('Value')
                ret_val.append(curr_value)

    return ret_val


# NOTE: Project LightSwitch method below.
def create_ssm_single_line_cmd_doc(doc_name, doc_desc,  doc_command):
    """
    ssm seems to have a problem with YAML documents according to
    this post in Dec. 2017. (2 months ago).
      https://github.com/aws/aws-cli/issues/3013
    Will try JSON formatted document.
    :param doc_name: Name of SSM Document. like:  Jupyter::Start_Jupyter_Lab
    :param doc_desc: Description like: Start Jupyter lab on this machine.
    :param doc_command:
    :return:
    """

    # doc_command = escape_double_quotes(doc_command)

    ret_val = '{'
    ret_val += ' "schemaVersion": "2.2",'
    ret_val += ' "description": "{}",'.format(doc_desc)
    ret_val += ' "mainSteps":['
    ret_val += '  {'
    ret_val += '    "action": "aws:runShellScript",'
    ret_val += '    "name": "{}",'.format(doc_name)
    ret_val += '    "inputs": {'
    ret_val += '     "runCommand": ["{}"]'.format(doc_command)
    ret_val += '    }'
    ret_val += '  }'
    ret_val += ' ]'
    ret_val += '}'

    return ret_val


def debug_find_ssm_document(ssm_client, ssm_doc_name):
    """
    See if you can find a document with this name before trying to run it.
    If you cannot find it list all documents that don't start with AWS-...
    :param ssm_doc_name:
    :return: True if the document is found.
    """
    # until implemented.
    print('Looking for System Manager doc: {}'.format(ssm_doc_name))

    response = ssm_client.get_document(
        Name=ssm_doc_name
    )

    print('response= {}'.format(response))

    status = response.get('Status')
    if status == 'Failed':
        status_info = response.get('StatusInformation')
        print('Failed to find document. Status Info: {}'.format(status_info))
        return False
    return True


# Create document.

# Send Command.

# List of possible commands.
# send_command()  <-- Requires a document name.
# list_commands()  <-- Would be good to include in status command.
# list_command_invocations()   <-- Or maybe this is for the status command.
# get_command_invocations()
# cancel_command()

# Will also need  document commands.
# create_document
# get_document
# list_documents

# NOTE: We remove script create away from here and do send command for document:
#     LightSwitch_Jupyter_StartJupyterLabs

# Here is a work-flow specific to Jupyter group.
# response_doc_list = ssm_client.list_documents(DocumentFilterList=[{'key': 'Jupyter_start'}])
# print('response_doc_list = {}'.format(response_doc_list))
#
# response_doc_create = ssm_client.create_document(
#     Content='sudo -u ec2-user bash -c -l "jupyter lab &> /home/ec2-user/jupyter_out.txt &disown"',
#     Name='Jupyter::StartJupyterLab',
#     DocumentFormat='YAML',
#     DocumentType='Command'
# )
# print('response_doc_create = {}'.format(response_doc_create))


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_jupyter_main():
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