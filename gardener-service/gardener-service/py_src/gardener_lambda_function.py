"""
Entry point for gardener (python) functions.

By convention. If an error occures the first word of the
response needs to be either.

ERROR...
 - or -
FAIL...

It can be case insensitive.

"""
import json
import time
import util.garden_helper_util as garden_helper_util
import util.aws_util as aws_util
import base64
import boto3
import datetime
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

SCHEDULED_EVENT_COUNT = 0

DYNAMODB = boto3.resource('dynamodb')
FARM_STATE_TABLE = DYNAMODB.Table('FarmState')
FARM_STATUS_TABLE = DYNAMODB.Table('FarmStatus')
FARM_SERVICE_STATUS_TABLE = DYNAMODB.Table('FarmServiceStatus')
SERVICE_HISTORY_TABLE = DYNAMODB.Table('FarmServiceHistory')
BUILD_VERSION_TABLE = DYNAMODB.Table('FarmBuildVersion')
BUILD_NUMBERS_TABLE = DYNAMODB.Table('BuildNumbers')
BUILD_HISTORY_TABLE = DYNAMODB.Table('BuildHistory')

STATE_RUN = "run"
STATE_STOP = "stop"
STATE_DELETE = "delete"
STATE_ERROR = "ERROR"
ITEM_NOT_FOUND_IN_DB = "ERROR: Item not found"


def lambda_handler(event, context):
    """
    Entry point for call between Gardener and GroundsKeeper.
    :param event:
    :param context:
    :return:
    """
    try:
        if is_scheduled_event(event):
            return 'done'

        # determine which api call.
        print('event: \n{}'.format(event))

        api_handler = event.get('api-handler')
        if api_handler == 'get-state':
            return get_state(event)
        elif api_handler == 'report-state':
            return report_state(event)
        elif api_handler == 'update-service':
            return update_service(event)
        elif api_handler == 'delete-service':
            return delete_service(event)
        elif api_handler == 'get-service-desired-state':
            return get_service_desired_state(event)
        elif api_handler == 'get-service-actual-status':
            return get_service_actual_status(event)
        elif api_handler == 'change-service-mode':
            return change_service_mode(event)
        elif api_handler == 'get-farm-inspect':
            return get_farm_inspect(event)
        elif api_handler == 'post-service-build-info':
            return post_service_build_info(event)
        elif api_handler == 'get_service_exists':
            return get_service_exists(event)
        elif api_handler == 'get_version_exists':
            return get_version_exists(event)
        elif api_handler == 'get-service-status-everywhere':
            return get_service_status_everywhere(event)
        else:
            print('ERROR: unknown api_handler: {}'.format(api_handler))
            raise ValueError('ERROR: Unknown api-handler value. Was: {}'.format(api_handler))

    except Exception as ex:
        garden_helper_util.log_traceback_exception(ex)
        print('Returning error with message: {}'.format(ex.message))
        return 'ERROR: {}'.format(ex.message)


def is_scheduled_event(event):
    """
    Schedule event to keep lambda function active.
    :param event:
    :return:
    """
    try:
        if type(event) is dict:
            key_list = list(event.keys())
            if 'detail-type' in key_list:
                detail_type = event['detail-type']
                if detail_type == 'Scheduled Event':

                    # Count and record every 10th event.
                    global SCHEDULED_EVENT_COUNT
                    SCHEDULED_EVENT_COUNT += 1
                    if SCHEDULED_EVENT_COUNT%10 == 1:
                        print('scheduled event #{}: {}'.format(SCHEDULED_EVENT_COUNT, event))

                    return True
        return False
    except Exception as ex:
        template = 'Failed at step "is_scheduled_event" type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))


