"""Implements Farm command by asnyder@roku.com"""
from __future__ import print_function
import traceback

import os
import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr
import requests
import json
import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.jwt_utils as jwt_utils
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface


class CmdFarm(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'farm',
            'sub_commands': ['deploy', 'inspect', 'undeploy', 'change', 'builds', 'status', 'debug'],
            'help_title': 'Manage Farms. Deploy, change, inspect, etc.',
            'permission_level': 'dev',
            'props_deploy': self.get_deploy_properties(),
            'props_inspect': self.get_inspect_properties(),
            'props_undeploy': self.get_undeploy_properties(),
            'props_change': self.get_change_properties(),
            'props_builds': self.get_builds_properties(),
            'props_status': self.get_status_properties(),
            'props_debug': self.get_debug_properties(),
        }

        return props


    def get_deploy_properties(self):
        """
        The properties for the "deploy" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`deploy`* _deploy or update the version of a services on a farm_',
            'help_examples': [
                '/run farm deploy -f groot -s protoservice -v 20180803-9-30add49-master',
                '/run farm deploy -f deckard -s my-service'
            ],
            'switch-templates': ['service'],
            'switch-f': {
                'aliases': ['f', 'farm'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Farm'
            },
            'switch-v': {
                'aliases': ['v', 'version'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Version of service to deploy. Default value is latest'
            },
            'switch-t': {
                'aliases': ['t', 'targetregion'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Region where service runs. Default: "all". Valid: "us-east-1", "us-west-2"'
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
            start_time = bud_helper_util.start_timer()

            arg_farm = cmd_inputs.get_by_key('farm')
            arg_service = cmd_inputs.get_by_key('service')
            arg_version = cmd_inputs.get_by_key('version')

            arg_target_regions = cmd_inputs.get_by_key('targetregion')
            if not arg_target_regions:
                arg_target_regions = 'all'

            arg_user_name = cmd_inputs.get_slack_user_name()

            # check that this service name is valid.
            if not service_is_in_build_numbers_table(arg_service):
                raise ValueError("Service not in BuildNumbers table: {}".format(arg_service))

            # verify that this version is valid.
            if not version_is_in_farm_build_version_table(arg_service, arg_version):
                raise ValueError("Could not find version: {} - {}".format(arg_service, arg_version))

            if arg_version:
                text = '*Deploying*\n  Farm: *{}*\n  Service: *{}*\n  Version: *{}*'.format(arg_farm, arg_service, arg_version)
            else:
                raise ShowSlackError("Need to include version.")

            text += '\nRegion(s): {}'.format(arg_target_regions)
            print(text)

            bud_helper_util.print_delta_time(start_time, 'looked for file')

            # Do HTTP POST of this file to Gardener.
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Accept-Charset': 'utf-8',
                'X-Roku-Farm-Target-Region': arg_target_regions
            }
            headers = jwt_utils.add_jwt_token_to_headers(headers)

            if arg_version:
                headers = add_deploy_headers_for_service_version(
                    headers, arg_service, arg_version, arg_user_name)
            gardener_api_url = get_gardener_api_url(cmd_inputs)
            api_url = 'https://{}/farm/{}/service/{}/{}'\
                .format(gardener_api_url, arg_farm, arg_service, arg_version)

            text += '```\n'
            # text += '\nPOST to: {}'.format(api_url)
            text += '\nHTTP Headers\n'
            printable_headers = headers.copy()

            # Remove JWT token from Slack output.
            printable_headers.pop('Authorization', None)
            text += '```{}```'.format(printable_headers)

            print('Sending url: {}'.format(api_url))
            print('Sending headers: {}'.format(headers))

            response = requests.post(api_url, data='', headers=headers)
            if response.status_code == 200:
                text += '\n`Success`'
            else:
                text += '\n`Failed` code: {}'.format(response.status_code)

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Deploy service into farm"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_inspect_properties(self):
        """
        The properties for the "inspect" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`inspect`* _list the services deployed on a farm_',
            'help_examples': [
                '/run farm inspect -f deckard'
            ],
            'switch-templates': [],
            'switch-f': {
                'aliases': ['f', 'farm'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Farm'
            }
        }
        return props

    def invoke_inspect(self, cmd_inputs):
        """
        Placeholder for "inspect" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_inspect")
            start_time = bud_helper_util.start_timer()

            arg_farm = cmd_inputs.get_by_key('farm')

            # Start Inspect code section #### output to "text" & "title".
            text = "farm: {}\n".format(arg_farm)

            headers = {'Content-Type': 'application/json'}
            headers = jwt_utils.add_jwt_token_to_headers(headers)

            gardener_api_url = get_gardener_api_url(cmd_inputs)
            api_url = 'https://{}/farm/{}/inspect' \
                .format(gardener_api_url, arg_farm)
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                text += build_inspect_response(response.text)
            else:
                text += '\nFAILED. code: {}'.format(response.status_code)

            # End Inspect code section. ####

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Inspect Farm: {}".format(arg_farm)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_status_properties(self):
        """
        The properties for the "inspect" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`status`* _show status of services on all farms_',
            'help_examples': [
                '/run farm status -s worldview'
            ],
            'switch-templates': [],
            'switch-s': {
                'aliases': ['s', 'service'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the service'
            }
        }
        return props

    def invoke_status(self, cmd_inputs):
        """
        Placeholder for "inspect" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_status")
            start_time = bud_helper_util.start_timer()

            arg_service = cmd_inputs.get_by_key('service')

            # Start Inspect code section #### output to "text" & "title".
            text = "farm: {}\n".format(arg_service)

            headers = {'Content-Type': 'application/json'}
            headers = jwt_utils.add_jwt_token_to_headers(headers)

            gardener_api_url = get_gardener_api_url(cmd_inputs)
            api_url = 'https://{}/service/{}/status' \
                .format(gardener_api_url, arg_service)
            response = requests.get(api_url, headers=headers)

            if response.status_code == 200:
                text += build_service_status_response(response.text)
            else:
                text += '\nFAILED. code: {}'.format(response.status_code)

            # End Inspect code section. ####

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Status of Service: {}".format(arg_service)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_debug_properties(self):
        """
        The properties for the "inspect" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`debug`* _show debug information for a service_',
            'help_examples': [
                '/run farm debug -s uploads'
            ],
            'switch-templates': [],
            'switch-s': {
                'aliases': ['s', 'service'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the service'
            }
        }
        return props

    def invoke_debug(self, cmd_inputs):
        """
        Placeholder for "inspect" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_debug")
            start_time = bud_helper_util.start_timer()

            arg_service = cmd_inputs.get_by_key('service')

            # Start Inspect code section #### output to "text" & "title".
            text = "farm: {}\n".format(arg_service)


            # NOTE: Ideally this would be a RESTful call to gardener...
            # instead we call the database directly, which shouldn't be done expect for a quicker result.
            # ToDo: in Gardener 2.0 add the API and replace this.
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table('FarmServiceStatus')

            response = table.query(
                IndexName='ByService',
                KeyConditionExpression=Key('serviceName').eq(arg_service)
            )

            for i in response['Items']:
                farm_name = i.get('farmName')
                version = i.get('version')
                status = i.get('status')
                error_msg = i.get('error_msg')
                error_details = i.get('error_details')

                text += '\n=== {} - {}\n'.format(farm_name, version)
                text += ' {} - {}\n'.format(status, error_msg)
                print('error_detail = {}'.format(error_details))
                if not error_details:
                    print('WARN: error_detail was None')
                elif error_details != '-':
                    text += "```{}```\n".format(error_details)

            # End Inspect code section. ####

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Error info for Service: {}".format(arg_service)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_undeploy_properties(self):
        """
        The properties for the "undeploy" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`undeploy`* _Remove a service completely from a farm_',
            'help_examples': [
                '/run farm undeploy -f deckard -s my-service'
            ],
            'switch-templates': ['service'],
            'switch-f': {
                'aliases': ['f', 'farm'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Farm'
            }
        }
        return props

    def invoke_undeploy(self, cmd_inputs):
        """
        Placeholder for "undeploy" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_undeploy")
            start_time = bud_helper_util.start_timer()

            arg_farm = cmd_inputs.get_by_key('farm')
            arg_service = cmd_inputs.get_by_key('service')

            arg_user_name = cmd_inputs.get_slack_user_name()
        
            # Start Remove code section #### output to "text" & "title".
            text = "Undeploy service: `{}` from farm: `{}`".format(arg_service, arg_farm)
        
            # End Remove code section. ####

            headers = {'Content-Type': 'application/json'}
            headers = jwt_utils.add_jwt_token_to_headers(headers)
            headers = add_deploy_headers_for_service_version(
                headers, arg_service, None, arg_user_name)

            gardener_api_url = get_gardener_api_url(cmd_inputs)
            api_url = 'https://{}/farm/{}/service/{}'\
                .format(gardener_api_url, arg_farm, arg_service)

            response = requests.delete(api_url, headers=headers)

            if response.status_code == 200:
                body = response.text
                print('undeploy body = _{}_'.format(body))

                if 'ERROR' in body:
                    text += '\n{}'.format(build_error_message_from_json_text(body))
                else:
                    text += '\n`Success`'
            else:
                text += '\nFAILED. code: {}'.format(response.status_code)

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Undeploy service:{} from farm:{}".format(arg_service, arg_farm)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_change_properties(self):
        """
        The properties for the "change" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`change`* _change the mode of a service_',
            'help_examples': [
                '/run farm change -f deckard -s my-service -m run'
            ],
            'switch-templates': ['service'],
            'switch-f': {
                'aliases': ['f', 'farm'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Name of the Farm'
            },
            'switch-m': {
                'aliases': ['m', 'mode'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Modes: < run | stop | delete >'
            }
        }
        return props

    def invoke_change(self, cmd_inputs):
        """
        Placeholder for "change" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_change")
            start_time = bud_helper_util.start_timer()

            arg_farm = cmd_inputs.get_by_key('farm')
            arg_service = cmd_inputs.get_by_key('service')
            arg_mode = cmd_inputs.get_by_key('mode')

            arg_user_name = cmd_inputs.get_slack_user_name()

            # Verify mode input.
            valid_modes_list = ['run', 'stop', 'delete']
            if arg_mode not in valid_modes_list:
                raise ShowSlackError(
                    'Invalid mode setting!. Was: {}. Expecting: <run|stop|delete>'.format(arg_mode)
                )

            # Start Remove code section #### output to "text" & "title".
            text = "farm: `{}` service: `{}` mode: `{}`".format(arg_farm, arg_service, arg_mode)

            # End Remove code section. ####

            headers = {'Content-Type': 'application/json'}
            headers = jwt_utils.add_jwt_token_to_headers(headers)
            headers = add_deploy_headers_for_service_version(
                headers, arg_service, None, arg_user_name)

            api_url = 'https://gardener.farmlab.asnyder.com/farm/{}/service/{}/mode/{}' \
                 .format(arg_farm, arg_service, arg_mode)

            print('Change command HTTP Headers: {}'.format(headers))
            print('api_url: {}'.format(api_url))

            response = requests.put(api_url, headers=headers)

            if response.status_code == 200:
                response_text = response.text
                print('response.text: _{}_'.format(response_text))
                if 'ERROR' in response_text:
                    text += '\n{}'.format(build_error_message_from_json_text(response_text))
                else:
                    text += '\n`Success`'
            else:
                text += '\nFAILED. code: `{}`'.format(response.status_code)

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Change service mode: < run | stop | delete >"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def check_access_for_s3_bucket(self, bucket_name):
        """
        determine access for S3 bucket.
        :param s3_bucket:
        :return:
        """
        try:
            s3 = boto3.resource('s3')
            s3.meta.client.head_bucket(Bucket=bucket_name)
            print("Bucket Exists with access! bucket: {}".format(bucket_name))
            return True
        except botocore.exceptions.ClientError as e:
            # If a client error is thrown, then check that it was a 404 error.
            # If it was a 404 error, then the bucket does not exist.
            error_code = int(e.response['Error']['Code'])
            if error_code == 403:
                print("Private Bucket. Forbidden Access! bucket: {}".format(bucket_name))
                return True
            elif error_code == 404:
                print("Bucket Does Not Exist! bucket: {}".format(bucket_name))
                return False

    def get_builds_properties(self):
        """
        The properties for the "builds" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`builds`* _list the services versions_',
            'help_examples': [
                '/run farm builds -s protoservice'
            ],
            'switch-templates': ['service']
        }
        return props

    # NOTE: This service doesn't go through the gardener, it goes
    # straight to the database, since it is UI only function.
    def invoke_builds(self, cmd_inputs):
        """
        Placeholder for "builds" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_builds")
            start_time = bud_helper_util.start_timer()

            arg_service = cmd_inputs.get_by_key('service')

            # Start Inspect code section #### output to "text" & "title".
            text = "service: {}\n".format(arg_service)

            # connet to database in us-west-2 region.
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table('FarmBuildVersion')

            response = table.query(
                KeyConditionExpression=Key('serviceName').eq(arg_service)
            )

            build_list = []
            for i in response['Items']:
                print(i['serviceName'], ":", i['buildNumber'])
                build_list.append(i['buildNumber'])
                # text += '  {}\n'.format(i['buildNumber'])

            build_list.sort(reverse=True)
            for j in build_list:
                text += '  {}\n'.format(j)

            # End Builds code section. ####

            bud_helper_util.print_delta_time(start_time, 'finished')
            # Standard response below. Change title and text for output.
            title = "Service Builds: {}".format(arg_service)
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


def service_is_in_build_numbers_table(arg_service):
    """

    :param arg_service:
    :return: True if found in table, otherwise False
    """
    # Look for entry in table, and update this.
    return True


def version_is_in_farm_build_version_table(arg_service, arg_version):
    """
    Verify this version, can be found in the FarmBuildVersion table.
    :param arg_service:
    :param arg_version:
    :return:
    """
    return True


def get_yaml_seed_file_url(arg_service, arg_version):
    """
    Constuct the path to get the yaml seed file, which is either in the git repo, or
    located in an S3 bucket. (In theory it could also be in an HTTP Server, but we won't
    implement that.
    :return: String URL that points to location of <serviceName>.seed_info.yaml file.
    """
    # Look for the seedUrl attribute in FarmBuildVersion table,
    # or "gitUrl" in "BuildNumbers" table which is the old soon to be DEPRECATED way.

    has_seed_url = True
    dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
    farm_build_version_table = dynamodb.Table('FarmBuildVersion')
    # Find the gitUrl for the service to download YAML file
    response = farm_build_version_table.get_item(
        Key={
            'serviceName': arg_service,
            'buildNumber': arg_version
        }
    )
    item = response.get('Item')
    if not item:
        has_seed_url = False
        print('No version for service in FarmBuildVersion table: {} - {}'.format(arg_service, arg_version))

    seed_url = None
    if has_seed_url:
        seed_url = item.get('seedUrl')
        if not seed_url:
            has_seed_url = False

    if not has_seed_url:
        # connected to database in us-west-2 region.
        table = dynamodb.Table('BuildNumbers')

        # Find the gitUrl for the service to download YAML file
        response = table.get_item(
            Key={
                'serviceName': arg_service
            }
        )
        item = response.get('Item')
        if not item:
            raise ShowSlackError('Could not find service: {}'.format(arg_service))

        git_url = item.get('gitUrl')
        if not git_url:
            raise ShowSlackError('Could not find gitUrl for service: {}'.format(arg_service))

        service_git_url = '{}/raw/master/{}.seed_info.yaml'.format(git_url, arg_service)
        print('Using old method to deploy. service_git_url={}'.format(service_git_url))
        seed_url = service_git_url

    if not seed_url:
        raise ShowSlackError('Could not find YALM file for: {} - {}'.format(arg_service, arg_version))

    return seed_url


def get_git_read_only_token():
    """
    Get the GitLab Repo private token from SSM Parameter Store.
    :return: String from Param Store
    """
    return aws_util.get_ssm_parameter('slack_bud_read_only_gitlab_token')


def add_deploy_headers_for_service_version(headers, arg_service, arg_version, arg_user_name):
    """
    If Deployment is including a version add it to Http headers.
    :param headers:
    :param arg_service:
    :param arg_version:
    :param arg_user_name:
    :return: headers with added X-Roku version and Repo-Url version.
    """
    # Look for a specific version from the FarmBuildHistory Table.
    try:
        # Added the user_name header if present.
        if arg_user_name:
            headers['X-Roku-Farm-User-Name'] = arg_user_name

        if arg_version:
            # Look for this version of the service in the table. Be picky.
            dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
            table = dynamodb.Table('FarmBuildVersion')

            response = table.query(
                KeyConditionExpression=Key('serviceName').eq(arg_service)
            )

            version_found = False
            for i in response['Items']:
                # look for the buildNumber match to arg_version
                service_name = i.get('serviceName')
                build_number = i.get('buildNumber')
                repo_url = i.get('repo')
                print(service_name, ":", build_number)
                if build_number == arg_version:
                    print('Found match! {} repo_url: {}'.format(arg_version, repo_url))
                    headers['X-Roku-Farm-Deploy-Repo-Url'] = repo_url
                    version_found = True

            if not version_found:
                print('Failed to find build! service: {} - {}'.format(arg_service, arg_version))

    except Exception as e:
        print('ERROR: Failed to deploy: {} - {}'.format(arg_service, arg_version))
        bud_helper_util.log_traceback_exception(e)
        raise ShowSlackError('Failed to deploy version: {}. See log for details'.format(arg_version))

    return headers


def build_inspect_response(response_text):
    """
    Build the response for from Gardener API response.
    :param response_text:
    :return: string
    """
    if response_text.find('SUCCESS') > 0:
        # get part after 'message ':
        content = response_text.split('"message":', 1)
        message = content[1]
        item_list = message.split('\\n')

        max_column_width = 10
        parts_list = []
        for curr_item in item_list:
            curr_item = curr_item.replace('\"', '')
            if curr_item.find(':') > 0:
                # for each line split on ':'
                parts = curr_item.split(':', 1)
                parts_list.append(parts)

                if len(parts[0]) > max_column_width:
                    max_column_width = len(parts[0])

        # build the response.
        if max_column_width > 40:
            max_column_width = 40
        ret_val = '```'
        for curr_part in parts_list:
            part0 = curr_part[0]
            part0 = part0.replace('\\', '')
            cp_len = len(part0)
            num_spaces = max_column_width - cp_len
            ret_val += '\n'
            ret_val += part0
            if num_spaces > 0:
                ret_val += ' ' * num_spaces
            ret_val += ': '
            part1 = curr_part[1]
            part1 = part1.replace('\\','')
            ret_val += part1
        # Look for Farm with no services.
        if ret_val == "```":
            ret_val += '\n No services running.'

        ret_val += '\n```'
        return ret_val
    else:
        return "No services found.\n{}".format(response_text)


def build_service_status_response(response_text):
    """
    Build the response for status from Gardener API response.
    :param response_text: This is likely a JSON String.
    :return: string in Slack UI format.
    """
    # turn this into
    resp = json.loads(response_text)

    lines_map = {}

    msg_status = resp.get('status')
    print('type(status)'.format(type(msg_status)))
    if msg_status:
        if msg_status == 'SUCCESS':
            data = resp.get('data')
            services = data.get('services')
            if len(services) == 0:
                return '`No running service found.`'
            for s in services:
                status = s.get('status')
                version = s.get('version')
                farm = s.get('farmName')
                running_count = s.get('running_count')
                err_message = s.get('err_message')

                if status == 'ERROR':
                    # Print an error line
                    map_line = '%-20s %s\n  %-19s %s\n-\n' % (farm, version, status, err_message)
                else:
                    # Print a success line
                    map_line = '%-20s %s\n  %-19s #Running: %s\n-\n' % (farm, version, status, running_count)

                # lines.append(line)
                lines_map[farm] = map_line

            ret_val = '```'
            title1 = '    FARM    '
            title1a = '-------------'
            title2 = '     VERSION     '
            title2a = '---------------'
            ret_val += '%-20s %s\n' % (title1, title2)
            ret_val += '%-20s %s\n' % (title1a, title2a)
            for key in sorted(lines_map.iterkeys()):
                ret_val += lines_map.get(key)
            ret_val += '```'

            return ret_val

        else:
            # Assume error and return that.
            message = resp.get('message')
            return 'ERROR: {}'.format(message)
    else:
        return 'Error: Unknown response. Check logs.'


def build_error_message_from_json_text(response_text):
    """
    Expect a message in the form:
     {"status":"ERROR","message":"\"ERROR: Cannot go from RUN to DELETE state.\""}

     Parse out just the part after "message":

     If the string isn't in the format log a warning to the log.
    :param response_text: Expect something like:
        {"status":"ERROR","message":"\"ERROR: Cannot go from RUN to DELETE state.\""}
    :return:
    """
    if response_text.find('ERROR'):
        content = response_text.split('"message":', 1)
        message = content[1]
        message = message.replace('\\','')
        message = message.replace('"','')
        message = message.replace('}','')

        return message
    else:
        print('WARN: Unexpected JSON in build_error_message_from_json_text method. _{}_'
              .format(response_text))
        return response_text


def get_gardener_api_url(cmd_inputs):
    """
    Returns the proper gardener api url.
    if /run
      gradener.farmlab.asnyder.com
    if /rundev
      gardener-dev.farmlab.asnyder.com

    :param cmd_inputs:
    :return: url to gardner api
    """
    slack_env = cmd_inputs.get_slack_bud_env()
    if slack_env == 'dev':
        print('Calling: gardener-dev.farmlab.asnyder.com')
        return 'gardener-dev.farmlab.asnyder.com'
    elif slack_env == 'prod':
        print('Calling: gardener.farmlab.asnyder.com')
        return 'gardener.farmlab.asnyder.com'

    raise ValueError('Unknown SlackBud environment! '
                     'Expected < dev | prod >.  '
                     'Was: {}'.format(slack_env))


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."


def test_cases_cmd_farm_main():
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
