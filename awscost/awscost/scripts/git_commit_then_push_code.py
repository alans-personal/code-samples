"""
git commit the code then push into pipeline.
"""
import os
import subprocess
import shutil


def confirm_commit_files():
    """

    :return: boolean True if should continue.
    """

    git_status_output = subprocess.check_output(['git', 'status'])

    print('-------- git status --------')
    print(git_status_output)
    print('^^^^^^^^    end     ^^^^^^^^')
    if "modified:" in git_status_output:
        file_added = raw_input('Are all the files you want included added to commit?\n (y/n): ')
        if not file_added.lower().startswith('y'):
            print("Please 'git add' those files")
            print('done.')
            return False

    yes = raw_input('\nDo you want to commit files?\n (y/n): ')
    if yes.lower().startswith('y'):
        return True
    else:
        print('done.')
    return False


def get_commit_message():
    """
    """
    jira = raw_input('What is JIRA ticket?\nExample: CTDEVOPS-700\n\nJIRA ticket: ')
    commit_message = raw_input('Commit message: ')
    commit_string = '"{}: {}"'.format(jira, commit_message)
    print('\n > git commit -m {}'.format(commit_string))
    yes = raw_input('(y/n): ')
    if yes.lower().startswith('y'):
        git_commit_output = subprocess.check_output(['git', 'commit', '-m', commit_string])
        print(git_commit_output)
        return True
    else:
        print('NOT committed.')
    return False


def do_git_push_origin_master():
    """

    :return:
    """
    print('\n > git push origin master')
    yes = raw_input('(y/n): ')
    if yes.lower().startswith('y'):
        git_commit_output = subprocess.check_output(['git', 'push', 'origin', 'master'])
        print(git_commit_output)
        return True
    return False


def push_aws_cost_to_pipeline():
    """

    :return:
    """
    print('Do you want to push latest into pipeline?')
    yes = raw_input('(y/n): ')
    if yes.lower().startswith('y'):
        script_output = subprocess.check_output(['./push_aws_cost_to_s3'])
        print(script_output)


if __name__ == '__main__':
    try:
        print('Start: ____ git_commit_then_push ____')
        if not confirm_commit_files():
            exit(0)
        if not get_commit_message():
            print('Not commited.')
            exit(0)
        if not do_git_push_origin_master():
            print('No code pushed. Done.')
            exit(0)
        if not push_aws_cost_to_pipeline():
            print ('Not pushed to pipeline')
            exit(0)

    except Exception as ex:
        print('git_commit script had exception: {}'.format(ex))
