"""
A temp file that takes the ../api/src/ directory and the ../api/src/build.gradle, zips it up and then
pushes that zip file into the gardener pipeline deployment bucket.
"""
import os
import shutil
import push_util


ZIP_BASE_DIR = os.path.expanduser(os.path.join('~', 'git', 'gardener-service', 'zip_java_code'))
ROOT_DIR = os.path.expanduser(os.path.join('~', 'git', 'gardener-service'))

# These values need to be in sync with gardener-py-service.stack.yaml file.
# arn:aws:s3:::gardener-pipeline-source/gardener-lambda-bare-repo-files.zip
SOURCE_S3_BUCKET = 'gardener-java-pipeline-source'
BARE_CODE_FILE_NAME = 'gardener-java-bare-repo-files.zip'


def create_temp_zip_directory():
    """
    Create a temp directory with path needed by gradle.build file and only the
    required files for the Gardener service.
    :return: None
    """
    archive_name = os.path.expanduser(os.path.join('..', 'gardener-bare-repo-files'))

    temp_sub_dirs = os.path.join(ZIP_BASE_DIR, 'api', 'src', 'main')

    if not os.path.exists(temp_sub_dirs):
        print('Creating dir: {}'.format(temp_sub_dirs))
        os.makedirs(temp_sub_dirs)


def move_files_to_zip_dir():
    """
    Move only the required files into the temp directory location
    :return: None
    """
    source_code_dir = os.path.expanduser(os.path.join(ROOT_DIR, 'api', 'src', 'main', 'java'))
    dest_code_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'api', 'src', 'main', 'java'))

    print('Copy source tree')
    print('Java Source: {}'.format(source_code_dir))
    print('Java Dest  : {}'.format(dest_code_dir))

    shutil.copytree(source_code_dir, dest_code_dir)

    # copy resource directory.
    source_resources_dir = os.path.expanduser(os.path.join(ROOT_DIR, 'api', 'src', 'main', 'resources'))
    dest_resources_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'api', 'src', 'main', 'resources'))
    dest_resources_2_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'api', 'resources'))

    print('Copy Resources directory')
    print('Resources Source: {}'.format(source_resources_dir))
    print('Resources Dest  : {}'.format(dest_resources_dir))
    print('Resources 2 Dest  : {}'.format(dest_resources_2_dir))

    shutil.copytree(source_resources_dir, dest_resources_dir)
    shutil.copytree(source_resources_dir, dest_resources_2_dir)

    print('Copy buildspec and appspec files')
    build_spec_file_path = os.path.expanduser(os.path.join(ROOT_DIR, 'appspec.yml'))
    app_spec_file_path = os.path.expanduser(os.path.join(ROOT_DIR, 'java-buildspec.yml'))
    dest_root_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR))
    shutil.copy(build_spec_file_path, dest_root_dir)
    shutil.copy(app_spec_file_path, dest_root_dir)

    print('Copy gradle build files')
    gradle_settings_path = os.path.expanduser(os.path.join(ROOT_DIR, 'settings.gradle'))
    gradle_build_root_path = os.path.expanduser(os.path.join(ROOT_DIR, 'build.gradle'))
    gradle_build_api_src_path = os.path.expanduser(os.path.join(ROOT_DIR, 'api', 'build.gradle'))
    api_dest_path = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'api'))

    shutil.copy(gradle_settings_path, dest_root_dir)
    shutil.copy(gradle_build_root_path, dest_root_dir)
    shutil.copy(gradle_build_api_src_path, api_dest_path)

    print('Copy entire scripts directory for codedeploy scripts')
    scripts_src_dir = os.path.expanduser(os.path.join(ROOT_DIR, 'scripts'))
    scripts_dest_dir = os.path.expanduser(os.path.join(ZIP_BASE_DIR, 'scripts'))
    shutil.copytree(scripts_src_dir, scripts_dest_dir, ignore=shutil.ignore_patterns('.idea'))

    print('Copy finished.')


def update_gardener_version_info():
    """
    A services info will be stored in a DynamoDB table and
    return the string with Gardeners build string.
    :return: String with latest build version
    """
    # ToDo: Get a commit hash with 'git log | grep commit' or from git-runner
    # ToDo: Get a timestamp from a utility class.
    # ToDo: Increment the build number for this service in DynamoDB table.
    return "notahash-master-{}-{}".format('20180629', '1')


def zip_temp_dir():
    """
    Zip the directory
    :return:
    """
    print('zip_temp_dir')

    archive_name = os.path.expanduser(os.path.join('..', 'gardener-java-bare-repo-files'))
    root_dir = os.path.expanduser(os.path.join('~', 'git', 'gardener-service', 'zip_java_code'))
    base_dir = os.path.expanduser(os.path.join('.'))

    print('archive: {}'.format(archive_name))
    print('root dir: {}'.format(root_dir))
    print('base dir: {}'.format(base_dir))

    shutil.make_archive(archive_name, 'zip', root_dir, base_dir)
    print("Zipped java temp directory (shutil).")


def upload_gardener_zip_to_s3_pipeline_bucket():
    """
    Upload zip file into pipeline's S3 bucket.
    :return: None
    """
    print('upload_gardener_zip_to_s3_pipeline_bucket')

    #s3_cmd = 'aws s3 cp ../gardener-java-bare-repo-files.zip s3://gardener-java-pipeline-source/gardener-java-bare-repo-files.zip --profile roku-cti_cti-admin'
    s3_cmd = 'aws s3 cp ../gardener-java-bare-repo-files.zip s3://gardener-java-pipeline-source/gardener-java-bare-repo-files.zip --profile roku-cti_cti-admin'

    print('S3 Upload command:\n> {}'.format(s3_cmd))
    os.system(s3_cmd)


def delete_zip_dir():
    """
    Delete the zip directory.
    :return: None
    """
    if os.path.exists(ZIP_BASE_DIR):
        print('Deleting dir: {}'.format(ZIP_BASE_DIR))
        os.removedirs(ZIP_BASE_DIR)


if __name__ == '__main__':
    try:
        print('\nStarting script: push_java_gardener_to_s3.py\n  .\n  .\n  .')
        create_temp_zip_directory()
        move_files_to_zip_dir()
        gardener_version = update_gardener_version_info()
        print('Gardener version is: {}'.format(gardener_version))
        zip_temp_dir()
        upload_gardener_zip_to_s3_pipeline_bucket()

        print('Skip delete dir to verify files.')
        #delete_zip_dir()
        print('Success')
    except Exception as ex:
        print('Exception: {}'.format(ex))
        #delete_zip_dir()