def get_state(event):
    """
    Pull the farmName from the event, look it up in the DynamoDB table and return the result as
    a JSON object.

    Also record the machine making the request.
    :param event:
    :return:
    """
    print('get_state')

    farm_name = event.get('farmName')

    response = FARM_STATE_TABLE.query(
        KeyConditionExpression=Key('farmName').eq(farm_name)
    )

    services = []
    services_str = None
    for i in response['Items']:
        try: 
            json_with_escape_chars = i.get('state')
            if not json_with_escape_chars:
                print('WARN: state not found for a service in farm: {}'.format(farm_name))
                continue
            raw_json = json_with_escape_chars.replace('\\', '')

            # replace $serviceMode
            service_mode = i['serviceMode']
            raw_json = raw_json.replace('$serviceMode', service_mode)

            # replace $repoUrl
            repo_url = i.get('repoUrl')
            if repo_url:
                raw_json = raw_json.replace('$repoUrl', repo_url)

            # replace $versionString
            version_string = i.get('versionString')
            if version_string:
                raw_json = raw_json.replace('$versionString', version_string)

            # replace $targetRegion
            target_region = i.get('targetRegion')
            if not target_region:
                target_region = 'all'
            raw_json = raw_json.replace('$targetRegion', target_region)

            services.append(raw_json)
            if not services_str:
                services_str = raw_json
            else:
                services_str += ', '+raw_json
        except Exception as ex:
            print('ERROR: get_state - {}'.format(ex.message))
            garden_helper_util.log_traceback_exception(ex)
            continue

    if len(services) == 0:
        ret_val = '{ "services": [] }'
    else:
        ret_val = '{ "services": [%s] }' % services_str

    return ret_val


def report_state(event):
    """
    This is the reported state of the machine. Look for differences between this and
    what is in the database, and highlight services that are out of sync in other applications.
    :param event:
    :return:
    """
    print('report_state')

    try:

        farm_name = event.get("farmName")
        az = event.get("az")
        state = event.get("state")

        print('TEMP: farm: {}, state: {}'.format(farm_name, state))

        state_d = convert_to_python_dictionary(state)
        data = state_d.get('data')
        services = data.get('services')

        for service in services:
            try:
                # Get the required names
                service_name = service.get('service_name')
                aws_region = az
                primary_key = '{}:{}'.format(farm_name, aws_region)

                version = service.get('version')

                # expire the row in one hour.
                ts_epoch = round(time.time())
                ttl = int(ts_epoch + 600)
                last_update = datetime.datetime.fromtimestamp(ts_epoch).strftime('%Y-%m-%d_%H:%M:%S')

                service_state = service.get('state')
                service_status = service.get('status')
                if service_status:
                    status = service_status.get('status')
                    error_msg = service_status.get('error_msg')
                    error_details = service_status.get('error_details')
                    if not error_details:
                        error_details = '-'
                    if not error_msg:
                        error_msg = '-'
                    else:
                        error_count = service_status.get('error_count')
                        error_msg = '{} ({})'.format(error_msg, error_count)
                    running_count = service_status.get('running_count')
                    when = service_status.get('when')
                    if not when:
                        when = '?'

                    # Take the required fields and put them into the database.
                    print('farmName: {}, serviceName: {}, region: {}, status: {}, version: {}, '
                          'error_msg: {}, when: {}, last_update: {}'
                          .format(farm_name, service_name, aws_region, status, version,
                                  error_msg, when, last_update))

                    # Populate the table.
                    FARM_SERVICE_STATUS_TABLE.put_item(
                        Item={
                            'farmName': primary_key,
                            'serviceName': service_name,
                            'status': status,
                            'version': version,
                            'running_count': running_count,
                            'error_msg': error_msg,
                            'error_details': error_details,
                            'when': when,
                            'last_update': last_update,
                            'ttl': ttl
                        }
                    )
                else:
                    # Populate the table with unknown results since no status block.
                    report_status = service_state.upper()
                    FARM_SERVICE_STATUS_TABLE.put_item(
                        Item={
                            'farmName': primary_key,
                            'serviceName': service_name,
                            'status': report_status,
                            'version': version,
                            'last_update': last_update,
                            'ttl': ttl
                        }
                    )

            except Exception as ex:
                print('ERROR: report_state - {}'.format(ex.message))
                garden_helper_util.log_traceback_exception(ex)

        return None

    except Exception as ex:
        print('ERROR: report_state.  message={}'.format(ex.message))
        garden_helper_util.log_traceback_exception(ex)


