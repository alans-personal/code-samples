"""Entry point for all slack calls"""
import json
from urlparse import parse_qs
from cmds.cmd_inputs import CmdInputs
from cmds.cmds_version import CmdVersion
from cmds.cmds_help import CmdHelp
from cmds.cmds_untagged import CmdUntagged
from cmds.cmds_user import CmdUser
from cmds.cmds_cmd import CmdCmd
from cmds.cmds_spend import CmdSpend
from cmds.cmds_farm import CmdFarm
from cmds.cmds_apps_flamegraph import CmdApps_Flamegraph
from cmds.cmds_jupyter import CmdJupyter
from cmds.cmds_awslogin import CmdAwslogin
from cmds.cmds_flamegraph import CmdFlamegraph
from cmds.cmds_dsnacpu import CmdDsnacpu
from cmds.cmds_s3stats import CmdS3Stats
from cmds.cmds_rtbproto import CmdRtbproto
from cmds.cmds_ri import CmdRi
from cmds.cmds_ri import CmdRi
from cmds.cmds_uxeng import CmdUxeng
from cmds.cmds_cost import CmdCost
from cmds.cmds_p4 import CmdP4
from cmds.cmds_unity import CmdUnity
from cmds.cmds_awsinfo import CmdAwsinfo
from cmds.cmds_ebs import CmdEbs
from cmds.cmds_patch import CmdPatch
from cmds.cmds_uitests import CmdUitests
# {cmdimportline}
import util.bud_helper_util as bud_helper_util
import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
from util.bud_helper_util import BudHelperError

# for panda 0.23 warnings about numpy
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")


def lambda_handler(event, context):
    """
    Entry point to SlackBud lambda function.
    :param event: event from the lambda entry point
    :param context: context from the lambda entry point
    :return: Slack response
    """
    try:
        # Check for scheduled event which just keeps this lambda function active.
        if is_scheduled_event(event):
            return 'done'

        print("REFACTORING lambda_function Event: {}".format(event))

        params = parse_qs(event['body'])
        print("REFACTORING params: {}".format(params))

        cmd_inputs = CmdInputs(params)
        cmd_inputs.set_where_am_i('shorttask')
        if cmd_inputs.is_confirmation_cmd():
            print('This is a confirmation command!'.format(cmd_inputs))
            cmd_inputs.log_state('ConfCmd:')
            print('VERIFY. cmd is set about, otherwise need to use callback_value')
        else:
            cmd_inputs.log_state('StdCmd:')

        slack_bud_env = cmd_inputs.get_slack_bud_env()
        print('SlackBud environment: {}'.format(slack_bud_env))

        # Confirmation commands use fallback_value with class name.
        if cmd_inputs.is_confirmation_cmd():
            cmd_inputs.convert_fallback_value_to_command()
            cmd_inputs.set_confirmation_params(params)

        command = cmd_inputs.get_command()
        print('REFACTORING: command={}'.format(command))

        # Create the Cmd class.
        cmd_class = None
        if command == 'version':
            cmd_class = CmdVersion(cmd_inputs)
        elif command == 'help':
            cmd_class = CmdHelp(cmd_inputs)
        elif command == 'untagged':
            cmd_class = CmdUntagged(cmd_inputs)
        elif command == 'user':
            cmd_class = CmdUser(cmd_inputs)
        elif command == 'cmd':
            cmd_class = CmdCmd(cmd_inputs)
        elif command == 'spend':
            cmd_class = CmdSpend(cmd_inputs)
        elif command == 'farm':
            cmd_class = CmdFarm(cmd_inputs)
        elif command == 'apps_flamegraph':
            cmd_class = CmdApps_Flamegraph(cmd_inputs)
        elif command == 'jupyter':
            cmd_class = CmdJupyter(cmd_inputs)
        elif command == 'awslogin':
            cmd_class = CmdAwslogin(cmd_inputs)
        elif command == 'flamegraph':
            cmd_class = CmdFlamegraph(cmd_inputs)
        elif command == 'dsnacpu':
            cmd_class = CmdDsnacpu(cmd_inputs)
        elif command == 's3stats':
            cmd_class = CmdS3Stats(cmd_inputs)
        elif command == 'rtbproto':
            cmd_class = CmdRtbproto(cmd_inputs)
        elif command == 'ri':
            cmd_class = CmdRi(cmd_inputs)
        elif command == 'ri':
            cmd_class = CmdRi(cmd_inputs)
        elif command == 'uxeng':
            cmd_class = CmdUxeng(cmd_inputs)
        elif command == 'cost':
            cmd_class = CmdCost(cmd_inputs)
        elif command == 'p4':
            cmd_class = CmdP4(cmd_inputs)
        elif command == 'unity':
            cmd_class = CmdUnity(cmd_inputs)
        elif command == 'awsinfo':
            cmd_class = CmdAwsinfo(cmd_inputs)
        elif command == 'ebs':
            cmd_class = CmdEbs(cmd_inputs)
        elif command == 'patch':
            cmd_class = CmdPatch(cmd_inputs)
        elif command == 'uitests':
            cmd_class = CmdUitests(cmd_inputs)
# {cmdswitchline}
        else:
            err_msg = "The command '{}' is invalid. Please enter a valid command...".format(command)
            return slack_ui_util.error_response(err_msg)

        cmd_class.authenticate_request(params)
        cmd_class.parse_inputs()
        return cmd_class.run_command()

    except BudHelperError as bhe:
        return slack_ui_util.error_response(bhe.message)

    except ShowSlackError as sse:
        return slack_ui_util.error_response(sse.message)

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        bud_helper_util.log_traceback_exception(ex)
        slack_error_message = 'An error occurred. Please check logs.'
        return slack_ui_util.error_response(slack_error_message)


def is_scheduled_event(event):
    """
    Events are sent by CloudWatch to keep the lambda function active
    and avoid start-up deploys after long idle periods.

    This method detects those events so they can be filtered from the logs.
    :param event: event from the lambda entry point
    :return: True if an Scheduled Event to keep lambda function active otherwise False
    """
    try:
        if type(event) is dict:
            key_list = list(event.keys())
            if 'detail-type' in key_list:
                detail_type = event['detail-type']
                if detail_type == 'Scheduled Event':
                    return True
        return False
    except Exception as ex:
        template = 'Failed at step "is_scheduled_event" type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))


def get_fallback_value(params):
    """
    The fallback value is the same as the class name as defined
    by the abstract base class.

    :param params:
    :return: string fallback value.
    """
    try:
        return json.loads(params['payload'][0])['original_message']['attachments'][0]['fallback']
    except Exception as ex:
        raise ShowSlackError('Failed to find fallback value. Reason: {}'.format(ex.message))
