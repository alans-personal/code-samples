"""Implements Spend command by asnyder"""
from __future__ import print_function
import datetime
import traceback
import pandas as pandas
import boto3
import botocore

import util.slack_ui_util as slack_ui_util
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
import util.cti_helper_util as cti_helper_util
from cmd_interface import CmdInterface
from util.slack_ui_util import ShowSlackError


class CmdSpend(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'admin',
            'sub_commands': ['tags', 'untagged', 'types', 'bill'],
            'help_title': 'Commands for tracking down AWS spending',
            'permission_level': 'dev',
            'props_tags': self.get_tags_properties(),
            'props_untagged': self.get_untagged_properties(),
            'props_types': self.get_types_properties(),
            'props_bill': self.get_bill_properties()

        }

        return props


    def get_tags_properties(self):
        """
        The properties for the "tags" sub-command
        Modify the values as needed, but leave keys alone.
        Valid 'run-type' values are ['shorttask, 'longtask, 'docker']
        The 'confirmation' section is and advanced feature and commented out.
        Remove it unless you plan on using confirmation responses.
        'help_text' needs a short one line description
        'help_examples' is a python list.
              Modify add remove examples (one per line) as needed.
        'switch-templates' contains common switchs (-e, -d, -s)
              remove the ones not need. Leave an empty list if needed.
              use 'region-optional' and 'service-optional' if param not required.        See 'switch-z' as an example custom parameter definition.
            valid 'types' are string | int | property
        Copy-paste that section as needed.
        Then delete the 'switch-z' section.
        
        When done reduce the DocString to a description of the 
            sub-commands properties.
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`tags`* _description here_',
            'help_examples': [
                '/run spend tags -e dev -r us-east-1 -s devnull',
                '/run spend tags -e dev -r us-west-2 -s devnull -t 30'
            ],
            'switch-templates': ['env', 'service', 'region-optional'],
            'switch-c': {
                'aliases': ['c', 'changeme'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Change this help string for switch'
            }
        }
        return props

    def invoke_tags(self, cmd_inputs):
        """
        Placeholder for "tags" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_tags")
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used
            arg_service = cmd_inputs.get_by_key('service')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start Tags code section #### output to "text" & "title".
        
            # End Tags code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Tags title"
            text = "Tags response. Fill in here"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_untagged_properties(self):
        """
        The properties for the "untagged" sub-command
        Modify the values as needed, but leave keys alone.
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`untagged`* _Create report of all untagged AWS resources of the type(s) specified_',
            'help_examples': [
                '/run spend untagged -e cti -r us-east-1 -t s3 -o excel',
                '/run spend untagged -e sr-dev -r us-east-1 -t ec2,s3,dynamo -o text',
                '/run spend untagged -e apps-qa -r us-east-1 -t all -o excel'
            ],
            'switch-templates': ['env', 'region'],
            'switch-t': {
                'aliases': ['t', 'type'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'List of AWS types to check or "all", if you want everything'
            },
            'switch-o': {
                'aliases': ['o', 'output'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Output format, valid formats are "text" | "excel"'
            }
        }
        return props

    def invoke_untagged(self, cmd_inputs):
        """
        Placeholder for "untagged" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_untagged")
            arg_region = cmd_inputs.get_by_key('region')
            arg_env = cmd_inputs.get_by_key('env')
            arg_type = cmd_inputs.get_by_key('type')
            arg_output = cmd_inputs.get_by_key('output')
            if not arg_output:
                arg_output = 'text'

            # Start Report code section #### output to "text" & "title".
            start_time = datetime.datetime.now()
            arg_env
            region = arg_region

            aws_type_list = []
            if arg_type == 'all':
                aws_type_list = ['autoscale', 'cloudfront', 'dynamo', 'ec2', 'elasticache', 'elb', 'logs', 'rds', 's3']
            elif ',' in arg_type:
                aws_type_list = arg_type.split(',')
            else:
                aws_type_list = [arg_type]

            session = cti_helper_util.create_security_auditor_session(arg_env)

            tagging_client = aws_util.get_tagging_client(session, arg_region)

            text = "List of untagged resources\n"
            types_count = 0

            print('Will look for following resources: [{}]'.format(aws_type_list))

            summary_data_frame = init_summary_data_frame()
            data_frame_dict = {}
            data_frame_dict.update({'summary': summary_data_frame})

            for aws_type in aws_type_list:
                print('Checking {}'.format(aws_type))
                data_frame = None
                if 'autoscale' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_autoscaling_groups(
                        session, region, tagging_client, summary_data_frame)
                elif 'cloudfront' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_cloud_front_distributions(
                        session, region, tagging_client, summary_data_frame)
                elif 'dynamo' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_dynamo_tables(
                        session, region, tagging_client, summary_data_frame)
                elif 'ec2' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_ec2_instances(
                        session, region, tagging_client, summary_data_frame)
                elif 'elasticache' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_elasticache_replication_groups(
                        session, region, tagging_client, summary_data_frame)
                elif 'elb' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_load_balancers(
                        session, region, tagging_client, summary_data_frame)
                elif 'logs' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_log_groups(
                        session, region, tagging_client, summary_data_frame)
                elif 'rds' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_rds_instances(
                        session, region, tagging_client, summary_data_frame)
                elif 'rds-cluster' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_rds_groups(
                        session, region, tagging_client, summary_data_frame)
                elif 's3' in aws_type:
                    types_count += 1
                    data_frame = check_for_untagged_s3_buckets(
                        session, region, tagging_client, summary_data_frame)
                # sqs
                # route53

                if not data_frame.empty:
                    data_frame_dict.update({aws_type: data_frame})
                else:
                    print('AWS type: {} was empty.'.format(aws_type))

                # Bail if we are taking too long. Lambda has a 5 min limit, so bail at 4:30 to
                # give time for wrap up and data-transfer
                bud_helper_util.print_delta_time(start_time, aws_type)
                total_sec = bud_helper_util.delta_time(start_time)
                if total_sec > 270:
                    print('Finished early after {} seconds, at stage: {}'.format(total_sec, aws_type))
                    break

            keys = data_frame_dict.keys()
            num_keys = len(keys)
            print('#keys = {}'.format(num_keys))
            if not arg_output:
                arg_output = 'text'

            if arg_output == 'excel':
                text = create_excel_file_in_s3_bucket(data_frame_dict, arg_env, arg_region)
            else:
                text = convert_data_frame_to_text(data_frame_dict)

            end_time = datetime.datetime.now()
            run_time = end_time - start_time
            text += 'run time: {} sec'.format(run_time.total_seconds())
            # End Report code section. ####

            # Standard response below. Change title and text for output.
            title = "AWS Spend_Category Tag report"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_types_properties(self):
        """
        The properties for the "types" sub-command
        Modify the values as needed, but leave keys alone.
        Valid 'run-type' values are ['shorttask, 'longtask, 'docker']
        The 'confirmation' section is and advanced feature and commented out.
        Remove it unless you plan on using confirmation responses.
        'help_text' needs a short one line description
        'help_examples' is a python list.
              Modify add remove examples (one per line) as needed.
        'switch-templates' contains common switchs (-e, -d, -s)
              remove the ones not need. Leave an empty list if needed.
              use 'region-optional' and 'service-optional' if param not required.        See 'switch-z' as an example custom parameter definition.
            valid 'types' are string | int | property
        Copy-paste that section as needed.
        Then delete the 'switch-z' section.
        
        When done reduce the DocString to a description of the 
            sub-commands properties.
        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`types`* _description here_',
            'help_examples': [
                '/run spend types -e dev -r us-east-1 -s devnull',
                '/run spend types -e dev -r us-west-2 -s devnull -t 30'
            ],
            'switch-templates': ['env', 'service', 'region-optional'],
            'switch-c': {
                'aliases': ['c', 'changeme'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Change this help string for switch'
            }
        }
        return props

    def invoke_types(self, cmd_inputs):
        """
        Placeholder for "types" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_types")
            response_url = cmd_inputs.get_response_url()

            # Start Types code section #### output to "text" & "title".
            text = 'Types of resources supported\n'
            text += '   *autoscale*   AutoScaling Groups\n'
            text += '   *cloudfront*  CloudFront distributions\n'
            text += '   *dynamo*      DynamoDB Tables\n'
            text += '   *ec2*         EC2 Instances\n'
            text += '   *elasticache* ElastiCache Replication Groups\n'
            text += '   *elb*         LoadBalancers (classic)\n'
            text += '   *logs*        CloudWatch Log Groups\n'
            # text += '   *rds*         RDS Instances\n'
            # text += '   *rds-cluster* RDS Clusters\n'
            text += '   *s3*          S3 Buckets\n'
            # End Types code section. ####

            # Standard response below. Change title and text for output.
            title = "Types avail in reports command"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_bill_properties(self):
        """
        The properties for the "bill" sub-command
        Modify the values as needed, but leave keys alone.
        Valid 'run-type' values are ['shorttask, 'longtask, 'docker']
        The 'confirmation' section is and advanced feature and commented out.
        Remove it unless you plan on using confirmation responses.
        'help_text' needs a short one line description
        'help_examples' is a python list.
              Modify add remove examples (one per line) as needed.
        'switch-templates' contains common switchs (-e, -d, -s)
              remove the ones not need. Leave an empty list if needed.
              use 'region-optional' and 'service-optional' if param not required.        See 'switch-z' as an example custom parameter definition.
            valid 'types' are string | int | property
        Copy-paste that section as needed.
        Then delete the 'switch-z' section.

        When done reduce the DocString to a description of the
            sub-commands properties.
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`bill`* _Download AWS spend bill and create reports from it_',
            'help_examples': [
                '/run spend bill -e sr-dev',
                '/run spend bill -e dev -r us-west-2 -s devnull -t 30'
            ],
            'switch-templates': ['env'],
            'switch-c': {
                'aliases': ['c', 'changeme'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'Change this help string for switch'
            }
        }
        return props

    def invoke_bill(self, cmd_inputs):
        """
        Placeholder for "bill" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_bill")
            arg_env = cmd_inputs.get_by_key('env')  # remove if not used

            # Start Untagged code section #### output to "text" & "title".

            # For now we are just doing a test to see how long it takes do download an object,
            # store it, and then read it.

            start_time = bud_helper_util.start_timer()

            bucket_name = 'asnyder-billing'
            key = '123456789012-aws-billing-csv-2018-06.csv'
            local_file = '/tmp/{}'.format(key)

            s3 = boto3.resource('s3')

            try:
                s3.Bucket(bucket_name).download_file(key, local_file)
                bud_helper_util.print_delta_time(start_time, 'Download from S3')
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    print("The object does not exist.")
                else:
                    raise

            # time how long this takes.
            num_lines = 0
            with open(local_file) as f:
                for line in f:
                    num_lines += 1
            bud_helper_util.print_delta_time(start_time, 'Count lines')
            print('Total lines = {}'.format(num_lines))
            # finish timing an count the number of lines.


            # End Untagged code section. ####

            # Standard response below. Change title and text for output.
            title = "Untagged title"
            text = "Untagged response. Fill in here"
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


