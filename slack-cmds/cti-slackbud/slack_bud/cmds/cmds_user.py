"""Implements User command by asnyder"""
from __future__ import print_function
import re
import boto3
import operator

from util.slack_ui_util import ShowSlackError
import util.bud_helper_util as bud_helper_util
import util.groups as groups
from cmd_interface import CmdInterface

DYNAMODB = boto3.resource('dynamodb')
BUD_USERS_TABLE = DYNAMODB.Table('SlackBudUsers')

USER_TABLE_CACHE = {}

RESULT_USER_NOT_FOUND = 'RESULT_USER_NOT_FOUND'
RESULT_GROUP_ADDED = 'RESULT_GROUP_ADDED'
RESULT_GROUP_REMOVED = 'RESULT_GROUP_REMOVED'
RESULT_NO_CHANGE = 'RESULT_NO_CHANGE'

class CmdUser(CmdInterface):
    # ###################################
    # Start Command's Properties section

    def get_cmd_properties(self):
        """
        Creates the properties for this file and returns it as a
        python dictionary.
        :return: python dictionary
        """
        props = {
            'group': 'admin',
            'sub_commands': ['add', 'remove', 'list', 'addgroup', 'removegroup', 'info', 'groups', 'groupsearch', 'search'],
            'help_title': 'Command (admin-only) for updating SlackBud users',
            'permission_level': 'dev',
            'props_add': self.get_add_properties(),
            'props_addgroup': self.get_addgroup_properties(),
            'props_groups': self.get_groups_properties(),
            'props_groupsearch': self.get_user_by_group_properties(),
            'props_info': self.get_info_properties(),
            'props_list': self.get_list_properties(),
            'props_remove': self.get_remove_properties(),
            'props_removegroup': self.get_removegroup_properties(),
            'props_search': self.get_user_by_name_properties()
        }
        return props

    def get_add_properties(self):
        """
        The properties for the "add" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`add`* _add a new user and assign a role_',
            'help_examples': [
                '/run user add [slack_user] [role] [corpID]',
                '/run user add @asnyder dev asnyder',
                '*Note:* _requires admin role access_',
                '*Roles:* _dev and admin_'
            ],
            'switch-templates': []
        }
        return props

    def invoke_add(self, cmd_inputs):
        """
        Placeholder for "add" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_add")
            arg_item_2 = cmd_inputs.get_by_index(2)
            arg_item_3 = cmd_inputs.get_by_index(3)
            arg_item_4 = cmd_inputs.get_by_index(4)
            cmd_specific_data = cmd_inputs.get_cmd_specific_data()
            userid = cmd_specific_data.get('userid')
            user_name = cmd_specific_data.get('user_name')

            # Start Add code section #### output to "text" & "title".

            text = ''
            if arg_item_2:
                text += 'user = {}\n'.format(arg_item_2)
            if arg_item_3:
                text += 'role = {}\n'.format(arg_item_3)
            if userid:
                text += 'userid = {}\n'.format(userid)
            if user_name:
                text += 'user_name = {}\n'.format(user_name)
            if arg_item_4:
                text += 'corp userID = {}\n'.format(arg_item_4)

            # Check the inputs.
            if not arg_item_2:
                raise ShowSlackError('need to specify a user and a role')
            if not arg_item_3:
                raise ShowSlackError('need to specify a role')
            user_role = arg_item_3
            if user_role not in 'dev admin':
                raise ShowSlackError('Unknown role. use dev or admin')
            corp_user_ID = arg_item_4

            print('name={}, userid={}'.format(user_name, userid))

            text = "adding user:\n"
            text += user_name
            text += '\n'
            text += user_role
            BUD_USERS_TABLE.put_item(
                Item={
                    'userid': userid,
                    'role': user_role,
                    'username': user_name,
                    'corpID': corp_user_ID,
                    'group': 'bill'
                }
            )

            # invalidate the user table cache. For reload on next use.
            USER_TABLE_CACHE = {}

            # append some useful command for the user to see.
            text += '\n\nSome useful commands:'
            text += '``` /run help\n /run awslogin help\n /run awslogin info\n /run awslogin params\n' \
                    ' /run awslogin request -u {} -a <Account> -r <Role>\n' \
                    ' /run awslogin roles -a <Account>```'.format(user_name)
            text += '\nand\n'
            text += '``` /run cmd help\n /run cmd history\n /run cmd history -n 30 -g <word-to-search-for>```'

            # End Add code section. ####
        
            # Standard response below. Change title and text for output.
            title = "Add User"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_removegroup_properties(self):
        """
        The properties for the "add" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`removegroup`* _Removes group from user(s)_',
            'help_examples': [
                '/run user removegroup -u [users] -g <group>',
                '/run user removegroup -u asnyder,jsmith,qzhong -g dsnacpu'
            ],
            'switch-templates': [],
            'switch-u': {
                'aliases': ['u', 'user'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'User(s). If more than one comma-delimited without a space'
            },
            'switch-g': {
                'aliases': ['g', 'group'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Group to remove'
            }
        }
        return props

    def invoke_removegroup(self, cmd_inputs):
        """
        Placeholder for "add" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_removegroup")
            arg_users = cmd_inputs.get_by_key('user')
            arg_group = cmd_inputs.get_by_key('group')

            print('arg_users = {}'.format(arg_users))
            print('arg_group = {}'.format(arg_group))

            # Group must start with either a (+) or a (-).
            operation = '-'
            group_name = arg_group

            text = ''
            # Check the group is real.
            group_list = groups.get_valid_group_list()
            if group_name not in group_list:
                msg = '*`{}`* not a valid group. {}'.format(arg_group, group_list)
                print('Warn: {}'.format(msg))
                # Just warn about the invalid name, but let it try anyway.
                text += 'Warning: {} \n'.format(msg)
                # raise ShowSlackError(msg)

            not_found_users = []
            removed_users = []

            # Loop through the list of user, and add or remove that group.
            user_list = arg_users.split(",")
            for curr_user in user_list:
                print('{}'.format(curr_user))
                result = modify_user_entry(curr_user, operation, group_name)
                if result == RESULT_USER_NOT_FOUND:
                    not_found_users.append(curr_user)
                elif result == RESULT_GROUP_ADDED:
                    raise ValueError('Error: Got Add user for remove command. user = {}'.format(curr_user))
                elif result == RESULT_GROUP_REMOVED:
                    removed_users.append(curr_user)
                else:
                    print('Error: Unrecognized result.  Result = {}'.format(result))

            # Print the result.
            for curr_user in removed_users:
                text += '*{}*: Group *{}* removed \n'.format(curr_user, group_name)
            for curr_user in not_found_users:
                text += '{}: USER NOT FOUND! \n '.format(curr_user)

            # End Add code section. ####

            # Standard response below. Change title and text for output.
            title = "Remove Group"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_addgroup_properties(self):
        """
        The properties for the "add" sub-command
        addgroup the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'longtask',
            'help_text': '*`addgroup`* _Adds a group to user(s)_',
            'help_examples': [
                '/run user addgroup -u [users] -g <group>',
                '/run user addgroup -u asnyder,jsmith,qzhong -g dsnacpu'
            ],
            'switch-templates': [],
            'switch-u': {
                'aliases': ['u', 'user'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'User(s). If more than one comma-delimited without a space'
            },
            'switch-g': {
                'aliases': ['g', 'group'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'Group to add'
            }
        }
        return props

    def invoke_addgroup(self, cmd_inputs):
        """
        Placeholder for "add" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_addgroup")
            arg_users = cmd_inputs.get_by_key('user')
            arg_group = cmd_inputs.get_by_key('group')

            # Group must start with either a (+) or a (-).
            operation = '+'
            group_name = arg_group

            # Check the group is real.
            group_list = groups.get_valid_group_list()
            if group_name not in group_list:
                msg = '*`{}`* not a valid group name. {}'.format(arg_group, group_list)
                print('Warn: {}'.format(msg))
                raise ShowSlackError(msg)

            text = ''
            not_found_users = []
            added_users = []

            # Loop through the list of user, and add or remove that group.
            user_list = arg_users.split(',')
            for curr_user in user_list:
                print('{}'.format(curr_user))
                result = modify_user_entry(curr_user, operation, group_name)
                if result == RESULT_USER_NOT_FOUND:
                    not_found_users.append(curr_user)
                elif result == RESULT_GROUP_ADDED:
                    added_users.append(curr_user)
                elif result == RESULT_GROUP_REMOVED:
                    raise ValueError('Error: Got Remove user for add command. user = {}'.format(curr_user))
                else:
                    print('Error: Unrecognized result.  Result = {}'.format(result))

            # Print the result.
            for curr_user in added_users:
                text += '*{}*: Group *{}* added \n'.format(curr_user, group_name)
            for curr_user in not_found_users:
                text += '{}: USER NOT FOUND! \n '.format(curr_user)
            # End Add code section. ####

            # Standard response below. Change title and text for output.
            title = "Add Group"
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_remove_properties(self):
        """
        The properties for the "remove" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`remove`* _remove an existing user_',
            'help_examples': [
                '/run user remove @jsmith'
            ],
            'switch-templates': []
        }
        return props

    def invoke_remove(self, cmd_inputs):
        """
        Placeholder for "remove" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_remove")
            arg_item_2 = cmd_inputs.get_by_index(2)
            cmd_specific_data = cmd_inputs.get_cmd_specific_data()
            userid = cmd_specific_data.get('userid')
            user_name = cmd_specific_data.get('user_name')

            # Start Remove code section #### output to "text" & "title".
            text = ''
            if arg_item_2:
                text += 'user = {}\n'.format(arg_item_2)
            if userid:
                text += 'userid = {}\n'.format(userid)
            if user_name:
                text += 'user_name = {}\n'.format(user_name)

            # End Remove code section. ####
            title = 'User remove'
            text = "removing user\n"
            text += user_name
            BUD_USERS_TABLE.delete_item(
                Key={
                    'userid': userid
                }
            )

            # invalidate the user table cache. For reload on next use.
            USER_TABLE_CACHE = {}
            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_list_properties(self):
        """
        The properties for the "list" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`list`* _list users_',
            'help_examples': [
                '/run user list'
            ],
            'switch-templates': []
        }
        return props

    def get_user_by_group_properties(self):
        """
        The properties for the "search for users by group" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`groupsearch`* _groupsearch groupname_',
            'help_examples': [
                '/run user groupsearch dev'
            ],
            'switch-templates': []
        }
        return props

    def get_user_by_name_properties(self):
        """
        The properties for the "search for users by name" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`search`* _search users_',
            'help_examples': [
                '/run user search asnyder'
            ],
            'switch-templates': []
        }
        return props

    def invoke_list(self, cmd_inputs):
        """
        Placeholder for "remove" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_list")

            # Start Remove code section #### output to "text" & "title".
            text = 'this is the list command.'
            # End Remove code section. ####
            title = 'User List'
            text = "User Role\n"
            table_data = BUD_USERS_TABLE.scan()
            # table_data = sorted(table_data['Items'], key=operator.itemgetter('corpID'))

            print(table_data)
            text += "Number of Users: "
            text += str(table_data['Count'])
            text += '\n'
            for item in table_data['Items']:
                slack_name = item.get('username')
                ldap_name = item.get('corpID')
                groups = item.get('group')

                text += '*`{}`*: *{}*, _groups:_ *{}*\n'.format(ldap_name, slack_name, groups)

            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def invoke_groupsearch(self, cmd_inputs):
        """
        Placeholder for "groupsearch" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        
        from boto3.dynamodb.conditions import Attr
        
        try:
            print("invoke_groupsearch")
            ### BEGIN add example BEGIN ###
            search_string = cmd_inputs.get_by_index(2)
        
            # Start Add code section #### output to "text" & "title".

            text = ''
            if search_string:
                text += 'search_string = {}\n'.format(search_string)
        
            # Check the inputs.
            if not search_string:
                raise ShowSlackError('need to specify a search string for groups')
        
            print('search_string={}'.format(search_string))

            ### END add example END ###

            text = 'this is the search by group command.'

            title = 'Group Search'
            text = "User list by Group\n"
            
            table_data = BUD_USERS_TABLE.scan(FilterExpression=Attr('group').contains(search_string))['Items']
            table_data = sorted(table_data, key=operator.itemgetter('corpID'))

            print(table_data)
            text += "Number of Users in found groups: "
            text += str(len(table_data))
            text += '\n'
            for item in table_data:
                slack_name = item.get('username')
                ldap_name = item.get('corpID')
                groups = item.get('group')

                text += '*`{}`*: *{}*, _groups:_ *{}*\n'.format(ldap_name, slack_name, groups)

            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def invoke_search(self, cmd_inputs):
        """
        Placeholder for "user search" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        
        from boto3.dynamodb.conditions import Attr
        
        try:
            print("invoke_user_search")
            ### BEGIN add example BEGIN ###
            search_string = cmd_inputs.get_by_index(2)
        
            # Start Add code section #### output to "text" & "title".

            text = ''
            if search_string:
                text += 'search_string = {}\n'.format(search_string)
        
            # Check the inputs.
            if not search_string:
                raise ShowSlackError('need to specify a search string for users')
        
            print('search_string={}'.format(search_string))

            ### END add example END ###

            text = 'this is the search by username command.'

            title = 'User Search'
            text = "User's matching search criteria\n"
            
            table_data = BUD_USERS_TABLE.scan(FilterExpression=Attr('corpID').contains(search_string))['Items']
            table_data = sorted(table_data, key=operator.itemgetter('corpID'))

            print(table_data)
            text += "Number of Users found matching search string: "
            text += str(len(table_data))
            text += '\n'
            for item in table_data:
                slack_name = item.get('username')
                ldap_name = item.get('corpID')
                groups = item.get('group')

                text += '*`{}`*: *{}*, _groups:_ *{}*\n'.format(ldap_name, slack_name, groups)

            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")
    
    def get_groups_properties(self):
        """
        The properties for the "remove" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`groups`* _list valid groups_',
            'help_examples': [
                '/run user groups'
            ],
            'switch-templates': []
        }
        return props

    def invoke_groups(self, cmd_inputs):
        """
        Placeholder for "remove" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_groups")

            # Start Remove code section #### output to "text" & "title".
            text = 'this is the list command.'
            # End Remove code section. ####
            title = 'User Groups'
            text = ''

            group_list = groups.get_valid_group_list()
            group_list.sort()
            group_map = groups.get_group_map()

            for curr_group in group_list:
                group_desc = group_map.get(curr_group)
                text += '*`{}`*: {}\n'.format(curr_group, group_desc)

            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    def get_info_properties(self):
        """
        The properties for the "remove" sub-command
        Modify the values as needed, but leave keys alone.

        :return: python dictionary
        """
        props = {
            'run-type': 'shorttask',
            'help_text': '*`info`* _display info on user_',
            'help_examples': [
                '/run user info -u [user(s)]'
            ],
            'switch-templates': [],
            'switch-u': {
                'aliases': ['u', 'user'],
                'type': 'string',
                'required': True,
                'lower_case': True,
                'help_text': 'User(s). If more than one comma-delimited without a space'
            }
        }
        return props

    def invoke_info(self, cmd_inputs):
        """
        Placeholder for "remove" sub-command
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print("invoke_info")

            arg_user = cmd_inputs.get_by_key('user')

            # Start Remove code section #### output to "text" & "title".
            text = 'this is the list command.'
            # End Remove code section. ####
            title = 'User(s) Info'
            text = ''

            user_list = arg_user.split(',')

            for curr_user in user_list:
                print(curr_user)
                text += '*`{}`*: '.format(curr_user)
                user_info = get_user_info(curr_user)
                if user_info:
                    text += '{}'.format(user_info)
                else:
                    text += ' NO INFO'
                text += '\n'

            # Standard response below. Change title and text for output.
            return self.slack_ui_standard_response(title, text)
        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    # End Command's Properties section
    # ###################################
    # Start Command's implemented interface method section

    def run_command(self):
        """
        DON'T change this method. It should only be changed but the
        create_command, add_sub_command, and remove_sub_command scripts.

        In this method we look up the sub-command being used, and then the
        properties for that sub-command. It parses and validates the arguments
        and deals with invalid arguments.

        If the arguments are good. It next determines if this sub command
        needs to be invoked via the longtask lambda, or can run in (this)
        shorttask lambda. It then packages the arguments up properly and
        runs that command.

        :return: SlackUI response.
        """
        return self.default_run_command()

    def build_cmd_specific_data(self):
        """
        If you need specific things common to many sub commands like
        dynamo db table names or sessions get it here.

        If nothing is needed return an empty dictionary.
        :return: dict, with cmd specific keys. default is empty dictionary
        """
        cmd_inputs = self.get_cmd_input()

        print('@build_cmd_specific_data cmd_inputs={}'.format(cmd_inputs))

        sub_command = cmd_inputs.get_sub_command()
        raw_inputs = cmd_inputs.get_raw_inputs()

        print("%s invokes %s" % (self.__class__.__name__, sub_command))
        print("raw_inputs", raw_inputs)

        if sub_command == 'add' or sub_command == 'remove':
            m = re.search('<@(.*)\|(.*)> *(.*)$', raw_inputs)
            userid = m.group(1)
            user_name = m.group(2)

            cmd_specific_data = {
                'userid': userid,
                'user_name': user_name
            }

        else:
            cmd_specific_data = {}

        return cmd_specific_data

    def invoke_confirm_command(self):
        """
        Only fill out this section in the rare case your command might
        prompt the Slack UI with buttons ect. for responses.
        Most commands will leave this section blank.
        :param cmd_inputs: class with input values.
        :return:
        """
        try:
            print('invoke_confirm_command')
            cmd_inputs = self.get_cmd_input()
            params = cmd_inputs.get_confirmation_params()
            callback_id = cmd_inputs.get_callback_id()
            print('callback_id = {}'.format(callback_id))

            # Start confirmation code section.
            # Callback Id convention is callback_<sub-command-name>_<anything>

            # Replace_example below.
            # if callback_id == 'callback_mysubcommand_prompt_env':
            #     return some_method_to_handle_this_case(params)
            # if callback_id == 'callback_mysubcommand_prompt_region':
            #     return some_other_method_to_handle_region(params)


            # End confirmation code section.
            # Default return until this section customized.
            title = 'Default invoke_confirm_command'
            text = 'Need to customize, invoke_confirm_command'
            return self.slack_ui_standard_response(title, text)

        except ShowSlackError:
            raise
        except Exception as ex:
            bud_helper_util.log_traceback_exception(ex)
            raise ShowSlackError("Invalid request. See log for details.")

    # End class functions
# ###################################
# Start static helper methods sections


class SlackUserNotFoundException(Exception):
    pass


def modify_user_entry(curr_user, operation, group_name):
    """
    Update the

    :param curr_user: User name as stored in SlackUser's table.
    :param operation: String.  Either '+' to add or '-' to remove
    :param group_name: Valid command group name like 'cti' | 'data' | 'farm'
    :return: String with one of four responses.
        RESULT_USER_NOT_FOUND | RESULT_GROUP_ADDED | RESULT_GROUP_REMOVED | RESULT_NO_CHANGE
    """
    # If we don't have the user-id then scan for 'corpID' or 'username'
    try:
        # inputs are lower case.
        curr_user = curr_user.lower()
        group_name = group_name.lower()
        result = 'RESULT_NO_CHANGE'

        user_id = get_slack_user_id_from_name(curr_user)

        response = BUD_USERS_TABLE.get_item(
            Key={'userid': user_id}
        )

        item = response.get('Item')
        if not item:
            raise SlackUserNotFoundException('No data for user: {}, (slack) userid={}'.format(curr_user, user_id))

        old_groups = item.get('group')
        group_list = old_groups.split(',')
        group_found_in_list = False
        if operation == '-':
            while group_name in group_list:
                group_found_in_list = True
                group_list.remove(group_name)
            if group_found_in_list:
                result = 'RESULT_GROUP_REMOVED'
        elif operation == '+':
            if group_name in group_list:
                group_found_in_list = True
                print('WARN: User already had group. user={}, group={}'.format(curr_user, group_name))
            else:
                group_list.append(group_name)
                result = 'RESULT_GROUP_ADDED'
        else:
            raise ValueError('Unknown operation! Was: _{}_'.format(operation))

        # Add a noop group if this is an empty list.
        if len(group_list) == 0:
            group_list.append('noop')

        new_groups = ','.join(group_list)

        print('user_id = {}, new_groups = {}'.format(user_id, new_groups))

        # BUD_USERS_TABLE.update_item(
        #     Key={'userid': user_id},
        #     UpdateExpression='set group = :g',
        #     ExpressionAttributeValues={
        #         ':g': new_groups
        #     },
        #     ReturnValues='UPDATED_NEW'
        #     # AttributeUpdates={
        #     #     'group': {new_groups}
        #     # }
        #)

        # TEMP. do a put item with everything in the original except group
        user_role = item.get('role')
        user_name = item.get('username')
        corp_user_ID = item.get('corpID')
        BUD_USERS_TABLE.put_item(
            Item={
                'userid': user_id,
                'role': user_role,
                'username': user_name,
                'corpID': corp_user_ID,
                'group': new_groups
            }
        )

        return result

    except SlackUserNotFoundException as uex:
        print("WARN: Didn't find use: {}".format(curr_user))
        return 'RESULT_USER_NOT_FOUND'


def get_user_info(curr_user):
    """
    Get all info for a specific user or return the String 'RESULT_USER_NOT_FOUND'
    :param curr_user:
    :return:
    """
    try:
        user_id = get_slack_user_id_from_name(curr_user)
        print('Look-up userid = {}'.format(user_id))
        response = BUD_USERS_TABLE.get_item(
            Key={'userid': user_id}
        )

        item = response.get('Item')
        if not item:
            print("Didn't find {}. userid = {}".format(curr_user, user_id))
            return 'RESULT_USER_NOT_FOUND'

        group = item.get('group')
        corp_id = item.get('corpID')
        user_name = item.get('username')
        if corp_id != user_name:
            return ' _groups:_ *{}*, _ldap name:_ *{}*, _slack name:_ {}'.format(group, corp_id, user_name)

        return ' _groups:_ *{}*'.format(group)

    except SlackUserNotFoundException as sunfe:
        return 'RESULT_USER_NOT_FOUND'
    except Exception as ex:
        print('ERROR: {}'.format(ex))
        bud_helper_util.log_traceback_exception(ex)
        return 'RESULT_USER_NOT_FOUND'


def get_slack_user_id_from_name(curr_user):
    """
    Read the information about
    :param curr_user: String can be either, SlackUserId, or Slack User name or LDAP user name.
    :return: Slack UserID
    :raises SlackUserNotFoundException: if could not find user in list.
    """
    # Return fixed user string for now.
    global USER_TABLE_CACHE
    cache_size = len(USER_TABLE_CACHE)
    if cache_size == 0:
        print('Loading User table cache')
        cache_slack_user_table()
        cache_size = len(USER_TABLE_CACHE)
        print('Put load cache size = {}'.format(cache_size))
    else:
        print('USER_TABLE_CACHE size = {}'.format(cache_size))

    slack_id = USER_TABLE_CACHE.get(curr_user)
    if not slack_id:
        raise SlackUserNotFoundException(curr_user)

    return slack_id


def cache_slack_user_table():
    """
    Scan the SlackUser table and cache result if not already there.

    Scans of DynamoDB are expensive, so do it just once and cache the
    result in a python dictionary with the key either the SlackUser use name
    or LDAP user name.
    :return:
    """
    global USER_TABLE_CACHE

    response = BUD_USERS_TABLE.scan()
    data = response.get('Items')

    print('data = {}'.format(data))

    for i in data:
        print('i = {}'.format(i))
        slack_name = i.get('username')
        corp_name = i.get('corpID')
        slack_id = i.get('userid')

        USER_TABLE_CACHE[slack_name] = slack_id
        USER_TABLE_CACHE[corp_name] = slack_id


# End static helper methods
# #########################
# Star unit-test section. All test function must start with "test_..."


def test_cases_cmd_user_main():
    """
    Entry point for command unit tests.
    :return: True if tests pass False if they fail.
    """
    try:
        # Test the regex parsing.
        raw_input_1 = 'user add <@U1RGUPMHA|someuser> dev'
        m = re.search('<@(.*)\|(.*)> *(.*)$', raw_input_1)
        userid = m.group(1)
        user_name = m.group(2)
        print('userid = {}'.format(userid))
        print('user_name = {}'.format(user_name))

        return True
    except Exception as ex:
        bud_helper_util.log_traceback_exception(ex)
        return False


if __name__ == '__main__':
    #  test methods below.
    test_cases_cmd_user_main()
