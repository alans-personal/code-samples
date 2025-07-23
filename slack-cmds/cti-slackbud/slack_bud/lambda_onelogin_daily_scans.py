"""
The entry point for the OneLogin daily scans.

Initially it will just scan all of the

 --
onelogin-policies

CloudFormation stacks for drift.



"""
from __future__ import print_function
import boto3
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from datetime import datetime
import requests
import json


## ToDo: Get this from a shared utility function, or move to database.
AWS_ACCOUNTS = {
    'apps-prod': '123456789012',
    'apps-qa': '123456789012',
    'apps-stg': '123456789012',
    'aws-tools': '123456789012',
    'bar': '123456789012',
    'cti': '123456789012',
    'dea': '123456789012',
    'delta-ml': '123456789012',
    'it':  '123456789012',
    'mobile': '123456789012',
    'mobile-dev': '123456789012',
    'net-eng':  '123456789012',
    'npi-audio': '123456789012',
    'pay-prod': '123456789012',
    'pay-qa': '123456789012',
    'pay-stg': '123456789012',
    'player-prod':  '123456789012',
    'player-stg':  '123456789012',
    'sr-dev': '123456789012',
    'sr-infra': '123456789012',
    'sr-prod': '123456789012',
    'sr-qa': '123456789012',
    'trust': '123456789012',
    'trust-prod': '123456789012',
    'web': '123456789012',
    'web-shop': '123456789012'
}


def handler(event, context):
    """
    Do the type of scan requested.

    :param event: We expect the event to have a work_type in it.
    :param context:
    :return: build number on success or ERROR: ... on failure
    """
    print('Starting OneLogin scans.')
    print('event: {}'.format(event))

    try:
        detail_type = event.get('detail-type')
        source = event.get('source')
        print('Event: {}, source: {}'.format(detail_type, source))

        # Get the type of work.
        work_type = event.get('work_type')
        print('Work type: {}'.format(work_type))
        if not work_type:
            print('No work-type found. Injecting work-type = start_drift_detection')
            work_type = 'start_drift_detection'

        # Detect drift in OneLogin CloudFormation stacks.
        if work_type == 'start_drift_detection':
            dict_drift_detection_ids = start_drift_detection()
            check_drift_results(dict_drift_detection_ids)
        elif work_type == 'generate_aws_console_access_report':
            generate_aws_console_access_report()
        else:
            print('WARN: Unknown work_type: {}'.format(work_type))

    except Exception as e:
        print('ERROR: {}'.format(e.message))

    return 'Done'


def start_drift_detection():
    """
    Go to all the AWS account in us-east-1 and start a drift detection.
    :return: dictionary of drift_detection_ids
    """
    print('start_drift_detection')
    drift_detection_ids_map = {}
    for curr_account_name in AWS_ACCOUNTS.keys():
        ids = start_drift_for_account(curr_account_name)
        if ids:
            drift_detection_ids_map.update(ids)

    print('Started drift detection for the following AWS accounts: {}'.format(drift_detection_ids_map))
    return drift_detection_ids_map


def start_drift_for_account(aws_account_name):
    """
    Start drift for account
    :param aws_account_name:
    :return: dictionary like:
    {
        'cti_onelogin-roles': 23475671467567,
        'cti_onelogin-policies': 67856473346234
    }
    """
    print('start drift for: {}'.format(aws_account_name))

    try:
        ret_val = {}

        session = create_security_auditor_session(aws_account_name)
        cf_client = aws_util.get_cloudformation_client(session, 'us-east-1')
        # roles_response = cf_client.detect_stack_drift(
        #     StackName='onelogin-roles'
        # )
        # key = '{}_{}'.format(aws_account_name, 'onelogin-roles')
        # value = roles_response.get('StackDriftDetectionId')
        # ret_val[key] = value

        policy_response = cf_client.detect_stack_drift(
            StackName='onelogin-policies'
        )
        key = '{}_{}'.format(aws_account_name, 'onelogin-policies')
        value = policy_response.get('StackDriftDetectionId')
        ret_val[key] = value

        return ret_val

    except Exception as ex:
        print('ERROR: {}'.format(ex.message))
        print(bud_helper_util.log_traceback_exception(ex))
        # Calling need to look for None.


