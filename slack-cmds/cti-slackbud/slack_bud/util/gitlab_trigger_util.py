# -*- coding: utf-8 -*-
import os
from pprint import pprint

import requests

CORP_GITLAB = 'gitlab.eng.asnyder.com'
# API_TOKEN = os.environ['GITLAB_API_TOKEN']


class GitlabProject(object):
    """
     Thin Gitlab wrapper
    """

    def __init__(self, token, host, namespace, projectname, timeout=120):

        if not token:
            raise ValueError('please specify a valid gitlab api token value')
        self.token = token
        self.headers = {'PRIVATE-TOKEN': self.token}

        if not host:
            raise ValueError('please specify a valid gitlab host')
        self.host = host.rstrip('/')
        if self.host.startswith('http://') or self.host.startswith('https://'):
            pass
        else:
            self.host = 'https://' + self.host

        if not namespace:
            raise ValueError('please specify a valid gitlab namespace (aka group)')
        self.namespace = namespace

        if not projectname:
            raise ValueError('please specify a valid gitlab project name')
        self.projectname = projectname

        # api url
        self.api_url = self.host + '/api/v4'

        # set response timeout
        self.timeout = timeout

        # get project id
        self.project_obj = self.get('/projects/{project}'.format(project=self.namespace + '%2F' + self.projectname))
        self.project_id = self.project_obj["id"]

    def get(self, uri, **kwargs):
        url = self.api_url + uri
        response = requests.get(url, params=kwargs, headers=self.headers, timeout=self.timeout)
        return self.response_handler(response)

    def post(self, uri, **kwargs):
        """"
        :param uri: String with the URI for the endpoint to POST to
        :param kwargs: Key word arguments representing the data to use in the POST (specified as data dictionary)
        """
        url = self.api_url + uri
        response = requests.post(url, headers=self.headers, data=kwargs, timeout=self.timeout)
        return self.response_handler(response)

    def delete(self, uri):
        url = self.api_url + uri
        response = requests.delete(url, headers=self.headers, timeout=self.timeout)
        return self.response_handler(response)

    def response_handler(self, response):
        # raise HTTPError on api error
        if not response.status_code == requests.codes.ok:
            response.raise_for_status()
        # raise JSONDecodeError if invalid Json was returned
        try:
            response_json = response.json()
        except ValueError:
          pass
        return response_json

    def get_branch(self, branch):
        """
        :param branch: branch name
        :return: branch object (including last commit sha)
        """
        return self.get('/projects/{0}/repository/branches/{1}'.format(self.project_id, branch))

    def get_commit(self, sha):
        return self.get('/projects/{0}/repository/commits/{1}'.format(self.project_id, sha))

    def get_commit_statuses(self, sha):
        return self.get('/projects/{0}/repository/commits/{1}/statuses'.format(self.project_id, sha))

    def get_job(self, job_id):
        return self.get('/projects/{0}/jobs/{1}'.format(self.project_id, job_id))

    def trigger_job(self, job_id, action='play'):
        """
        :param job_id: job id
        :param action: string: play, retry (cancel and erase not supported yet)
        :return:
        """
        if action == 'play' or action == 'retry':
            return self.post('/projects/{0}/jobs/{1}/{2}'.format(self.project_id, job_id, action))
        raise (Exception('invalid action'))


def deploy_pod_container(token, host, namespace, project, branch, stage):
    def print_trigger_response(r):
        pprint("triggered job_id {0} stage {1} status {2}".format(r["name"], r["id"], r['status']))
    # create gitlab object
    gl = GitlabProject(token, host, namespace, project)
    #  get commit sha, get last commit based on sha and job by stage name
    sha = gl.get_branch(branch)['commit']['id']
    statuses = gl.get_commit_statuses(sha)
    for sts in statuses:
        status = sts['status']
        job_id = sts["id"]
        if sts['name'] == stage and sts['ref'] == branch:
            if status == 'manual' or status == 'skipped' or status == 'created':
                response = gl.trigger_job(job_id, 'play')
                print_trigger_response(response)
                return
            elif (status == 'pending' or status == 'running'):
                print("stage is currently pending or running, please retry later ...")
                exit(1)
            else:
                response = gl.trigger_job(job_id, 'retry')
                print_trigger_response(response)
                return

# if __name__ == '__main__':
#   """
#     invoke gitlab trigger for
#   """
#   namespace = 'cloudtech'
#   project = 'tf-pod'
#   branch = 'master'
#   stage = 'devops:deploy_perfbean'
#   deploy_pod_container(API_TOKEN, CORP_GITLAB, namespace, project, branch, stage)
