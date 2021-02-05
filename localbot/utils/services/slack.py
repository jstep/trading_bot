import requests


def post(message, channel='#reporting', username='TradeBot', icon_emoji=':chart_with_upwards_trend:'):
    hook = "https://hooks.slack.com/services/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"
    headers = {'content-type': 'application/json'}
    payload = {
        "text": message,
        "channel": channel,
        "username": username,
        "icon_emoji": icon_emoji,
        "fallback": "fallback text"
    }

    r = requests.post(hook, json=payload, headers=headers)
    if r.status_code != 200:
        print 'Request to slack returned an error {}, the response is:\n{}'\
            .format(r.status_code, r.text)