import json
import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from fastapi import FastAPI, HTTPException, Request

logger = logging.getLogger()
logger.setLevel(logging.INFO)

API_KEY = os.getenv('API_KEY')
SLACK_WEBHOOK = os.getenv('SLACK_WEBHOOK')

app = FastAPI()

SLACK_MSG_COLORS = {
    'warning': '#f2c744',
    'error': '#e70707',
    'info': '#d0d0d0'
}


async def parse_event_tags(tag_list):
    """
    Convert list of tag to tag dict

    :param tag_list:
    :return:
    """
    return {r[0]: r[1] for r in tag_list}


async def build_slack_message_block(msg):
    """
    Build Slack block message

    building layout https://api.slack.com/messaging/composing/layouts

    :param msg:
    :return:
    """
    project_slug = msg['project_slug']

    # project slug format: dev-project-name, stg-project-name, prod-project-name
    run_env = project_slug.split('-')[0]

    tags = await parse_event_tags(msg.get('event', {}).get('tags', {}))

    dt = datetime.fromtimestamp(
        msg['event']['timestamp'],
        tz=ZoneInfo('UTC')
    )
    local_dt = dt.astimezone(tz=ZoneInfo('Asia/Ho_Chi_Minh'))

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": project_slug
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*severity:*\n{msg['level'].upper()}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*timestamp:*\n{local_dt}"
                }
            ]
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*hostname:*\n{tags.get('server_name')}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*environment:*\n{run_env}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*event id:* <{msg['url']}|{msg['event']['event_id']}>"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*message*:\n{msg['message']}"
            }
        }
    ]


@app.get('/')
async def catch_all_other():
    return {'msg': 'Nothing here'}


@app.post('/webhook/sentry/{api_key}')
async def webhook_sentry(api_key: str, request: Request):
    if api_key != API_KEY:
        raise HTTPException(status_code=404, detail="Project not found")

    msg = await request.body()
    issue = json.loads(msg)

    # Begin slack
    color = SLACK_MSG_COLORS.get(issue['level'].lower(), SLACK_MSG_COLORS['info'])

    slack_msg = {
        'attachments': [
            {
                "color": f"{color}",
                "blocks": await build_slack_message_block(issue)
            }
        ]
    }

    try:
        r = requests.post(SLACK_WEBHOOK, json=slack_msg)

        # Handling error: https://api.slack.com/messaging/webhooks#handling_errors
        r.raise_for_status()
    except Exception as e:
        logger.error(e)
        raise e
    # End slack

    return {'msg': 'ok'}
