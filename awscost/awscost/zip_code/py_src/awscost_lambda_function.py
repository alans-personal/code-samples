"""
AWS Cost project entry point for lambda functions.
"""

import boto3
import datetime
import time
import json
import os
import pandas as pd
import numpy as np
import util.awscost_helper_util as awscost_helper_util
import util.aws_util as aws_util
from boto3.dynamodb.conditions import Key, Attr
from dateutil.tz import tzutc

DYNAMODB = boto3.resource('dynamodb')
AWS_COST_TABLE = DYNAMODB.Table('AWSCost')
AWS_COST_MAP_TABLE = DYNAMODB.Table('AWSCostMap')


def lambda_handler(event, context):
    """
    Entry point to AwsCost lambda function
    :param event:
    :param context:
    :return:
    """
    try:
        print('AWS Cost entry-point Version: {}'.format(awscost_helper_util.get_aws_cost_version()))

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
        elif work_type == 'summary':
            do_summary(time_index)
        elif work_type == 'hourly_scan':
            do_hourly_scan(curr_time)
        elif work_type == 'ec2_scan':
            do_ec2_scan(curr_time)
        elif work_type == 'daily_scan':
            do_daily_scan(curr_time)
        elif work_type == 'gather_ri_stats':
            do_gather_ri_stats(curr_time)
        elif work_type == 'make_excel_file':
            do_make_excel_file(time_index)
        elif work_type == 'cost_explorer_reports':
            do_cost_explorer_reports(time_index)
        elif work_type == 'make_team_ec2_cost_report':
            do_make_team_ec2_cost_report(event)
        elif work_type == 'repair_summaries':
            print("Nothing to repair")
            # repair_redshift_and_es_daily_summaries_dec_03_2018_to_dec_20_2018(event, context)
        else:
            raise ValueError('Unrecognized work_type.  work_type={}'.format(work_type))

        print("Time remaining: {} ms".format(context.get_remaining_time_in_millis()))
        print('Memory Limit: {}'.format(context.memory_limit_in_mb))

        # Check aws resource utilization.

        # Log time-remaining.
        print('Finished scanning for usage for time = {}'.format(curr_time))
        return 'Success'

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def do_make_team_ec2_cost_report(event):
    """
    Make a per team EC2 Cost Report.

    ToDo: make this a monthly report, to pre printed out first day for previous month.
    ToDo: Look into include an hourly cost per hour chart.

    :param event:
    :return:
    """
    print('do_make_team_ec2_cost_report')
    print('event={}'.format(event))

    # month = event.get('month')

    try:
        print('Start EC2 Monthly Cost Report')

        aws_region_list = ['us-east-1', 'us-west-2']
        prefix = 'ec2os'

        # Get the data_frames per account
        data_frames = {}
        price_data = {}
        for curr_account in awscost_helper_util.AWS_ACCOUNTS:
            for curr_region in aws_region_list:
                key = '{}:{}:{}'.format(prefix, curr_account, curr_region)

                time_index = '20190201-00' # temp for this report. Need to fix this up with a start and end date.
                curr_df = create_hourly_data_frame_for_aws_account(prefix, curr_account, curr_region, time_index)

                if curr_df is not None:
                    print('Adding: {}'.format(key))
                    data_frames[key] = curr_df
                    # Convert hours into prices.
                    curr_price_df = make_price_df_from_hourly_df(curr_df, curr_region,price_data)
                    if curr_price_df is not None:
                        price_key = 'price:{}'.format(key)
                        data_frames[price_key] = curr_price_df
                    else:
                        print("WARN: No Price DataFrame for: {}".format(key))
                else:
                    print('WARN: No data_frame for key: {}'.format(key))

        # write out data-frames into an report.
        date_str = awscost_helper_util.get_awscost_daily_time_format()

        path = '/tmp/AwsCostEC2TeamReport.xlsx'
        excel_file = open(path, "w+")
        excel_file.close()
        writer = pd.ExcelWriter(path, engine='openpyxl')

        num_data_frames = len(data_frames)
        print('Adding: {} pages to Excel report'.format(num_data_frames))
        if num_data_frames == 0:
            print('WARN: No dataframes to add to Excel file.')

        for curr_key in data_frames:
            try:
                print('Add {} to Excel file.'.format(curr_key))
                curr_df = data_frames.get(curr_key)
                sheet_name = curr_key.replace(':', ' ')
                sheet_name = sheet_name.replace('ec2os',' ')
                sheet_name = sheet_name.strip()

                curr_df.to_excel(writer, sheet_name)
            except Exception as ex:
                print('Failed: {}'.format(ex.message))
                awscost_helper_util.log_traceback_exception(ex)
                print('Continue making excel file')
                # don't return just continue

        writer.save()

        #  S3 copy this file into a bucket, or attach it to an e-mail.
        bucket_name = 'awscost-data'
        folder_name = awscost_helper_util.get_awscost_daily_time_format()
        file_name = '{}-AwsEC2TeamReport.xlsx'.format(date_str)

        s3 = boto3.resource('s3')
        s3.meta.client.upload_file(
            path, bucket_name,
            '{}/{}'.format(folder_name, file_name),
        )

        print('S3 upload: {} / {} / {}'.format(bucket_name, folder_name, file_name))

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def make_price_df_from_hourly_df(hourly_df, region, price_data):
    """
    Take the EC2 Hourly data and convert it into hourly cost data.
    The data will come in as columns with the EC2 type and OS.  Look up the hourly
    cost of that type and and then create the hourly cost.

    :param hourly_df: Panda data_frame per account with hourly data.
    :param region: AWS region.   us-east-1 or us-west-2
    :param price_data: dictionary with cache of prices. Example key:  "linux:c3.2xlarge:us-west-2"
    :return: Panda DataFrame the converts hours into cost.
    """
    print('Error make_price_df_from_hourly_df() Not Implemented yet!!')

    num_found = 0
    num_not_found = 0

    for curr_column in hourly_df:
        print('TEMP: curr_column = {}'.format(curr_column))
        part = curr_column.split('-')
        os_type = part[0]
        instance_type = part[1]

        if os_type == '?':
            os_type = 'linux'

        # look for price in cache first.
        price_key = '{}:{}:{}'.format(os_type, instance_type, region)
        cached_price = price_data.get(price_key)

        if cached_price is None:
            num_not_found += 1
            price = awscost_helper_util.get_price(region, instance_type, os_type)
            print('{} costs {} / hr'.format(price_key, price))
            price_data[price_key] = price
        else:
            # found price in cache.
            num_found += 1

    print('Price cache:  found: {}, not found: {}'.format(num_found, num_not_found))
    num_prices_cached = len(price_data)
    print('Price cache: size = {}'.format(num_prices_cached))


    # raise ValueError("Warning 'make_price_df_from_hourly_df()' not implemented. Still need to create data_frame. STOP UNTIL IMPLEMENTED.")


