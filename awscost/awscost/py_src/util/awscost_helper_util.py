"""
Non-AWS related utility for gardener and the pipeline.
"""
from __future__ import print_function

import zipfile
import os
import datetime
import traceback
import pendulum
import boto3
import json
import re
import pandas as pd
import numpy as np
from boto3.dynamodb.conditions import Key, Attr

# This is a mapping of account names to account IDs. This is used to create the ctipoke role and below is 
# are a few accounts as an example. Replace with actual account IDs and names. The size of list is unlimited.
AWS_ACCOUNTS = {
    'example-prod': '123456789012',
    'example-qa': '223456789012',
    'example-stg': '323456789012',
    'example-tools':  '423456789012'
}


# This is the reverse of AWS_ACCOUNTS, but is lazy loaded, and created on
# first call.
AWS_NAMES = {}


# Filter for get_price
# Search product filter
FLT = '[{{"Field": "tenancy", "Value": "shared", "Type": "TERM_MATCH"}},'\
      '{{"Field": "operatingSystem", "Value": "{o}", "Type": "TERM_MATCH"}},'\
      '{{"Field": "preInstalledSw", "Value": "NA", "Type": "TERM_MATCH"}},'\
      '{{"Field": "instanceType", "Value": "{t}", "Type": "TERM_MATCH"}},'\
      '{{"Field": "location", "Value": "{r}", "Type": "TERM_MATCH"}}]'

# Contains likely regions, but not all. Add more if needed.
REGIONS = {
    "us-east-1": "US East (N. Virginia)",
    "us-west-2": "US West (Oregon)",
    "us-east-2": "US East (Ohio)",
    "us-west-1": "US West (N. California)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ca-central-1": "Canada (Central)",
    "eu-central-1": "EU (Frankfurt)",
    "eu-west-1": "EU (Ireland)",
    "eu-west-2": "EU (London)"
    # "sa-east-1": "South America (So Paulo)" # What does price api expect for this?
}

# These values are used by the sort algorithm for charting node types.
NODE_SORT_VALUES = {
    # sizes
    "nano": 1,
    "micro": 3,
    "small": 5,
    "medium": 7,
    "large": 9,
    "xlarge": 11,
    "*xlarge": -99,   # special value to invoke calculation
    # family types
    "a1": 100,
    "t1": 200,
    "t2": 300,
    "t3": 400,
    "m1": 500,
    "m3": 600,
    "m4": 700,
    "m5": 800,
    "c4": 900,
    "c5": 1000,
    "r3": 1100,
    "r4": 1200,
    "r5": 1300,
    "p2": 1400,
    "p3": 1500,
    "g3": 1600,
    "f1": 1700,
    "h1": 1800,
    "i3": 1900,
    "d2": 2000,
    # os-types
    "linux": 10000,
    "rhel": 20000,
    "windows": 30000,
    "?": 10001,  # unknown OS, but assume linux for chart
    # database engines
    "mariadb": 100000,
    "mysql": 110000,
    "aurora": 120000,
    "aurora-mysql": 130000,
    "postgres": 140000,
    "aurora-postgresql": 150000,
    "sqlserver-se": 160000,
    "multi_az": 1
}


class AwsCostHelperError(Exception):
    """Catch this exception from bud_helper_util methods that throw it.
    An error message needs to be propagated back out to the user.

    NOTE: Don't throw this exception, only catch and convert it.
    """
    def __init__(self, *args):
        Exception.__init__(self, *args)


def create_cti_poke_session(aws_account_name):
    """
    Create a session with read access to AWS accounts.
    :param aws_account_name: Same as ENVIRONMENT above.
    :return: session.
    """
    sts = boto3.client('sts')
    session = sts.assume_role(
        RoleArn='arn:aws:iam::{}:role/ctipoke'.format(AWS_ACCOUNTS[aws_account_name]),
        RoleSessionName='ctipoke')
    return session


def create_cost_explorer_session():
    """
    Need to decide how to do this.
     Option A) modify ctipoke role in NetEng
     Option B) add trust entity to ReadBills role in NetEng.
    :return:
    """
    return create_cti_poke_session('net-eng')


