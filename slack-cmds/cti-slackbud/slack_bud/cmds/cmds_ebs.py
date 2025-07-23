"""Implements Ebs command by ekong"""
from __future__ import print_function
import traceback
import boto3
import os
import json
import requests

from pkg_resources import to_filename

import util.slack_ui_util as slack_ui_util
from util.slack_ui_util import ShowSlackError
import util.aws_util as aws_util
import util.bud_helper_util as bud_helper_util
from cmd_interface import CmdInterface
import util.cti_helper_util as cti_helper_util
import util.aws_account_info_util as aws_account_info_util
from datetime import datetime

class CmdEbs(CmdInterface):

    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'bill',
            'sub_commands': ['report', 'info', 'list'],
            'help_title': 'Finds and fixes unattached EBS volumes and generates a report.',
            'permission_level': 'dev',
            'props_report': self.get_report_properties(),
            'props_info': self.get_info_properties(),
            'props_list': self.get_list_properties()
        }
        return props

    def get_report_properties(self):
        """
        The properties for the "report" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`report`* _Generates a downloadable report of unattached EBS volumes_',
            'help_examples': [
                '/run ebs report -a sr-dev -r us-east-1 -d edmond -c spend_category -s stack'
            ],
            'switch-templates': [],
            #account and region switch might be optional depending on other filters
            #account and region (R). Other categories optional. No DRI
            #Either do account or DRI, not both. DRI is a lookup for multiple accounts
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            #have a default set of regions: [us-east-1, us-west-2, us-east-2, (OCCASIONAL), ireland, sydney]
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'AWS Region'
            },
            'switch-d': {
                'aliases': ['d', 'dri'],
                'type': 'string',
                'required': False,
                'lower_case': True,
                'help_text': 'DRI, entered as a username (e.g. Chat Godsay = cgodsay) or first name, case insensitive'
            },
            'switch-c': {
                'aliases': ['c', 'category'],
                'type': 'string',
                'required': False,
                'lower_case': False,
                'help_text': 'Spend Category'
            },
            'switch-s': {
                'aliases': ['s', 'stack'],
                'type': 'string',
                'required': False,
                'lower_case': False,
                'help_text': 'Stack'
            }
        }
        return props

    def invoke_report(self, cmd_inputs):
        """
        Placeholder for "report" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_report")
            arg_account = cmd_inputs.get_by_key('account')
            arg_region = cmd_inputs.get_by_key('region')
            arg_dri = cmd_inputs.get_by_key('dri')
            arg_category = cmd_inputs.get_by_key('category')
            arg_stack = cmd_inputs.get_by_key('stack')
            response_url = cmd_inputs.get_response_url()
            print("Trying to see if username is found")
            print(cmd_inputs.get_slack_user_name())
            print(cmd_inputs.get_slack_user_id())
    
            print("Done finding")
            print("Performing DRI lookup")
            lookup_dri(cmd_inputs.get_slack_user_id())
            print("ARG_REGION: {}, ARG_DRI: {}, ARG_CATEGORY, {}".format(arg_region,arg_dri,arg_category))
            # Start Report code section #### output to "text" & "title".
            #handle cases where someone uses DRI

            # Throw an error message if the following occur:
            # 1) DRI and account are specified
            # 2) Neither DRI or account specified
            # 3) Region specified, but no DRI or Account
            if (arg_account and arg_dri) or (not arg_dri and not arg_account):
                return self.slack_ui_standard_response("Error", "Please enter either an account or DRI, not both")
            else:
                #make a filter dictionary, with key values as a list of filter values
                filters = {}
                account_list = []
                if arg_dri:
                    filters['dri'] = list(set(arg_dri.split(',')))
                if arg_category:
                    filters['spend_category'] = list(set(arg_category.split(',')))
                if arg_stack:
                    filters['stack'] = list(set(arg_stack.split(',')))
                #regions not specified by user: default to us-east-1, us-west-1, us-east-2, us-west-2
                if not arg_region:
                    arg_region = 'us-east-1,us-west-1,us-east-2,us-west-2'
                #if accounts not specified
                #TODO: what if accounts not specified? lookup by DRI
                if arg_account:
                    account_list = arg_account.split(',')
                region_list = list(set(arg_region.split(',')))
                #only DRI specified
                #if someone uses DRI, need to find a way to locate their accounts. Call a service that could 
                #Assume the account list for the DRI service returns string of account names -> 'account1,account2,account3'
                if arg_dri:
                    dri_to_accounts_dict = find_dri_accounts()
                    #TODO: intermediate step of matching dri 'Chat', 'chat', 'cgodsay'
                    for dri in list(set(arg_dri.split(','))):
                        account_list += dri_to_accounts_dict[dri]
                        print("lookedup by DRI, here's account_list")

                slack = do_ebs_search(account_list, region_list, filters)
            # End Report code section. ####
            # Standard response below. Change title and text for output.
            title = "Report for Account: {} Region: {}".format(arg_account, arg_region)
            # return self.slack_ui_standard_response(title, text)
            return self.slack_ui_build_kit_response(slack)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")


    # def invoke_report2(self, cmd_inputs):
    #     """
    #     Placeholder for "report" sub-command
    #     :param cmd_inputs: class with input values.
    #     :return:
    #     """
    #     try:
    #         print("invoke_report")
    #         arg_account = cmd_inputs.get_by_key('account')
    #         arg_region = cmd_inputs.get_by_key('region')  #if specified, get in the form of a string: 'us-west-1,us-east-1'
    #         response_url = cmd_inputs.get_response_url()
        
    #         # Start Report code section #### output to "text" & "title".
    #         #handle cases where someone uses DRI
    #         #if someone uses DRI, need to find a way to locate their accounts. Call a service that could 
    #         #Assume the account list for the DRI service returns string of account names -> 'account1,account2,account3'
    #         text = do_ebs_search_for_region(arg_account, arg_region)

    #         #text = do_ebs_search(account, region, filters)
    #         # End Report code section. ####
        
    #         # Standard response below. Change title and text for output.
    #         title = "Report for Account: {} Region: {}".format(arg_account, arg_region)
    #         return self.slack_ui_standard_response(title, text)
    #     except ShowSlackError:
    #         raise
    #     except Exception as ex:
    #         bud_helper_util.log_traceback_exception(ex)
    #         raise ShowSlackError("Invalid request. See log for details.")

    def get_info_properties(self):
        """
        The properties for the "info" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`info`* _Retrieves information about a specific volume_',
            'help_examples': [
                '/run ebs info -a sr-dev -r us-east-1 -i vol-00000' 
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Region'
            },
            'switch-i': {
                'aliases': ['i', 'id'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Volume ID'
            }
        }
        return props

    def invoke_info(self, cmd_inputs):
        """
        Placeholder for "info" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_info")
            arg_account =  cmd_inputs.get_by_key('account')
            arg_region = cmd_inputs.get_by_key('region')
            arg_id = cmd_inputs.get_by_key('id')
            response_url = cmd_inputs.get_response_url()
        
            # Start Info code section #### output to "text" & "title".

            # End Info code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Account: {}, Region: {},  Volume: {}".format(arg_account, arg_region, arg_id)
            text = describe_single_volume(arg_account, arg_region, arg_id)
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_list_properties(self):
        """
        The properties for the "list" sub-command
        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`list`* _Returns a list of unattached EBS volumes_',
            'help_examples': [
                '/run ebs list -a sr-dev -r us-east-1'
            ],
            'switch-templates': [],
            'switch-a': {
                'aliases': ['a', 'account'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Account'
            },
            'switch-r': {
                'aliases': ['r', 'region'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'AWS Region'
            }
            #new switch to limit the number of entries returned?
        }
        return props

    def invoke_list(self, cmd_inputs):
        """
        Placeholder for "list" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_list")
            arg_account = cmd_inputs.get_by_key('account')  # remove if not used
            arg_region = cmd_inputs.get_by_key('region')  # remove if not used
            response_url = cmd_inputs.get_response_url()
        
            # Start List code section #### output to "text" & "title".
            account = aws_account_info_util.get_account_id_from_name(arg_account)
            session = cti_helper_util.create_security_auditor_session(account)

            # End List code section. ####
        
            # Standard response below. Change title and text for output.
            print("account name   ", arg_account, "   arg region  ", arg_region)
            title = "Listing unattached EBS Volumes for {} in {}".format(arg_account, arg_region)
            text = list_unattached_volumes(arg_account, arg_region)
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

