"""Utility class for enhanced Slack UI features. Including Modal Forms"""
from __future__ import print_function

import json
import requests

HEADER = {"Content-type": "application/json"}

# ToDo: move this into parameter store.
# Put all Slack channels that have a webhook here.
SLACK_NAME_TO_WEBHOOK_MAP = {
    'sr-slack-deploy': 'https://hooks.slack.com/services/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'
}


# Exception class to pass messages back to Slack UI
class ShowEnhancedSlackError(Exception):
    """Raise this exception when you want to show an error in Slack UI."""
    def __init__(self, *args):
        Exception.__init__(self, *args)


def respond(err, res=None):
    """Response wrapper needed for all Slack UI responses."""
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


# Generate an enhanced response to an exception. More distinct than just Markdown text.
def error_response(text, post=False, response_url=''):
    """Slack UI response for errors."""

    slack = {
        "response_type": "ephemeral",
        "attachments": [
            {
                "text": "%s" % text,
                "mrkdwn_in": ["text"],
                "color": "#ff3d3d"
            }
        ]
    }
    if post:
        requests.post(response_url, data=json.dumps(slack), headers=HEADER)
        return None

    return respond(None, slack)


"""NOTE: the raw format needs to look something like this.

    {
        'body':
            'token=bTS__REDACTED__WG7aB4'
            '&team_id=T025H70HY&team_domain=roku&channel_id=D5FKEN3HD&'
            'channel_name=directmessage&user_id=U5E4YURHN&user_name=asnyder&command=%2Fctidev&text=help&'
            'response_url=https%3A%2F%2Fhooks.slack.com%2Fcommands%2FT025H70HY%2F335764193537%2FOCHFLvLdTjfGNTagKYHDANiI&'
            'trigger_id=123456789012.123456789012.ab4ad1ed10dccc59cb03000c7cd16db5',
         'resource': '/slackapi',
         'requestContext': {
             'requestTime': '26/Mar/2018:17:42:59 +0000',
             'protocol': 'HTTP/1.1',
             'resourceId': 'n9ibvg',
             'apiId': '4umlc7fcuh',
             'resourcePath': '/slackapi',
             'httpMethod': 'POST',
             'requestId': '1fc819ca-311d-11e8-90ac-856a4e02a6b5',
             'extendedRequestId': 'EXSdfGTtvHcFhUw=',
             'path': '/dev/slackapi',
             'stage': 'dev',
             'requestTimeEpoch': 1522086179182,
             'identity': {
                 'userArn': None,
                 'cognitoAuthenticationType': None,
                 'accessKey': None,
                 'caller': None,
                 'userAgent': 'Slackbot 1.0 (+https://api.slack.com/robots)',
                 'user': None,
                 'cognitoIdentityPoolId': None,
                 'cognitoIdentityId': None,
                 'cognitoAuthenticationProvider': None,
                 'sourceIp': '54.85.176.102',
                 'accountId': None
             },
             'accountId': '123456789012'  # TODO: Replace with actual account ID
         },
        'queryStringParameters': None,
        'httpMethod': 'POST',
        'pathParameters': None,
        'headers': {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Via': '1.1 738914e1c987985551e83e7e80882749.cloudfront.net (CloudFront)',
            'Accept-Encoding': 'gzip,deflate',
            'CloudFront-Is-SmartTV-Viewer': 'false',
            'CloudFront-Forwarded-Proto': 'https',
            'X-Forwarded-For': '54.85.176.102, 204.246.180.43',
            'CloudFront-Viewer-Country': 'US',
            'Accept': 'application/json,*/*',
            'User-Agent': 'Slackbot 1.0 (+https://api.slack.com/robots)',
            'X-Amzn-Trace-Id': 'Root=1-5ab93123-4a7d097e17199de869406272',
            'Host': 'ah9aodktq6.execute-api.us-east-1.amazonaws.com',
            'X-Forwarded-Proto': 'https',
            'X-Amz-Cf-Id': 'QScRVRCqsVUjTFmu-nByLHCkxAp8BJixojsg_1nB3g1lQRgPPafa1A==',
            'CloudFront-Is-Tablet-Viewer': 'false',
            'X-Forwarded-Port': '443',
            'CloudFront-Is-Mobile-Viewer': 'false',
            'CloudFront-Is-Desktop-Viewer': 'true'
        },
        'stageVariables': None,
        'path': '/slackapi',
        'isBase64Encoded': False
    }

"""


def open_raw_modal_view(slack_json_payload, trigger_id, post=False, response_url=None):
    """

    :param slack_json_payload: JSON string in Slack JSON format.
    :param trigger_id:
    :return: String JSON views.open response.
    """

    # ToDo: Do we need to wrap this with something? Where does trigger_id go?
    slack = slack_json_payload


    if post:
        requests.post(response_url, data=json.dumps(slack), headers=HEADER)
        return None

    return respond(None, slack)


def start_modal_json_build(app_name):
    """
    Start building a modal block of json.

    the standard opening block for a modal input

    When finished building a block it needs to be closed with end_modal_json_build(slack_json)
    :return: string json.
    """
    json = """{
	"type": "modal",
	"title": {
		"type": "plain_text",
		"text": "{}",
		"emoji": true
	},
	"submit": {
		"type": "plain_text",
		"text": "Submit",
		"emoji": true
	},
	"close": {
		"type": "plain_text",
		"text": "Cancel",
		"emoji": true
	},
	"blocks": [        
"""
    json = json.format(app_name)
    return json


def finish_modal_json_build(slack_json):
    """
    The closing item need to build a modal UI block.

    :return:
    """
    ret_val = slack_json+']}'

    temp_print_debug('INFO', 'Verify this is valid JSON:\n{}'.format(ret_val))

    return ret_val


# Below is an example markdown block.
"""{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "This is a mrkdwn section block :ghost: *this is bold*, and ~this is crossed out~, and <https://google.com|this is a link>"
        }
    },
"""


def add_markdown_text_block(slack_json, markdown_text):
    """
    Add a block of markdown text.
    :param slack_json:
    :param markdown_text: String that is markdown format, but not json. See example in code above.
    :return:
    """
    json_data = """{
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "{}"
        }
    },
    """
    json_data = json_data.format(markdown_text)
    return json_data


def temp_print_debug(msg, level=None):
    """
    Temporary debug messages until new Slack format is figured out.
    :param msg:
    :param level:
    :return:
    """
    if level:
        print('Slack_UI - {}: {}'.format(level.upper(), msg))
    else:
        print('Slack-UI: {}'.format(msg))


def poc_table_fixed_result(response_url):
    """

    :return:
    """
    build_kit_resp = """
        {
            "type": "section",
            "text": {
                "text": "Conference Standings:",
                "type": "mrkdwn"
            },
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Team*"
                },
                {
                    "type": "mrkdwn",
                    "text": "*W-L*"
                },
                {
                    "type": "plain_text",
                    "text": "Team1\nTeam2\nTeam3\nTeam4\nTeam5\n"
                },
                {
                    "type": "plain_text",
                    "text": "1\n2\n3\n4\n5\n"
                }
            ]
        }
    """

    requests.post(response_url, data=json.dumps(build_kit_resp), headers=HEADER)
    return None