def create_excel_file_in_s3_bucket(data_frame_dict, arg_env, arg_region):
    """
    Load an Excel file into an S3 bucket for the report.
    :param data_frame_dict: A Python dictionary with a key as a string and value of pandas DataFrame.
    :param arg_env: String with AWS Account short name.
    :param arg_region: String with region.
    :return: String just indicating the file was uploaded.
    """
    # Create the file name based on a time-stamp for now.
    date_str = datetime.datetime.today().strftime('%m-%d--%H-%M')

    path = '/tmp/AwsUntaggedReport.xlsx'
    excel_file = open(path, "w+")
    excel_file.close()

    writer = pandas.ExcelWriter(path, engine='openpyxl')

    keys = data_frame_dict.keys()
    keys.sort()

    for curr_key in keys:
        curr_data_frame = data_frame_dict.get(curr_key)
        curr_data_frame.to_excel(writer, curr_key, index=False)
        writer.save()

    #  S3 copy this file into a bucket, or attach it to an e-mail.
    bucket_name = 'cti-image-server-bucket'

    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(
        path, bucket_name,
        'quarter/untagged_{}_{}_{}.xlsx'.format(arg_env, arg_region, date_str)
    )

    path = 'quarter/untagged_{}_{}_{}.xlsx'.format(arg_env, arg_region, date_str)
    report_file_url = 'https://http://internal-image-svc.eng.asnyder.com/static/{}'.format(path)

    return 'Report for {} at:\n```{}```\n'.format(arg_env, report_file_url)