def lookup_dri(slack_user):
    print("SLACK USER ", slack_user)
    temp = "AROAJNJENBX4X422VI3Q4"
    response = requests.get(url='https://slack.com/api/users.profile.get', headers={"Authorization": "bTSapM8aTH8fSgsKdrWG7aB4"}, params={"user": slack_user})
    response2 = requests.get(url='https://slack.com/api/users.profile.get', headers={"Authorization": "bTSapM8aTH8fSgsKdrWG7aB4"} ,params={"user": temp})
    print("REsponse 1")
    print(response.json())
    print("Response 2")
    print(response2.json())
    return response

def find_dri_accounts():
    """
    Looks up all the accounts associated with a list of DRIs
    :return: dictionary 
    """
    ##get DRI information
    s3_client = boto3.client('s3')
    s3_client.download_file('cti-image-server-bucket', 'forever/cost/dri.json', '/tmp/dri.json')
    dri_to_accounts = {}
    with open('/tmp/dri.json', 'r') as s:
        accounts_info= json.load(s)
    for account_id, attribs in accounts_info.items():
        dri = attribs['DRI User Name']
        if dri not in dri_to_accounts:
            dri_to_accounts[dri] = []
        else:
            try:
                dri_to_accounts[dri].append(attribs["Roku Account ID"])
            except:
                ShowSlackError("Error loading account list for DRI")
    print("Compiled dri account list ", dri_to_accounts)
    return dri_to_accounts