def do_cost_explorer_reports(time_index):
    """
    Call the Cost Explorer reports, and put them into an S3 bucket for the current day in a
    CSV text format that can be imported into a Jupyter Notebook. The Cost Explorer reports
    are in the NetEng account.

    :param time_index: Not sure this will be useful, since the report is just for that time.
    :return:
    """
    print('do_cost_explorer_reports')
    print('time_index = {}'.format(time_index))

    try:
        print('Start Cost Explorer')

        # Get a cti-poke-like session to NetEng account, but with ce cost-explorer and budget permissions.
        session = awscost_helper_util.create_cost_explorer_session()
        ce_client = aws_util.get_boto3_client_by_name('ce', session, 'us-east-1')

        # NOTE: start and end dates need to be in format:   2017-01-01
        # start_date = '2018-12-29'  # hard coded for testing.
        # end_date = '2019-01-04'  # hard coded for testing.

        # anecdotal evidence is it takes 24 hours before these reports are accurate, so -1 and -8 days
        # for one weeks coverage.
        start_date = awscost_helper_util.get_cost_explorer_format_yyyy_mm_dd(-8)
        end_date = awscost_helper_util.get_cost_explorer_format_yyyy_mm_dd(-1)

        write_reservation_coverage_report(ce_client, 'ec2', start_date, end_date)
        write_reservation_utilization_report(ce_client, 'ec2', start_date, end_date)
        write_reservation_purchase_recommendation_report(ce_client, 'ec2', start_date, end_date)

        write_reservation_coverage_report(ce_client, 'rds', start_date, end_date)
        write_reservation_utilization_report(ce_client, 'rds', start_date, end_date)
        write_reservation_purchase_recommendation_report(ce_client, 'rds', start_date, end_date)

        write_reservation_coverage_report(ce_client, 'elasticache', start_date, end_date)
        write_reservation_utilization_report(ce_client, 'elasticache', start_date, end_date)
        write_reservation_purchase_recommendation_report(ce_client, 'elasticache', start_date, end_date)

        write_reservation_coverage_report(ce_client, 'es', start_date, end_date)
        write_reservation_utilization_report(ce_client, 'es', start_date, end_date)
        write_reservation_purchase_recommendation_report(ce_client, 'es', start_date, end_date)

        write_reservation_coverage_report(ce_client, 'redshift', start_date, end_date)
        write_reservation_utilization_report(ce_client, 'redshift', start_date, end_date)
        write_reservation_purchase_recommendation_report(ce_client, 'redshift', start_date, end_date)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def do_make_excel_file(time_index):
    """
    The Excel file will have the following tabs:
     One tab that summarizes the last 7 days, hourly, and each column is a RI category.
     They types are

     One page that is a summary of all the data. It is just min, max, median and P95 of the
     hourly data.
    :param time_index:
    :return:
    """
    print('do_make_excel_file')
    print('time_index = {}'.format(time_index))

    df_test_page = create_test_page_data_frame()

    # Get each of the excel files here
    df_rds_east_hourly = create_hourly_data_frame('rds', 'us-east-1', time_index)
    df_rds_west_hourly = create_hourly_data_frame('rds', 'us-west-2', time_index)
    df_dynamodb_east_hourly = create_hourly_data_frame('dynamodb', 'us-east-1', time_index)
    df_dynamodb_west_hourly = create_hourly_data_frame('dynamodb', 'us-west-2', time_index)
    df_elasticache_east_hourly = create_hourly_data_frame('elasticache', 'us-east-1', time_index)
    df_elasticache_west_hourly = create_hourly_data_frame('elasticache', 'us-west-2', time_index)
    df_ec2_east_hourly = create_hourly_data_frame('ec2', 'us-east-1', time_index)
    df_ec2_west_hourly = create_hourly_data_frame('ec2', 'us-west-2', time_index)
    df_ec2os_east_hourly = create_hourly_data_frame('ec2os', 'us-east-1', time_index)
    df_ec2os_west_hourly = create_hourly_data_frame('ec2os', 'us-west-2', time_index)
    df_ri_ec2_east_hourly = create_hourly_data_frame('ri-ec2', 'us-east-1', time_index) #create_daily
    df_ri_ec2_west_hourly = create_hourly_data_frame('ri-ec2', 'us-west-2', time_index) #create_daily
    df_ri_rds_east_hourly = create_hourly_data_frame('ri-rds', 'us-east-1', time_index) #create_daily
    df_ri_rds_west_hourly = create_hourly_data_frame('ri-rds', 'us-west-2', time_index) #create_daily
    # es_daily_data_frame = create_daily_data_frame('es')
    # redshift_daily_data_frame = create_daily_data_frame('redshift')
    # summary_data_frame

    # Test creating the Excel file.
    # date_str = datetime.datetime.today().strftime('%m-%d')
    date_str = awscost_helper_util.get_awscost_daily_time_format()

    path = '/tmp/AwsCostRIReport.xlsx'
    excel_file = open(path, "w+")
    excel_file.close()

    writer = pd.ExcelWriter(path, engine='openpyxl')

    try:
        df_test_page.to_excel(writer, 'TestPage')
        df_dynamodb_east_hourly.to_excel(writer, 'dynamo-us-east-1')
        df_dynamodb_west_hourly.to_excel(writer, 'dynamo-us-west-2')
        df_rds_east_hourly.to_excel(writer, 'rds-us-east-1')
        df_rds_west_hourly.to_excel(writer, 'rds-us-west-2')
        df_elasticache_east_hourly.to_excel(writer, 'elasticache-us-east-1')
        df_elasticache_west_hourly.to_excel(writer, 'elasticache-us-west-2')
        df_ec2_east_hourly.to_excel(writer, 'ec2-us-east-1')
        df_ec2_west_hourly.to_excel(writer, 'ec2-us-west-2')
        df_ec2os_east_hourly.to_excel(writer, 'ec2os-us-east-1')
        df_ec2os_west_hourly.to_excel(writer, 'ec2os-us-west-2')
        df_ri_ec2_east_hourly.to_excel(writer, 'ri-ec2-us-east-1')
        df_ri_ec2_west_hourly.to_excel(writer, 'ri-ec2-us-west-2')
        df_ri_rds_east_hourly.to_excel(writer, 'ri-rds-us-east-1')
        df_ri_rds_west_hourly.to_excel(writer, 'ri-rds-us-west-2')
    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        print('Continue making excel file')
        # don't return just continue

    try:
        create_stats_from_data_frame(df_dynamodb_east_hourly, writer, 'P95 Dynamo East')
        create_stats_from_data_frame(df_dynamodb_west_hourly, writer, 'P95 Dynamo West')
        create_stats_from_data_frame(df_rds_east_hourly, writer, 'P95 RDS East')
        create_stats_from_data_frame(df_rds_west_hourly, writer, 'P95 RDS West')
        create_stats_from_data_frame(df_elasticache_east_hourly, writer, 'P95 Elasticach East')
        create_stats_from_data_frame(df_elasticache_west_hourly, writer, 'P95 Elasticach West')
        create_stats_from_data_frame(df_ec2_east_hourly, writer, 'P95 EC2 East')
        create_stats_from_data_frame(df_ec2_west_hourly, writer, 'P95 EC2 West')
        create_stats_from_data_frame(df_ec2os_east_hourly, writer, 'P95 EC2OS East')
        create_stats_from_data_frame(df_ec2os_west_hourly, writer, 'P95 EC2OS West')
        create_stats_from_data_frame(df_ri_ec2_east_hourly, writer, 'P95 RI-EC2 East')
        create_stats_from_data_frame(df_ri_rds_east_hourly, writer, 'P95 RI-RDS East')
        create_stats_from_data_frame(df_ri_rds_west_hourly, writer, 'P95 RI-RDS West')
        create_stats_from_data_frame(df_ri_ec2_west_hourly, writer, 'P95 RI-EC2 West')
    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        print('Continue making excel file')
        # don't return just continue.

    writer.save()

    #  S3 copy this file into a bucket, or attach it to an e-mail.
    bucket_name = 'awscost-data'
    folder_name = awscost_helper_util.get_awscost_daily_time_format()
    file_name = '{}-AwsRIUsageReport.xlsx'.format(date_str)

    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(
        path, bucket_name,
        '{}/{}'.format(folder_name, file_name),
    )


def do_daily_scan(time_index):
    """
    Do AWS resources that only need to be scanned once per day.
    :param time_index:
    :return: None
    """
    print('do_daily_scan')
    print('time = {}'.format(time_index))

    active_regions = ['us-east-1', 'us-west-2']
    aws_account = awscost_helper_util.AWS_ACCOUNTS
    for name, account_num in aws_account.iteritems():
        for region in active_regions:
            check_red_shift_node_types(name, account_num, region, time_index)
            check_elastic_search_service(name, account_num, region, time_index)


def do_ec2_scan(time_index):
    """
    EC2 scan, might be more API calls that other types, so run it alone.
    :param time_index:
    :return: None
    """
    print('do_ec2_scan')
    print('time = {}'.format(time_index))

    active_regions = ['us-east-1', 'us-west-2']
    aws_account = awscost_helper_util.AWS_ACCOUNTS
    for name, account_num in aws_account.iteritems():
        for region in active_regions:
            check_ec2_usage(name, account_num, region, time_index)


def do_hourly_scan(time_index):
    """
    Do non-EC2 resources that need to be scanned once per hour.
    :param time_index:
    :return: None
    """
    print('do_hourly_scan')
    print('time = {}'.format(time_index))

    active_regions = ['us-east-1', 'us-west-2']
    aws_account = awscost_helper_util.AWS_ACCOUNTS
    for name, account_num in aws_account.iteritems():
        for region in active_regions:
            check_dynamo_usage(name, account_num, region, time_index)
            check_rds_usage(name, account_num, region, time_index)
            check_elasticache_usage(name, account_num, region, time_index)


def do_summary(time_index):
    """
    Create the Roku-wide summary, of hourly or daily data.
    :param time_index:
    :return: None
    """
    print('do_summary')
    print('time_index = {}'.format(time_index))

    # We summarizing results. Event specifies the time-stamp.
    print('Summarizing data.')
    print('Summarizing result for time = {}'.format(time_index))
    summarize_results('rds', time_index)
    summarize_results('dynamodb', time_index)
    summarize_results('ec2', time_index)
    summarize_results('ec2os', time_index)
    summarize_results('elasticache', time_index)

    if time_index.endswith('-01'):
        # summarize daily_results at end of day time_index = *-01
        summarize_results('redshift', time_index)
        summarize_results('es', time_index)

    # print("Time remaining: {} ms".format(context.get_remaining_time_in_millis()))
    print('Finished summarizing results for time = {}'.format(time_index))