def grep(filename, needle):
    """Find text within file.
    This returns a list of matching lines.
    """
    ret = []
    with open(filename) as f_in:
        for i, line in enumerate(f_in):
            if needle in line:
                ret.append(line)
    return ret


def read_key_value_file_to_dictionary(filepath, delim='='):
    """Read a file in the following format.
    key1 = value1
    key2 = value2
    key3 = value3

    and convert it into a dictionary.

    :param filepath: path to the file
    :param delim: delimiter used. '=' is default. ': ' will also be common.
    :return: dictionary values of file.
    """
    f = open(filepath, 'r')
    answer = {}
    for line in f:
        k, v = line.strip().split(delim)
        answer[k.strip()] = v.strip()

    f.close()
    return answer


def unzip_file(zip_file_path, to_dir):
    """Unzip a *.zip file in a local directory."""

    try:
        print('Unzip verifying path: %s' % zip_file_path)
        # Verify zip file
        if not os.path.isfile(zip_file_path):
            message = 'Unzip failed to verify file: %s' % zip_file_path
            print(message)
            raise AwsCostHelperError(message)
        else:
            print('Verified "{}" is a file.'.format(zip_file_path))

        # unzip
        zip_ref = zipfile.ZipFile(zip_file_path, 'r')
        zip_ref.extractall(to_dir)
        zip_ref.close()
    except AwsCostHelperError:
        raise
    except Exception as ex:
        message = 'Failed to unzip file: %s \nto dir: %s.\nReason: %s'\
                  % (zip_file_path, to_dir, ex.message)
        print(message)
        raise AwsCostHelperError(message)


def get_files_in_dir_by_type(dir_path, file_ext):
    """Get files of extension in directory."""
    included_extensions = [file_ext]
    file_names = [fn for fn in os.listdir(dir_path)
                  if any(fn.endswith(ext) for ext in included_extensions)]

    return file_names


def get_awscost_hourly_time_format():
    """
    Get timestamp in hourly format for the 'time' index in AWSCost table.

    Will be in this format: 20181116-18
    """
    time = pendulum.now('US/Pacific').strftime("%Y%m%d-%H")
    return time


def get_awscost_daily_time_format():
    """
    Get timestamp in hourly format for the 'time' index in AWSCost table.

    Will be in this format: 20181116
    """
    time = pendulum.now('US/Pacific').strftime("%Y%m%d")
    return time


def increment_time_index(time_index, add_hours=1):
    """
    Increment the time_index.
    :param time_index: string in format YYYYMMDD-HH
    :param add_hours: integer +1 in future, -1 in past.
    :return:
    """
    # print('increment_time_index(time_index={}, add_hours={})'.format(time_index, add_hours))

    date = datetime.datetime.strptime(time_index, '%Y%m%d-%H')
    next_interval = date + datetime.timedelta(hours=add_hours)

    return next_interval.strftime('%Y%m%d-%H')


def get_verbose_cost_explorer_service_names_from_key(service_key):
    """
    Return verbose names needed by AWS Cost Explorer API (version. dec 2018)

    :param service_key: Value values 'ec2' | 'rds' | 'redshift' | 'elasticache' | 'es'
    :return: String with long name like: 'Amazon Elastic Compute Cloud - Compute', if
    """

    # For some unknown reason Cost Explorer API want verbose names instead of abbreviations.
    service_name_map = {
        'ec2': 'Amazon Elastic Compute Cloud - Compute',
        'rds': 'Amazon Relational Database Service',
        'redshift': 'Amazon Redshift',
        'elasticache': 'Amazon ElastiCache',
        'es': 'Amazon Elasticsearch Service'
    }

    # turn key into value.
    service_name = service_name_map.get(service_key)
    if not service_name:
        print('WARN: Method "get_verbose_cost_explorer_service_names_from_key" '
              'cannot find service name for key: {}. Returning key instead.'.format(service_key))
        service_name = service_key

    return service_name


def get_cost_explorer_format_yyyy_mm_dd(delta_days=0):
    """
    Cost Explorer Reports want format: YYYY-MM-DD
    Default give the date for today.
    For days in the past pass in a negative number.
    For days in the future pass in a possitive number.

    :param delta_days: Number
    :return: string in YYYY-MM-DD format. Ex. 2019-01-07
    """
    today = pendulum.now('US/Pacific')
    display_date = today + datetime.timedelta(days=delta_days)

    return display_date.strftime("%Y-%m-%d")