def update_service(event):
    """
    Look-up the farm and service and update that entry in the database.
    :param event:
    :return:
    """
    print('update_service')
    print('(update_service) event: {}'.format(event))

    farm_name = event.get('farmName')
    service = event.get('service')
    target_region = event.get('targetRegion')

    service_json = event.get('service-json')
    # state_map = convert_to_python_dictionary(service_json)
    user = event.get('user')
    if not user:
        user = 'unknown'

    # version and repoUrl
    version_string = event.get('versionString')
    repo_url = event.get('repoUrl')

    # Change per: CTDEVOPS-706
    if version_string:
        print('Deploying {}'.format(version_string))
    else:
        raise ValueError('Service: {}. Is missing version string.')

    farm_build_version_response = get_farm_build_version_data(service, version_string)
    if not response_has_data(farm_build_version_response):
        raise ValueError('No version for service: {} - {}.'.format(service, version_string))
    service_json = farm_build_version_response.get('Item').get('serviceInfo')
    repo_url = farm_build_version_response.get('Item').get('repo')
    # Throw an error is version or repo url is missing.
    if not repo_url:
        raise ValueError('Missing repoUrl for service: {} - {}.'.format(service, version_string))
    if service_json is None:
        raise ValueError('Missing JSON for service: {} - {}'.format(service, version_string))

    FARM_STATE_TABLE.put_item(
        Item={
            'farmName': farm_name,
            'serviceName': service,
            'state': service_json,
            'serviceMode': STATE_RUN,
            'versionString': version_string,
            'targetRegion': target_region,
            'repoUrl': repo_url
        }
    )

    # Add entry to SERVICE_HISTORY_TABLE
    state = 'deploy'
    if version_string:
        state = 'deploy-{}'.format(version_string)
    put_service_history_table_entry(service, farm_name, state, user)

    return 'Done'


def delete_service(event):
    """
    Delete a service from a farm.
    :param event:
    :return:
    """
    print('delete_service')

    farm_name = event.get('farmName')
    service = event.get('service')
    user = event.get('user')
    if not user:
        user = 'unknown'

    print('Deleting service: {} from farm: {}'.format(service, farm_name))
    print('FarmState table created: {}'.format(FARM_STATE_TABLE.creation_date_time))

    # Verify that the serviceMode of service is DELETE.
    service_mode = get_current_mode_from_farm_state_table(farm_name, service)
    print('serviceMode={}'.format(service_mode))
    if not service_mode:
        message = 'ERROR: missing serviceMode attribute in database.'
        print(message)
        return message

    if service_mode != STATE_DELETE:
        return 'ERROR: {}.{} needs to be in serviceMode DELETE. It is in: {}'.format(farm_name, service, service_mode)

    FARM_STATE_TABLE.delete_item(
        Key={
            'farmName': farm_name,
            'serviceName': service
        }
    )

    # ToDo: Added delete to history table. Verify user is included.
    # SERVICE_HISTORY_TABLE - undeploy
    put_service_history_table_entry(service, farm_name, 'undeploy', user)

    return 'Success'


def get_service_desired_state(event):
    """
    Delete a service from a farm.
    :param event:
    :return:
    """
    print('get_service_desired_state')

    farm_name = event.get('farmName')
    service = event.get('service')

    try:
        response = FARM_STATE_TABLE.get_item(
            Key={
                'farmName': farm_name,
                'serviceName': service,
            }
        )
    except ClientError as e:
        message = 'Failed to find: {}.{}. Due to error: {}'.format(farm_name, service, e.message)
        print(message)
        return message
    else:
        item = response['Item']
        if not item:
            message = 'Failed to find: {}.{}'.format(farm_name, service)
            print(message)
            return message
        else:
            print('item={}'.format(item))
            return item