def do_gather_ri_stats(time_index):
    """
    Gather and summarize the status of Reserved Instances, to compare
    against the capacity used so we can make adjustments.

    NOTE: We don't know yet if this modification happen hourly, or
    if this can be monitored daily.

    NOTE: We don't yet know if other accounts MIGHT have RIs and therefore need
    to be monitored, or if other accounts don't need to be monitored.

    :param time_index:
    :return:
    """
    print('do_gather_ri_stats')
    print('curr_time = {}'.format(time_index))

    # for calculating expire time.
    now = datetime.datetime.utcnow().replace(tzinfo=tzutc())

    active_regions = ['us-east-1', 'us-west-2']
    for region in active_regions:
        check_ec2_reserved_instances_in_all_accounts(region, time_index)
        check_rds_reserved_instances_in_all_accounts(region, time_index)
        check_elasticache_reserved_instances_in_all_accounts(region, time_index)
        check_dynamo_reserved_capacity_in_all_accounts(region, time_index)
        # check_es_reserved_capacity_in_all_accounts(region, time_index)
        check_redshift_reserved_capacity_in_all_accounts(region, time_index)

    print('Done RI testing')


# Helper methods below #############################

def write_reservation_coverage_report(ce_client, service_key, start_date, end_date):
    """
    Call AWS Cost Explorer reservation_coverage report
    :param ce_client:
    :param service_key: valid values: ec2 | rds | redshift | elasticache | es
    :param start_date:
    :param end_date:
    :return: None
    """
    try:
        print('write_reservation_coverage_report')
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))

        service_name = awscost_helper_util.get_verbose_cost_explorer_service_names_from_key(service_key)

        # Note boto3 document say only daily Granularity covered, test if hourly is possible.
        response = ce_client.get_reservation_coverage(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service_name]
                }
            }
        )

        date_for_s3_dir = awscost_helper_util.get_awscost_daily_time_format()

        # Get details here.
        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_reservation_coverage
        if response:
            file_name = '{}_{}_reservation_coverage.json'.format(date_for_s3_dir, service_key)
            awscost_helper_util.upload_json_to_awscost_data_s3_bucket(
                date_for_s3_dir, file_name, response)

            # ToDo: Convert JSON into CSV formation and save to S3, and the put into dynamo for trend plots.
            # convert_keys = awscost_helper_util.get_conversion_for_report(
            # coverage_report_panda = awscost_helper_util.json_to_panda(convert_keys, response)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))
        awscost_helper_util.log_traceback_exception(ex)


def write_reservation_utilization_report(ce_client, service_key, start_date, end_date):
    """
    Call AWS Cost Explorer reservation_utilization report
    :param ce_client:
    :param service_key: valid values: ec2 | rds | redshift | elasticache | es
    :param start_date:
    :param end_date:
    :return: None
    """
    try:
        print('write_reservation_utilization_report')
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))

        # Note boto3 document say only daily Granularity covered, test if hourly is possible.
        service_name = awscost_helper_util.get_verbose_cost_explorer_service_names_from_key(service_key)

        response = ce_client.get_reservation_utilization(
            TimePeriod={
                'Start': start_date,
                'End': end_date
            },
            Granularity='DAILY',
            Filter={
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': [service_name]
                }
            }
        )

        date_for_s3_dir = awscost_helper_util.get_awscost_daily_time_format()

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_reservation_coverage
        if response:
            file_name = '{}_{}_utilization_report.json'.format(date_for_s3_dir, service_key)
            awscost_helper_util.upload_json_to_awscost_data_s3_bucket(
                date_for_s3_dir, file_name, response)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))
        awscost_helper_util.log_traceback_exception(ex)


def write_reservation_purchase_recommendation_report(ce_client, service_key, start_date, end_date):
    """
    Call AWS Cost Explorer reservation_purchase_recommendation report
    :param ce_client:
    :param service_key: valid values: ec2 | rds | redshift | elasticache | es
    :param start_date:
    :param end_date:
    :return: None
    """
    try:
        print('write_reservation_purchase_recommendation_report')
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))

        # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ce.html#CostExplorer.Client.get_reservation_coverage
        service_name = awscost_helper_util.get_verbose_cost_explorer_service_names_from_key(service_key)

        if service_key == 'ec2':
            response = ce_client.get_reservation_purchase_recommendation(
                Service=service_name,
                AccountScope='PAYER',
                LookbackPeriodInDays='SEVEN_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='ALL_UPFRONT',
                ServiceSpecification={
                    'EC2Specification': {
                        'OfferingClass': 'CONVERTIBLE'
                    }
                }
            )
        elif service_key == 'elasticache':
            response = ce_client.get_reservation_purchase_recommendation(
                Service=service_name,
                AccountScope='PAYER',
                LookbackPeriodInDays='SEVEN_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='HEAVY_UTILIZATION'
            )
        else:
            response = ce_client.get_reservation_purchase_recommendation(
                Service=service_name,
                AccountScope='PAYER',
                LookbackPeriodInDays='SEVEN_DAYS',
                TermInYears='ONE_YEAR',
                PaymentOption='ALL_UPFRONT'
            )

        date_for_s3_dir = awscost_helper_util.get_awscost_daily_time_format()

        if response:
            file_name = '{}_{}_recommendations.json'.format(date_for_s3_dir, service_key)
            awscost_helper_util.upload_json_to_awscost_data_s3_bucket(
                date_for_s3_dir, file_name, response)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        print('service: {}, start: {}, end: {}'.format(service_key, start_date, end_date))
        awscost_helper_util.log_traceback_exception(ex)


def normalize_rds_families(node_types):
    """
    Take node_type which is dict with key and number.
    For each family/db engine pair determine the
    family and apply the following factor to it.

    4xlarge = 8
    2xlarge = 4
    xlarge = 2
    large = 1
    medium = 0.5
    small = 0.25
    micro = 0.125
    nano = 0.0625

    :param node_types: python dict with key is node type value is number.
    :return: python dict with families all normalized to large.
    """
    ret_val = {}
    # iterate through all the keys
    for key, value in node_types.items():
        key_family = get_family_from_key(key)
        key_size = normalize_key_size(key)
        key_db_engine = get_rds_db_engine_from_key(key)

        # Print out family and key size to verify
        print('{}-{}: {}  - {}'.format(key_family, key_db_engine, key_size, key))

        normalized_key = '{}-{}'.format(key_family, key_db_engine)

        # Is this key in ret_val:
        if normalized_key in ret_val:
            curr_size = ret_val[normalized_key]
            ret_val[normalized_key] = curr_size + key_size
        else:
            ret_val[normalized_key] = key_size

    return ret_val


def normalize_key_size(key):
    """
    Get the size factor base on key.
    :param key: rds key
    :return: float value 0.0625 to 12.00
    """
    is_multi_az = False
    if key.startswith('multi_az'):
        is_multi_az = True
    factor = 0.0
    if 'nano' in key:
        factor = 0.0625
    elif 'micro' in key:
        factor = 0.125
    elif 'small' in key:
        factor = 0.25
    elif 'medium' in key:
        factor = 0.50
    elif '2x' in key:
        factor = 4.0
    elif '4x' in key:
        factor = 8.0
    elif '8x' in key:
        factor = 16.0
    elif '16x' in key:
        factor = 32.0
    elif '32x' in key:
        factor = 64.0
    elif 'xlarge' in key:
        factor = 2.0
    elif 'large' in key:
        factor = 1.0

    if is_multi_az:
        factor = factor * 2.0

    if factor == 0.0:
        # if we get here we don't know type
        err_msg = 'Unknown Key: {}'.format(key)
        raise ValueError(err_msg)

    return factor


def get_family_from_key(key):
    """
    For EC2, RDS, Elasticache, or ES get the node_family.
    :param key: example db.r4.xlarge:aurora
    :return: r4
    """
    try:
        return key.split('.')[1]
    except Exception as ex:
        print("Failed for find family for key: {}".format(key))
        return '?'


def get_rds_db_engine_from_key(key):
    """
    Get the database engine from an rds key. This is
    typical key:
       db.t2.small:aurora-mysql
    :param key: example db.t2.small:aurora-mysql
    :return: r4
    """
    try:
        return key.split(':')[1]
    except Exception as ex:
        print("Failed for find DB engine for key: {}".format(key))
        return '?'


def create_stats_from_data_frame(data_frame, excel_writer, tab_name):
    """
    Try to create stats from a data from, but if frame is empty catch the
    exception record all relevant info and then create a placeholder page.
    :param data_frame: panda DataFrame data structure
    :param excel_writer: panda writer to Excel file
    :param tab_name: name of tab in Excel file
    :return: None
    """
    try:
        if not data_frame.empty:
            print('Creating stats page: {}'.format(tab_name))
            stats_df = data_frame.quantile([0.0, 0.05, 0.5, 0.95, 1.0])
            stats_df.to_excel(excel_writer, tab_name)
        else:
            print('No data to create stats page: {}'.format(tab_name))

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def convert_ec2_prod_desc_to_ri_type(prod_desc):
    """
    Calling boto3 gives verbose "product descriptions" which need to be converted into a simpler type.

    NOTE: AWS makes a distinction between SQL Standard, SQL Web and SQL Enterprise.
    Only see SQL Standard in account, and expect this destintion to go away.

    :param prod_desc:
    :return: string type. limited to the following. < linux | rhel | windows | windows.sql | ... >
    """
    if prod_desc.startswith('Linux/UNIX'):
        if prod_desc.find('SQL') > -1:
            return 'linux.sql'
        else:
            return 'linux'
    if prod_desc.startswith('Windows'):
        if prod_desc.find('SQL') > -1:
            return 'windows.sql'
        else:
            return 'windows'
    if prod_desc.startswith('Red Hat'):
        if prod_desc.find('SQL') > -1:
            return 'rhel.sql'
        else:
            return 'rhel'
    if prod_desc.startswith('SUSE'):
        if prod_desc.find('SQL') > -1:
            return 'suse.sql'
        else:
            return 'suse'