def convert_data_frame_to_text(data_frame_dict):
    """

    :param data_frame_dict:
    :return:
    """
    keys = data_frame_dict.keys()
    keys.sort()

    text = ''
    for curr_key in keys:
        curr_data_frame = data_frame_dict.get(curr_key)
        text += '\n\n--- {} ---\n'.format(curr_key)
        for index, row in curr_data_frame.iterrows():
            line = '{}, {}'.format(row['name'], row['cost-estimate'])
            print(line)
            text += '{}\n'.format(line)

    return text


def init_standard_data_frame():
    """
    Create the standard data_frame within all apps that use it.
    :return: panda DataFrame object
    """
    data_frame = pandas.DataFrame(columns=['name', 'cost-estimate'])
    return data_frame


def init_ec2_data_frame():
    """
    Create a data_frame specific to EC2 Instances
    :return: panda DataFrame object
    """
    ec2_type_data_frame = pandas.DataFrame(columns=[
        'name', 'instance_id', 'cost-estimate', 'spend_category', 'department', 'owner'
    ])
    return ec2_type_data_frame


def init_summary_data_frame():
    """
    Create a data_frame specific for summary.
    :return: panda DataFrame object
    """
    summary_type_data_frame = pandas.DataFrame(columns=['AWS Type', 'run-time', 'untagged instance', 'total instance'])
    return summary_type_data_frame