def start_timer():
    """
    Standard way to start timer.
    :return:
    """
    return datetime.datetime.now()


def delta_time(start_time):
    """
    Use datetime and start_time for delta from a start time stamp.

    returns a float  in seconds like:  x.xxxx

    :param start_time:
    :return: float or deltatime with time in seconds for a delta.
    """
    end_time = datetime.datetime.now()
    tot_time = end_time - start_time
    ret_val = tot_time.total_seconds()
    return ret_val


def print_delta_time(start_time, stage):
    """
    Prints the delta time from start_time into the aws lambda function's log.
    Format is:  'TIMER <stage-comment>: <delta time> sec.'
    :param start_time:
    :param stage: The comment to append to front of timer log.
    :return: None
    """
    delta_time_float = delta_time(start_time)
    log_line = 'TIMER {}: {} sec.'.format(stage, delta_time_float)
    print(log_line)


def log_traceback_exception(ex):
    """
    Helper class for logging exception.
    :param ex: python exception class
    :return: None
    """
    try:
        template = 'Failed during execution. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))
    except Exception as e:
        print('Something went wrong with traceback logging')
        print('Traceback Exception: {}'.format(e))


def get_aws_cost_version():
    """
    Return the AWS Cost Version string.
    The version is changed manually. The build time is changed
    by the script.

    Note: "{#sbuild_time_string#}" is modified by push_aws_cost_s3.

    :return: "AWS_Cost_V_1.00_{build-time}"
    """
    version = 'AWS_Cost_V_1.09'
    build_time = '{#build_time_string#}'

    return '{}_{}'.format(version, build_time)


def get_account_id_from_session(session):
    """
    Get the account id from the session.

    An example session has the below format, need to grab it from the Arn.
    {u'AssumedRoleUser': {
       u'AssumedRoleId': 'AROA_ROLE_ID:ctipoke',
       u'Arn': 'arn:aws:sts::123456789012:assumed-role/ctipoke/ctipoke'
       },
    u'Credentials': {
       u'SecretAccessKey': 'OuQ0P...xYPVs',
       u'SessionToken': 'FQoG..REDACTED..LZ4QU=',
       u'Expiration': datetime.datetime(2019, 1, 9, 20, 20, 4, tzinfo=tzlocal()),
       u'AccessKeyId': 'ASIAR...PYOWR'
       },
    'ResponseMetadata': {
       'RetryAttempts': 0,
       'HTTPStatusCode': 200,
       'RequestId': '91340374-1443-11e9-8249-bd132d0f5c1f',
       'HTTPHeaders': {'x-amzn-requestid': '91340374-1443-11e9-8249-bd132d0f5c1f', 'date': 'Wed, 09 Jan 2019 19:20:03 GMT', 'content-length': '1048', 'content-type': 'text/xml'}
       }
    }

    :param session:
    :return: AWS account id.
    """
    try:
        assumed_role_user = session.get('AssumedRoleUser')
        if assumed_role_user:
            arn = assumed_role_user.get('Arn')
            if arn:
                arn_parts = arn.split(':')
                print('arn_parts: {}'.format(arn_parts))
                return arn_parts[4]
        else:
            raise ValueError("Couldn't parse session")

    except Exception as ex:
        raise ValueError('Could not parse session. Reason: {}'.format(ex))


def init_aws_names():
    """
    Method called just once to reverse the key values from AWS_ACCOUNT.
    :return:
    """
    print('init_aws_names')
    if len(AWS_NAMES)>0:
        print('WARN: already created')

    for k, v in AWS_ACCOUNTS.iteritems():
        AWS_NAMES[v] = AWS_NAMES.get(v, [])
        AWS_NAMES[v].append(k)


def get_account_name_from_session(session):
    """
    Get the name of an account from the session.
    :param session:
    :return:
    """
    aws_account_id = get_account_id_from_session(session)
    if len(AWS_NAMES) == 0:
        init_aws_names()

    return AWS_NAMES.get(aws_account_id)


def get_aws_account_id_from_name(aws_account_name):
    """
    If you have the account name, but need the account_id.
    :param aws_account_name:
    :return:
    """
    return AWS_ACCOUNTS.get(aws_account_name)


