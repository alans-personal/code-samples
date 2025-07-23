"""
Utilites methods need by both java and python deployments.
"""
import os
import zipfile
import shutil


def zip_path_from_script_dir(zip_file_name, dest_path, zip_path):
    """
    We are in the script directory.
    :zip_file_name: Name of zip file to create.  Example: Python.zip
    :dest_path: Destination path relative to script directory.   Example: ../
    :zip_path: File to zip relative to script directory.
    :return: None
    """

    archive_name = os.path.expanduser(os.path.join('..', 'gardener-lambda-bare-repo-files'))
    root_dir = os.path.expanduser(os.path.join('~', 'git', 'gardener-service'))
    base_dir = os.path.expanduser(os.path.join('py_src'))

    print('archive: {}'.format(archive_name))
    print('root dir: {}'.format(root_dir))
    print('base dir: {}'.format(base_dir))

    shutil.make_archive(archive_name, 'zip', root_dir, base_dir)
    print("Zipped directory.")

    # print('zip_path_from_script_dir\n  name: {}\n  dest: {}\n  zip_path: {}'
    #       .format(zip_file_name, dest_path, zip_path))

    # zipf = zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED)
    # for root, dirs, files in os.walk(zip_path):
    #     for curr_file in files:
    #         zipf.write(os.path.join(root, curr_file))
    # zipf.close()

    # Move the zip_file somewhere.
    #shutil.move(zip_file_name, dest_path)