def append_summary_data(summary_data_frame, aws_type, run_time, untagged_resource_count, all_resource_count):
    """
    Appends a row to the summary page in Excel file in a standard way, since this is done in many places.
    :param summary_data_frame: panda DataFrame that summarizes the information.
    :param aws_type: String that is type of AWS resource like (rds, ec2, dynamo, ...)
    :param run_time: float that is runtime in seconds.
    :param untagged_resource_count:
    :param all_resource_count:
    :return:
    """
    # keep this in sync with init_summary_data_frame
    summary_data_frame.loc[len(summary_data_frame)] = [aws_type, run_time, untagged_resource_count, all_resource_count]


def check_for_untagged_autoscaling_groups(session, region, tagging_client, summary_data_frame):
    """
    List all untagged AutoScaling Groups resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    autoscaling_client = aws_util.get_boto3_client_by_name('autoscaling', session, region)
    response = autoscaling_client.describe_auto_scaling_groups()
    all_groups_list = response['AutoScalingGroups']
    all_group_arns_list = []
    for curr_group in all_groups_list:
        curr_arn = curr_group['AutoScalingGroupARN']
        all_group_arns_list.append(curr_arn)
    all_groups_len = len(all_group_arns_list)

    arn_list = get_tagged_resource_list(tagging_client, 'autoscaling:autoScalingGroup')
    arn_list_len = len(arn_list)
    ret_val = 'AutoScaling found {} tagged of {} total groups\n'.format(arn_list_len, all_groups_len)

    tagged_arn_set = set(arn_list)
    untagged_set = set(all_group_arns_list).difference(tagged_arn_set)
    untagged_set_len = len(untagged_set)

    if untagged_set_len > 0:
        ret_val = 'AutoScaling found {} untagged of {} total groups\n'.format(untagged_set_len, all_groups_len)
        sorted_untagged_table_list = sorted(untagged_set)
        index = 0
        for curr_name in sorted_untagged_table_list:
            index += 1
            # ret_val += '    {}) {}\n'.format(index, curr_name)
            data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
    else:
        ret_val = 'All {} Autoscaling groups tagged.\n'.format(all_groups_len)
        data_frame.loc[0] = [ret_val, 'n/a']

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'autoscaling', run_time, untagged_set_len, all_groups_len)

    return data_frame


def check_for_untagged_cloud_front_distributions(session, region, tagging_client, summary_data_frame):
    """
    List all untagged CloudFront Distributions resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    cfront_client = aws_util.get_boto3_client_by_name('cloudfront', session, region)
    response = cfront_client.list_distributions()

    # all_cfront_distros = response['DistributionList']['Items'] # remove.
    dl = response.get('DistributionList')
    if not dl:
        print("WARN: No response['DistributionList']")
        return data_frame
    all_cfront_distros = dl.get('Items')
    if not all_cfront_distros:
        print("WARN: No response['DistributionList']['Items']")
        return data_frame

    all_cf_distro_arns = []
    for curr_cfront_distro in all_cfront_distros:
        curr_arn = curr_cfront_distro['ARN']
        all_cf_distro_arns.append(curr_arn)
    all_cf_distros_len = len(all_cf_distro_arns)

    arn_list = get_tagged_resource_list(tagging_client, 'cloudfront:distribution')
    arn_list_len = len(arn_list)
    # ret_val = 'CloudFront found {} tagged distribution\n'.format(arn_list_len)

    tagged_arn_set = set(arn_list)
    untagged_set = set(all_cf_distro_arns).difference(tagged_arn_set)
    untagged_set_len = len(untagged_set)

    if untagged_set_len > 0:
        ret_val = 'CloudFront found {} untagged of {} total distributions\n'.format(untagged_set_len, all_cf_distros_len)
        sorted_untagged_table_list = sorted(untagged_set)
        index = 0
        for curr_name in sorted_untagged_table_list:
            index += 1
            # ret_val += '    {}) {}\n'.format(index, curr_name)
            data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
    else:
        ret_val = 'All {} CloudFront distributions tagged.\n'.format(all_cf_distros_len)
        data_frame.loc[0] = [ret_val, 'n/a']

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'cloudfront', run_time, untagged_set_len, all_cf_distros_len)

    return data_frame


