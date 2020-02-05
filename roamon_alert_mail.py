# encoding: UTF-8

import smtplib
from email.mime.text import MIMEText
import asyncio

class MailSender():
    def __init__(self, smtp_host, smtp_port, sender_email_address):
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.sender_mail_address = sender_email_address


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

        loop = asyncio.get_event_loop()
        loop.run_until_complete(worker())
        # try:
        #     loop.run_until_complete(worker())
        # finally:
        #     loop.close()


