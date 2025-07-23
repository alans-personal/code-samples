"""
Utility to make fixed width tables in Slack
Use ''' to get fixed width font.
python2.7 (latest) compatible for now.  :(

"""



"""Give below different names."""

def obscure_string(value, num_chars=3):
    """
    Obscure a string so the full value doesn't appear in the log, but
    the start and end are correct so you can validate it is correct value.

    If long:
    Th!s!s4P4ssword
    Th!***(15)***ord

    If short:
    ASh0rtStr
    AS**(9)**tr

    The result will be the first three and last three characters, and something in the middle to indicate
    the length. If the len is less than 10 characters it will be shorter.

    :param value: Some string the needs to be obscured, but logged partially to verify.
    :param num_chars: Number of characters to put at start and end of string
    :return: String like
    """
    if value is None:
        return 'None'

    str_len = len(value)

    ret_val = ''
    if str_len > 10:
        ret_val += value[0:3]
        ret_val += '***({})***'.format(str_len)
        ret_val += value[-3:]
    else:
        ret_val += value[0:2]
        ret_val += '**({})**'.format(str_len)
        ret_val += value[-2:]

    return ret_val


def shorten_string(value, num_char):
    """

    :param value:
    :param num_char:
    :return:
    """
    if value is None:
        return 'None'

    str_len = len(value)

    ret_val = ''
    if str_len > 10:
        ret_val += value[0:num_char]
        ret_val += '***({})***'.format(str_len)
        ret_val += value[-1*num_char:]
    else:
        ret_val += value[0:2]
        ret_val += '**({})**'.format(str_len)
        ret_val += value[-2:]

    return ret_val