def check_for_untagged_dynamo_tables(session, region, tagging_client, summary_data_frame):
    """
    List all untagged DynamoDB table resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    dynamodb = aws_util.get_dynamo_resource(session, region, client=True)
    response = dynamodb.list_tables()
    table_names = response['TableNames']

    table_names_len = len(table_names)
    print('Dynamo found {} tables: /n{}'.format(table_names_len, table_names))

    arn_list = get_tagged_resource_list(tagging_client, 'dynamodb:table')
    arn_list_len = len(arn_list)
    # print('Dynamo search found {} table and {} were tagged'
    #       .format(table_names_len, arn_list_len))
    # print('List of tagged tables: {}'.format(arn_list))

    normalized_arn_list = normalize_arn_list(arn_list)
    tagged_arn_set = set(normalized_arn_list)

    print('tagged_arn_set:\n{}'.format(tagged_arn_set))
    untagged_set = set(table_names).difference(tagged_arn_set)

    print('This should be the set of untagged DynamoDB tables\n{}'.format(untagged_set))

    untagged_set_len = len(untagged_set)
    if untagged_set_len > 0:
        ret_val = 'Found {} untagged of {} total tables\n'.format(untagged_set_len, table_names_len)
        sorted_untagged_table_list = sorted(untagged_set)
        index = 0
        for curr_name in sorted_untagged_table_list:
            index += 1
            ret_val += '    {}) {}\n'.format(index, curr_name)
            data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
    else:
        ret_val = 'All {} DynamoDB tables tagged.\n'.format(table_names_len)
        data_frame.loc[0] = [ret_val, 'n/a']

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'dynamo', run_time, untagged_set_len, table_names_len)

    return data_frame


def check_for_untagged_ec2_instances(session, region, tagging_client, summary_data_frame):
    """
    List all untagged EC2 Instances resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """
    ec2_type_data_frame = init_ec2_data_frame()
    start_time = bud_helper_util.start_timer()

    try:
        ec2_client = aws_util.get_ec2_resource(session, region, client=True)
        response = ec2_client.describe_instances()
        all_ec2_instance_list = []
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance['InstanceId']
                instance_type = instance['InstanceType']
                tags = instance['Tags']
                print('tags={}'.format(tags))
                name_value = cti_helper_util.get_tag_value_from_list(tags, 'Name')
                # if possible get name and ec2-instance-type, and cost-estimate(assuming 24/7 for a month)
                all_ec2_instance_list.append(instance_id)

                # Check for 'Spend_Category' Tag.
                spend_category_tag = cti_helper_util.get_tag_value_from_list(tags, 'Spend_Category')
                if not spend_category_tag:
                    spend_category_tag = ''
                # Check for 'Department' Tag.
                department_tag = cti_helper_util.get_tag_value_from_list(tags, 'Department')
                if not department_tag:
                    department_tag = ''
                owner_tag = cti_helper_util.get_tag_value_from_list(tags, 'Owner')
                if not owner_tag:
                    owner_tag = ''

                ec2_type_data_frame.loc[len(ec2_type_data_frame)] = [name_value, instance_id, instance_type,
                                                                     spend_category_tag, department_tag, owner_tag]
        all_ec2_instance_len = len(all_ec2_instance_list)

        tagged_arn_list = get_tagged_resource_list(tagging_client, 'ec2:instance')

        # ToDo:  fix this method, it should only show the untagged instances.

        tagged_len = len(tagged_arn_list)
        untagged_len = all_ec2_instance_len - tagged_len
        ret_val = 'EC2 found {} tagged of {} total instances\n'.format(tagged_len, all_ec2_instance_len)
        # Add info to summary data_frame.
        run_time = bud_helper_util.delta_time(start_time)
        append_summary_data(summary_data_frame, 'ec2', run_time, untagged_len, all_ec2_instance_len)

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        template = 'Failed during EC2 phase. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))

    return ec2_type_data_frame


def check_for_untagged_elasticache_replication_groups(session, region, tagging_client, summary_data_frame):
    """
    List all untagged ElastiCache Clusters resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    elasticache_client = aws_util.get_boto3_client_by_name('elasticache', session, region)
    response = elasticache_client.describe_replication_groups()

    all_rep_groups = response['ReplicationGroups']
    all_rep_group_list = []
    for curr_rep_group in all_rep_groups:
        curr_rep_group_id = curr_rep_group['ReplicationGroupId']
        all_rep_group_list.append(curr_rep_group_id)

    total_rep_groups = len(all_rep_group_list)

    arn_list = get_tagged_resource_list(tagging_client, 'elasticache:cluster')
    arn_list_len = len(arn_list)
    ret_val = 'ElastiCache found {} tagged of {} total clusters\n'.format(arn_list_len, total_rep_groups)

    # # ToDo: Figure out of arn_list need normalizing before.
    # print('All elasticache regroup ids:\n{}'.format(all_rep_group_list))
    # print('ElastiCache tagged ARN list:\n{}'.format(arn_list))

    normalized_arn_list = normalize_elasticache_list(arn_list)

    # print('Normalized ARN list:\n{}'.format(normalized_arn_list))

    untagged_set = set(all_rep_group_list).difference(set(normalized_arn_list))

    ret_val = write_untagged_items(untagged_set, total_rep_groups, 'ElastiCache Groups')

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'elasticache', run_time, arn_list_len, total_rep_groups)

    return data_frame


