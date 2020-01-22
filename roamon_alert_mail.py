# encoding: UTF-8

import smtplib
from email.mime.text import MIMEText

class MailSender():
    def __init__(self, smtp_host, smtp_port):
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)


    # TODO: 送信失敗時のリトライ
    # TODO: 非同期に送信 (送信に時間がかかった場合、後続の処理も遅れる)
    def send_mail(self, fromaddr, toaddr, subject, msg):

        m = MIMEText(msg)
        m['Subject'] = subject
        m['From'] = fromaddr
        m['To'] = toaddr

        s = smtplib.SMTP(host=self.smtp_host, port=self.smtp_port)
        s.sendmail(fromaddr, toaddr, m.as_string())
        s.close()