def get_volume_tag_value(tags, key):
    """
    Pull the key value from the tags on the EBS Volume if it exists. 
    If no key value is found or an error occurs then return a space since CSV column is output.
    """
    ret_val = ' '
    try:
        if tags:
            for curr_tag in tags:
                kv = curr_tag.get('Key')
                if kv==key:
                    ret_val = curr_tag.get('Value')
                    break
    except Exception as ex:
        print('get_volume_tag_value has error: {}'.format(ex))
    return ret_val


def parse_ebs_volume_response(response):
    """
    Parse the response of a describe_volumes call and return list string with results. 
    Uses filters such as Spend_Category, Stack
    Headers = 'DRI,Account,Spend_Category,Stack,Volume_Name,Size,Cost'
    """
    print('parse_ebs_volume_response')
    # ret_val = ['sort_key,volume_id,name,state,size,type,created,snapshot_id,comment']
    # ret_val = ['sort_key,DRI,Account,Spend_Category,Stack,Volume_Name,Volume_Id,Volume_Type,Size,Cost']
    ret_val = []
    error_count=0
    volumes = response['Volumes']
    for curr_volume in volumes:
        try:
            volume_id = curr_volume['VolumeId']
            create_time = curr_volume['CreateTime']
            size = curr_volume['Size']
            volume_type = curr_volume['VolumeType']

            tags = response.get('Tags')
            spend_category = get_volume_tag_value(tags, 'Spend_Category')
            stack = get_volume_tag_value(tags, 'Stack')
            volume_name = get_volume_tag_value(tags, 'Name')

            # value = '{},{},{},{},{},{},{},{}'.format(volume_id, volume_name, state, size, volume_type, create_time.date(), snapshot_id,'y/n')
            #TO-DO:
            #add a way to look for DRI
            #lookup account name by DRI?

            cost = 0
            value = '{},{},{},{},{},{},{},{},{}'.format('DRI_temp', 'account_temp', spend_category, stack, volume_name, volume_id, volume_type, size, cost)
            # create the sort key, so oldest and largest are first.
            digits_in_size = len(str(size))
            create_time_str = str(create_time.date())
            year_in_create_time = create_time_str.split('-')[0]
            sort_key = '{}-{}-{}-{}'.format(digits_in_size, size, year_in_create_time, create_time)
            item = '{}, {}'.format(sort_key, value)
            ret_val.append(item)
        except Exception as ex:
            error_count += 1
            print('Error: {}'.format(ex))
    print('num errors: {}'.format(error_count))
    print('list size: {}'.format(len(ret_val)))
    print("ret val from parse ebs volume response")
    return ret_val