def check_ec2_reserved_instances_in_all_accounts(region, time_index, is_test=False):
    """
    Iterate through all of the AWS accounts in a region. Get the RIs used.
    NOTE: we don't see to specify the AZ so just record the type and amount.
    Put this into the AWS Cost table once per day with the key prefix.

    "ri-ec2:<account>:<region>

    {
      <type>: <count>,
      :
    }

    Type will just be simple. <os_type>-m3.large without an AZ associated with it.
    Examples include:
        windows.sql-m3.large
        linux-t2.medium
        rhel-t2.small

    :param name:
    :param account_num:
    :param region:
    :param time_index:
    :param is_test: setting this to True doesn't write to database, instead it prints to log.
    :return: None. Output goes to logs and database.
    """
    try:
        ec2_ri_node_type_counter = {}
        aws_account = awscost_helper_util.AWS_ACCOUNTS
        for name, account_num in aws_account.iteritems():

            session = awscost_helper_util.create_cti_poke_session(name)
            ec2_read_only_client = aws_util.get_boto3_client_by_name('ec2', session, region)

            ri_response = ec2_read_only_client.describe_reserved_instances()
            ri_list = ri_response.get('ReservedInstances')
            if ri_list:
                for curr_ri in ri_list:
                    curr_ri_state = curr_ri.get('State')
                    curr_ri_prod_desc = curr_ri.get('ProductDescription')
                    curr_ri_type = curr_ri.get('InstanceType')
                    curr_ri_az = curr_ri.get('AvailabilityZone')
                    curr_ri_count = curr_ri.get('InstanceCount')

                    # Calculate the expire time.
                    curr_ri_start = curr_ri.get('Start')
                    curr_ri_duration = curr_ri.get('Duration')

                    curr_ri_expire_time = curr_ri_start + datetime.timedelta(seconds=curr_ri_duration)

                    # Print something about this RI, so we can decide how to reconcile it.
                    if curr_ri_state == 'active':
                        print('RI {}-{}: state=_{}_, prod desc=_{}_, type=_{}_, az=_{}_, count={}, expire={}'
                              .format(name, region, curr_ri_state, curr_ri_prod_desc,
                                      curr_ri_type, curr_ri_az, curr_ri_count, curr_ri_expire_time))

                        ec2_ri_type = '{}-{}'.format(convert_ec2_prod_desc_to_ri_type(curr_ri_prod_desc),curr_ri_type)
                        increment_count_in_dictionary(ec2_ri_node_type_counter, ec2_ri_type, inc_by=curr_ri_count)

                        # ToDo: Check for expiration in next month and turn them into "Notifications".
                        # if will_expire_soon(curr_ri_expire_time):
                        #   notify_for_expiring_reserved_instances(name, region, curr_ri_state,
                        #       curr_ri_prod_desc, curr_ri_type, curr_ri_az, curr_ri_count, curr_ri_expire_time)
                    else:
                        # Just log a non-active RI.
                        print("Expired RI: {}-{}, {}, {}, {}".format(name, region, curr_ri_type, curr_ri_count, curr_ri_expire_time))

        # RI net-eng-us-east-1: state=_active_, prod desc=_Linux/UNIX (Amazon VPC)_, type=_t2.xlarge_, az=_None_, count=3, expire=2021-02-01 00:00:00+00:00
        # RI net-eng-us-east-1: state=_active_, prod desc=_Windows (Amazon VPC)_, type=_m4.large_, az=_None_, count=3, expire=2021-04-12 18:00:00+00:00
        # RI net-eng-us-east-1: state=_active_, prod desc=_Windows with SQL Server Enterprise (Amazon VPC)_, type=_i3.8xlarge_, az=_None_, count=3, expire=2019-10-03 16:12:00.737000+00:00
        # RI net-eng-us-east-1: state=_active_, prod desc=_Windows with SQL Server Enterprise (Amazon VPC)_, type=_i3.16xlarge_, az=_None_, count=1, expire=2019-10-03 16:12:00.526000+00:00

        # Write Roku-wide summary.
        aws_resource_key = 'ri-ec2:roku:{}'.format(region)

        store_map_to_aws_cost_table(aws_resource_key, time_index, ec2_ri_node_type_counter)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def check_rds_reserved_instances_in_all_accounts(region, time_index, is_test=False):
    """
    Get the current Elasticache Reserved Node data. 
    :param region:
    :param time_index:
    :param is_test: setting this to True doesn't write to database, instead it prints to log.
    :return: None. Output goes to logs and database.
    """
    try:
        rds_ri_type_counter = {}
        aws_account = awscost_helper_util.AWS_ACCOUNTS
        for name, account_num in aws_account.iteritems():

            session = awscost_helper_util.create_cti_poke_session(name)
            rds_read_only_client = aws_util.get_boto3_client_by_name('rds', session, region)

            # use describe_reserved_cache_nodes
            paginator = rds_read_only_client.get_paginator('describe_reserved_db_instances')

            pages = paginator.paginate()
            for page in pages:
                ri_list = page.get('ReservedDBInstances')
                if ri_list:
                    for curr_ri in ri_list:
                        db_instance_class = curr_ri.get('DBInstanceClass')
                        start_time = curr_ri.get('StartTime')
                        duration = curr_ri.get('Duration')
                        fixed_price = curr_ri.get('FixedPrice')
                        useage_price = curr_ri.get('UsagePrice')
                        state = curr_ri.get('State')
                        db_instance_count = curr_ri.get('DBInstanceCount')
                        multi_az = curr_ri.get('MultiAZ')
                        prod_desc = curr_ri.get('ProductDescription')
                        offering_type = curr_ri.get('OfferingType')

                        # Print out to figure out key schema.
                        print('RI {}-{}: state={}, db_type={}, mulit_az={}, duration={}, offer_type={}, description={}'
                              .format(name, region, state, db_instance_class, multi_az, duration, offering_type, prod_desc))

                        if state == 'active':
                            rds_ri_type = '{}-{}'.format(prod_desc, db_instance_class)
                            if multi_az:
                                rds_ri_type += '-multi_az'

                            increment_count_in_dictionary(rds_ri_type_counter, rds_ri_type, inc_by=db_instance_count)
                else:
                    print('No Reserved_DB_Instances in {}-{}'.format(name, region))

        # Write Roku-wide summary.
        aws_resource_key = 'ri-rds:roku:{}'.format(region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, rds_ri_type_counter)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def check_elasticache_reserved_instances_in_all_accounts(region, time_index, is_test=False):
    """
    Get the current Elasticache Reserved Node data. 
    :param region:
    :param time_index:
    :param is_test: setting this to True doesn't write to database, instead it prints to log.
    :return: None. Output goes to logs and database.
    """
    try:
        elasticache_ri_node_type_counter = {}
        aws_account = awscost_helper_util.AWS_ACCOUNTS
        for name, account_num in aws_account.iteritems():

            session = awscost_helper_util.create_cti_poke_session(name)
            elasticache_read_only_client = aws_util.get_boto3_client_by_name('elasticache', session, region)

            # use describe_reserved_cache_nodes
            paginator = elasticache_read_only_client.get_paginator('describe_reserved_cache_nodes')
            pages = paginator.paginate()
            for page in pages:
                ri_list = page.get('ReservedCacheNodes')
                if ri_list:
                    for curr_ri in ri_list:
                        cache_node_type = curr_ri.get('CacheNodeType')
                        start_time = curr_ri.get('StartTime')
                        duration = curr_ri.get('Duration')
                        fixed_price = curr_ri.get('FixedPrice')
                        useage_price = curr_ri.get('UsagePrice')
                        state = curr_ri.get('State')
                        cache_node_count = curr_ri.get('CacheNodeCount')
                        prod_desc = curr_ri.get('ProductDescription')
                        offering_type = curr_ri.get('OfferingType')

                        # Print out to figure out key schema.
                        print('RI {}-{}: state={}, node_type={}, duration={}, offer_type={}, description={}'
                              .format(name, region, state, cache_node_type, duration, offering_type, prod_desc))

                        if state == 'active':
                            elasticache_ri_type = '{}'.format(cache_node_type)
                            increment_count_in_dictionary(elasticache_ri_node_type_counter, elasticache_ri_type, inc_by=cache_node_count)

                else:
                    print('No Reserved_Cache_Nodes in {}-{}'.format(name, region))

        # Write Roku-wide summary.
        aws_resource_key = 'ri-elasticache:roku:{}'.format(region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, elasticache_ri_node_type_counter)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def check_dynamo_reserved_capacity_in_all_accounts(region, time_index, is_test=False):
    try:
        # No 'dynamodb' boto3 API, but might look into Cost Explorer `ce` boto3 APIs
        # Could be indirect way to get amount.
        return None
    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)


