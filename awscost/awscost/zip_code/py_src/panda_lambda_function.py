"""
AWS Cost project entry point for panda lambda functions which might require lots of memory,
or tasks that could run a long time.

This function will also be where on-the-fly graphs can be created.
"""

import os.path
import zipfile
import datetime

import boto3
import util.aws_util as aws_util
import util.awscost_helper_util as awscost_helper_util

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DYNAMODB = boto3.resource('dynamodb')
AWS_COST_TABLE = DYNAMODB.Table('AWSCost')


def lambda_handler(event, context):
    """
    Entry-point for AWS Cost Panda.
    :param event:
    :param context:
    :return:
    """
    try:
        print('Panda entry-point Version: {}'.format(awscost_helper_util.get_aws_cost_version()))

        curr_time = awscost_helper_util.get_awscost_hourly_time_format()
        print('time: {}'.format(curr_time))

        work_type = event.get('work_type')
        time_index = event.get('time_index')
        if not work_type:
            raise ValueError('No work_type found in event.')

        if work_type == 'no_update':
            print('No update')
            return 'Success'
        elif work_type.startswith('test'):
            test_handler(event, context)
        elif work_type == 'make_ec2_plots':
            do_make_ec2_plots(event)
        elif work_type == 'export_excel_for_account':
            do_export_excel_for_account(event)
        elif work_type == 'read_billing_file':
            do_read_billing_file(event)
        elif work_type == 'plot_ce_reports':
            do_plot_ce_reports(event)
        else:
            raise ValueError('Unrecognized work_type.  work_type={}'.format(work_type))

        print("Time remaining: {} ms".format(context.get_remaining_time_in_millis()))
        print('Memory Limit: {}'.format(context.memory_limit_in_mb))

        # Check aws resource utilization.

        # Log time-remaining.
        print('Finished scanning for usage for time = {}'.format(curr_time))
        print('Finished @ {}'.format(datetime.datetime.now()))
        return 'Success'

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def do_plot_ce_reports(event):
    """

    Read the CE plots from S3 bucket. Convert to CSV if needed and then plot reports.

    :param event:
    :return:
    """


def do_read_billing_file(event):
    """
    Read the cost file.

    NOTE: The /tmp directory on a lambda function is limited to 512 MB, but the downloaded billing file
    is larger than that zipped and unzipped could be as much as 4 GB.
    It seems this function will need to move to a EC2 Instance, or Docker image.

    ToDo: Initially we need to measure how long it takes and what size lambda function is required.
    ToDo: Estimate cost of doing this in lambda vs. docker(FarGate).
    ToDo: Read the timestamp on the Cost File before downloading it, if not updated, store file
    ToDo: in lambda's /tmp directory and read it from there to save download cost/time.

    :param event:
    :return:
    """
    print('do_read_billing_file')
    session = awscost_helper_util.create_cost_explorer_session()
    s3_resource = aws_util.get_boto3_resource_by_name('s3', session, 'us-east-1')

    # ToDo: fill in month date.
    # s3://roku-billing/088414020449-aws-billing-detailed-line-items-with-resources-and-tags-2019-01.csv.zip
    billing_file_name = '088414020449-aws-billing-detailed-line-items-with-resources-and-tags-2019-01.csv.zip'
    bill_file_summary = s3_resource.ObjectSummary('roku-billing', billing_file_name)

    bill_file_last_modified = bill_file_summary.last_modified
    bill_file_size = bill_file_summary.size

    update_billing_file = True
    billing_file_metadata = {}

    # store info in /tmp/billing_file_metadata.txt
    if not os.path.exists('/tmp/billing_file_metadata.txt'):
        print('/tmp/billing_file_metadata.txt does not exist')
        update_billing_file = True
    else:
        # read the file.
        print('reading /tmp/billing_file_metadata.txt')
        with open('/tmp/billing_file_metadata.txt') as bill_metafile:
            for line in bill_metafile:
                (key, value) = line.split(': ')
                billing_file_metadata[key] = value
        curr_last_modified = billing_file_metadata.get('last_modified')
        if bill_file_last_modified == curr_last_modified:
            update_billing_file = False

    # Look at last modified for the files we will want to load into pandas.
    # ... detailed-line-items-with-resources-and-tags-2019-01.csv.zip   (zipped it ends up being...  1012.4 MB)
    download_successful = False
    if update_billing_file:
        try:
            # download latest.
            billing_file_obj = s3_resource.Object('roku-billing', billing_file_name)
            bill_file_local_path = '/tmp/{}'.format(billing_file_name)
            billing_file_obj.download_file(bill_file_local_path)

            download_successful = True

            # write the meta-data file
            print('updating /tmp/billing_file_metadata.txt')
            with open('/tmp/billing_file_metadata.txt', "w") as bill_metafile:
                bill_metafile.write('last_modified: {}\nsize: {}'.format(bill_file_last_modified, bill_file_size))

        except Exception as ex:
            # log error.
            print('Exception: {}'.format(ex.message))
            awscost_helper_util.log_traceback_exception(ex)

    unzip_successful = False
    if download_successful:
        # if new billing file downloaded, unzip it, otherwise use existing unzipped file.
        try:
            print('unzipping new file: {}\nlast_updated: {}\nsize: {}'
                  .format(bill_file_local_path, bill_file_last_modified, bill_file_size))

            with zipfile.ZipFile(bill_file_local_path, 'r') as zip_ref:
                zip_ref.extractall('/tmp')

            unzip_successful = True
        except Exception as ex:
            # log error.
            print('Exception: {}'.format(ex.message))
            awscost_helper_util.log_traceback_exception(ex)

    # ToDo: load this into panda to measure memory needed.
    if unzip_successful:
        print('Unzip finished.')


