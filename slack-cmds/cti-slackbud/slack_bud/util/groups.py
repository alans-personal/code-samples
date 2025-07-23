"""
All the information about groups in one place.
"""


def get_group_map():
    """
    Return list of teams for multi-tenant slack-bud.
    :return:
    """
    # Keep this in sync with ../scripts/create_slack_cmd.py
    ret_val = {
        'noop': 'NoOp group. Only for no group association',
        'admin': 'Admin commands',
        'apps': 'Apps Team',
        'bill': 'Billing Team',
        'cti': 'CloudTech',
        'data': 'BigData Team',
        'dsna-cpu': 'DSNA CPU only users',
        'dsna-gpu': 'DSNA GPU users',
        'farm': 'Farm users',
        'firmware': 'Firmware team',
        'mobile': 'Mobile Team',
        'sr': 'Search and Recommendations',
        'trust': 'Trust Engineering',
        'unity': 'Unity Team',
        'uxeng': 'UX Engineering',
        'web': 'Web Team',
    }

    return ret_val


def get_valid_group_list():
    """
    Return a list of valid groups.
    :return: list like ['sr', 'cti', ...]
    """
    group_dict = get_group_map()
    return list(group_dict.keys())


# if __name__ == '__main__':
#     #  test string to list.
#     str = 'abccde'
#     print(str)
#     str_list = str.split(',')
#     print(str_list)