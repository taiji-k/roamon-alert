# encoding: UTF-8

import slackweb
import asyncio


def send_slack(text, url='https://slack.com/api/chat.postMessage'):
    # TODO: もっと凝ったメッセージを送る
    # TODO: 送信失敗時のリトライの実装
    async def worker():
        slackweb.Slack(url="https://hooks.slack.com/services/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").notify(
            text=text)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(worker())
