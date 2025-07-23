import boto3
import mysql.connector
import string
import random
import threading
import logging
import traceback

select_accounts = """
    SELECT account, security_role FROM roku_aws_accounts;
    """

regions = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2',
    'ca-central-1',
    #'cn-north-1',
    'ap-south-1',
    'ap-northeast-2',
    'ap-southeast-1',
    'ap-southeast-2',
    'ap-northeast-1',
    'eu-central-1',
    'eu-west-1',
    'eu-west-2',
    'eu-west-3',
    'sa-east-1'
]

regions_us = [
    'us-east-1',
    'us-east-2',
    'us-west-1',
    'us-west-2'
]

class AWSAccountHelper:

    @staticmethod
    def get_accounts_info_test(cnx):
        account_info = []
        acct_entry = {}
        acct_entry['AccountID'] = '018405429474'
        #acct_entry['SecurityRole'] = 'arn:aws:iam::018405429474:role/ctipoke'
        acct_entry['SecurityRole'] = ''
        account_info.append(acct_entry)

        return account_info

    @staticmethod
    def get_accounts_info(cnx):
        """Collects ROKU account info from database."""
        cursor = cnx.cursor()
        cursor.execute(select_accounts)
        account_info = []
        for acct in cursor:
            acct_entry = {}
            acct_entry['AccountID'] = acct[0]
            acct_entry['SecurityRole'] = acct[1]
            account_info.append(acct_entry)

        return account_info

    @staticmethod
    def get_regions():
        return regions

    @staticmethod
    def get_regions_us():
        return regions_us


    @staticmethod
    def get_aws_client(client_type, account_info, aws_credentials, region=None):
        sts_client = boto3.client("sts",
                                  aws_access_key_id=aws_credentials['keyid'],
                                  aws_secret_access_key=aws_credentials['key'])
        account_id = account_info['AccountID']
        arn = account_info.get('SecurityRole', '')
        if (arn != ''):
            try:
                role = sts_client.assume_role(
                    RoleArn=arn,
                    RoleSessionName="default",
                    DurationSeconds=3600
                )
            except Exception as e:
                logging.error(arn, e)
                raise Exception("failed to switch AWS role.")

            credentials = role["Credentials"]

            session = boto3.session.Session(
                aws_access_key_id=credentials["AccessKeyId"],
                aws_secret_access_key=credentials["SecretAccessKey"],
                aws_session_token=credentials["SessionToken"]
            )

            if (region == None):
                aws_client = session.client(client_type)
            else:
                aws_client = session.client(client_type, region_name=region)
        else:
            if (region == None):
                aws_client = boto3.client(client_type,
                                          aws_access_key_id=aws_credentials['keyid'],
                                          aws_secret_access_key=aws_credentials['key'])
            else:
                aws_client = boto3.client(client_type, region_name=region,
                                          aws_access_key_id=aws_credentials['keyid'],
                                          aws_secret_access_key=aws_credentials['key'])

        return aws_client