# def get_all_unattached_volumes(ec2_client):
#     """
#     Get all unattached volumes even if need to pageinate.
#     Sort them by size and age. 4 digit sizes first, the 3 digit sizes then 2 digit sizes.
#     :param ec2_client: ec2_client object for the specific account and region
#     :return: list with oldest and largest unattached EBS volumes at top
#     """
#     unsorted_list = []
#     keep_going = True
#     loop_count = 0
#     next_token = None
#     while keep_going:
#         if not next_token:
#             response = ec2_client.describe_volumes(Filters=[],)
#             keep_going = False
#         else:
#             response = ec2_client.describe_volumes(Filters=[], NextToken=next_token)
#         print('parse_ebs_volume_response')    
#         list = parse_ebs_volume_response(response)
#         unsorted_list = unsorted_list + list
#         loop_count += 1
#         print('iteration #{}'.format(loop_count))
#         print('list size = {}'.format(len(list)))
#         if loop_count > 10:
#             keep_going = False
#     unsorted_list.sort(reverse=True)
#     print('# EBS volumes: {}'.format(len(unsorted_list)))
#     return unsorted_list


def get_all_unattached_volumes(ec2_client, filters):
    """
    Get all unattached volumes even if need to pageinate.
    Sort them by size and age. 4 digit sizes first, the 3 digit sizes then 2 digit sizes.
    :param ec2_client: ec2_client object for the specific account and region
    :param filters: dictionary containing key-value pairs of filter name and value
    :return: list with oldest and largest unattached EBS volumes at top
    """
    unsorted_list = []
    response = ec2_client.describe_volumes(Filters=filters,)
    parsed = parse_ebs_volume_response(response)

    return []


#  S3 copy this file into a bucket
def upload_to_s3(file_name):
    """
    Uploads a file to S3 bucket cti-image-server-bucket/month/ with the format 'unattached-ebs-{account}-{region}'.
    Deletes .csv files in /tmp after uploading to S3 to avoid entry duplicates in the case where the same 
    parameters are run within a short timeframe.
    :param file_name: string representing local filename to be uploaded to S3
    :return: string URL of S3 download link
    """
    path = '/tmp/{}'.format(file_name)
    bucket_name = 'cti-image-server-bucket'
    # aws_account = make_camel_case(arg_env)
    # aws_region = make_camel_case(arg_region)
    # path = '/home/ec2-user/SageMaker/{}'.format(file_name)
    file_path = 'month/unattached-ebs-{}'.format(file_name)
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(path, bucket_name, file_path)
    os.remove(path)
    link_to_report = 'http://internal-image-svc.eng.asnyder.com/static/{}'.format(file_path)
    return link_to_report

# def write_list_to_file(file_name, first_line=None, list=[]):
#     '''
#     Write the first line and a list to a file. 
#     '''
#     try:
#         full_path = '/tmp/{}'.format(file_name)
#         with open(full_path, 'a') as output_file:
#             if first_line:
#                 print('first: {}'.format(first_line))
#                 output_file.write(first_line+'\n')
#             for line in list:
#                 print('list: {}'.format(line))
#                 output_file.write(line+'\n')
#         return True
#     except Exception as e:
#         print('Failed to write file. Reason:{}'.format(e))

def write_list_to_file(file_name, headers, entries):
    '''
    Write the first line and a list to a csv file. 
    '''
    print("Writing to CSV.")
    print("Headers = ", headers)
    print("Entries: ", entries)
    try:
        full_path = '/tmp/{}'.format(file_name)
        with open(full_path, 'a') as output_file:
            output_file.write(headers+'\n')
            for line in entries:
                print('list: {}'.format(line))
                output_file.write(line+'\n')
        return True
    except Exception as e:
        print('Failed to write file. Reason:{}'.format(e))


