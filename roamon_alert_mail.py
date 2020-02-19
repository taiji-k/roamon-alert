# encoding: UTF-8

# Copyright (c) 2019-2020 Japan Network Information Center ("JPNIC")
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute and/or sublicense of
# the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import smtplib
from email.mime.text import MIMEText
import asyncio


class MailSender():
    def __init__(self, smtp_host, smtp_port, sender_email_address):
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.sender_email_address = sender_email_address

    # TODO: 送信失敗時のリトライ
    def send_mail(self, toaddr, subject, msg):
        async def worker():
            fromaddr = self.sender_email_address

            m = MIMEText(msg)
            m['Subject'] = subject
            m['From'] = fromaddr
            m['To'] = toaddr

            s = smtplib.SMTP(host=self.smtp_host, port=self.smtp_port)
            s.sendmail(fromaddr, toaddr, m.as_string())
            s.close()

        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(worker())
        except:
            traceback.print_exc()