def check_for_untagged_load_balancers(session, region, tagging_client, summary_data_frame):
    """
    List all untagged Load Balancers resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    elb_client = aws_util.get_boto3_client_by_name('elb',session, region)
    response = elb_client.describe_load_balancers()

    all_load_balancers = response['LoadBalancerDescriptions']
    all_lb_name_list = []
    for curr_load_balancer in all_load_balancers:
        curr_lb_name = curr_load_balancer['LoadBalancerName']
        all_lb_name_list.append(curr_lb_name)
    total_lb_count = len(all_lb_name_list)

    arn_list = get_tagged_resource_list(tagging_client, 'elasticloadbalancing:loadbalancer')
    arn_list_len = len(arn_list)
    ret_val = 'ELB found {} tagged of {} total load balancers\n'.format(arn_list_len, total_lb_count)

    try:
        # print('All ELB names:\n{}'.format(all_lb_name_list))
        # print('Tagged (un-normalized) ELBs:\n{}'.format(arn_list))

        normalized_arn_list = normalize_arn_list(arn_list)
        tagged_arn_set = set(normalized_arn_list)
        untagged_set = set(all_lb_name_list).difference(tagged_arn_set)

        untagged_set_len = len(untagged_set)
        if untagged_set_len > 0:
            ret_val = 'Found {} untagged of {} total (classic)ELB\n'.format(untagged_set_len, total_lb_count)
            sorted_untagged_table_list = sorted(untagged_set)
            index = 0
            for curr_name in sorted_untagged_table_list:
                index += 1
                ret_val += '    {}) {}\n'.format(index, curr_name)
                data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
        else:
            ret_val = 'All {} ELBs (classic) tagged.\n'.format(total_lb_count)
            data_frame.loc[len(data_frame)] = [ret_val, 'n/a']

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        template = 'Failed during ELB phase. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))
        ret_val += '  ELB had an error processing results. Check logs.'

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'elb', run_time, untagged_set_len, total_lb_count)

    return data_frame


def check_for_untagged_log_groups(session, region, tagging_client, summary_data_frame):
    """
    List all untagged Log Groups
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    log_client = aws_util.get_boto3_client_by_name('logs',session, region)
    response = log_client.describe_log_groups()
    all_log_groups = response['logGroups']
    total_log_groups = len(all_log_groups)
    log_group_list = []
    for curr_log_group in all_log_groups:
        log_group_arn = curr_log_group['arn']
        log_group_list.append(log_group_arn)

    arn_list = get_tagged_resource_list(tagging_client, 'logs:log-group')
    arn_list_len = len(arn_list)
    ret_val = 'CloudWatch Logs found {} tagged log groups\n'.format(arn_list_len)

    try:
        # Note we don't need to normalize this list since we seem to have the ARN.
        untagged_set = set(log_group_list).difference(set(arn_list))

        untagged_set_len = len(untagged_set)
        if untagged_set_len > 0:
            ret_val = 'Found {} untagged of {} total log groups\n'.format(untagged_set_len, total_log_groups)
            sorted_untagged_table_list = sorted(untagged_set)
            index = 0
            for curr_name in sorted_untagged_table_list:
                index += 1
                # ret_val += '    {}) {}\n'.format(index, curr_name)
                data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
        else:
            ret_val = 'All {} Log Groups tagged.\n'.format(total_log_groups)
            data_frame.loc[0] = [ret_val, 'n/a']

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        template = 'Failed during Log Group phase. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))
        ret_val += '  Log Group had an error processing results. Check logs.'
        data_frame.loc[0] = [ret_val, 'n/a']

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 'logs', run_time, untagged_set_len, total_log_groups)

    return data_frame


def check_for_untagged_rds_instances(session, region, tagging_client, summary_data_frame):
    """
    List all untagged RDS Instances resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    arn_list = get_tagged_resource_list(tagging_client, 'rds:db')
    arn_list_len = len(arn_list)
    ret_val = 'RDS found {} tagged Instances\n'.format(arn_list_len)

    run_time = bud_helper_util.delta_time(start_time)

    return data_frame


def check_for_untagged_rds_groups(session, region, tagging_client, summary_data_frame):
    """
    List all untagged RDS Groups resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    arn_list = get_tagged_resource_list(tagging_client, 'rds:cluster')
    arn_list_len = len(arn_list)
    ret_val = 'RDS Groups found {} tagged clusters\n'.format(arn_list_len)

    run_time = bud_helper_util.delta_time(start_time)

    return data_frame


