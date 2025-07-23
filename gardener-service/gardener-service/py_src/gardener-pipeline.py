"""
Python code to work the Code Pipeline.
"""
from __future__ import print_function

import json

import json
import urllib
import os
import base64
import datetime
import requests
import traceback
import boto3
import util.garden_helper_util as bud_helper_util
import util.aws_util as aws_util
from util.aws_util import CodePipelineStageError


def lambda_deploy_handler(event, context):
    """
    Deploy the garden lambda function to either dev or prod lambdas.
    :param event:
    :param context:
    :return:
    """
    print("Received event: " + json.dumps(event))
    start_time = datetime.datetime.now()

    job_id = event['CodePipeline.job']['id']
    print('CodePipeline JobID=%s' % job_id)
    deploy_stage = event['CodePipeline.job']['data']['actionConfiguration']['configuration']['UserParameters']

    print("UserParameter - deploy_stage=%s" % deploy_stage)

    s3bucket = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['bucketName']
    s3key = event['CodePipeline.job']['data']['inputArtifacts'][0]['location']['s3Location']['objectKey']

    print("s3bucket = %s" % s3bucket)
    print("s3key = %s" % s3key)

    cp_client = boto3.client('codepipeline')
    try:
        print("deploy_stage = %s" % deploy_stage)

        if deploy_stage == 'dev':

            update_lambda_function_code(
                'gardener-api-dev',
                s3bucket, s3key, True
            )
            bud_helper_util.print_delta_time(
                start_time, 'Finished: gardener-api-dev')

            update_lambda_function_code(
                'gardener-pipeline-deploy-prod',
                s3bucket, s3key
            )
            bud_helper_util.print_delta_time(
                start_time, 'Finished: gardener-pipeline-deploy-prod')

            update_lambda_function_code(
                'gardener-pipeline-deploy-dev',
                s3bucket, s3key
            )
            bud_helper_util.print_delta_time(
                start_time, 'Finished: gardener-pipeline-deploy-dev')

        elif deploy_stage == 'prod':
            # ToDo update this section when deploying to prod.
            update_lambda_function_code(
                'gardener-api',
                s3bucket, s3key, True
            )
            bud_helper_util.print_delta_time(
                start_time, 'Finished: gardener-pipeline-deploy-prod')

        else:
            error_msg = "Unknown deploy stage. Expected 'dev'|'prod'. Was %s."\
                        % deploy_stage
            raise CodePipelineStageError(error_msg)

        cp_client.put_job_success_result(
            jobId=job_id,
        )

        bud_helper_util.print_delta_time(
            start_time, 'Sent stage success result.')

        # Look inside the zip file to get the build_info.txt
        unzip_dir = '/tmp/deployed'
        upload_and_unzip_source_code(s3bucket, s3key, unzip_dir)

        bud_helper_util.print_delta_time(
            start_time, 'upload_and_unzip_source_code')

        extra_build_info = get_build_info_from_zip(unzip_dir)

        bud_helper_util.print_delta_time(
            start_time, 'get_build_info_from_zip')

        slack_msg_text = "Deployed Gardener-API to %s" % deploy_stage
        if extra_build_info is not None:
            slack_msg_text += '\nversion: %s' % extra_build_info

        # Put a success message on a Slack Channel
        post_message_to_slack_channel(
            title="Deployment",
            text=slack_msg_text
        )

        bud_helper_util.print_delta_time(
            start_time, 'Sent success message to Slack deploy channel')

    except CodePipelineStageError as ex:
        error_msg = 'FAILED Stage! reason %s' % ex.message
        print(error_msg)
        cp_client.put_job_failure_result(
            jobId=job_id,
            failureDetails={
                'type': 'JobFailed',
                'message': error_msg
            }
        )
        # Put a message about deployment failure
        post_message_to_slack_channel(
            title='Failed deployment',
            text=error_msg,
            color='#ff3d3d'
        )
    except Exception as e:
        error_msg = 'FAILED Stage! reason: %s' % e.message
        print(error_msg)
        cp_client.put_job_failure_result(
            jobId=job_id,
            failureDetails={
                'type': 'JobFailed',
                'message': error_msg
            }
        )
        # Put a message about deployment failure
        post_message_to_slack_channel(
            title='General error',
            text=error_msg,
            color='#ff3d3d'
        )

        bud_helper_util.print_delta_time(
            start_time, 'Done')

    return 'done'


