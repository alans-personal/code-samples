"""
AWS Cost Controller sends events to the AWS Cost via "invoke lambda" functions calls.
It keeps state using the AWS Cost dynamodb table with special keys.


The controller reads state from AwsCost DynamoDB table in us-west-2.

The key is:
(awsResource) primary key: state
(time) sort key:   now

The attribute for this row is: 'state'
This attribute is a DynamoDB Map which becomes python dictionary
and has the following structure.

{
    'next_ec2_scan': (time for next ec2 read)
    'next_daily_scan': (time for next data gather)
    'next_hourly_scan': (time for next)
    'next_summary': (time for next summary)
    'next_excel_file': (time for next Excel file)
}

As needed more will be added to this state later.

"""

import boto3
import json
import util.awscost_helper_util as awscost_helper_util
# import util.aws_util as aws_util
# from datetime import datetime, timedelta # remove

DYNAMODB = boto3.resource('dynamodb')
AWS_COST_TABLE = DYNAMODB.Table('AWSCost')


def controller_handler(event, context):
    """
    Entry point to AwsCost lambda function
    :param event:
    :param context:
    :return:
    """
    try:
        print('AWS Cost Controller version: {}'.format(awscost_helper_util.get_aws_cost_version()))

        time = awscost_helper_util.get_awscost_hourly_time_format()
        print('time: {}'.format(time))

        # Read keys to get state.
        state = read_state()

        if state.get('Error'):
            print('Failed to read state. state = {}'.format(state))
            return 'Failed'

        # Send commands.
        result = do_commands(state, time)

        if result.get('Error'):
            print('Failed to do commands. result = {}'.format(result))
            return 'Failed'

        # If success update keys to reflect this.
        write_next_state(state, result)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def read_state():
    """
    Read state from AWSCost dynamodb channel
    :return: python dictionary with state read from database.
    """
    ret_val = {}
    try:
        print('read_state')

        # "awsResource = state"
        # "time = now"
        # Attribute : 'state'
        response = AWS_COST_TABLE.get_item(
            Key={
                'awsResource': 'state',
                'time': 'now'
            }
        )

        item = response.get('Item')
        if item:
            print('Item = {}'.format(item))
            state = item.get('state')
            if state:
                ret_val['Success'] = 'success'
                ret_val['state'] = state
            else:
                ret_val['Error'] = 'No "state" attribute in Item.'
        else:
            ret_val['Error'] = 'DynamoDB had no Item in response'

        return ret_val

    except Exception as ex:
        print('read_state Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        ret_val['Error'] = '{}'.format(ex.message)
        return ret_val


def write_next_state(state, result):
    """
    Based on the state and result write into the database information needed for the
    next step

    :param state:
    :param result:
    :return: None
    """
    try:
        print('write_next_state')
        print('result = {}'.format(result))
        print('state = {}'.format(state))

        event_for_worker = result.get('Success')
        if event_for_worker:
            print('wns - event_for_worker = {}'.format(event_for_worker))
            work_type = event_for_worker.get('work_type')
            if not work_type:
                raise ValueError("Write_Next_State: Missing work_type.")

            # increment time for this work_type in state.
            if work_type == 'daily_scan':
                increment_state_index('next_daily_scan', 24)
            if work_type == 'ec2_scan':
                increment_state_index('next_ec2_scan')
            if work_type == 'hourly_scan':
                increment_state_index('next_hourly_scan')
            if work_type == 'summary':
                increment_state_index('next_summary')
            if work_type == 'make_excel_file':
                increment_state_index('next_excel_file', 24)
            if work_type == 'gather_ri_stats':
                increment_state_index('next_gather_ri_stats', 24)
            if work_type == 'cost_explorer_reports':
                increment_state_index('next_cost_explorer_reports', 24)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        raise ex


def do_commands(dc_state, time):
    """
    Figure out which command to run and invoke it.

    :param dc_state:
    :param time: Current time to hour in YYYYMMDD-HH format.
    :return:
    """
    try:
        print('do_commands')
        print('do_command state = {}'.format(dc_state))
        ret_val = {}

        success = dc_state.get('Success')
        if success:
            state = dc_state.get('state')
            if state:
                print('starting....')
                # Look for the following items and run them in the following order.
                # daily_scan, hourly_scan (non-ec2 stuff), hourly_ec2_scan, summary, excel file.
                # try to keep ec2 and hourly scan apart in case there is some AWS API calling limit.
                event_for_worker = get_next_event_type(dc_state, time)
                print('do - event_for_worker = {}'.format(event_for_worker))

                lambda_client = boto3.client('lambda')
                result = lambda_client.invoke(
                    FunctionName='awscost-dev',
                    InvocationType='Event',
                    Payload=json.dumps(event_for_worker)
                )

                print('invoke lambda result: {}'.format(result))
                status_code = result.get('StatusCode')
                print('Worker lambda status_code: {}'.format(status_code))
                payload = result.get('Payload')

                if payload:
                    payload_str = result['Payload'].read()
                    print('Payload: _{}_'.format(payload_str))
                    if payload_str.startswith('Failed'):
                        ret_val['Error'] = '{}'.format(payload_str)
                    else:
                        ret_val['Success'] = event_for_worker

            else:
                msg = 'Failed: do_command No state key found'
                ret_val['Error'] = msg
                print(msg)
        else:
            msg = 'Failed: do_command dc_state had Error'
            ret_val['Error'] = msg
            print(msg)

        return ret_val

    except Exception as ex:
        print('do_commands Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def get_next_event_type(dc_state, time):
    """
    determine the next item that needs to be run, and create the
    event to pass to the worker lambda function.
    :param dc_state:
    :param time:
    :return:
    """
    print('get_next_event_type')
    print('dc_state={}'.format(dc_state))
    print('time={}'.format(time))

    state = dc_state.get('state')
    if not state:
        raise ValueError('No state attribute found')

    print('state={}'.format(state))
    next_daily_scan_time = state.get('next_daily_scan')
    next_ec2_scan_time = state.get('next_ec2_scan')
    next_hourly_scan_time = state.get('next_hourly_scan')
    next_summary_time = state.get('next_summary')
    next_excel_file_time = state.get('next_excel_file')
    next_gather_ri_stats_time = state.get('next_gather_ri_stats')
    next_cost_explorer_reports = state.get('next_cost_explorer_reports')

    # NOTE: These values need to be in sync with awscost_controller entry point.
    work_type = 'no_update'
    time_index = ''

    if next_gather_ri_stats_time:
        print('ri_stats: {}<{}?'.format(next_gather_ri_stats_time, time))
        if next_gather_ri_stats_time < time:
            work_type = 'gather_ri_stats'
            time_index = next_gather_ri_stats_time
    if next_excel_file_time:
        print('excel: {}<{}?'.format(next_excel_file_time, time))
        if next_excel_file_time < time:
            work_type = 'make_excel_file'
            time_index = next_excel_file_time
    if next_cost_explorer_reports:
        print('cost_explorer_reports: {}<{}?'.format(next_cost_explorer_reports, time))
        if next_cost_explorer_reports < time:
            work_type = 'cost_explorer_reports'
            time_index = next_cost_explorer_reports
    if next_summary_time:
        print('summary: {}<{}?'.format(next_summary_time, time))
        if next_summary_time < time:
            work_type = 'summary'
            time_index = next_summary_time
    if next_hourly_scan_time:
        print('hourly: {}<{}?'.format(next_hourly_scan_time, time))
        if next_hourly_scan_time < time:
            work_type = 'hourly_scan'
            time_index = next_hourly_scan_time
    if next_ec2_scan_time:
        print('ec2: {}<{}?'.format(next_ec2_scan_time, time))
        if next_ec2_scan_time < time:
            work_type = 'ec2_scan'
            time_index = next_ec2_scan_time
    if next_daily_scan_time:
        print('daily: {}<{}?'.format(next_daily_scan_time, time))
        if next_daily_scan_time < time:
            work_type = 'daily_scan'
            time_index = next_daily_scan_time
    else:
        print('ERROR: No updates found! dc_state={}'.format(dc_state))

    print('work_type={}, time_index={}'.format(work_type, time_index))

    return {
        'work_type': work_type,
        'time_index': time_index
    }


def increment_state_index(state_key, add_hours=1):
    """

    :param state_key:
    :return:
    """
    response = AWS_COST_TABLE.get_item(
        Key={
            'awsResource': 'state',
            'time': 'now'
        }
    )

    item = response.get('Item')
    if item:
        print('Item = {}'.format(item))
        state = item.get('state')
        if not state:
            raise ValueError('Could not find attribute "state"')

        time_index = state.get(state_key)
        if not time_index:
            print('ERROR. Could not find key: {}'.format(state_key))
            print('state={}'.format(state))
            raise ValueError('Could not find key: {}'.format(state_key))

        next_time_index = awscost_helper_util.increment_time_index(time_index, add_hours)
        print('Setting {} to {}'.format(state_key, next_time_index))
        state[state_key] = next_time_index

    AWS_COST_TABLE.put_item(
        Item={
            'awsResource': 'state',
            'time': 'now',
            'state': state
        }
    )