def check_for_untagged_s3_buckets(session, region, tagging_client, summary_data_frame):
    """
    List all untagged S3 resources
    and estimate percent tagged resource of this type.
    :param session:  session to the AWS account.
    :param region: AWS Region:  us-east-1
    :param tagging_client: boto3 client for reading tags
    :param summary_data_frame: panda DataFrame to store summary information
    :return: text in SlackUI format with report values.
    """

    data_frame = init_standard_data_frame()
    start_time = bud_helper_util.start_timer()

    ret_val = "S3 check ..."
    try:
        s3_client = aws_util.get_s3_client(session, region)
        s3_bucket_name_list = []

        response = s3_client.list_buckets()
        all_s3_buckets = response['Buckets']
        for curr_bucket in all_s3_buckets:
            s3_bucket_name_list.append(curr_bucket['Name'])

        total_s3_buckets = len(s3_bucket_name_list)

        arn_list = get_tagged_resource_list_globally(session, 's3')
        normalize_s3_arn_list = normalize_s3_list(arn_list)
        arn_list_len = len(normalize_s3_arn_list)
        ret_val = 'S3 found {} tagged of {} total buckets\n'.format(arn_list_len, total_s3_buckets)

        untagged_set = set(s3_bucket_name_list).difference(set(normalize_s3_arn_list))

        untagged_set_len = len(untagged_set)
        if untagged_set_len > 0:
            ret_val = 'Found S3 {} untagged of {} total buckets\n'.format(untagged_set_len, total_s3_buckets)
            sorted_untagged_table_list = sorted(untagged_set)
            index = 0
            for curr_name in sorted_untagged_table_list:
                index += 1
                # ret_val += '    {}) {}\n'.format(index, curr_name)
                data_frame.loc[len(data_frame)] = [curr_name, 'n/a']
        else:
            ret_val = 'All {} S3 buckets tagged.\n'.format(total_s3_buckets)
            data_frame.loc[0] = [ret_val, 'n/a']

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        template = 'Failed during S3 phase. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))
        ret_val += 'Error during S3 phase. Check logs\n'
        data_frame.loc[0] = [ret_val, 'n/a']

    run_time = bud_helper_util.delta_time(start_time)
    append_summary_data(summary_data_frame, 's3', run_time, untagged_set_len, total_s3_buckets)

    return data_frame


def get_tagged_resource_list_globally(session, resource_type):
    """
    S3 is a global-ish service and needs to be treated differently.
    We need to get the tags for all the (likely) regions.
    :param session:
    :param resource_type:
    :return:
    """
    # Get tagging clients from several regions.
    tagging_client_us_east_1 = aws_util.get_tagging_client(session, 'us-east-1')
    tagging_client_us_east_2 = aws_util.get_tagging_client(session, 'us-east-2')
    tagging_client_us_west_2 = aws_util.get_tagging_client(session, 'us-west-2')
    tagging_client_us_west_1 = aws_util.get_tagging_client(session, 'us-west-1')
    tagging_client_ap_southeast_2 = aws_util.get_tagging_client(session, 'ap-southeast-2')
    tagging_client_eu_west_1 = aws_util.get_tagging_client(session, 'eu-west-1')

    arn_list_us_east_1 = get_tagged_resource_list(tagging_client_us_east_1, resource_type)
    arn_list_us_east_2 = get_tagged_resource_list(tagging_client_us_east_2, resource_type)
    arn_list_us_west_2 = get_tagged_resource_list(tagging_client_us_west_2, resource_type)
    arn_list_us_west_1 = get_tagged_resource_list(tagging_client_us_west_1, resource_type)
    arn_list_ap_southeast_2 = get_tagged_resource_list(tagging_client_ap_southeast_2, resource_type)
    arn_list_eu_west_1 = get_tagged_resource_list(tagging_client_eu_west_1, resource_type)

    arn_list = []
    arn_list.extend(arn_list_us_east_1)
    arn_list.extend(arn_list_us_east_2)
    arn_list.extend(arn_list_us_west_2)
    arn_list.extend(arn_list_us_west_1)
    arn_list.extend(arn_list_ap_southeast_2)
    arn_list.extend(arn_list_eu_west_1)

    print('{} found the following number of tagged items.\n'
          'us-east-1 {}, us-east-2 {}, us-west-2 {}, us-west-1 {},'
          'ap-southeast-2 {}, eu-west-1 {}'.format(resource_type, len(arn_list_us_east_1),
                                                   len(arn_list_us_east_2), len(arn_list_us_west_2),
                                                   len(arn_list_us_west_1), len(arn_list_ap_southeast_2),
                                                   len(arn_list_eu_west_1)))

    return arn_list