def create_time_column_values(start_time, end_time):
    """

    :param start_time:
    :param end_time:
    :return:
    """
    print('create_time_column_values start_time={}, end_time={}'.format(start_time, end_time))

    # verify end_time is valid, and raise ValueError if it isn't.
    if not end_time.startswith('20'):
        raise ValueError('Invalid time_index. Does not start with 20... was: {}'.format(end_time))
    if '-' not in end_time:
        raise ValueError('Invalid time_index. Missing (-). was: {}'.format(end_time))

    curr_time_index = start_time
    ret_val = []
    while curr_time_index > end_time:
        ret_val.append(curr_time_index)
        next_time = increment_time_index(curr_time_index, -1)
        curr_time_index = next_time

    return ret_val


def upload_json_to_awscost_data_s3_bucket(s3_dir, s3_filename, json_text):
    """
    Upload a json text to an s3 bucket with a given key. Which in the context of
    AWS Cost can be a date or time stamp.
    :param s3_dir: name of directory in S3 bucket. ex: "20190102"
    :param s3_filename: name of file in S3. ex: "reservation_coverage_total.json"
    :param json_text:
    :return: None.
    """
    try:
        temp_path = '/tmp/' + s3_filename

        len_txt = len(json_text)
        print('local file: {} has {} keys in dictionary'.format(temp_path, len_txt))

        with open(temp_path, 'w') as outfile:
            json.dump(json_text, outfile)

        upload_file_to_awscost_s3_bucket(s3_dir, s3_filename, temp_path)

    except Exception as ex:
        print('Failed to upload to awscost-data S3 bucket: {}'.format(ex.message))
        log_traceback_exception(ex)


def upload_file_to_awscost_s3_bucket(s3_dir, s3_filename, local_path, delete_local_file=False):
    """
    Upload a file in lambda functions `/tmp` directory into an S3 bucket.
    :param s3_dir: name of directory in S3 bucket. ex: "20190102"
    :param s3_filename: name of file in S3. ex: "reservation_coverage_total.json"
    :param local_path: local path to file. ex: "/tmp/reservation_coverage_total.json"
    :param delete_local_file: True if you want to delete file after upload. Default it False.
    :return:
    """
    try:
        bucket_name = 'awscost-data'
        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(
            local_path, bucket_name,
            '{}/{}'.format(s3_dir, s3_filename)
        )

        if delete_local_file:
            os.remove(local_path)

    except Exception as ex:
        print('Failed to upload to awscost-data S3 bucket: {}'.format(ex.message))
        log_traceback_exception(ex)


def get_panda_for_resource(awscost_table, key, start_time, end_time):
    """
    Create a panda object (either for analysis or plotting) from the
    AWSCost table.
    :param key: AWSCost key value like: dynamodb:roku:us-east-1
    :param start_time: Time index like:  201901-12
    :param end_time: Time index like: 201909-14
    :return: panda with all data loaded and unpacked.
    """
    try:
        print('get_panda_for_resource: key={}, start_time={}, end_time={}'.format(key, start_time, end_time))

        # Go back 3 weeks.
        # row_0 = create_time_column_values(time_index, -1, hours_in_3_weeks)
        row_0 = create_time_column_values(start_time, end_time)
        time_dict = {'time': row_0}

        ret_val_data_frame = pd.DataFrame(index=time_dict.get('time'))
        ret_val_data_frame.index.name = 'time'

        # swap start and end time if one is larger than other. DynamoDB "between" is picky.
        if start_time < end_time:
            swap = end_time
            end_time = start_time
            start_time = swap
            print('Swapped start and end times. start_time={}, end_time={}'.format(start_time, end_time))

        response = awscost_table.query(
            KeyConditionExpression=Key('awsResource').eq(key) & Key('time').between(end_time, start_time)
        )

        column_names_set = set()

        items = response.get('Items')
        if items:
            for curr_item in items:
                node_types = curr_item.get('node_types')
                time_index = curr_item.get('time')

                key_list = node_types.keys()
                key_list.sort()

                for curr_key in key_list:
                    if curr_key not in column_names_set:
                        col_num = len(ret_val_data_frame.columns)
                        print('adding column: {} @ {}'.format(curr_key, col_num))

                        ret_val_data_frame.insert(col_num, curr_key, np.nan)
                        column_names_set.add(curr_key)

                    curr_value = node_types.get(curr_key)
                    # print('{}: {}'.format(curr_key, curr_value))
                    ret_val_data_frame.at[time_index, curr_key] = curr_value

        return ret_val_data_frame

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        log_traceback_exception(ex)
        return None