def check_drift_results(dict_drift_detection_ids):
    """
    :param dict_drift_detection_ids: dict like
            {
                'cti_onelogin-roles': 123456789012,
                'cti_onelogin-policies': 123456789012
            }
    :return:
    """
    print('check_drift_result')
    print('dict_drift_detection_ids: {}'.format(dict_drift_detection_ids))

    ret_val = {}

    session = None
    session_name = None

    start_time = datetime.now()
    max_run_time = 5 * 60  # 5 minutes.

    # We are going to wait up to five minutes for drift detection to complete.
    # sleep 20 seconds to give drift detection time to work.
    while True:

        try:
            for curr_drift_detection_key in dict_drift_detection_ids.keys():
                drift_id = dict_drift_detection_ids.get(curr_drift_detection_key)
                parts = curr_drift_detection_key.split('_')
                aws_account_name = parts[0]
                role_name = parts[1]
                if session_name != aws_account_name:
                    session = create_security_auditor_session(aws_account_name)
                    session_name = aws_account_name
                drift_detected_response = detect_drift_for(session, drift_id, aws_account_name,role_name)

                # Expected results:
                # 'DETECTION_IN_PROGRESS' (keep going)
                # 'DETECTION_FAILED'|'DRIFTED'|'IN_SYNC'|'UNKNOWN'|'NOT_CHECKED' (finished)
                print('{} for {} - {}'.format(drift_detected_response, aws_account_name, role_name))
                if drift_detected_response != 'DETECTION_IN_PROGRESS':
                    ret_val[curr_drift_detection_key] = drift_detected_response
                    dict_drift_detection_ids.pop(curr_drift_detection_key, None)
                    if drift_detected_response != 'IN_SYNC':
                        # Process this as an error.
                        send_drift_detected_message(drift_detected_response, aws_account_name, role_name)
        except Exception as ex:
            print('ERROR: {}'.format(ex.message))
            print(bud_helper_util.log_traceback_exception(ex))
            print('continuing')

        # Stop when we have found all of the results.
        detect_keys = dict_drift_detection_ids.keys()
        print('Number drift detection results pending: #{}'.format(len(detect_keys)))
        if len(detect_keys) == 0:
            print('FINISHED all result complete.')
            break

        if is_time_to_stop(start_time, max_run_time):
            print('WARN: Ran out of time.')
            print('The following are not complete.')
            print(dict_drift_detection_ids)
            break

    return ret_val


def is_time_to_stop(start_time, max_run_time):
    """
    Return True when it is time to stop.
    :param start_time:
    :param max_run_time:
    :return: True or False. True if max time has been exceeded.
    """
    total_time = datetime.now() - start_time
    if total_time > max_run_time:
        return True
    else:
        return False


def detect_drift_for(session, drift_id, aws_account_name, role_name):
    """

    :param session:
    :param drift_id:
    :param aws_account_name:
    :param role_name:
    :return: String - drift detection result from the boto3 call.

    """
    try:
        cf_client = aws_util.get_cloudformation_client(session, 'us-east-1')
        response = cf_client.describe_stack_drift_detection_status(
            StackDriftDetectionId=drift_id
        )

        detection_status = response.get('DetectionStatus')
        drift_status = response.get('StackDriftStatus')

        if detection_status == 'DETECTION_IN_PROGRESS':
            return detection_status
        else:
            # log the result
            status_reason = response.get('DetectionStatusReason')
            print('{} - {}: {}, {}'.format(aws_account_name, role_name, drift_status, status_reason))

            # return status if detection is complete
            if detection_status == 'DETECTION_COMPLETE':
                return drift_status

        return detection_status

    except Exception as ex:
        return 'ERROR: {}'.format(ex.message)
        bud_helper_util.log_traceback_exception(ex)


def send_drift_detected_message(drift_detected_response, aws_account_name, role_name):
    """
    The response was not 'IN_SYNC' for detecting drift. Send messages to warn people.

    :param drift_detected_response:
    :param aws_account_name:
    :param role_name:
    :return:
    """
    print('ToDo: Send error message to #onelogin-sso and e-mail')

    title = 'WARN: Manual permission file change.'
    text = 'Account {}:  {} - {}'.format(aws_account_name, role_name, drift_detected_response)

    post_message_to_slack_channel(title, text, color='#36a64f')
    send_email_to_account_owners(aws_account_name, role_name, drift_detected_response)


def generate_aws_console_access_report():
    """
    This will be the user usage report.
    :return:
    """
    print('generate_aws_console_access_report')


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

    # NOTE: Need to configure Incoming WebHooks at:
    #   https://my.slack.com/apps.manage
    #
    # url = "https://hooks.slack.com/services/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" # sr-slack-deploy
    url = "https://hooks.slack.com/services/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" # onelogin-sso (monkey emoji)
    res = requests.post(
        url=url,
        data=json.dumps(slack_message),
        headers={"Content-type": "application/json"}
    )
    print('Slack status code: {}'.format(res.status_code))


def send_email_to_account_owners(aws_account_name, role_name, drift_detected_response):
    """
    ToDo:
    Step 1) Look-up the AWS Admin and Approver.
    Step 2) Send e-mail to these people, in addition to asnyder and omontamayor

    :param aws_account_name:
    :param role_name:
    :param drift_detected_response:
    :return:
    """
    print('send_email_to_account_owners({}, {}, {})'.format(aws_account_name, role_name, drift_detected_response))
    print('ToDo:  Still need to implement e-mail.')


# === Helper functions

def create_security_auditor_session(aws_account_name):
    """
    Create a session with read access to AWS accounts.
    :param aws_account_name: Same as ENVIRONMENT above.
    :return: session.
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::{}:role/SecurityAuditor'.format(AWS_ACCOUNTS[aws_account_name]),
        RoleSessionName='ctipoke')
    return session