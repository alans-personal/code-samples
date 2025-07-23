"""Implements P4 command by redacted@email.com"""
from __future__ import print_function
import traceback

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface
import boto3
import json
import requests

class CmdP4(CmdInterface):

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
            'sub_commands': ['status'],
            'help_title': 'Check perforce server status.',
            'permission_level': 'dev',
            'props_status': self.get_status_properties()

        }

        return props


    def get_status_properties(self):
        """
        Get status of Perforce server
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`status`* _Status of Perforce server_',
            'help_examples': [
                '/run p4 status'
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

            # Start Status code section #### output to "text" & "title".

            # Get boto3 session to BAR account using the PerforceCrossAccountRole
            sts = boto3.client('sts')
            session = sts.assume_role(
                RoleArn='arn:aws:iam::123456789012:role/PerforceCrossAccountRole',
                RoleSessionName='PerforceCrossAccountRoleSession')

            print('debug session: {}'.format(session))

            # invoke the lambda function
            payload = {
                'cmd-meta-data': 'Perforce Status'
            }

            # check the result
            payload_str = json.dumps(payload)
            # payload_bytes = bytes(payload_str, encoding='utf8')
            payload_bytes = bytes(payload_str)

            print('debug payload: {}'.format(payload))

            lambda_client = aws_util.get_boto3_client_by_name('lambda', session, 'us-west-2')
            response = lambda_client.invoke(
                FunctionName='perforce-slackbot',
                InvocationType='RequestResponse',
                Payload=payload_bytes
            )

            resp_payload = json.loads(response['Payload'].read())

            print('debug response payload: {}'.format(resp_payload))

            perforce_status = get_status_from_database()
            print('Perforce Status from DynamoDB = {}'.format(perforce_status))
            send_msg_to_slack = False
            perforce_status_color = '#36a64f'  # GREEN if perforce is UP
            if ' down' in resp_payload:
                text = 'Perforce master server is DOWN: p4 info execution failed'
                perforce_status_color = '#ff3d3d'  # RED if perforce is DOWN

                if perforce_status != 'DOWN':
                    put_status_to_database("DOWN")
                    send_msg_to_slack = True
            elif ' up' in resp_payload:
                text = 'Perforce master server is UP: p4 info executed successfully'
                if perforce_status != 'UP':
                    put_status_to_database("UP")
                    send_msg_to_slack = True

            else:
                text = 'UNKNOWN RESPONSE: __'.format(resp_payload)

            # End Status code section. ####

            # Standard response below. Change title and text for output.
            title = 'Perforce Status'

            if send_msg_to_slack:
                post_message_to_slack_channel(title, text, color=perforce_status_color)

            return self.slack_ui_standard_response(title, text, color=perforce_status_color)
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

def post_message_to_slack_channel(title, text, color='#36a64f'):
    """
    Post a message to the #'sr-slack-deploy' channel.
    :param title:
    :param text:
    :param color:
    :return:
    """
    print("'#sr-slack-deploy' channel should get message.\n{}\n{}"
          .format(title, text))

    slack_message = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": text
            }
        ]
    }
    # url = "https://hooks.slack.com/services/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" #perforce channel
    # url = "https://hooks.slack.com/services/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" # shared channel.
    url = "https://hooks.slack.com/services/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" # perforce channel.
    res = requests.post(
        url=url,
        data=json.dumps(slack_message),
        headers={"Content-type": "application/json"}
    )
    print('Slack status code: {}'.format(res.status_code))


def get_status_from_database():
    dynamodb = boto3.resource('dynamodb')
    SLACK_SESSION_TABLE = dynamodb.Table('SlackBudSession')

    response = SLACK_SESSION_TABLE.get_item(
        Key={
            'slackBudSessionId': 'perforce-status'
        }
    )

    item = response.get('Item')
    if item:
        perforce_status = item.get('Status')
        return perforce_status
    else:
        return "UNKNOWN"


def put_status_to_database(status):
    dynamodb = boto3.resource('dynamodb')
    SLACK_SESSION_TABLE = dynamodb.Table('SlackBudSession')

    SLACK_SESSION_TABLE.put_item(
        Item={
            'slackBudSessionId': 'perforce-status',
            'Status': status
        }
    )


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_p4_main():
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