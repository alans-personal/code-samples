"""
A temp file that takes the ../py_src directory zips it up and then
pushes that zip file into the gardener pipeline deployment bucket.
"""
import os
import shutil
# import push_util

ZIP_BASE_DIR = os.path.expanduser(os.path.join('~', 'git', 'gardener-service', 'zip_python_code'))
ROOT_DIR = os.path.expanduser(os.path.join('~', 'git', 'gardener-service'))

# These values need to be in sync with gardener-py-service.stack.yaml file.
# arn:aws:s3:::gardener-pipeline-source/gardener-lambda-bare-repo-files.zip
SOURCE_S3_BUCKET = 'gardener-pipeline-source'
BARE_CODE_FILE_NAME = 'gardener-lambda-bare-repo-files.zip'


def create_zip_python_code_directory():
    """

    :return: None
    """
    print('create_zip_python_code_directory')
    temp_sub_dirs = os.path.join(ZIP_BASE_DIR)

    if not os.path.exists(temp_sub_dirs):
        print('Creating dir: {}'.format(temp_sub_dirs))
        os.makedirs(temp_sub_dirs)


def move_files_to_zip_dir():
    """

    :return: None
    """
    print('move_files_to_zip_dir')
    source_code_dir = os.path.expanduser(os.path.join(ROOT_DIR, 'py_src'))
    dest_code_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'py_src'))

    shutil.copytree(source_code_dir, dest_code_dir)


def update_gardener_version_info():
    """
    Read a build info file and a dynamo ServiceBuildVersion table
    to create the version of this code.
    :return: Version string number.
    """
    # On first tire we will use fixed value.
    print('update_gardener_version_info')

    # ToDo: Get a commit hash with 'git log | grep commit' or from git-runner
    # ToDo: Get a timestamp from a utility class.
    # ToDo: Increment the build number for this service in DynamoDB table.

    return '12345678-master-20180629-1'


def create_build_info_file(gardener_version):
    """
    Create a build info file in the zip directory.
    :param gardener_version:
    :return: None
    """
    print('create_build_info_file')


def zip_temp_dir():
    """
    Zip the directory.
    :return: None
    """
    print('zip_temp_dir')

    archive_name = os.path.expanduser(os.path.join('..', 'gardener-lambda-bare-repo-files'))
    root_dir = os.path.expanduser(os.path.join('~', 'git', 'gardener-service'))
    base_dir = os.path.expanduser(os.path.join('py_src'))

    print('archive: {}'.format(archive_name))
    print('root dir: {}'.format(root_dir))
    print('base dir: {}'.format(base_dir))

    shutil.make_archive(archive_name, 'zip', root_dir, base_dir)
    print("Zipped python source directory (shutil).")


def upload_gardener_zip_to_s3_pipeline_bucket():
    """

    :return: None
    """
    print('upload_gardener_zip_to_s3_pipeline_bucket')

    # s3_cmd = 'aws s3 cp {}/{} s3://{}/{} --profile roku-cti_cti-admin'.\
    #     format(ZIP_BASE_DIR, BARE_CODE_FILE_NAME, SOURCE_S3_BUCKET, BARE_CODE_FILE_NAME)

    # s3_cmd = 'aws s3 cp {} s3://{}/{} --profile roku-cti_cti-admin'.\
    #     format(BARE_CODE_FILE_NAME, SOURCE_S3_BUCKET, BARE_CODE_FILE_NAME)

    #s3_cmd = 'aws s3 cp ../gardener-lambda-bare-repo-files.zip s3://gardener-pipeline-source/gardener-lambda-bare-repo-files.zip --profile roku-cti_cti-admin'
    s3_cmd = 'aws s3 cp ../gardener-lambda-bare-repo-files.zip s3://gardener-pipeline-source/gardener-lambda-bare-repo-files.zip --profile roku-cti_cti-admin'

    print('S3 Upload command:\n> {}'.format(s3_cmd))
    os.system(s3_cmd)


def delete_zip_dir():
    """

    :return: None
    """
    print('delete_zip_dir')


if __name__ == '__main__':
    try:
        print('\nStarting script: push_py_gardener_to_s3.py\n  .\n  .\n  .')
        create_zip_python_code_directory()
        move_files_to_zip_dir()
        gardener_version = update_gardener_version_info()
        print('Gardener version is: {}'.format(gardener_version))
        create_build_info_file(gardener_version)
        zip_temp_dir()
        upload_gardener_zip_to_s3_pipeline_bucket()

        #print('Deleting temp zip directory.')
        #delete_zip_dir()
        print('Success')
    except Exception as ex:
        print('Exception: {}'.format(ex))
        #delete_zip_dir()