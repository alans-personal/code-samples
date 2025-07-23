"""
Non-AWS related utility for gardener and the pipeline.
"""
from __future__ import print_function

import zipfile
import os
import datetime
import traceback
import pendulum


class GardenHelperError(Exception):
    """Catch this exception from bud_helper_util methods that throw it.
    An error message needs to be propagated back out to the user.

    NOTE: Don't throw this exception, only catch and convert it.
    """
    def __init__(self, *args):
        Exception.__init__(self, *args)


def grep(filename, needle):
    """Find text within file.
    This returns a list of matching lines.
    """
    ret = []
    with open(filename) as f_in:
        for i, line in enumerate(f_in):
            if needle in line:
                ret.append(line)
    return ret


def read_key_value_file_to_dictionary(filepath, delim='='):
    """Read a file in the following format.
    key1 = value1
    key2 = value2
    key3 = value3

    and convert it into a dictionary.

    :param filepath: path to the file
    :param delim: delimiter used. '=' is default. ': ' will also be common.
    :return: dictionary values of file.
    """
    f = open(filepath, 'r')
    answer = {}
    for line in f:
        k, v = line.strip().split(delim)
        answer[k.strip()] = v.strip()

    f.close()
    return answer


def unzip_file(zip_file_path, to_dir):
    """Unzip a *.zip file in a local directory."""

    try:
        print('Unzip verifying path: %s' % zip_file_path)
        # Verify zip file
        if not os.path.isfile(zip_file_path):
            message = 'Unzip failed to verify file: %s' % zip_file_path
            print(message)
            raise GardenHelperError(message)
        else:
            print('Verified "{}" is a file.'.format(zip_file_path))

        # unzip
        zip_ref = zipfile.ZipFile(zip_file_path, 'r')
        zip_ref.extractall(to_dir)
        zip_ref.close()
    except GardenHelperError:
        raise
    except Exception as ex:
        message = 'Failed to unzip file: %s \nto dir: %s.\nReason: %s'\
                  % (zip_file_path, to_dir, ex.message)
        print(message)
        raise GardenHelperError(message)


def get_files_in_dir_by_type(dir_path, file_ext):
    """Get files of extension in directory."""
    included_extensions = [file_ext]
    file_names = [fn for fn in os.listdir(dir_path)
                  if any(fn.endswith(ext) for ext in included_extensions)]

    return file_names


def get_gardener_time_format():
    """Get timestamp in format for dynamo table backups.
    The name is restricted to regular expression pattern: [a-zA-Z0-9_.-]+

    Will be in this format: 2018-jan-19-0955
    """
    time = pendulum.now('US/Pacific').strftime("%Y-%m-%d-%H:%M:%S")
    return time


def start_timer():
    """
    Standard way to start timer.
    :return:
    """
    return datetime.datetime.now()


def delta_time(start_time):
    """
    Use datetime and start_time for delta from a start time stamp.

    returns a float  in seconds like:  x.xxxx

    :param start_time:
    :return: float or deltatime with time in seconds for a delta.
    """
    end_time = datetime.datetime.now()
    tot_time = end_time - start_time
    ret_val = tot_time.total_seconds()
    return ret_val


def print_delta_time(start_time, stage):
    """
    Prints the delta time from start_time into the aws lambda function's log.
    Format is:  'TIMER <stage-comment>: <delta time> sec.'
    :param start_time:
    :param stage: The comment to append to front of timer log.
    :return: None
    """
    delta_time_float = delta_time(start_time)
    log_line = 'TIMER {}: {} sec.'.format(stage, delta_time_float)
    print(log_line)


def log_traceback_exception(ex):
    """
    Helper class for logging exception.
    :param ex: python exception class
    :return: None
    """
    try:
        template = 'Failed during execution. type {0} occurred. Arguments:\n{1!r}'
        print(template.format(type(ex).__name__, ex.args))
        traceback_str = traceback.format_exc()
        print('Error traceback \n{}'.format(traceback_str))
    except Exception as e:
        print('Something went wrong with traceback logging')
        print('Traceback Exception: {}'.format(e))