def sort_nodes_by_size(node_list):
    """
    Given a list of AWS nodes with sizes in the name. Sort them by size.

    Sort by smallest to largest.
    nano, micro, small, medium, large, xlarge, 2xlarge, 4xlarge, ....  (n)xlarge.

    AWS convention is typically...   *.<size>. This algorithm splits on (.) and ignores what is in front.

    If an exception occurs then return the original unsorted list.

    :param node_list: list of nodes, and are unsorted.
    :return: list of nodes, sorted from smallest to largest.
    """
    try:
        node_sorted_list = sorted(node_list, key=assign_by_type_size_os_and_db_engine)
        return node_sorted_list

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        log_traceback_exception(ex)
        return node_list


# deprecated.
# def assign_node_size_value(elem):
#     """
#     This method is a lambda function into a python sort routine.
#     Assign values to the *.<size> part of string.
#     .nano=1
#     .micro=2
#     .small=3
#     .medium=4
#     .large=5
#     .xlarge=6
#     .(number)xlarge=6+number
#     Any values that doesn't have any of the following sub-strings is assigned 0 for the sort.
#     :param elem: node size string for sorting.
#     :return:
#     """
#     # NOTE: RDS has format.    db.m5.12xlarge:mysql.  Remove part after :
#     if ':' in elem:
#         # remove anything after :
#         r = elem.split(':')
#         elem = r[0]
#
#     parts = elem.split('.')
#     num_parts = len(parts)
#     size_part = parts[num_parts-1]
#     # print('size={}'.format(size_part))
#     if size_part == 'nano':
#         return 1
#     elif size_part == 'micro':
#         return 2
#     elif size_part == 'small':
#         return 3
#     elif size_part == 'medium':
#         return 4
#     elif size_part == 'large':
#         return 5
#     elif size_part == 'xlarge':
#         return 6
#     num_xlarge_part = size_part.replace('xlarge', '')
#     if is_int(num_xlarge_part):
#         size = int(num_xlarge_part)
#         return size+6
#     else:
#         return 0


def assign_by_type_size_os_and_db_engine(elem):
    """
    This is a generic sort function that needs to combine node families and size
    into the and adding values used for sorting.  This is needed for consistent
    graphing.

    In this sort.        medium < large < xlarge < 2xlarge
    Also family nodes    t2 < t3 < m3 < m4 < m5 < c ... < r ... < i ... < p ...

    Below is one or two examples from each resource type.
    EC2: linux-t2.xlarge
         ?-p2.xlarge
    RDS: multi_az-db.t2.micro:mysql
         db.r3.large:aurora
    Elasticache: cache.r3.2xlarge
    Elastic search: r4.2xlarge.elasticsearch

    :param elem: string like: multi_az-db.t2.micro:mysql
    :return: int value to indicate sort order
    """
    sort_value = 0
    try:
        # print('elem={}'.format(elem))
        parts = re.split('\.|-|:', elem)
        # print('parts={}'.format(parts))
        for curr_part in parts:
            # Accumulate points
            value = NODE_SORT_VALUES.get(curr_part)
            if value:
                sort_value += value
            else:
                if 'xlarge' in curr_part:
                    # Do the calculation for node size.
                    # print('calculating size for "{}"'.format(curr_part))
                    num_xlarge_part = curr_part.replace('xlarge', '')
                    if is_int(num_xlarge_part):
                        size = int(num_xlarge_part)
                        value = size + 11
                        # print('{}={}'.format(curr_part, value))
                    sort_value += value
        print('sort value: {} = {}'.format(elem, sort_value))
        return sort_value
    except Exception as ex:
        print('WARN: ')
        return sort_value


def is_int(str):
    """
    Is string an integer?

    return True if integer
    otherwise return False
    :param str: Any string
    :return: True if integer otherwise return False
    """
    try:
        int(str)
        return True
    except ValueError:
        return False