def do_export_excel_for_account(event):
    """
    Export the data AWS Cost table to an excel file for an individual account or Roku summary.

    The JSON (event) format needs the following keys.
    "resource_key": key used in DynamoDB table to store resources.
    "account_name": AWS Account name. Needs either the account name or the id.
    "account_id": AWS Account IDNeeds either the account name or the id.
    "aws_region":  value either:   us-east-1 | us-west-2
    "start_time": first time to the hour in "YYYYMMDD-HH" format.
    "end_time": last time to the hour in "YYYYMMDD-HH" format.

    This will get exported into an Excel file and put in the awscost-data S3 bucket with the following
    name format:

    <resource_key>-<account_id>-<aws_region>-<start_time>-<end_time>.xlsx

    :param event: JSON format needs the following.
    :return:
    """
    print('do_export_excel_for_account')
    print('event = {}'.format(event))

    # Get the needed data.
    resource_key = event.get('resource_key')
    account_name = event.get('account_name')
    account_id = event.get('account_id')
    aws_region = event.get('aws_region')
    start_time = event.get('start_time')
    end_time = event.get('end_time')

    # raise an exception if any inputs missing.
    if not resource_key or not aws_region or not start_time:
        raise ValueError('Missing parameters in event. event={}'.format(event))

    if not account_id and not account_name:
        raise ValueError('Missing account_id or account_name')

    if not end_time:
        print('WARN. No end_time. Use current time.')
        end_time = awscost_helper_util.get_awscost_hourly_time_format()

    key = '{}:{}:{}'.format(resource_key, account_id, aws_region)
    print('Calling AWSCost table with key: {}'.format(key))

    df_for_excel = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, key, start_time, end_time)

    # Write this locally then upload to S3.
    region_under_score = aws_region.replace('-','_')
    file_key = '{}-{}-{}'.format(resource_key, account_id, region_under_score)
    start_under_score = start_time.replace('-', '_')
    end_under_score = end_time.replace('-', '_')

    file_name = '{}-{}-{}.xlsx'.format(file_key, start_under_score, end_under_score )
    local_path = '/tmp/{}.xlsx'.format(file_name)
    excel_file = open(local_path, "w+")
    excel_file.close()

    writer = pd.ExcelWriter(local_path, engine='openpyxl')
    df_for_excel.to_excel(writer, file_key)
    writer.save()

    s3_dir = awscost_helper_util.get_awscost_daily_time_format()
    awscost_helper_util.upload_file_to_awscost_s3_bucket(s3_dir, file_name, local_path)