def do_ebs_search(account_list, region_list, filters):
    """
    Retrieves unattached ebs volume information from CostEbsServiceVolumes
    :param account_list:
    :param region_name_list:
    :param filters: dict
    :return: text to be displayed in Slack UI
    """
    #run a report for every account
    #make a list that contains CSV entries for all accounts/regions
    headers = 'DRI,Account,Region,Spend,Stack,Volume_Name,Volume_ID,Size,Days_Unattached,Cost'
    write_to_csv_strings = []
    write_to_slack_dicts = []
    #table only accessible from cti, us-east-1
    session = cti_helper_util.create_security_auditor_session('cti')
    dynamo_client = aws_util.get_boto3_client_by_name('dynamodb', session, 'us-east-1')
    for account in account_list:
        # session = cti_helper_util.create_security_auditor_session(account)
        for region in region_list:
            print('starting: {} {}'.format(account, region))
            # dynamo_client = aws_util.get_boto3_client_by_name('dynamodb', session, region)
            account_id = aws_account_info_util.get_account_id_from_name(account)
            dynamo_primary_key = 'a#{}:{}r#{}'.format(account_id,account,region)
            print("DYNAMO KEY:  ", dynamo_primary_key)
            if len(filters) == 0:
                print("No filters")
                response = dynamo_client.query(
                    TableName = 'CostEbsServiceVolumes',
                    ProjectionExpression = 'SK, account, account_id, account_region, days_unattached, volume_name, volume_id, dri, dri_name, spend_category, stack, size',
                    KeyConditionExpression ='PK = :PK',
                    ExpressionAttributeValues = {
                        ':PK': {'S': dynamo_primary_key},
                    }
                )
            else:
                print("filters found: ", filters)
                filter_expression, expression_attribute_values = create_dynamo_args(filters)
                print("FilterExpression: ", filter_expression, " Expression Attribute Values:  ", expression_attribute_values)
                expression_attribute_values[':PK'] = {'S': dynamo_primary_key}
                response = dynamo_client.query(
                    TableName = 'CostEbsServiceVolumes',
                    ProjectionExpression = 'SK, account, account_id, account_region, days_unattached, volume_name, volume_id, dri, dri_name, spend_category, stack, size',
                    KeyConditionExpression ='PK = :PK',
                    FilterExpression = filter_expression,
                    ExpressionAttributeValues= expression_attribute_values
                )
            print("response from dynamodb", response)
            parsed_dict = parse_dynamo_response(response['Items'])
            write_to_csv_strings += parsed_dict['write_to_csv_strings']
            write_to_slack_dicts += parsed_dict['write_to_slack_dicts']
    #format of write_to_csv_list = [[cost1, csv_string1], [cost2, csv_string2], [cost3, csv_string3]]
    print("Finished ebs search, have this dict: ", parsed_dict)
    if len(write_to_csv_strings) == 0:
        return {}
    #sort the elements based on cost, then create new list without 0th cost key
    sorted_write_to_csv_strings = [elem[1] for elem in sorted(write_to_csv_strings, key=lambda x: x[0], reverse=True)]
    sorted_write_to_slack_dicts = [elem[1] for elem in sorted(write_to_slack_dicts, key=lambda x: x[0], reverse=True)]

    #timestamp for filename
    now = datetime.now()
    date_time = now.strftime("%b%d-%H%M")
    file_name = '{}-{}-{}.csv'.format('Test', 'File', date_time)
    print('writing file: {}'.format(file_name))
    write_list_to_file(file_name, headers=headers, entries=sorted_write_to_csv_strings)
    link_to_report = upload_to_s3(file_name)
    print("Uploaded to S3")

    #generate slack body
    slack_json = create_blockkit_payload(volumes=sorted_write_to_slack_dicts, filters=filters, download_link=link_to_report)
    print("Finished making JSON for Slack: ", slack_json)
    return slack_json


def create_dynamo_args(filters):
    '''
    :param filters: dictionary
    'spend_category', 'stack', 'dri'
    :return: filter_expression, expression_attribute_values
    (1) filter_expression = string of characters used by DynamoDB to filter query results before they are returned
        Example: 
        Given a set of filters:
            filters = {
                'stack': ['stack_filter_1', 'stack_filter_2'],
                'spend_category': ['spend_filter_1']
            }
        - Individual filters values will be joined by OR:
            - 'contains (stack, :var1) OR contains (stack, :var2)'
            - 'contains (spend_category, :var3)'
        - where contains(attribute, placeholder) checks for the attribute in the DynamoDB table and the placeholder's value is declared in the
          expression_attribute_values dictionary(2)
        - Individual filter value strings are then joined with other filter value strings with AND
        - Filter expression to be returned is '(contains (spend_category, var1) OR contains (spend_category, var2)) AND contains (spend_category, var3)'
    (2) expression_attribute_values = dictionary that contains one or more values that can be substituted in the filter expression
        Example:
        expression_attribute_values = {
            'var1: {'S': 'stack_filter_1'},
            'var2: {'S': 'stack_filter_2'},
            'var1: {'S': 'spend_filter_1'},
        }
        - Three arbitrary, but unique, placeholder variables are defined for the filter values (var1, var2, var3)
    '''
    expression_attribute_values = {}
    ind = 1
    to_join_by_and = []
    for filter_type, filter_vals in filters.items():
        to_join_by_or = []
        for val in filter_vals:
            temp_var = ':var{}'.format(str(ind))
            ind += 1
            s = 'contains ({}, {})'.format(filter_type, temp_var)
            expression_attribute_values[temp_var] = {'S': val}
            to_join_by_or.append(s)
        joined_with_or = ' OR '.join(to_join_by_or)
        filter_string = '( {} )'.format(joined_with_or)
        to_join_by_and.append(filter_string)
    filter_expression = ' AND '.join(to_join_by_and)
    print("finished creating  dynamo args", filter_expression, expression_attribute_values)
    return filter_expression, expression_attribute_values


