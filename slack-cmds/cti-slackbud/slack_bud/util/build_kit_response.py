"""Utility class for Slack UI responses."""
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
class ShowBuildKitError(Exception):
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


def test_build_kit(is_public=False, response_url='', post=False):

    response_type = 'ephemeral'
    if is_public:
        response_type = "in_channel"

    test_resp = {
        "response_type": response_type,
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Android PhraseCloud for Positive Ratings"
                }
            },
            {
                "type": "image",
                "block_id": "image_block",
                "image_url": "https://images.sr.asnyder.com/sr/uploads/images/2aed939b-0843-4228-a601-66f0b2fbf2ae_image",
                "alt_text": "random"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Click for bigger image. <https://images.sr.asnyder.com/sr/uploads/images/2aed939b-0843-4228-a601-66f0b2fbf2ae_image>"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Select To See Reviews with a Phrase"
                },
                "accessory": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an phrase",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Private Listening"
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Connection Errors"
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Love"
                            },
                            "value": "value-2"
                        }
                    ]
                }
            }
        ]
    }

    if post:
        requests.post(response_url, data=json.dumps(test_resp), headers=HEADER)
        return None

    return respond(None, test_resp)


def test_build_kit2(is_public=False, response_url='', post=False):

    response_type = 'ephemeral'
    if is_public:
        response_type = "in_channel"

    test_resp = {
        "blocks": [
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Remote*\n:star::star::star::star: 1000 reviews\n I love this app can control multiple TVs I can control my kids TV from my bedroom to make sure it stays off when it's time to go to bed"
                },
                "accessory": {
                    "type": "image",
                    "image_url": "https://images.sr.asnyder.com/sr/uploads/images/13466391-7e2f-47fc-96f0-fb43b77de646_image",
                    "alt_text": "alt text for image"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Private Listening*\n:star::star::star::star: 600 reviews\n I use this app for private listening while on my treadmill at home so I don't have to have my tv at full volume Lately my phone has lost its mind while I'm using the app"
                },
                "accessory": {
                    "type": "image",
                    "image_url": "https://www.flatpanelshd.com/pictures/rokuos75-2l.jpg",
                    "alt_text": "alt text for image"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Connectivity*\n:star::star: 539 reviews\n When I have the remote open on one tab and then I go to a different app, when I come back on this one I have to reconnect the phone to the TV all over again"
                },
                "accessory": {
                    "type": "image",
                    "image_url": "https://images.sr.asnyder.com/sr/uploads/images/a6fe3401-014f-48f9-8c11-6d79fc13d85a_image",
                    "alt_text": "alt text for image"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*General*\n:star::star::star: 2082 reviews\n I would really recommend the  Yum Koh Moo Yang - Spicy lime dressing and roasted quick marinated pork shoulder, basil leaves, chili & rice powder."
                },
                "accessory": {
                    "type": "image",
                    "image_url": "https://www.lifewire.com/thmb/m6cmgQ6TCRFtg_kJ6PXymWN_G_A=/1500x844/smart/filters:no_upscale()/roku-mobile-redacted-e77c00269e3d77.jpg",
                    "alt_text": "alt text for image"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Show Ratings for Remote",
                            "emoji": True
                        },
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Show Ratings for Pvt Listening",
                            "emoji": True
                        },
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Show Ratings for Connectivity",
                            "emoji": True
                        },
                        "value": "click_me_123"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Show Ratings for General",
                            "emoji": True
                        },
                        "value": "click_me_123"
                    }
                ]
            }
        ]
    }

    if post:
        requests.post(response_url, data=json.dumps(test_resp), headers=HEADER)
        return None

    return respond(None, test_resp)


def test_build_kit3(is_public=False, response_url='', post=False):

    response_type = 'ephemeral'
    if is_public:
        response_type = "in_channel"

    test_resp = {
        # "response_type": response_type,
        "title": {
            "type": "plain_text",
            "text": "Reply To Review"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit"
        },
        "type": "modal",
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Section block with radio buttons"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thank you for your feedback",
                                "emoji": True
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thanks for reporting the issue. We will fix this.",
                                "emoji": True
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Glad To Know you are enjoying Roku",
                                "emoji": True
                            },
                            "value": "value-2"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "ml_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Type your own reply"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": " "
                }
            }
        ]
    }

    # if post:
    #     requests.post(response_url, data=json.dumps(test_resp), headers=HEADER)
    #     return None

    return respond(None, test_resp)


def test_build_kit_table(is_public=False, response_url='', post=False):

    response_type = 'ephemeral'
    if is_public:
        response_type = "in_channel"

    test_resp = {
        # "response_type": response_type,
        "title": {
            "type": "plain_text",
            "text": "Reply To Review"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit"
        },
        "type": "modal",
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Section block with radio buttons"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thank you for your feedback",
                                "emoji": True
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thanks for reporting the issue. We will fix this.",
                                "emoji": True
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Glad To Know you are enjoying Roku",
                                "emoji": True
                            },
                            "value": "value-2"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "ml_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Type your own reply"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": " "
                }
            }
        ]
    }

    # if post:
    #     requests.post(response_url, data=json.dumps(test_resp), headers=HEADER)
    #     return None

    return respond(None, test_resp)


def hack_a_thon_modal(trigger_id):
    """
    Send a fixed request to make the modal appear.
    :return:
    """

    token = 'abc'
    modal = json.dumps(get_modal())
    args = {
        'token': token,
        'trigger_id': trigger_id,
        'view': modal
    }

    requests.post('https://slack.com/api/views.open', json=json.dumps(args))


def get_modal():
    return {
        # "response_type": response_type,
        "title": {
            "type": "plain_text",
            "text": "Reply To Review"
        },
        "submit": {
            "type": "plain_text",
            "text": "Submit"
        },
        "type": "modal",
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Section block with radio buttons"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thank you for your feedback",
                                "emoji": True
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Thanks for reporting the issue. We will fix this.",
                                "emoji": True
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Glad To Know you are enjoying Roku",
                                "emoji": True
                            },
                            "value": "value-2"
                        }
                    ]
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "ml_input",
                    "multiline": True,
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Type your own reply"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": " "
                }
            }
        ]
    }