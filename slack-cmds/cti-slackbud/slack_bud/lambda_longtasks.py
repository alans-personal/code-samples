"""Entry point for longer running lambda tasks for the lambda function, called from slack-bud."""
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
from cmds.cmds_uxeng import CmdUxeng
from cmds.cmds_cost import CmdCost
from cmds.cmds_p4 import CmdP4
from cmds.cmds_unity import CmdUnity
from cmds.cmds_awsinfo import CmdAwsinfo
from cmds.cmds_ebs import CmdEbs
from cmds.cmds_patch import CmdPatch
from cmds.cmds_uitests import CmdUitests
# {cmdimportline}
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
from util.bud_helper_util import BudHelperError


def lambda_handler(event, context):
    try:
        # Check for scheduled event which just keeps this lambda function active.
        if is_scheduled_event(event):
            return 'done'

        print '(Z) LONGTASKS event: {}'.format(event)
        task = event.get('task')
        print('(Z) TASK: {}'.format(task))

        cmd_inputs = get_cmd_inputs_from_event(event)
        cmd_inputs.set_where_am_i('longtask')
        print('lambda_handler cmd_inputs: {}'.format(cmd_inputs))

        response_url = cmd_inputs.get_response_url()

        if task == 'CmdVersion':
            cmd_class = CmdVersion(cmd_inputs)
        elif task == 'CmdHelp':
            cmd_class = CmdHelp(cmd_inputs)
        elif task == 'CmdUntagged':
            cmd_class = CmdUntagged(cmd_inputs)
        elif task == 'CmdUser':
            cmd_class = CmdUser(cmd_inputs)
        elif task == 'CmdCmd':
            cmd_class = CmdCmd(cmd_inputs)
        elif task == 'CmdSpend':
            cmd_class = CmdSpend(cmd_inputs)
        elif task == 'CmdFarm':
            cmd_class = CmdFarm(cmd_inputs)
        elif task == 'CmdApps_Flamegraph':
            cmd_class = CmdApps_Flamegraph(cmd_inputs)
        elif task == 'CmdJupyter':
            cmd_class = CmdJupyter(cmd_inputs)
        elif task == 'CmdAwslogin':
            cmd_class = CmdAwslogin(cmd_inputs)
        elif task == 'CmdFlamegraph':
            cmd_class = CmdFlamegraph(cmd_inputs)
        elif task == 'CmdDsnacpu':
            cmd_class = CmdDsnacpu(cmd_inputs)
        elif task == 'CmdS3Stats':
            cmd_class = CmdS3Stats(cmd_inputs)
        elif task == 'CmdRtbproto':
            cmd_class = CmdRtbproto(cmd_inputs)
        elif task == 'CmdRi':
            cmd_class = CmdRi(cmd_inputs)
        elif task == 'CmdRi':
            cmd_class = CmdRi(cmd_inputs)
        elif task == 'CmdUxeng':
            cmd_class = CmdUxeng(cmd_inputs)
        elif task == 'CmdCost':
            cmd_class = CmdCost(cmd_inputs)
        elif task == 'CmdP4':
            cmd_class = CmdP4(cmd_inputs)
        elif task == 'CmdUnity':
            cmd_class = CmdUnity(cmd_inputs)
        elif task == 'CmdAwsinfo':
            cmd_class = CmdAwsinfo(cmd_inputs)
        elif task == 'CmdEbs':
            cmd_class = CmdEbs(cmd_inputs)
        elif task == 'CmdPatch':
            cmd_class = CmdPatch(cmd_inputs)
        elif task == 'CmdUitests':
            cmd_class = CmdUitests(cmd_inputs)
# {cmdlongtaskswitchline}

        else:
            print("WARNING: Unrecognized task value: {}".format(task))
            response_url = cmd_inputs.get_response_url
            error_text = "Unrecognized long task '{}'. Check error logs".format(task)
            return slack_ui_util.error_response(error_text, post=True, response_url=response_url)

        cmd_class.run_command()

        print('Finished task: {}'.format(task))

    except BudHelperError as bhe:
        return slack_ui_util.error_response(
            bhe.message,
            post=True,
            response_url=response_url
        )

    except ShowSlackError as sse:
        return slack_ui_util.error_response(
            sse.message,
            post=True,
            response_url=response_url
        )

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        bud_helper_util.log_traceback_exception(ex)
        slack_error_message = 'An error occurred. Please check logs.'
        return slack_ui_util.error_response(
            slack_error_message,
            post=True,
            response_url=response_url
        )


def get_cmd_inputs_from_event(event):
    """
    Read the event and pull out the cmd_input class.
    :param event:
    :return:
    """
    cmd_inputs_serialized = event.get('params')
    print('longtask params: {}'.format(cmd_inputs_serialized))

    cmd_inputs = CmdInputs()
    cmd_inputs.deserialize(cmd_inputs_serialized)
    cmd_inputs.log_state('longtask deserialized:')

    return cmd_inputs


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