def do_make_ec2_plots(event):
    """
    Create plots/charts from data collected .....details TBD.

    Initially read the EC2 file into a panda and then try to make some plots with them.
    It we want to make the charts per account will need to read them from the
    database table.

    After that will want to print-out the coverage and utilization reports.

    :param event:
    :return:
    """
    print('do_make_ec2_plots')
    # ToDo: Decide a variables needed for the plots. start/end dates?
    # Goal is to have an hourly plot for each EC2 node family, for all Roku and each account.

    timestamp = awscost_helper_util.get_awscost_daily_time_format()
    end_date = '{}-00'.format(timestamp)

    # EC2 data us-west-1
    df_ec2os_west = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'ec2os:roku:us-west-2',
                                                               end_date, '20181221-00')
    print('ec2 west head(): \n{}'.format(df_ec2os_west.head()))
    # ec2_westfamily_list = ['linux-c5', 'linux-m5', 'linux-r4', 'linux-t2']
    ec2_westfamily_list = ['linux-c', 'linux-m', 'linux-r', 'linux-t']
    plot_node_families_from_awscost_data_frame(df_ec2os_west, ec2_westfamily_list, 'EC2_us-west-2')

    # EC2 data us-east-1
    df_ec2os_east = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'ec2os:roku:us-east-1',
                                                               end_date, '20181221-00')
    print('ec2 east head(): \n{}'.format(df_ec2os_east.head()))
    # ec2_east_family_list = ['linux-c5', 'linux-m4', 'linux-m5', 'linux-r4', 'linux-r5', 'linux-t2']
    ec2_east_family_list = ['linux-c', 'linux-m', 'linux-r', 'linux-t']
    plot_node_families_from_awscost_data_frame(df_ec2os_east, ec2_east_family_list, 'EC2_us-east-1')

    # RDS data us-west-2
    df_rds_west = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'rds:roku:us-west-2',
                                                             end_date, '20181221-00')
    rds_west_family_list = ['r4.aurora-postgresql',
                            't2.postgres', 't2.mysql', 't2.aurora-mysql',
                            'm4.mysql']
    plot_node_families_from_awscost_data_frame(df_rds_west, rds_west_family_list,
                                               'RDS_us-west-2', lambda_filter_func=rds_lambda_filter_func)

    # RDS data us-east-1
    df_rds_west = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'rds:roku:us-east-1',
                                                             end_date, '20181221-00')
    rds_west_family_list = ['t2.postgres', 't2.mysql', 't2.aurora-mysql', 't2.aurora', 't2.mariadb',
                            'r3.mysql',
                            'r4.aurora-postgresql', 'r4.aurora', 'r4.aurora-mysql', 'r4.postgres',
                            'm3.mysql', 'm3.sqlserver-se', 'r3.aurora', 'r3.mysql',
                            'm4.mysql', 'm4.postgres',
                            'm5.mysql']
    plot_node_families_from_awscost_data_frame(df_rds_west, rds_west_family_list,
                                               'RDS_us-east-1', lambda_filter_func=rds_lambda_filter_func)

    # next need to figure out how store plot to S3 and crate multiple stacked plots.
    print('Done.')

    # Elasticache us-west-2
    df_elasticache_west = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'elasticache:roku:us-west-2',
                                                               end_date, '20181221-00')
    print('elasticache west head(): \n{}'.format(df_elasticache_west.head()))
    elasticache_westfamily_list = ['cache.r',  'cache.t']
    plot_node_families_from_awscost_data_frame(df_elasticache_west, elasticache_westfamily_list, 'Elasticache_us-west-2')

    # Elasticache us-east-1
    df_elasticache_east = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'elasticache:roku:us-east-1',
                                                               end_date, '20181221-00')
    print('elasticache east head(): \n{}'.format(df_elasticache_east.head()))
    elasticache_eastfamily_list = ['cache.m', 'cache.r',  'cache.t']
    plot_node_families_from_awscost_data_frame(df_elasticache_east, elasticache_eastfamily_list, 'Elasticache_us-east-1')

    # Elasticsearch Service us-west-2
    df_elasticsearch_west = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'es:roku:us-west-2',
                                                               end_date, '20181221-00')
    print('elasticsearch west head(): \n{}'.format(df_elasticsearch_west.head()))
    elastsearch_westfamily_list = ['i', 'm',  'r', 't']
    plot_node_families_from_awscost_data_frame(df_elasticsearch_west, elastsearch_westfamily_list, 'Elasticsearch_us-west-2')

    # Elasticsearch Service us-east-1
    df_elastisearch_east = awscost_helper_util.get_panda_for_resource(AWS_COST_TABLE, 'es:roku:us-east-1',
                                                               end_date, '20181221-00')
    print('elasticsearch east head(): \n{}'.format(df_elastisearch_east.head()))
    elasticsearch_eastfamily_list = ['i', 'm',  'r', 't']
    plot_node_families_from_awscost_data_frame(df_elastisearch_east, elasticsearch_eastfamily_list, 'Elasticsearch_us-east-1')