def get_service_actual_status(event):
    """

    :param event:
    :return:
    """
    print('get_service_actual_status')

    farm_name = event.get('farmName')
    service = event.get('service')

    response = FARM_STATE_TABLE.get_item(
        Key={
            'farmName': farm_name,
            'serviceName': service,
        }
    )

    item = response['Item'] is None
    if item:
        message = 'Failed to find: {}.{}'.format(farm_name, service)
        print(message)
        return message
    else:
        return item


def change_service_mode(event):
    """
    Change state from "RUN" to "STOPPED", to "DELETING".
    Need some logic to prevent it from going directly between "RUN" and "DELETING".
    It needs to be in STOP first.
    :param event:
    :return: On success. the name of the new state. On fail. "ERROR: <message>\n<state>"
    """
    print('change_service_mode')

    farm_name = event.get('farmName')
    service = event.get('service')
    state = event.get('mode')
    user = event.get('user')
    if not user:
        user = 'unknown'

    # Verify we are not going from RUN to DELETE.
    curr_state = get_current_mode_from_farm_state_table(farm_name, service)
    if curr_state == ITEM_NOT_FOUND_IN_DB:
        message = 'ERROR: Item not found.'
        print(message)
        return message

    if state == STATE_DELETE:
        if curr_state == STATE_RUN:
            print('ERROR: Cannot go from RUN to DELETE state.')
            return 'ERROR: Cannot go from RUN to DELETE state.'
        elif curr_state.startswith(STATE_ERROR):
            print('ERROR state: {}'.format(curr_state))
            return curr_state
    # Verify we are not going from DELETE to RUN
    if state == STATE_RUN:
        if curr_state == STATE_DELETE:
            message = 'ERROR: Cannot go from DELETE to RUN state.'
            print(message)
            return message
        elif curr_state.startswith(STATE_ERROR):
            print('ERROR state: {}'.format(curr_state))
            return curr_state

    # Make the change.
    FARM_STATE_TABLE.update_item(
        Key={
            'farmName': farm_name,
            'serviceName': service
        },
        UpdateExpression='SET serviceMode = :val',
        ExpressionAttributeValues={
            ':val': state
        }
    )

    # SERVICE_HISTORY_TABLE - change state
    put_service_history_table_entry(service, farm_name, state, user)

    print('Success: new mode: {}'.format(state))

    return state


def put_service_history_table_entry(service, farm_name, state, user):
    """
    Add an service event into service history table.
    :param service:
    :param farm_name:
    :param state:
    :param user:
    :return:
    """
    # Add entry to SERVICE_HISTORY_TABLE.
    event_name = 'service-change-{}-{}'.format(service, farm_name)
    time_stamp = garden_helper_util.get_gardener_time_format()

    SERVICE_HISTORY_TABLE.put_item(
        Item={
            'eventName': event_name,
            'timestamp': time_stamp,
            'state': state,
            'user': user
        }
    )


def get_farm_inspect(event):
    """
    Simple list of service name and mode.
    :param event:
    :return:
    """
    print('get_farm_inspect')

    farm_name = event.get('farmName')

    # Make call for all services in farm.
    response = FARM_STATE_TABLE.query(
        KeyConditionExpression=Key('farmName').eq(farm_name)
    )
    ret_val = ''
    for i in response['Items']:
        service_name = i['serviceName']
        service_mode = i['serviceMode']
        optional_version_string = i.get('versionString')
        if optional_version_string:
            ret_val += '{}: {} {}\n'.format(service_name, service_mode, optional_version_string)
        else:
            ret_val += '{}: {}\n'.format(service_name, service_mode)

    return ret_val


