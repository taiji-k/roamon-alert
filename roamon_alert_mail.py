# encoding: UTF-8

import smtplib
from email.mime.text import MIMEText


def send_mail(fromaddr, toaddr, subject, msg):

    m = MIMEText(msg)
    m['Subject'] = subject
    m['From'] = fromaddr
    m['To'] = toaddr

    s = smtplib.SMTP(host="mailhog", port=1025)
    s.sendmail(fromaddr, toaddr, m.as_string())
    s.close()

