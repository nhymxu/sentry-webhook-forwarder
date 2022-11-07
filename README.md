# sentry-webhook-forwarder
Receive sentry webhook message, re-format and send to slack.


## Setup
Go to Vercel dashboard, and setup two environment variable:
- `API_KEY`: secret key to protect your app
- `SLACK_WEBHOOK`: your slack webhook to post message
- `TELEGRAM_WEBHOOK`: your telegram bot webhook to post message
Format normally like that:
```
TELEGRAM_CHAT_ID = 'channel/group chat id here'
TELEGRAM_BOT_TOKEN = 'bot token here'
TELEGRAM_WEBHOOK = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&parse_mode=HTML&disable_web_page_preview=true'
```

## Deploy
- Install Vercel CLI not you don't have
```shell
yarn global add vercel
```

- Log on
```shell
vercel login
```

- Build
```shell
vercel .
```


## Local dev

Run this command to start web-server
```shell
pip install -r requirements.txt
python local_dev.py
```
