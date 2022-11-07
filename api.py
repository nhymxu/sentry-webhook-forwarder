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
TELEGRAM_WEBHOOK = os.getenv('TELEGRAM_WEBHOOK')

app = FastAPI()


async def parse_event_tags(tag_list):
    """
    Convert list of tag to tag dict

    :param tag_list:
    :return:
    """
    return {r[0]: r[1] for r in tag_list}


async def _build_slack_message_block(msg):
    """
    Build Slack block message

    building layout https://api.slack.com/messaging/composing/layouts

    :param msg:
    :return:
    """
    project_slug = msg.get('project_slug')

    # project slug format: dev-project-name, stg-project-name, prod-project-name
    run_env = project_slug.split('-')[0]

    tags = await parse_event_tags(msg.get('event', {}).get('tags', {}))

    dt = datetime.fromtimestamp(
        msg.get('event', {}).get('timestamp', datetime.now().timestamp()),
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
                    "text": f"*severity:*\n{msg.get('level', '').upper()}"
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
                "text": '*message*:\n{}\n{}\n{}'.format(
                    msg.get('event', {}).get('title', ''),
                    msg.get('message', ''),
                    msg.get('culprit', '')
                )
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "See more",
                    "emoji": True
                },
                "value": "show_more_information",
                "url": msg['url'],
                "action_id": "button-action"
            }
        }
    ]


async def _build_telegram_message_block(msg: dict) -> str:
    """
    Build telegram block message

    :param msg:
    :return:
    """
    project_slug = msg.get('project_slug')

    # project slug format: dev-project-name, stg-project-name, prod-project-name
    run_env = project_slug.split('-')[0]

    tags = await parse_event_tags(msg.get('event', {}).get('tags', {}))

    dt = datetime.fromtimestamp(
        msg.get('event', {}).get('timestamp', datetime.now().timestamp()),
        tz=ZoneInfo('UTC')
    )
    local_dt = dt.astimezone(tz=ZoneInfo('Asia/Ho_Chi_Minh'))

    output_message = f"Sentry / {project_slug} - {local_dt}\n"

    output_message += f"*message*:\n{msg.get('message')}"

    output_message += "\n\n#notification"

    return output_message


@app.get('/')
async def catch_all_other():
    """
    Other catch all function for vercel

    :return:
    """
    return {'msg': 'Nothing here'}


@app.post('/webhook/slack/{api_key}')
async def webhook_slack(api_key: str, request: Request):
    """
    Endpoint receive sentry message and forward to Slack

    :param api_key:
    :param request:
    :return:
    """
    SLACK_MSG_COLORS = {
        'warning': '#f2c744',
        'error': '#e70707',
        'info': '#d0d0d0'
    }

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
                "blocks": await _build_slack_message_block(issue)
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

    # return slack_msg
    return {'msg': 'ok'}


@app.post('/webhook/telegram/{api_key}')
async def webhook_telegram(api_key: str, request: Request):
    """
    Endpoint receive sentry message and forward to Telegram

    :param api_key:
    :param request:
    :return:
    """
    if api_key != API_KEY:
        raise HTTPException(status_code=404, detail="Project not found")

    msg = await request.body()
    issue = json.loads(msg)

    message_builder = _build_telegram_message_block(issue)

    try:
        url = f'{TELEGRAM_WEBHOOK}&text={message_builder}'
        r = requests.get(url)
        r.raise_for_status()

        response = r.json()
        if not response['ok']:
            raise ValueError("Failed to send message to Telegram")
    except Exception as e:
        logger.error(e)
        raise e

    return {'msg': 'ok'}