def check_redshift_reserved_capacity_in_all_accounts(region, time_index, is_test=False):
    try:
        redshift_ri_node_type_counter = {}
        aws_account = awscost_helper_util.AWS_ACCOUNTS
        for name, account_num in aws_account.iteritems():

            session = awscost_helper_util.create_cti_poke_session(name)
            redshift_read_only_client = aws_util.get_boto3_client_by_name('redshift', session, region)

            # use describe_reserved_cache_nodes
            paginator = redshift_read_only_client.get_paginator('describe_reserved_nodes')
            pages = paginator.paginate()
            for page in pages:
                ri_list = page.get('ReservedNodes')
                if ri_list:
                    for curr_ri in ri_list:
                        node_type = curr_ri.get('NodeType')
                        node_count = curr_ri.get('NodeCount')
                        state = curr_ri.get('State')
                        duration = curr_ri.get('Duration')
                        start_time = curr_ri.get('StartTime')
                        offering_type = curr_ri.get('OfferingType')
                        reserved_node_offering_type = curr_ri.get('ReservedNodeOfferingType')

                        # Print out to figure out key schema.
                        print('RI {}-{}: state={}, node_type={}, duration={}, offer_type={}, ReservedNodeOfferingType={}'
                              .format(name, region, state, node_type, duration, offering_type, reserved_node_offering_type))

                        if state == 'active':
                            redshift_ri_type = '{}'.format(node_type)
                            increment_count_in_dictionary(redshift_ri_node_type_counter, redshift_ri_type, inc_by=node_count)

                else:
                    print('No Reserved_Nodes in {}-{}'.format(name, region))

        # Write Roku-wide summary.
        aws_resource_key = 'ri-redshift:roku:{}'.format(region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, redshift_ri_node_type_counter)

    except Exception as ex:
        print('Failed: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return 'Failed: {}'.format(ex.message)

# Below here methods look for actual usage.


def check_elasticache_usage(name, account_num, region, time_index):
    """
    Elasticache Reserved Instances are by node-type.
    :param name:
    :param account_num:
    :param region:
    :param time_index:
    :return:
    """
    try:
        print('Check Elasticach Usage starting: {} in {}'.format(name, region))
        session = awscost_helper_util.create_cti_poke_session(name)
        elasticache_read_only_client = aws_util.get_boto3_client_by_name('elasticache', session, region)

        elasticache_node_type_counter = {}

        paginator = elasticache_read_only_client.get_paginator('describe_replication_groups')
        pages = paginator.paginate()
        for page in pages:
            for curr_ec_node in page['ReplicationGroups']:
                ec_node_type = curr_ec_node.get('CacheNodeType')
                increment_count_in_dictionary(elasticache_node_type_counter, ec_node_type)

        aws_resource_key = 'elasticache:{}:{}'.format(account_num, region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, elasticache_node_type_counter)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def check_dynamo_usage(name, account_num, region, time_index):
    """
    Store current read / write capacity for this account in table.
    :param name: string - short account name
    :param account_num: string - aws account number
    :param region: string - aws region. like: 'us-east-1'
    :param time_index: string - time down to hour like: '20181113-14'
    :return: None
    """
    try:
        print('Check Dynamo Usage starting: {} in {}'.format(name, region))
        session = awscost_helper_util.create_cti_poke_session(name)
        dynamodb_read_only_client = aws_util.get_boto3_client_by_name('dynamodb', session, region)

        table_names = []
        table_count = 0
        total_read_capacity = 0
        total_write_capacity = 0

        # Get list of tables in region with pagination in regions with more than 100.
        paginator = dynamodb_read_only_client.get_paginator('list_tables')
        pages = paginator.paginate()
        for page in pages:
            for curr_table_name in page['TableNames']:
                dt_response = dynamodb_read_only_client.describe_table(
                    TableName=curr_table_name
                )
                table_details = dt_response.get('Table')
                if table_details:
                    table_count += 1
                    table_names.append(table_details.get('TableName'))
                    pt = table_details.get('ProvisionedThroughput')
                    if pt:
                        total_read_capacity += pt.get('ReadCapacityUnits')
                        total_write_capacity += pt.get('WriteCapacityUnits')
                    else:
                        print('WARN: No provisioned capacity for table: {}'.format(curr_table_name))
                else:
                    print('WARN: No details for table: {}'.format(curr_table_name))

        # write results
        aws_resource_key = 'dynamodb:{}:{}'.format(account_num,region)
        print('Result {}: key={}, tables={}, read={}, write={}'.format(
            name, aws_resource_key, table_count, total_read_capacity, total_write_capacity))

        dynamodb_stats_map = {
            'table_count': table_count,
            'read_capacity': total_read_capacity,
            'write_capacity': total_write_capacity
        }

        # Local dynamodb client for writing.
        AWS_COST_TABLE.put_item(
            Item={
                'awsResource': aws_resource_key,
                'time': time_index,
                'node_types': dynamodb_stats_map
            }
        )

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def check_red_shift_node_types(name, account_num, region, time_index):
    """
    Read all the RedShift clusters in a region and write out the number of
    each node type.
    :param name: string - short account name
    :param account_num: string - aws account number
    :param region: string - aws region. like: 'us-east-1'
    :param time_index: string - time down to hour like: '20181113-14'
    :return: None
    """
    try:
        print('Check RedShift Usage starting: {} in {}'.format(name, region))
        session = awscost_helper_util.create_cti_poke_session(name)
        redshift_read_only_client = aws_util.get_boto3_client_by_name('redshift', session, region)

        redshift_node_type_counter = {}

        # Get list of tables in region with pagination in regions with more than 100.
        paginator = redshift_read_only_client.get_paginator('describe_clusters')
        pages = paginator.paginate()
        for page in pages:
            for curr_cluster in page['Clusters']:
                node_type = curr_cluster.get('NodeType')
                cluster_id = curr_cluster.get('ClusterIdentifier')
                print('Redshift Cluster: {}  type: {}'.format(cluster_id, node_type))
                increment_count_in_dictionary(redshift_node_type_counter, node_type)

        # Local dynamodb client for writing.
        aws_resource_key = 'redshift:{}:{}'.format(account_num, region)

        store_map_to_aws_cost_table(aws_resource_key, time_index, redshift_node_type_counter)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def check_rds_usage(name, account_num, region, time_index):
    """
    Check the usage of RDS instance record the engine and family type pre account and region.
    :param name: string - short account name
    :param account_num: string - aws account number
    :param region: string - aws region. like: 'us-east-1'
    :param time_index: string - time down to hour like: '20181113-14'
    :return: None 
    """
    try:
        print('Check RDS Usage starting: {} in {}'.format(name, region))
        session = awscost_helper_util.create_cti_poke_session(name)
        rds_read_only_client = aws_util.get_boto3_client_by_name('rds', session, region)

        rds_type_counter = {}

        # Get list of tables in region with pagination in regions with more than 100.
        paginator = rds_read_only_client.get_paginator('describe_db_instances')
        pages = paginator.paginate()
        for page in pages:
            for curr_db_instance in page['DBInstances']:
                instance_class = curr_db_instance.get('DBInstanceClass')
                db_engine = curr_db_instance.get('Engine')
                db_instance_id = curr_db_instance.get('DBInstanceIdentifier')
                multi_az = curr_db_instance.get('MultiAZ')
                rds_type = '{}:{}'.format(instance_class, db_engine)
                print('RDS Instance: {}  type: {}'.format(db_instance_id, rds_type))
                if multi_az:
                    rds_type = 'multi_az-'+rds_type
                increment_count_in_dictionary(rds_type_counter, rds_type)

        aws_resource_key = 'rds:{}:{}'.format(account_num, region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, rds_type_counter)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def check_elastic_search_service(name, account_num, region, time_index):
    """
    Check for useage of Elastic Search Service. Record information about the cluster.
    :param name: string - short account name
    :param account_num: string - aws account number
    :param region: string - aws region. like: 'us-east-1'
    :param time_index: string - time down to hour like: '20181113-14'
    :return: None
    """
    try:
        print('Check ES Usage starting: {} in {}'.format(name, region))
        session = awscost_helper_util.create_cti_poke_session(name)
        es_read_only_client = aws_util.get_boto3_client_by_name('es', session, region)

        es_type_counter = {}

        response = es_read_only_client.list_domain_names()
        domain_names = response.get('DomainNames')
        domain_name_list = []
        for curr_name in domain_names:
            domain_name_list.append(curr_name.get('DomainName'))

        print('DomainNames= {}'.format(domain_name_list))
        response = es_read_only_client.describe_elasticsearch_domains(
            DomainNames=domain_name_list
        )
        if response.get('DomainStatusList'):
            domain_status_list = response.get('DomainStatusList')
            es_version = response.get('ElasticsearchVersion')
            for curr_domain_status in domain_status_list:
                cluster_config = curr_domain_status.get('ElasticsearchClusterConfig')
                es_instance_type = cluster_config.get('InstanceType')
                es_count = cluster_config.get('InstanceCount')
                key = '{}'.format(es_instance_type)
                increment_count_in_dictionary(es_type_counter, key, es_count)
                has_dedicated_master = cluster_config.get('DedicatedMasterEnabled')
                if has_dedicated_master:
                    dm_instance_type = cluster_config.get('DedicatedMasterType')
                    key = '{}'.format(dm_instance_type)
                    dm_count = cluster_config.get('DedicatedMasterCount')
                    increment_count_in_dictionary(es_type_counter, key, dm_count)

        aws_resource_key = 'es:{}:{}'.format(account_num, region)
        store_map_to_aws_cost_table(aws_resource_key, time_index, es_type_counter)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def check_ec2_usage(aws_account_name, account_num, region, time_index):
    """
    Summarize all of the running EC2 Instances.

    :param aws_account_name: string - short account name
    :param account_num: string - aws account number
    :param region: string - aws region. like: 'us-east-1'
    :param time_index: string - time down to hour like: '20181113-14'
    :return: None
    """
    try:
        print('Check EC2 Instance Usage starting: {} in {}'.format(aws_account_name, region))
        session = awscost_helper_util.create_cti_poke_session(aws_account_name)

        ec2_resource = aws_util.get_ec2_resource(session, region)

        # ec2 has AZ, but not OS-type.
        ec2_az_type_counter = {}
        # ec2v2 has OS-type which is estimated based on AMI-ids, but no AZ info.
        ec2_os_type_counter = {}

        filters = [{'Name': 'instance-state-name', 'Values': ['running','terminated']}]

        instances = ec2_resource.instances.filter(Filters=filters)
        if not instances:
            raise ValueError("No EC2 Instances for: {}:{}".format(aws_account_name, region))

        ec2_instance_counter = 0
        unknown_os_type_counter = 0  # likely most will be linux, but keep tabs.

        image_id_to_os_map = {}
        uncategorized_image_descriptions = {}
        for instance in instances:
            try:
                ec2_type = instance.instance_type
                ec2_placement_map = instance.placement
                
                # determine if spot instance.
                is_spot_instance = False
                if instance.spot_instance_request_id:
                    is_spot_instance = True
                    print('Spot instance: {}-{} id={}'.format(
                        aws_account_name, region, instance.spot_instance_request_id))
                
                ec2_az = ec2_placement_map.get('AvailabilityZone')

                key_ec2_az = '{}:{}'.format(ec2_type, ec2_az)
                if is_spot_instance:
                    key_ec2_az = 'spot-'+key_ec2_az
                increment_count_in_dictionary(ec2_az_type_counter, key_ec2_az)
                ec2_instance_counter += 1

                # Get OS type for ec2v2. count
                os_type = convert_ec2_image_id_to_os_type(session, region, instance,
                                                          image_id_to_os_map,
                                                          uncategorized_image_descriptions,
                                                          unknown_os_type_counter)

                # add to ec2_os map here.
                key_ec2_os = '{}-{}'.format(os_type, ec2_type)
                if is_spot_instance:
                    key_ec2_os = 'spot-'+key_ec2_os
                
                increment_count_in_dictionary(ec2_os_type_counter, key_ec2_os)

            except Exception as ex:
                # log error.
                print('Exception: {}'.format(ex.message))
                awscost_helper_util.log_traceback_exception(ex)

        print('Debug: {}:{} Found total EC2 Instances: {}'.format(aws_account_name, region, ec2_instance_counter))
        print('Debug: {}:{} Number EC2 Instances with unverified os_type: {}'.format(aws_account_name, region, unknown_os_type_counter))
        print('WARN: Some images not categorized (linux|rhel|sles): {}'.format(uncategorized_image_descriptions))

        aws_resource_key_ec2_az = 'ec2:{}:{}'.format(account_num, region)
        store_map_to_aws_cost_table(aws_resource_key_ec2_az, time_index, ec2_az_type_counter)

        # Store data in version 2 format.
        aws_resource_key_ec2_os = 'ec2os:{}:{}'.format(account_num, region)
        store_map_to_aws_cost_table(aws_resource_key_ec2_os, time_index, ec2_os_type_counter)

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def store_map_to_aws_cost_table(aws_resource_key, time_index, type_counter):
    """
    Store map into AWSCost DynamoDB table in the standard format with
        awsResource -- key
        time -- range key
        node_types -- map of type to count.
    :param aws_resource_key:
    :param time_index:
    :param type_counter:
    :return: None
    """
    type_map = {}
    for x in type_counter:
        this_item = {
            x: {'N': str(type_counter.get(x))}
        }
        type_map.update(this_item)

    dynamodb_write_client = boto3.client('dynamodb')
    dynamodb_write_client.put_item(
        TableName='AWSCost',
        Item={
            'awsResource': {'S': aws_resource_key},
            'time': {'S': time_index},
            'node_types': {'M': type_map}
        }
    )


def convert_ec2_image_id_to_os_type(session, region, instance,
                                    image_id_to_os_map,
                                    uncategorized_image_descriptions,
                                    unknown_os_type_counter):
    """
    AMI ids are used to estimate the os_type of an ec2_instance for reserved instance reports.
    :param session:
    :param region:
    :param instance:
    :param image_id_to_os_map:
    :param uncategorized_image_descriptions:
    :param unknown_os_type_counter:
    :return: OS-type as string like: linux | rhel | windows | windows
    """
    # OS-type is a combination of "platform" Windows and image_id (ami-...) info.
    try:
        os_type = instance.platform
        # print('platform = {}'.format(instance.platform))
        if not os_type:
            os_type = '?'

        image_id = instance.image_id
        print('Debug: image_id = {}'.format(image_id))
        if not image_id_to_os_map.get(image_id):
            # look up image_id info and cache it.
            ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)

            response = ec2_client.describe_images(
                ImageIds=[image_id]
            )
            if response:
                resp_images = response.get('Images')
                print('Debug: resp_image = {}'.format(resp_images))
                for curr_image in resp_images:
                    cid = curr_image.get('Description')
                    cin = curr_image.get('Name')
                    # cil = curr_image.get('ImageLocation')
                    print('DEBUG: ImageId - desc: {}  name: {}'.format(cid, cin))
                    if cid:
                        image_id_to_os_map[image_id] = cid
                    elif cin:
                        image_id_to_os_map[image_id] = cin

        image_desc = image_id_to_os_map.get(image_id)
        if image_desc:
            if image_desc.startswith('Amazon Linux'):
                os_type = 'linux'
            elif image_desc.startswith('Cent'):
                os_type = 'rhel'
            elif image_desc.startswith('SLES'):
                os_type = 'sles'
            elif 'elasticbeanstalk-amzn' in image_desc:
                os_type = 'linux'
            elif 'Elastic MapReduce ebs|Amazon' in image_desc:
                os_type = 'linux'
            elif 'Amazon Linux' in image_desc:
                os_type = 'linux'
            elif 'buntu' in image_desc:
                # Ubuntu can be reserved as linux RIs
                os_type = 'linux'
            elif 'roku-build-teamcity' in image_desc:
                # player services accounts use frequently update teamcity AMIs. @cyeh for questions
                os_type = 'linux'
            else:
                if not os_type == 'windows':
                    print('WARN: unknown image_desc = _{}_'.format(image_desc))
        else:
            if 'windows' == os_type:
                image_id_to_os_map[image_id] = 'windows - {}'.format(image_id)
            else:
                print('WARN: No os_type info for: image_id = {}'.format(image_id))
                # Add to list of un-categorized image descriptions.
                count = uncategorized_image_descriptions.get(image_id)
                if not count:
                    uncategorized_image_descriptions[image_id] = 1
                else:
                    count += 1
                    uncategorized_image_descriptions[image_id] = count

        # Check database if AMI Id and Description are ambiguous about OS type.
        if os_type == '?':
            os_type = check_database_for_type(image_id, image_desc, region, session)

        if os_type == '?':
            print('WARN: EC2 os_type: {}, ami desc: {}'.format(os_type, image_desc))
            unknown_os_type_counter += 1

        return os_type
    except Exception as ex:
        print('ERROR: getting EC2 Instance data')
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)

        return '?'