def plot_node_families_from_awscost_data_frame(df_source, family_list, region_title, lambda_filter_func=None):
    """
    Given an EC2 DataFrame with the AWS Cost data in it, plot the family if it is found in the data-frame.
    Note: EC2 node types are different than other resource types (RDS, Elasticache, Elastisearch Service),
    so EC2 needs it's own sort algorithm.


    :param df_source: A DataFrame create by the "get_panda_for_resource" function.
    :param family_list: list if prefixes to plot. Example for EC2. 'linux-c5'
    :param region_title: either 'us-east-1' or 'us-west-2'
    :return:
    """
    try:
        timestamp = awscost_helper_util.get_awscost_daily_time_format()
        column_names = list(df_source)
        print('columns: {}'.format(column_names))

        for curr_family in family_list:
            print('Creating {} family graph'.format(curr_family))

            column_names_filtered = []
            if not lambda_filter_func:
                column_names_filtered = filter(lambda s: s.startswith(curr_family), column_names)
            else:
                column_names_filtered = lambda_filter_func(curr_family, column_names)

            # Don't make this graph if we don't find any of this type.
            num_columns = len(column_names_filtered)
            if num_columns == 0:
                print('Skipping "{}" family. No data found.'.format(curr_family))
                continue

            column_names_filtered = awscost_helper_util.sort_nodes_by_size(column_names_filtered)
            print('{} columns: {}'.format(column_names_filtered, column_names_filtered))

            df_filtered = df_source[column_names_filtered].copy()
            print('{} df head(): \n{}'.format(curr_family, df_filtered.head()))

            graph_title = '{} family - {}'.format(curr_family, region_title)
            region_title_under_score = region_title.replace('-','_')
            file_name = '{}-{}-{}.svg'.format(timestamp, curr_family, region_title_under_score)
            tmp_dir_path = '/tmp/{}'.format(file_name)

            print('Graph title: {}'.format(graph_title))
            print('local directory: {}'.format(tmp_dir_path))

            ax = df_filtered.plot(kind='area', title=graph_title)
            ax.set(xlabel='time', ylabel='# instances')
            # ax.set_xticks(df_filtered.index)
            # ax.set_xticklabels(df_filtered.time, rotation='45')
            figure = ax.get_figure()
            figure.savefig(tmp_dir_path)

            print('Saving local graph {} to: {} / {}'.format(tmp_dir_path, timestamp, file_name))
            awscost_helper_util.upload_file_to_awscost_s3_bucket(timestamp, file_name, tmp_dir_path)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def rds_lambda_filter_func(curr_family, column_names):
    """
    Lambda function passed to plot_* function for RDS type nodes which have the format: db.r4.large:aurora-mysql



    :param curr_family: in format.    r4.aurora-mysql
    :param column_names: unfiltered list of column names in format.
    :return: filtered list of columns that match.
    """
    filtered_column_names = []
    for curr_column_name in column_names:
        try:
            # print('checking: {}'.format(curr_column_name))
            engine_parts = curr_column_name.split(':')
            dot_parts = curr_column_name.split('.')
            check_name = '{}.{}'.format(dot_parts[1], engine_parts[1])
            if check_name == curr_family:
                filtered_column_names.append(curr_column_name)

        except Exception as ex:
            # log error.
            print('WARN. Leaving out column name. Could not process: {}'.format(curr_column_name))

    return filtered_column_names