def get_service_exists(event):
    """
    Return exists, if the service name is found in BuildNumber table.

    We are going to send an invoke command to the gardener api, instead of
    call database directly here.

    :param event: must have "serviceName" in it.
    :return: "True\nFound {serviceName}, | "False\nDid not Find {serviceName}"
    """
    try:
        BUILD_NUMBERS_TABLE.get_item()
    except Exception as ex:
        print('ERROR: get_service_exists.')


def get_version_exists(event):
    """

    :param event:
    :return:
    """


def post_service_build_info(event):
    """
    Put the seedUrl in the FarmBuildVersion table.
    The calculate and return a valid build string.
    :param event:
    :return: JSON string in format:  { version: "20180924-19-144a37b-master" }
    """
    print('post_service_build_info')

    service = event.get('service')
    if not service:
        raise ValueError('Call post_service_build_info is missing: service')

    seed_url = event.get('seedUrl')
    service_json_base64 = event.get('serviceJsonBase64')
    if not seed_url and not service_json_base64:
        raise ValueError('Call post_service_build_info is missing: seedUrl')

    short_git_hash = event.get('shortGitHash')
    if not short_git_hash:
        raise ValueError('Call post_service_build_info is missing: shortGitHash')

    docker_repo_url = event.get('dockerRepoUrl')
    if not docker_repo_url:
        raise ValueError('Call post_service_build_info is missing: dockerRepoUrl')

    build_user = event.get('buildUser')
    if not build_user:
        raise ValueError('Call post_service_build_info is missing: buildUser')

    build_branch = event.get('buildBranch')
    if not build_branch:
        print('WARN: Failed to get the build_branch. Will use "master" as default.')
        build_branch = 'master'

    print('service: {}, user: {}, '.format(service, build_user))

    # get the next version number for this service.

    # invoke lambda function... build-number-service
    lambda_client = boto3.client("lambda")

    build_event = {
        "service": service,
        "user": build_user
    }

    response = lambda_client.invoke(
        FunctionName='build-number-service',  # This is ctidev
        InvocationType="RequestResponse",
        Payload=json.dumps(build_event)
    )

    print('DEBUG: Build-Number-Service response: {}'.format(response))

    # log result.
    status_code = response['StatusCode']
    print('Build-Number-Service Status Code: {}'.format(status_code))

    payload = response['Payload'].read()
    print('Payload={}'.format(payload))

    now = datetime.datetime.now()
    date_string = now.strftime('%Y%m%d')
    print('post_service_build_info date_string: _{}_'.format(date_string))

    build_number = payload

    build_version = '{}-{}-{}-{}'.format(date_string, build_number, short_git_hash, build_branch)

    # put values in database.
    if service_json_base64:
        service_json = base64.b64decode(service_json_base64)

        print('DEBUG: service_json=_{}_'.format(service_json))

        # inject the restricted keys. state, repo, version, target_region
        service_json = inject_restricted_json_keys(service_json)

        BUILD_VERSION_TABLE.put_item(
            Item={
                'serviceName': service,
                'buildNumber': build_version,
                'repo': docker_repo_url,
                'serviceInfo': service_json
            }
        )
    else:
        # this is old method which will be deprecated.
        BUILD_VERSION_TABLE.put_item(
            Item={
                'serviceName': service,
                'buildNumber': build_version,
                'repo': docker_repo_url,
                'seedUrl': seed_url
            }
        )

    print('service: _{}_, build_version: _{}_'.format(service, build_version))

    return build_version