def check_database_for_type(image_id, image_desc, region, session):
    """
    If we are calling this method it is because the OS of an AMI is ambiguous.
    In those cases we store the AMI-ID in a database and manually annotate which OS (likely linux)
    it is.

    The the AMI-ID isn't in the database then add it with a '?' to indicated it needs to be filled in.
    In practice (assuming we don't find a better method to determine OS) This should only happen
    when a new AMI is created. Such an event could trigger a notification.
    :param image_id: AMI Id - this is key into database
    :param image_desc: - Image description helps determine type.
    :param region: - Region just for record keeping.
    :param session: - To get account id.
    :return: os_type -   linux | rhel | sles |  (maybe) windows
    """
    try:

        # ToDo: we need to cache this dynamo response in a map from parent subroutine.

        # Look up in database.
        response = AWS_COST_MAP_TABLE.get_item(
            Key={
                'id': image_id
            }
        )

        if response.get('Item'):
            item = response.get('Item')
            os_type = item.get('os_type')

            if os_type == '?':
                print('WARN: Unknown AMI-ID in AwsCostMap table: {} - {}'.format(image_id, image_desc))

            return os_type

        else:
            account_id = awscost_helper_util.get_account_id_from_session(session)
            added_date = awscost_helper_util.get_awscost_hourly_time_format()

            # We didn't find this id, so write it. Put a '?' in the os_type column.
            AWS_COST_MAP_TABLE.put_item(
                Item={
                    'id': image_id,
                    'image_desc': image_desc,
                    'region': region,
                    'os_type': '?',
                    'account_id': account_id,
                    'added_date': added_date
                }
            )
            print('Add {} to AwsCostMap table. image_desc={}'.format(image_id, image_desc))

            return '?'

    except Exception as ex:
        print('ERROR: getting EC2 Instance data')
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)

        return '?'