def print_data_type(name, obj):
    """
    Just to avoid typing over and over.
    :param name: to put on string
    :param obj: object
    :return:
    """
    print('{} type: {}'.format(name, type(obj)))


# some test methods here #
def test_handler(event, context):
    """
    If you get a work_type that starts with test, it gets forwarded to this entry point.
    :param event:
    :param context:
    :return:
    """
    try:
        # Test CostExplorer Report access in NetEng account.
        print('Panda lambda test_handler. event={}'.format(event))

        print('Testing get_price helper function')

        price = awscost_helper_util.get_price('EU (Ireland)', 'c5.xlarge', 'Linux')
        print('Price Ireland: {}'.format(price))

        p_i3_large = awscost_helper_util.get_price('us-east-1', 'i3.large', 'Linux')

        print_price_for_type('i3.large')
        print_price_for_type('i3.xlarge')
        print_price_for_type('m3.xlarge')
        print_price_for_type('m4.2xlarge')
        print_price_for_type('m5.4xlarge')
        print_price_for_type('t2.xlarge')
        print_price_for_type('c4.2xlarge')
        print_price_for_type('c4.xlarge')
        print_price_for_type('c5.2xlarge')
        print_price_for_type('c5.4xlarge')
        print_price_for_type('i3.2xlarge')
        print_price_for_type('i3.large')
        print_price_for_type('i3.xlarge')
        print_price_for_type('m3.2xlarge')
        print_price_for_type('m3.medium')
        print_price_for_type('m4.2xlarge')
        print_price_for_type('m4.4xlarge')

        print('\n **** \n')

        print_price_for_type('m4.large')
        print_price_for_type('m4.xlarge')
        print_price_for_type('m5.12xlarge')
        print_price_for_type('m5.2xlarge')
        print_price_for_type('m5.large')
        print_price_for_type('m5.xlarge')
        print_price_for_type('r4.2xlarge')
        print_price_for_type('r5.2xlarge')
        print_price_for_type('t2.2xlarge')
        print_price_for_type('t2.large')
        print_price_for_type('t2.medium')
        print_price_for_type('t2.micro')
        print_price_for_type('t2.small')
        print_price_for_type('t3.medium')
        print_price_for_type('m4.2xlarge')
        print_price_for_type('m3.xlarge')
        print_price_for_type('m5.4xlarge')
        print_price_for_type('t2.xlarge')
        print_price_for_type('c3.large')
        print_price_for_type('t3.2xlarge')
        print_price_for_type('r4.4xlarge')


    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def print_price_for_type(ec2_type):
    """

    :param ec2_type:
    :return:
    """
    price = awscost_helper_util.get_price('us-east-1', ec2_type, 'Linux')
    print('{} $ {} /hr'.format(ec2_type, price))


# Do quick local tests here.
if __name__ == '__main__':
    try:
        print('testing RDS lambda function.')

        test_col_names = ['db.r4.large:aurora-postgresql', 'db.t2.large:postgres',
                          'multi_az-db.t2.micro:mysql', 'db.t2.small:postgres', 'blah']
        print('test names: {}'.format(test_col_names))
        filtered_col_names = rds_lambda_filter_func('t2.postgres', test_col_names)
        print('filtered names: {}'.format(filtered_col_names))

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
