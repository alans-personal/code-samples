"""
A temporary file that takes the ../slack_bud directory, zips it up and the
pushes that zip file into the SlackBud pipeline deployment bucket.
"""
import os
import shutil
import time
import datetime
import boto3


def zip_slack_bud_dir():
    """
    Zip the files in the ../slack_bud directory.
    :return:
    """
    archive_name = os.path.expanduser(os.path.join('..', 'slack-bud-bare-repo-files'))
    if os.environ.get('GITPATH'):
        root_dir = os.path.expanduser(os.path.join(os.environ.get('GITPATH'),'cti-slackbud'))
    else:
        root_dir = os.path.expanduser(os.path.join('~', 'git', 'cti-slackbud'))
    base_dir = os.path.expanduser(os.path.join('slack_bud'))

    print('archive: {}'.format(archive_name))
    print('root dir: {}'.format(root_dir))
    print('base dir: {}'.format(base_dir))

    shutil.make_archive(archive_name, 'zip', root_dir, base_dir)
    print("Zipped directory.")


def upload_zip_to_s3():
    """
    Upload the zip file to S3
    :return:
    """

    # print file size.
    file_size_bytes = os.path.getsize('../slack-bud-bare-repo-files.zip')
    print('Zip file size: {}'.format(file_size_bytes))

    # data = open('../slack-bud-bare-repo-files.zip')  # delete line.
    os.system('aws s3 cp ../slack-bud-bare-repo-files.zip s3://cti-pipeline-source/slack-bud-bare-repo-files.zip --profile CTI-Admin')
    print("Moved zip file to bucket.")


def delete_zip_file():
    """
    Delete the zip file if it exists.
    :return:
    """
    zip_file_path = '../slack-bud-bare-repo-files.zip'
    if os.path.exists(zip_file_path):
        os.remove(zip_file_path)
        print("Removed zip file.")
    else:
        print("Didn't find zip file.")


# def update_build_info_file():
#     """
#     Below is what a build_info file looks like.
#     Modify it, so the version command displays something different.
#
#         build_time: May 09, 2018 - 14:54:27
#         version: slackbud-master-abcdefgh-20180509-1
#         mail: asnyder@roku.com
#         commit: abcdefghijklmnopqrstuvwxyz0123456789abcd
#     :return:
#     """
#     with open('temp_build_info.txt') as f:
#         content = f.readlines()
#     # strip whitespace.
#     content = [x.strip() for x in content]
#
#     # turn contents into dictionary for easy update.
#     build_info_map = {}
#     for curr_line in content:
#         kv = curr_line.split(':')
#         if len(kv) == 2:
#             key = kv[0]
#             value = kv[1]
#             build_info_map[key] = value
#             print('added: {}={}'.format(key, value))
#
#     # start write to file.
#     with open('temp_build_info.txt', 'w') as output:
#         # increment the date and build number.
#         build_time = create_build_time_line()
#         output.write('build_time: {}\n'.format(build_time))
#
#         # put in fixed values here, until we update this later.
#         curr_version = build_info_map['version']
#         version = update_version_line(curr_version)
#         output.write('version: {}\n'.format(version))
#
#         # Some fixed stuff that needs to be updated later.
#         output.write('mail: asnyder@roku.com\n')
#         output.write('commit: abcdefghijklmnopqrstuvwxyz0123456789abcd\n')
#
#
# def create_build_time_line():
#     """
#     Create build time string in format:
#     May 09, 2018 - 14:54:27
#     :return: string
#     """
#     ret_val = datetime.datetime.now().strftime('%b %d, %Y - %H:%M:%S')
#     print('Build time: {}'.format(ret_val))
#     return ret_val
#
#
# def update_version_line(curr_version):
#     """
#     Update the version string.
#     :param curr_version:
#     :return: string
#     """
#     date_str = datetime.datetime.now().strftime('%Y%m%d')
#     curr_build_num = curr_version.split('-')[-1]
#     print('curr_build_num = {}'.format(curr_build_num))
#     new_build_num = int(curr_build_num)+1
#     print('new_build_number = {}'.format(new_build_num))
#
#     ret_val = 'slackbud-master-{}-{}'.format(date_str,new_build_num)
#     print('New build string: {}'.format(ret_val))
#
#     return ret_val
#
#
# def download_build_info_file():
#     """
#     Download the build_info.txt file to a temp location to update.
#     :return:
#     """
#     os.system('aws s3 cp s3://cti-pipeline-source/build_info.txt temp_build_info.txt --profile CTI-Admin')
#
#
# def upload_build_info_file():
#     """
#     Upload and then delete the build_info.txt file if successful.
#     :return:
#     """
#     os.system('aws s3 cp temp_build_info.txt s3://cti-pipeline-source/build_info.txt --profile CTI-Admin')
#     if os.path.exists('temp_build_info.txt'):
#         print('deleting temp_build_info.txt')
#     else:
#         print('could not find: temp_build_info.txt')


