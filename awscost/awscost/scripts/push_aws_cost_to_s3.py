"""
Zip ../py_src and push it into the pipeline to be deployed to lambda
"""
import os
import shutil
import pendulum

ZIP_BASE_DIR = os.path.expanduser(os.path.join('~', 'git', 'awscost', 'zip_code'))
ROOT_DIR = os.path.expanduser(os.path.join('~', 'git', 'awscost'))

# These values need to be in sync with gardener-py-service.stack.yaml file.
# arn:aws:s3:::gardener-pipeline-source/gardener-lambda-bare-repo-files.zip
SOURCE_S3_BUCKET = 'awscost-pipeline-source'
BARE_CODE_FILE_NAME = 'awscost-bare-repo-files.zip'


def create_temp_zip_directory():
    """

    :return:
    """
    print('create_temp_zip_directory')
    temp_sub_dirs = os.path.join(ZIP_BASE_DIR)

    if not os.path.exists(temp_sub_dirs):
        print('Creating dir: {}'.format(temp_sub_dirs))
        os.makedirs(temp_sub_dirs)


def move_src_files():
    """

    :return:
    """
    print('move_src_files')
    source_code_dir = os.path.expanduser(os.path.join(ROOT_DIR, 'py_src'))
    dest_code_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'py_src'))

    shutil.copytree(source_code_dir, dest_code_dir)




def update_aws_cost_version():
    """

    :return: string version
    """
    return '12345678-master-20181107-2'


def replace_build_time_string():
    """
    Find code file. awscost_helper_util.py,
    replace string: {#build_time_string#}
    with: YYYYMMDD_HHMM
    example 20181210_1405

    If we fail to find the file or replace it just continue with a
    printed warning.
    :return:
    """
    try:
        curr_time = get_time_in_build_format()
        print("Build Time: {}".format(curr_time))
        zip_code_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'py_src/util'))
        with open(zip_code_dir+'/awscost_helper_util.py', "r+") as f:
            original_file = f.read()
            replaced_file = original_file.replace('{#build_time_string#}', curr_time)
            f.seek(0)
            f.write(replaced_file)
            f.truncate()
            f.close()

        print("Replaced build time")

    except Exception as ex:
        print("WARN: Failed to replace '{#build_time_string#}' string")


def create_build_info_file(aws_cost_version):
    """

    :param aws_cost_version:
    :return:
    """
    print('create_build_info_file')


def zip_temp_code_dir():
    """

    :return:
    """
    print('zip_temp_code_dir')

    archive_name = os.path.expanduser(os.path.join('..', 'awscost-bare-repo-files'))
    zip_dir = os.path.expanduser(os.path.join('~', 'git', 'awscost/zip_code'))
    code_base_dir = os.path.expanduser(os.path.join('py_src'))

    print('archive: {}'.format(archive_name))
    print('zip dir: {}'.format(zip_dir))
    print('code base dir: {}'.format(code_base_dir))

    shutil.make_archive(archive_name, 'zip', zip_dir, code_base_dir)
    print("Zipped python source directory (shutil).")


def upload_aws_cost_zip_file():
    """

    :return:
    """
    print('upload_aws_cost_zip_file')
    s3_cmd = 'aws s3 cp ../awscost-bare-repo-files.zip s3://awscost-pipeline-source/awscost-bare-repo-files.zip --profile roku-cti_cti-admin'

    print('S3 Upload command:\n> {}'.format(s3_cmd))
    os.system(s3_cmd)


def delete_temp_zip_dir_if_exists():
    """

    :return:
    """
    print('delete_temp_zip_dir')

    # does the directory exist?
    if os.path.exists('../zip_code'):
        # delete zip_code directory.
        print('Deleting ../zip_code directory')
        delete_zip_dir_cmd = 'rm -rf ../zip_code'
        os.system(delete_zip_dir_cmd)
    else:
        print('Did not find directory: ../zip_code')


def get_time_in_build_format():
    """Get timestamp in format for dynamo table backups.
    The name is restricted to regular expression pattern: [a-zA-Z0-9_.-]+

    Will be in this format: 2018-jan-19-0955
    """
    time = pendulum.now('US/Pacific').strftime("%Y%m%d-%H%M")
    return time


def display_finish_time():
    """
    Print current time.
    :return:
    """
    finished_time = get_time_in_build_format()
    print('Uploaded @ time: {}'.format(finished_time))


if __name__ == '__main__':
    try:
        print('Starting ...')
        delete_temp_zip_dir_if_exists()
        create_temp_zip_directory()
        move_src_files()
        replace_build_time_string()
        # aws_cost_version = update_aws_cost_version()
        # print('AWS Cost version: {}'.format(aws_cost_version))
        # create_build_info_file(aws_cost_version)
        zip_temp_code_dir()
        upload_aws_cost_zip_file()
        display_finish_time()

    except Exception as ex:
        print('Exception: {}'.format(ex))