def get_price(region, instance, os_type):
    """
    Get the OnDemand price for a specific EC2 Instance type.
    :param region: String - Short name for region. us-east-1 | us-west-2
    :param instance: String - like m5.4xlarge
    :param os_type: String - values: Windows | Linux | RHEL | SUSE
    :return:
    """
    try:
        pricing_client = boto3.client('pricing', region_name='us-east-1')

        # Convert short name, to long name expected by this API.
        long_region_name = REGIONS.get(region)
        if long_region_name:
            region = long_region_name

        f = FLT.format(r=region, t=instance, o=os_type)
        data = pricing_client.get_products(ServiceCode='AmazonEC2', Filters=json.loads(f))

        # print('Debug: data={}'.format(data))

        price_list = data.get('PriceList')
        if price_list:
            # print('PriceList size={}'.format(len(price_list)))

            od = json.loads(data['PriceList'][0])['terms']['OnDemand']
            id1 = list(od)[0]
            id2 = list(od[id1]['priceDimensions'])[0]
            return od[id1]['priceDimensions'][id2]['pricePerUnit']['USD']
        else:
            raise KeyError('Missing "PriceList" key')
    except Exception as e:
        print('Error: {} get_price api. region={}, instance_type={}, os_type={}'
              .format(e, region, instance, os_type))


# Unit tests below here.
def test_sort_nodes():
    """
    Unit tests for sorting nodes, etc...
    :return: None
    """
    print('\nTest node sort for EC2 format')
    ec2_start_list = [
        'linux-c5.2xlarge', 'linux-c5.nano', 'linux-c5.large', 'linux-c5.xlarge', 'linux-c5.4xlarge',
        'linux-c5.small', 'linux-c5.medium', 'blah', 'linux-c5.11xlarge', 'linux-c5.64xlarge'
    ]
    ec2_sorted_list = sort_nodes_by_size(ec2_start_list)
    print('ec2_sorted_list = {}'.format(ec2_sorted_list))

    print('\nTest node sort for RDS format')
    rds_start_list = ['db.r4.12xlarge:aurora-mysql', 'db.r4.large:aurora-mysql', 'db.r4.medium:aurora-mysql']
    rds_sorted_list = sort_nodes_by_size(rds_start_list)
    print('rds_sorted_list = {}'.format(rds_sorted_list))

    print('\nTest node sort for Elasticache format')
    cache_start_list = ['cache.r3.2xlarge', 'cache.r3.12xlarge', 'cache.r3.micro']
    cache_sorted_list = sort_nodes_by_size(cache_start_list)
    print('elasticache_sorted_list = {}'.format(cache_sorted_list))

    # mix families into one chart.
    print('\nTest node sort for EC2 format with mixed families')
    ec2_families_start_list = [
        'linux-c5.2xlarge', 'linux-c5.nano', 'linux-c5.large', 'linux-c5.xlarge', 'linux-c5.4xlarge',
        'linux-c5.small', 'linux-c5.medium', 'blah', 'linux-c5.11xlarge', 'linux-c5.64xlarge',
        'linux-c4.2xlarge', 'linux-c4.nano', 'linux-m4.large', 'linux-m4.xlarge'
    ]
    ec2_families_sorted_list = sort_nodes_by_size(ec2_families_start_list)
    print('ec2_sorted_list = {}'.format(ec2_families_sorted_list))

    print('\nTest node sort for RDS format mixed families and database engines')
    rds_mixed_start_list = [
        'db.r4.12xlarge:aurora-mysql', 'db.r4.large:aurora-mysql', 'db.r4.medium:aurora-mysql',
        'db.r3.12xlarge:aurora-mysql', 'db.r3.large:aurora-mysql', 'db.r3.medium:aurora-mysql',
        'multi_az-db.r3.large:mysql', 'db.r3.large:mysql', 'multi_az-db.t2.medium:aurora-mysql'
    ]
    rds_mixed_sorted_list = sort_nodes_by_size(rds_mixed_start_list)
    print('rds_sorted_list = {}'.format(rds_mixed_sorted_list))


# Use main for quick tests.
if __name__ == '__main__':
    try:
        test_sort_nodes()

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        log_traceback_exception(ex)