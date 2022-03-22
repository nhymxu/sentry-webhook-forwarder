# slack-sentry-bot
Receive sentry webhook message, re-format and send to slack.


## Setup
Go to Vercel dashboard, and setup two environment variable:
- `API_KEY`: secret key to protect your app
- `SLACK_WEBHOOK`: your slack webhook to post message

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
