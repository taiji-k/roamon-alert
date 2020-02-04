# encoding: UTF-8

import requests
import json
import slackweb
import asyncio

def send_slack(text, url = 'https://slack.com/api/chat.postMessage'):
    # TODO: もっと凝ったメッセージを送る
    # TODO: 送信失敗時のリトライの実装
    async def worker():
        slackweb.Slack(url="https://hooks.slack.com/services/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").notify(text=text)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker())
    # try:
    #     loop.run_until_complete(worker())
    # finally:
    #     loop.close()

    # username = "roamon_notify"
    # link_names = 3
    #
    # requests.post(url, data=json.dumps({
    #     'text': text,  # 通知内容
    #     'username': username,  # ユーザー名
    #     'icon_emoji': u':smile_cat:',  # アイコン
    #     'link_names': link_names,  # 名前をリンク化
    # }))


# def send_slack(token, channel, text, username, url = 'https://slack.com/api/chat.postMessage'):
#     # post
#     post_json = {
#         'token': token,
#         'text': text,
#         'channel': channel,
#         'username': username,
#         'link_names': 1
#     }
#     requests.post(URL, data = post_json)