def parse_dynamo_response(response):
    '''
    Formats the items retrieved from a DynamoDB response
    :param response: List containing dictionaries representing DynamoDB rows. Each of these dictionaries has DynamoDB attributes as keys,
    mapped to a dictionary containing the type and value of the attribute
        Example:
        [
            {
                'spend_category': {'S': 'Voice'}, 
                'volume_name': {'S': 'praful-asr-dev'},
                'stack': {'S': 'Voice'}, 
                'SK': {'S': '10010.496'}, 
                'days_unattached': {'N': '17'}, 
                'dri': {'S': 'sriise'}, 
            },
        ]
    DynamoDB attributes to search for:
    - account: name of account
    - account_id: AWS ID of account
    - account_region: 
    - SK: sort key of Dynamo table. Represents monthly EBS cost
    - dri_name: first name and last name of the account DRI
    - stack: stack tag of volume
    - spend_category: spend category tag of volume
    - volume_id
    - volume_name
    - days_unattached
    :return:
        Dictionary containing two nested lists that have have the cost(SK) as the 0th element, to be used as a sorting key, and:
        1) string to write to csv: 'cost,account,account_id,account_region,volume_name,volume_id,days_unattached,dri,stack,spend_category,size'
        2) dictionary containing attributes to display to slack: cost, account, account_id, account_region, ..., ... ,... ,..., ..., spend_category, size
    '''
    ret_dict = {'write_to_csv_strings': [], 'write_to_slack_dicts': []}
    attributes = ['account', 'account_id', 'account_region', 'SK', 'dri_name','stack','spend_category', 'size', 'volume_name', 'volume_id', 'days_unattached']

    for dynamo_row in response:
        print("Looking at this Dynamo Row: ", dynamo_row)
        #create a dictionary to store attributes and their values, as retrieved from DynamoDB table
        tdict = {}
        for attribute in attributes:
            print("Looking for attribute: ", attribute)
            attribute_dict= dynamo_row.get(attribute)
            print("This is attribute dict: ", attribute_dict)
            attr_type, attr_val = list(attribute_dict.items())[0]
            tdict[attribute] = attr_val
        print(tdict, " Done with row")
        csv_string = "{},{},{},{},{},{},{},{},{},{}".format(tdict['dri_name'],tdict['account'], tdict['account_region'],tdict['spend_category'],tdict['stack'],
                                            tdict['volume_name'],tdict['volume_id'], tdict['size'], tdict['days_unattached'], tdict['SK'])
        # display_to_slack_list = [tdict['dri_name'], tdict['account'], tdict['account_region'], tdict['spend_category'], tdict['stack'], 
        #                         tdict['volume_name'], tdict['volume_id'], tdict['size'], tdict['days_unattached'], tdict['SK']]
        cost_and_csv_list = [float(tdict['SK']), csv_string]
        cost_and_display_to_slack_dict = [float(tdict['SK']), tdict]
        ret_dict['write_to_csv_strings'].append(cost_and_csv_list)
        ret_dict['write_to_slack_dicts'].append(cost_and_display_to_slack_dict)
    return ret_dict