def update_githook_info_file(commit):
    """
    Below is what a githook_info file looks like.
    Modify it, so the version command displays something different.

        build_time: May 09, 2018 - 14:54:27
        version: slackbud-master-abcdefgh-20180509-1
        mail: asnyder@roku.com
        commit: abcdefghijklmnopqrstuvwxyz0123456789abcd
    :return:
    """
    print('update_githook_info_file')
    if commit:
        print('Using commit: _{}_'.format(commit))

    if not os._exists('temp_githook_info.txt'):
        print('Creating temp_githook_info.txt')
        os.system('touch temp_githook_info.txt')


    with open('temp_githook_info.txt') as f:
        content = f.readlines()
    # strip whitespace.
    content = [x.strip() for x in content]

    # turn contents into dictionary for easy update.
    githook_info_map = {}
    githook_key_list = []
    for curr_line in content:
        kv = curr_line.split('=')
        if len(kv) == 2:
            key = kv[0]
            value = kv[1]
            if key == 'BUILD_NUMBER':
                int_value = int(value)
                value = int_value+1

            githook_info_map[key] = value
            githook_key_list.append(key)
            print('added: {}={}'.format(key, value))

    # replace commit key if present
    if commit:
        githook_info_map['commit'] = commit
        githook_info_map['gitlabAfter'] = commit
        githook_info_map['gitlabBefore'] = commit
        githook_info_map['gitlabMergeRequestLastCommit'] = commit

    print('githook_info_map={}'.format(githook_info_map))

    # write to file.
    with open('temp_githook_info.txt', 'w') as output:
        # write to file.
        for curr_key in githook_key_list:
            curr_value = githook_info_map.get(curr_key)
            line = '{}={}\n'.format(curr_key, curr_value)
            output.write(line)
            print(line)


def get_latest_git_info():
    """
    Parse the result of `git log` to get the latest information.
    :return:
    """
    git_log = os.popen('git log | head -6').read()

    # Parse below output.
    # --
    # commit 37d057d0bd50ebbb37c9ff903702758b2630dfea
    # Author: Alan Snyder <asnyder@roku.com>
    # Date:   Wed Nov 21 13:33:57 2018 - 0800
    #
    # CTDEVOPS - 783: Deal with case of no service found in UI
    #

    commit = os.popen('git log | head -6').read()
    if commit.startswith('commit '):
        commit = commit.replace('commit ', '')

    print('commit={}'.format(commit))
    print('git_log={}'.format(git_log))

    return commit


def download_githook_info_file():
    """
    Download the githool_info.txt file to a temp location to update.
    :return:
    """
    os.system('aws s3 cp s3://cti-pipeline-source/githook_info.txt temp_githook_info.txt --profile CTI-Admin')


def upload_githook_info_file():
    """
    Upload and then delete the githook_info.txt file if successful.
    :return:
    """

    if os.path.exists('temp_githook_info.txt'):
        os.system(
            'aws s3 cp temp_githook_info.txt s3://cti-pipeline-source/githook_info.txt --profile CTI-Admin')
        print('deleting temp_githook_info.txt')
        os.remove('temp_githook_info.txt')
    else:
        print('could not find: temp_githook_info.txt')


if __name__ == '__main__':
    #  from AWS CodeBuild during build stage
    try:
        zip_slack_bud_dir()
        # download_build_info_file()
        # update_build_info_file()
        download_githook_info_file()
        commit = get_latest_git_info()
        update_githook_info_file(commit)
        upload_zip_to_s3()
        # upload_build_info_file()
        upload_githook_info_file()
        delete_zip_file()
        print('Done')
    except Exception as ex:
        print('Exception: {}'.format(ex))
        delete_zip_file()
