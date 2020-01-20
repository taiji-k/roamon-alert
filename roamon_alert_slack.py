# encoding: UTF-8

import requests
import sys

def send_slack(token, channel, text, username, url = 'https://slack.com/api/chat.postMessage'):
    # post
    post_json = {
        'token': token,
        'text': text,
        'channel': channel,
        'username': username,
        'link_names': 1
    }
    requests.post(URL, data = post_json)