def summarize_results(aws_resource_type, time_index):
    """
    Summarize the results for a time slice.
    Read entries for that time-slice which will look like
        awsResource = <aws_resource_type>:<account-id>:<region>
        time = <time>

    Write a new row which summarized all of the accounts, and leaves a result like.
        awsResource = <aws_resource_type>:roku:<region>
        time = <time>

    That row can then be queried for display.

    :param aws_resource_type: type of resource to summarize. 'dynamodb' | 'rds' | 'redshift' | 'ec2' | 'es'
    :param time_index: string. the time-slice to summarize. like '20181115-14'
    :return: None
    """
    try:
        print('Summarize type: {}  time: {}'.format(aws_resource_type, time_index))
        # dynamodb_client = boto3.client('dynamodb')

        # For each aws account
        active_regions = ['us-east-1', 'us-west-2']

        aws_account = awscost_helper_util.AWS_ACCOUNTS
        for region in active_regions:
            roku_wide_node_types = {}
            for name, account_num in aws_account.iteritems():
                key = '{}:{}:{}'.format(aws_resource_type, account_num, region)

                response = AWS_COST_TABLE.get_item(
                    Key={
                        'awsResource': key,
                        'time': time_index
                    }
                )

                item = response.get('Item')
                if item:
                    node_types = item.get('node_types')
                    if not node_types and aws_resource_type == 'dynamodb':
                        # Note before Nov. 16th. dynamodb would have separate columns.
                        # It was eventually made same as other, so this "if not" clause can go away eventually.
                        try:
                            rc = item.get('read_capacity')
                            wc = item.get('write_capacity')
                            tt = item.get('table_count')
                            node_types = {
                                'table_count': tt,
                                'read_capacity': rc,
                                'write_capacity': wc
                            }
                        except Exception as ex:
                            print('Failed to create node for key={}'.format(key))
                            print('Exception: {}'.format(ex.message))
                            awscost_helper_util.log_traceback_exception(ex)

                    # Add this result to the node types.
                    accumulate_node_types(roku_wide_node_types, node_types)
                else:
                    print('No item for {}: {}  {}'.format(name, key, time_index))

            # write result into database.
            summary_key = '{}:roku:{}'.format(aws_resource_type, region)
            AWS_COST_TABLE.put_item(
                Item={
                    'awsResource': summary_key,
                    'time': time_index,
                    'node_types': roku_wide_node_types
                }
            )

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def increment_count_in_dictionary(python_dict_as_counter, key, inc_by=1):
    """
    Expect a python dictionary in format.
    {
        'key1': 15,
        'key2':  3
    }

    If the key is new add it with count 'inc_by', which is 1 by default.
    Otherwise increment existing counter.

    :param python_dict_as_counter: MOST be Python dict used
    :param key:
    :param inc_by: the amount to increment the count by. If not specified it is one.
    :return: None
    """
    if type(python_dict_as_counter) is not dict:
        raise ValueError('"increment_count_in_dictionary" method expect "python_dict_as_counter" as <dict>')
    if type(key) is not str:
        raise ValueError('"increment_count_in_dictionary" method expect "key" as <str>')

    count = python_dict_as_counter.get(key)
    if not count:
        python_dict_as_counter[key] = inc_by
    else:
        python_dict_as_counter[key] = count + inc_by


def accumulate_node_types(roku_wide_node_types, node_types):
    """
    Accumulate the counts from 'node_types' into 'roku_wide_node_types'
    :param roku_wide_node_types:
    :param node_types:
    :return: None
    """
    if type(roku_wide_node_types) is not dict:
        raise ValueError('"accumulate_node_types" method expect "roku_wide_node_types" as <dict>')
    if type(node_types) is not dict:
        raise ValueError('"accumulate_node_types" method expect "node_types" as <dict>')

    for key, value in node_types.iteritems():
        if not value:
            value = 0
        rw_key = roku_wide_node_types.get(key)
        print('DEBUG accumulate_node_type: key={}, value={}, rw_key={}'.format(key, value, rw_key))
        if not rw_key:
            # Add the key with a starting value of zero.
            roku_wide_node_types[key] = 0
        rw_value = roku_wide_node_types.get(key)

        # print('DEBUG rw_value = {}, type: {}, value = {}, type: {}'.format(rw_value, type(rw_value), value, type(value)))
        if not rw_value:
            rw_value = 0

        if type(value) == unicode:
            print('WARN Unicode value: {}'.format(value))
            value = int(value)
        roku_wide_node_types[key] = rw_value + value


def create_hourly_data_frame_for_aws_account(prefix, aws_account_name, aws_region, time_index):
    """
    Create a detailed hourly report that goes back one week, for the
    resource type specified.
    :param prefix: string like 'dynamodb', 'es', 'ec2', 'redshift'
    :param aws_account_name: Roku AWS Account name like: 'apps-prod', 'dea', 'cti', 'sr-infra'
    :param aws_region: AWS Region like: 'us-east-1'
    :param time_index: string in format 'YYYYMMDD-HH' like '20181204-15'
    :return: Panda DataFrame object.
    """
    print('create_hourly_data_frame_for_aws_account')
    print('prefix={}, aws_account_name={}, aws_region={}, time_index={}'.format(
        prefix, aws_account_name, aws_region, time_index))

    try:
        # Init the data frame rows with time_index.
        hours_in_week = 24 * 7
        hours_in_4_weeks = 4 * hours_in_week

        # Go back 3 weeks.
        row_0 = create_time_column_values(time_index, -1, hours_in_4_weeks)
        time_dict = {'time': row_0}

        ret_val_data_frame = pd.DataFrame(index=time_dict.get('time'))
        ret_val_data_frame.index.name = 'time'

        # Turn account_name into an account_id
        aws_account_id = awscost_helper_util.get_aws_account_id_from_name(aws_account_name)

        # Make the following query:  {prefix}.roku.{region} for time_index > 28 days ago... expect about
        start_time = awscost_helper_util.increment_time_index(time_index, -672)
        aws_resource_key = '{}:{}:{}'.format(prefix, aws_account_id, aws_region)
        response = AWS_COST_TABLE.query(
            KeyConditionExpression=Key('awsResource').eq(aws_resource_key) & Key('time').gte(start_time)
        )

        column_names_set = set()

        # Create a panda to hold the cells.
        items = response.get('Items')
        if items:
            for curr_item in items:
                print('item: {}'.format(curr_item))
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
                    # print('{}: {}'.format(curr_key, curr_value)) # to verbose
                    ret_val_data_frame.at[time_index, curr_key] = curr_value

        # sort the column names.
        return ret_val_data_frame

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)
        return None


def create_hourly_data_frame(prefix, aws_region, time_index):
    """
    Create a detailed hourly report that goes back one week, for the
    resource type specified.
    :param prefix: string like 'dynamodb', 'es', 'ec2', 'redshift'
    :param aws_region: AWS Region like: 'us-east-1'
    :param time_index: string in format 'YYYYMMDD-HH' like '20181204-15'
    :return: Panda DataFrame object.
    """
    print('create_hourly_data_frame: {}, {}'.format(prefix, time_index))

    # Init the data frame rows with time_index.
    hours_in_week = 24 * 7
    hours_in_4_weeks = 4 * hours_in_week

    # Go back 3 weeks.
    row_0 = create_time_column_values(time_index, -1, hours_in_4_weeks)
    time_dict = {'time': row_0}

    ret_val_data_frame = pd.DataFrame(index=time_dict.get('time'))
    ret_val_data_frame.index.name = 'time'

    # Make the following query:  {prefix}.roku.{region} for time_index > 28 days ago... expect about
    start_time = awscost_helper_util.increment_time_index(time_index, -672)
    aws_resource_key = '{}:roku:{}'.format(prefix, aws_region)
    response = AWS_COST_TABLE.query(
        KeyConditionExpression=Key('awsResource').eq(aws_resource_key) & Key('time').gte(start_time)
    )

    column_names_set = set()

    # Create a panda to hold the cells.
    items = response.get('Items')
    if items:
        for curr_item in items:
            print('item: {}'.format(curr_item))
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
                print('{}: {}'.format(curr_key, curr_value))
                ret_val_data_frame.at[time_index, curr_key] = curr_value

    # sort the column names.
    return ret_val_data_frame