def get_tagged_resource_list(tagging_client, resource_type, get_more_list=None, pagination_token=None):
    """
    Use boto3 tagging client to get list of all resources that
    have the Spend_Category tag.
    :param tagging_client:
    :param resource_type: sting like: 'dynamodb:table'
    :param get_more_list: list passed only during pagination to hold current results.
    :param pagination_token: sting passed for recursive call only if previous result had pagination_token.
    :return: list of results.
    """
    if pagination_token is not None:
        list_len = len(get_more_list)
        print('PaginationToken={}'.format(pagination_token))
        print('Recursive call already has {} items in list'.format(list_len))
        arn_list = get_more_list
    else:
        arn_list = []

    try:
        if pagination_token:
            tagged_response = tagging_client.get_resources(
                PaginationToken=pagination_token,
                TagFilters=[{'Key': 'Spend_Category'}],
                ResourceTypeFilters=[resource_type]
            )
        else:
            tagged_response = tagging_client.get_resources(
                TagFilters=[{'Key': 'Spend_Category'}],
                ResourceTypeFilters=[resource_type]
            )

        resource_tag_mapping_list = tagged_response['ResourceTagMappingList']

        for curr_resource in resource_tag_mapping_list:
            curr_arn = curr_resource['ResourceARN']
            arn_list.append(curr_arn)

        if 'PaginationToken' in tagged_response:
            pagination_token = tagged_response['PaginationToken']
            if pagination_token:
                print('WARN tagging_client.get_resources() has more results: PaginationToken={}'.format(pagination_token))
                arn_list = get_tagged_resource_list(tagging_client, resource_type, arn_list, pagination_token)

    except Exception as ex:
        # Report back an error to the user, but ask to check logs.
        template = 'Failed during get_tagged_resource_list. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))

    return arn_list


def normalize_arn_list(arn_list):
    """
    Given a list of ARNs normalize the list by removing everything before the '\'
    :param arn_list: list or ARNs in the format 'arn:aws:dynamodb:us-east-1:123456789012:table/FeedGroups'
    :return: list normalized to look like 'FeedGroups'
    """
    normalize_list = []
    for curr_arn in arn_list:
        if '/' in curr_arn:
            curr_arn = curr_arn.split('/')[1]
        normalize_list.append(curr_arn)

    return normalize_list


def write_untagged_items(untagged_items_set, total_items_len, description):
    """
    Method to list all untagged items.
    :param untagged_items_set:
    :param total_items_len:
    :param description:
    :return:
    """
    ret_val = ''
    untagged_set_len = len(untagged_items_set)
    if untagged_set_len > 0:
        ret_val = 'Found {} untagged of {} total {}\n'\
            .format(untagged_set_len, total_items_len, description)
        sorted_untagged_table_list = sorted(untagged_items_set)
        index = 0
        for curr_name in sorted_untagged_table_list:
            index += 1
            ret_val += '    {}) {}\n'.format(index, curr_name)
    else:
        ret_val = 'All {} {} tagged.\n'.format(total_items_len, description)

    return ret_val


def normalize_elasticache_list(elasticache_list):
    """
    Need to convert this:
    arn:aws:elasticache:us-east-1:123456789012:cluster:recsys-b-20170525-0001-001
    into:
    recsys-b-20170525
    and eliminate duplicates.


    :param elasticache_list: Raw ARN with duplicates.
    :return: deduplicated list like: recsys-b-20170525
    """
    trimmed_list = []
    for curr_arn in elasticache_list:
        post_fix = curr_arn.rpartition(':')[2]
        element = post_fix.rpartition('-')[0]
        element = element.rpartition('-')[0]
        trimmed_list.append(element)
    ret_val = list(set(trimmed_list))
    return ret_val


def normalize_s3_list(s3_arn_list):
    """
    Need to convert:
    arn:aws:s3:::roku-downloader-123456789012
    into:
    roku-downloader-123456789012
    :param s3_arn_list:
    :return:
    """
    ret_val_list = []
    for curr_arn in s3_arn_list:
        post_fix = curr_arn.rpartition(':')[2]
        ret_val_list.append(post_fix)
    return ret_val_list


def get_type_from_args(args):
    """
    Parse the args parameters and return of string of types
    :param args:
    :return:
    """
    print('get_type_from_args() args={}'.format(args))
    if args.table is not None:
        return args.table
    return ''



# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_spend_main():
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