def create_blockkit_payload(volumes, filters, download_link):
    '''
    Creates payload (dict) for Slack Block Kit
    '''
    filter_string = 'No filters'
    if filters:
        filter_strings = ["{}={} ".format(key, val) for key, val in filters.items()]
        filter_string = ', '.join(filter_strings)
    print("This is the filter string ", filter_string)
    payload = {
        "blocks": []
    }
    #title section
    title = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "_*Found*_: {} volumes. _*Filters*_: {}".format(len(volumes), filter_string)
        }
    }
    #download link and top 5 description text section
    volumes_to_display = min(5, len(volumes))
    download_section = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "Showing *{}* of *{}* results".format(volumes_to_display, len(volumes))
        },
        "accessory": {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": "Download full report"
            },
            "url": download_link
        }
    }
    payload["blocks"].append(title)
    payload["blocks"].append(download_section)
    payload["blocks"].append({"type": "divider"})
    i = 0
    while i < volumes_to_display:
        current_vol = volumes[i]
        #make content
        entry_body = {
            "type": "section",
            "fields": []
        }
        entry_body["fields"].append({"type": "mrkdwn", "text": "*{}) Volume ID: {}*".format(i+1, current_vol['volume_id'])})
        entry_body["fields"].append({"type": "mrkdwn", "text": "*Cost: ${}* ".format(round(float(current_vol['SK']),2))})
        entry_body["fields"].append({"type": "plain_text","text": "DRI: {}".format(current_vol['dri_name'])})
        entry_body["fields"].append({"type": "plain_text","text": "Account: {}".format(current_vol['account'])})
        entry_body["fields"].append({"type": "plain_text","text": "Region: {}".format(current_vol['account_region'])})
        entry_body["fields"].append({"type": "plain_text","text": "Spend Category: {}".format(current_vol['spend_category'])})
        entry_body["fields"].append({"type": "plain_text","text": "Stack: {}".format(current_vol['stack'])})
        entry_body["fields"].append({"type": "plain_text","text": "Volume Name: {}".format(current_vol['volume_name'])})
        entry_body["fields"].append({"type": "plain_text","text": "Size: {}".format(current_vol['size'])})
        entry_body["fields"].append({"type": "plain_text","text": "Days Unattached: {}".format(current_vol['days_unattached'])})

        payload["blocks"].append(entry_body)
        payload["blocks"].append({"type": "divider"})
        
        i += 1

    #add bottom download button
    # download_button = {
    #     "type": "actions",
    #     "elements": [
    #         {
    #             "type": "button",
    #             "text": {
    #                 "type": "plain_text",
    #                 "text": "Download full report"
    #             },
    #             "url": download_link
    #         }
    #     ]
    # }
    # payload["blocks"].append(download_button)
    return payload

def describe_single_volume(account, region, volume_id):
    text = ""
    session = cti_helper_util.create_security_auditor_session(account)
    ec2 = aws_util.get_boto3_client_by_name('ec2', session, region)
    response = ec2.describe_volumes(
        Filters=[
            {'Name': 'volume-id', 'Values': [volume_id]}
        ]
    )
    parsed = parse_ebs_volume_response(response)
    p1 = 0
    p2 = 0
    cols = parsed[0].split(',')
    vals = parsed[1].split(',')
    for _ in range(len(cols)):
        text += "{}: {} \n".format(cols[p1], vals[p2])
        p1 += 1
        p2 += 1
    return text


def list_unattached_volumes(account, region):
    text = ''
    session = cti_helper_util.create_security_auditor_session(account)
    ec2_client = aws_util.get_boto3_client_by_name('ec2', session, region)
    ebs_volume_list = get_all_unattached_volumes(ec2_client, [])
    if len(ebs_volume_list) > 1:
        text += '*Found {} unattached ebs volumes in {} {}*\n'.format(len(ebs_volume_list)-1, account, region)
        ind = len(ebs_volume_list[1].split(','))
        val_index = 1
        for _ in range(1, len(ebs_volume_list)):
            text += "*Volume {}*\n".format(val_index)
            inner_cols = 0
            inner_data = 0
            cols = ebs_volume_list[0].split(',')
            data = ebs_volume_list[val_index].split(',')
            for _ in range(ind):
                text += "{}: {} \n".format(cols[inner_cols], data[inner_data])
                inner_cols += 1
                inner_data += 1
            val_index += 1
        return text
    else:
        text += 'No unattached ebs volumes found'


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."

def test_cases_cmd_ebs_main():
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