def create_time_column_values(time, hour_increment=-1, steps=168):
    """
    Create a the time_index row.
    :param time:
    :param hour_increment:
    :param steps:
    :return:
    """
    ret_val = []

    curr_time = time
    for x in range(1, steps):
        ret_val.append(curr_time)
        curr_time = awscost_helper_util.increment_time_index(curr_time, hour_increment)

    return ret_val


def create_test_page_data_frame():
    """
    Create a Test Page to try panda features
    :return: Panda DataFrame object
    """

    print('pandas version = {}'.format(pd.__version__))
    print('numpy version = {}'.format(np.__version__))

    time_dict = {'time': ['20181129-11', '20181129-12', '20181129-13', '20181129-14']}

    panda_first_data_frame = pd.DataFrame(index=time_dict.get('time'))
    panda_first_data_frame.index.name = 'time'

    panda_first_data_frame.insert(0, 't2.micro', np.nan)
    panda_first_data_frame.at['20181129-11', 't2.micro'] = 100
    panda_first_data_frame.at['20181129-12', 't2.micro'] = 110
    panda_first_data_frame.at['20181129-13', 't2.micro'] = 120
    panda_first_data_frame.at['20181129-14', 't2.micro'] = 130

    panda_first_data_frame.insert(1, 'm3.medium', np.nan)
    panda_first_data_frame.at['20181129-11', 'm3.medium'] = 50
    panda_first_data_frame.at['20181129-12', 'm3.medium'] = 54
    panda_first_data_frame.at['20181129-13', 'm3.medium'] = 55
    panda_first_data_frame.at['20181129-14', 'm3.medium'] = 56

    # Now can we add a new column and insert elements from that?
    panda_first_data_frame.insert(2,'m3.large', np.nan)
    panda_first_data_frame.at['20181129-11', 'm3.large'] = 200
    # un-filled items are NaNs.

    return panda_first_data_frame


def archived_repair_west_included_east_results_in_summaries(event, context):
    """
    @Deprecated. This method repaired summary results. before Dec. 7, where
    us-west-2 Roku wide summaries added in results from us-east-1. This
    method was run on all effected data back into start of data collection in mid November.

    Bug in summaries where "us-east-1" data was added to "us-west-2" data.
    Was fixed in the 20181207-11 and after.
    To repair all the summaries before this time just need to re-run
    the do_summary method with the time index.

    This method takes the time_index and works backwards for
    as long as it is allowed.

    We will repair back to Nov. 15.
    :param event:
    :param context:
    :return:
    """
    try:
        print('######## REPAIR SUMMARY ########')
        print('event: {}'.format(event))
        time_index = event.get('time_index')

        if not time_index:
            print('ERROR: Not time_index in event. Abort process.')

        print('time_index={}'.format(time_index))

        count = 0
        count_limit = 24*4
        while count < count_limit:
            count += 1
            print('REPAIR: summary {}'.format(time_index))
            do_summary(time_index)
            time_index = awscost_helper_util.increment_time_index(time_index, -1)

            # Sleep for a few seconds for DynamoDB capacity to catch-up.
            time.sleep(4)

        print('REPAIR DONE.')

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


def archived_repair_redshift_and_es_daily_summaries_dec_03_2018_to_dec_20_2018(event, context):
    """
    Redshift and Elastic Search Service data is collected once per day after Dec. 3rd.
    The once daily index for this data in *-01.   But summaries were looking or *-00.
    This method repairs all ES And Redshift Roku-wide daily summaries.
    :param event:
    :param context:
    :return:
    """
    try:
        # summarize daily_results at end of day time_index = *-01
        # fix redshift data.
        print('###### Start Redshift daily summary repair')
        summarize_results('redshift', '20181203-01')
        summarize_results('redshift', '20181204-01')
        summarize_results('redshift', '20181205-01')
        summarize_results('redshift', '20181206-01')
        summarize_results('redshift', '20181207-01')
        summarize_results('redshift', '20181208-01')
        summarize_results('redshift', '20181209-01')
        summarize_results('redshift', '20181210-01')
        summarize_results('redshift', '20181211-01')
        summarize_results('redshift', '20181212-01')
        summarize_results('redshift', '20181213-01')
        summarize_results('redshift', '20181214-01')
        summarize_results('redshift', '20181215-01')
        summarize_results('redshift', '20181216-01')
        summarize_results('redshift', '20181217-01')
        summarize_results('redshift', '20181218-01')
        summarize_results('redshift', '20181219-01')
        print('###### End Redshift daily summary repair')

        # fix es data.
        print('###### Start ES daily summary repair')
        summarize_results('es', '20181203-01')
        summarize_results('es', '20181204-01')
        summarize_results('es', '20181205-01')
        summarize_results('es', '20181206-01')
        summarize_results('es', '20181207-01')
        summarize_results('es', '20181208-01')
        summarize_results('es', '20181209-01')
        summarize_results('es', '20181210-01')
        summarize_results('es', '20181211-01')
        summarize_results('es', '20181212-01')
        summarize_results('es', '20181213-01')
        summarize_results('es', '20181214-01')
        summarize_results('es', '20181215-01')
        summarize_results('es', '20181216-01')
        summarize_results('es', '20181217-01')
        summarize_results('es', '20181218-01')
        summarize_results('es', '20181219-01')
        print('###### End ES daily summary repair')

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


# some test methods here #
def test_handler(event, context):
    """
    If you get a work_type that starts with test, it gets forwarded to this entry point.
    :param event:
    :param context:
    :return:
    """
    try:
        # Print session data format to get AWS account from it.
        session = awscost_helper_util.create_cost_explorer_session()
        print('session = {}'.format(session))
        account_id = awscost_helper_util.get_account_id_from_session(session)
        print('account_id = {}'.format(account_id))

        # Test CostExplorer Report access in NetEng account.
        # print('Start CostExplorer Report testing')
        # do_cost_explorer_reports('20181230-01')

        # Quick test on new EC2 scan with one account at a fixed time.
        #'cti':  '141602222194'
        #check_ec2_usage('dea', '182333787270', 'us-east-1', '20181220-08')

        # print('###### TESTING RI results ######')
        # print('version: {}'.format(awscost_helper_util.get_aws_cost_version()))
        # region = 'us-east-1'
        # time_index = '20181211-18'
        # print('========= EC2 Reserved Instances ========= ')
        # check_ec2_reserved_instances_in_all_accounts(region, time_index, is_test=True)
        # print('========= Elasticache Reserved Nodes ========= ')
        # check_elasticache_reserved_instances_in_all_accounts(region, time_index, is_test=True)
        # print('========= RDS Reserved Instances ========= ')
        # check_rds_reserved_instances_in_all_accounts(region, time_index, is_test=True)
        # print('========= Redshift Reserved Instances ========= ')
        # check_redshift_reserved_capacity_in_all_accounts(region, time_index, is_test=True)

        # print('++++++++ TESTING panda P95 stats ++++++++')
        # print('event: {}'.format(event))
        #
        # df = create_hourly_data_frame('rds', 'us-east-1', '20181205-11')
        # print('TEST: hourly dataframe: {}'.format(df))
        #
        # print('\n---\nDo some calculations to get min, max, media and P95.\n')
        #
        # stats_quantile = df.quantile([0.0, 0.5, 0.95, 1.00])
        # print('Quantile\n')
        # print('type(stats_quantile) = {}'.format(type(stats_quantile)))
        # print('{}'.format(stats_quantile))

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)


# Keep for quick tests.
if __name__ == '__main__':
    try:
        # try different panda building functions.
        test_df = create_test_page_data_frame()

        print('Test DataFrame')
        print('{}'.format(test_df))

        print('\n---\nDo some calculations to get min, max, media and P95.\n')

        # stats_quantile = test_df.quantile([0.0, 0.05, 0.5, 0.95, 1.00])
        # print('Quantile\n')
        # print('type(stats_quantile) = {}'.format(type(stats_quantile)))
        # print('{}'.format(stats_quantile))

        # write file to see if issue is there.
        path = '/Users/asnyder/Desktop/TestStats.xlsx'
        excel_file = open(path, "w+")
        excel_file.close()
        print('Created {}'.format(path))

        excel_writer = pd.ExcelWriter(path, engine='openpyxl')

        create_stats_from_data_frame(test_df, excel_writer, "TestFirstColumn")

        excel_writer.save()

        # time_list = create_time_column_values('20181204-18')
        # print('time_list')
        # print('{}'.format(time_list))
        #
        # stat_time = awscost_helper_util.start_timer()
        # print('start_time = {}'.format(stat_time))
        # time.sleep(.5)
        # awscost_helper_util.print_delta_time(stat_time, 'Should sleep half second.')

    except Exception as ex:
        # log error.
        print('Exception: {}'.format(ex.message))
        awscost_helper_util.log_traceback_exception(ex)