def update_lambda_function_code(function_name, s3_bucket, s3_key,
                                fail_stage_on_error=False):
    """Update code but handle and report errors gracefully"""
    try:
        print('Updating code for lambda function: %s' % function_name)
        lambda_client = boto3.client('lambda')

        # BELOW check is OPTIONAL. Skipping.
        # Check for lambda function name, to verify it exists.
        # print("Verify lambda function {} exists.".format(function_name))
        # list_function_response = lambda_client.list_functions(
        #     MasterRegion='us-west-2',
        #     FunctionVersion='$LATEST'
        # )
        # while True:
        #     if found_lambda_function(list_function_response, function_name):
        #         print("Found: {}".format(function_name))
        #         break
        #     else:
        #         print("Didn't find: {}. Looking for paginated response".format(function_name))
        #         if list_function_response['NextMarker']:
        #             print("NextMarker={}".format(list_function_response['NextMarker']))
        #             list_function_response = lambda_client.list_functions(
        #                 MasterRegion='us-west-2',
        #                 Marker=list_function_response['NextMarker']
        #             )

        response = lambda_client.update_function_code(
            FunctionName=function_name,
            S3Bucket=s3_bucket,
            S3Key=s3_key
        )

        # If status code is 200 return success.
        status_code = response['ResponseMetadata']['HTTPStatusCode']
        if status_code == 200:
            print('Deployed function: {}'.format(function_name))
        else:
            print('FAILED to deploy function: %s' % function_name)
            print('Status Code: %s' % status_code)
            print('Response: %s' % json.dumps(response))
            if fail_stage_on_error:
                error_log = 'Failed to update function %s. Check logs'\
                            % function_name
                raise CodePipelineStageError(error_log)
        return response

    except Exception as ex:
        error_log = 'Failed to update function %s. Reason: %s'\
                    % (function_name, ex)
        if fail_stage_on_error:
            raise CodePipelineStageError(error_log)
        else:
            print(error_log)


def upload_and_unzip_source_code(
        s3bucket, s3key,
        unzip_dir='/tmp/deployed'):
    """
    Get the source code zip file and unzip is locally with
    the specified name and directory.
    :param s3bucket: Source S3 bucket.
    :param s3key: Source S3 object key.
    :param unzip_dir: Local lambda directory to unzip
    :return: None. Let any exceptions be thrown
    """
    dest_zip_file_path = unzip_dir+'.zip'
    s3_client = boto3.client('s3')
    s3_client.download_file(
        s3bucket,
        s3key,
        dest_zip_file_path
    )
    bud_helper_util.unzip_file(dest_zip_file_path, unzip_dir)


def get_build_info_from_zip(unzip_dir):
    """
    After calling 'unload_and_unzip_source_code' function
    Call this method to read the 'build_info.txt' file in
    the unzip directory.
    :param unzip_dir: unzip directory like '/tmp/deployed'
    :return: version string like 'slackbud-master-ca16386f-20180216-373'
    """
    # """Get the build info from the zip file.
    # Handle errors by logging and returning None"""
    try:
        txt_files = bud_helper_util.get_files_in_dir_by_type(
            unzip_dir, 'txt'
        )

        if len(txt_files) > 0:
            build_info_file_path = unzip_dir+'/build_info.txt'
            build_info_map =\
                bud_helper_util.read_key_value_file_to_dictionary(
                    build_info_file_path,
                    ': '
                )
            version = build_info_map['version']
            if version is not None:
                return version
            else:
                print("Failed to find version in build_info.txt file.")
        else:
            print("Didn't find build_info.txt")

    except Exception as ex:
        print('Failed to get build info from zip. Reason %s' % ex.message)


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
    url = "https://hooks.slack.com/services/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"
    res = requests.post(
        url=url,
        data=json.dumps(slack_message),
        headers={"Content-type": "application/json"}
    )
    print('Slack status code: {}'.format(res.status_code))


def create_build_info_file():
    """Create a build_info file"""

    print('Start create_build_info_file()')
    for curr_file in os.listdir("."):
        print(os.path.join(".", curr_file))

    try:
        # Write the build_info.txt file.
        build_info_file = open("build_info.txt", "w")

        build_time = aws_util.get_prop_table_time_format()
        build_info_file.write("build_time: %s" % build_time)

        # Include the githook information.
        if os.path.isfile('githook_info.txt'):
            githook_file = open('githook_info.txt', 'r')
            lines = githook_file.readlines()
            build_map = {}
            build_map['date'] = aws_util.get_build_info_time_format()
            for line in lines:
                part = line.split('=')
                key = part[0].strip()
                value = part[1].strip()
                if key == 'gitlabAfter':
                    build_map['commit'] = value.strip()
                if key == 'gitlabUserEmail':
                    build_map['mail'] = value.strip()
                if key == 'gitlabBranch':
                    build_map['branch'] = value.strip()
                if key == 'BUILD_NUMBER':
                    build_map['build'] = value.strip()
            commit = build_map['commit']
            short_commit = commit[:8]
            version = ('slackbud-%s-%s-%s-%s' %
                       (build_map['branch'], short_commit,
                        build_map['date'], build_map['build'])
            )
            build_info_file.write('\nversion: %s' % version)
            build_info_file.write('\nmail: %s' % build_map['mail'])
            build_info_file.write('\ncommit: %s' % build_map['commit'])
        else:
            print("Didn't find githook file. Skipping githook step.")

        build_info_file.close()

    except Exception as ex:
        print("Could not write build_info.txt file.")
        print("Reason: %s" % ex)


if __name__ == '__main__':
    #  from AWS CodeBuild during build stage
    create_build_info_file()