def get_service_status_everywhere(event):
    """
    Scan the FarmStatus table and return information about
    a service status in JSON format.



    :param event:
    :return: JSON or "ERROR: <message> if an error occurs.
    """
    print('post_service_build_info')

    # Build a python dictionary.
    service = event.get('service')
    if not service:
        raise ValueError('Call post_service_build_info is missing: service')

    # Scan the FarmStatus table.
    response = FARM_SERVICE_STATUS_TABLE.query(
        IndexName='ByService',
        KeyConditionExpression=Key('serviceName').eq(service)
    )

    services = []

    items = response.get('Items')
    if items:
        for i in response['Items']:

            status = i.get('status')
            version = i.get('version')
            running_count = i.get('running_count')
            last_update = i.get('last_update')
            farm_name = i.get('farmName')
            err_message = i.get('error_msg')

            # add the
            curr_service = {
                'farmName': farm_name,
                'status': status,
                'version': version,
                'running_count': running_count,
                'last_update': last_update,
                'err_message': err_message
            }

            services.append(curr_service)

    ret_val = {
        'services': services
    }

    print('ret_val={}'.format(ret_val))

    return ret_val


###
# helper methods below here.
###


def get_farm_build_version_data(service, version_string):
    """
    Query DynamoDB table to look for row with service and version.

    The method returns a response even if the row doesn't exist.

    :param service: string - Name of service like: drss
    :param version_string: string - Version like: 20181107-30-1b178b42-master
    :return: dynamo_response to query
    """
    try:

        response = BUILD_VERSION_TABLE.get_item(
            Key={
                'serviceName': service,
                'buildNumber': version_string
            }
        )
        return response
    except ClientError as ce:
        err_msg = ce.response['Error']['Message']
        print('Failed to call FarmBuildVersion table. Error: {}'.format(err_msg))
        return None
    except Exception as e:
        print('Exception during call to FarmBuildVersion table. Exception: {}'.format(e.message))
        return None


def response_has_data(farm_build_version_response):
    """
    Verify that this response has some data in it.
    :param farm_build_version_response: dynamodb response
    :return:
    """
    if not farm_build_version_response:
        print('farm_build_version_response was None')
        return False
    if not farm_build_version_response.get('Item'):
        print('farm_build_version_response: Did not find Item {}'.format(farm_build_version_response))
        return False
    return True


def inject_restricted_json_keys(service_json):
    """
    Injects the following keys into the service_json.
    repo: $repoUrl
    version: $serviceVersion
    state: $serviceMode
    target_region: $targetRegion
    :param service_json:
    :return:
    """
    print('type(service_json)={}'.format(type(service_json)))

    try:
        service_dict = json.loads(service_json)

        service_dict['repo'] = '$repoUrl'
        service_dict['version'] = '$versionString'
        service_dict['state'] = '$serviceMode'
        service_dict['target_region'] = '$targetRegion'

        ret_val = json.dumps(service_dict)
        return ret_val

    except Exception as ex:
        print('inject_restricted_json_keys had Error: {}'.format(e.message))
        garden_helper_util.log_traceback_exception(e)

        return service_json


def get_current_mode_from_farm_state_table(farm_name, service):
    """
    Just return the current state of the dynamodb table.
    :return: on ERROR <message> return error, otherwise the state.
    """
    print('get_current_mode_from_farm_state_table')

    try:

        response = FARM_STATE_TABLE.get_item(
            Key={
                'farmName': farm_name,
                'serviceName': service
            }
        )
        item = response['Item']
        if not item:
            return ITEM_NOT_FOUND_IN_DB

        service_mode = item['serviceMode']

        return service_mode

    except Exception as e:
        print('Get Current Mode had Error: {}'.format(e.message))
        garden_helper_util.log_traceback_exception(e)
        return '{}: {}'.format(STATE_ERROR, e.message)


def convert_to_python_dictionary(service):
    """
    Service likely comes in as a JSON String. Convert it into a python dictionary.
    :param service:
    :return: python dictionary or None if an exception.
    """
    try:
        print('Converting to dictionary: service=_{}_'.format(service))
        service_map = json.loads(service)
        return service_map
    except Exception as e:
        print('Could not convert service. Reason: {}'.format(e.message))
        garden_helper_util.log_traceback_exception(e)
        return None
