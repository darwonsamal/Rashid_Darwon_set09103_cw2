import time
from flask import current_app, Flask

from flask_mail import Message, Mail
import datetime
import arrow
import bleach
from settings import MAIL_USERNAME


import os

app = Flask(__name__)


def utc_now_ts():
    return int(time.time())

def utc_now_ts_ms():
    return lambda: int(round(time.time() * 1000))

def ms_stamp_humanize(ts):
    ts = datetime.datetime.fromtimestamp(ts/1000.0)
    return arrow.get(ts).humanize()

def linkify(text):
    text = bleach.clean(text, tags=[], attributes={}, styles=[], strip=True)
    return bleach.linkify(text)

with app.app_context():

    app.config.from_pyfile('../settings.py')
    mail = Mail(app)

    
    def email(toEmail, subject, bodyHtml, bodyText):
        
        print(app.config)
        msg = Message(subject = subject, recipients = [toEmail], sender = MAIL_USERNAME)

        msg.body = bodyText
        msg.html = bodyHtml
        mail.send(msg)


def fetchNotifications(logged_user):

    notifications = Notification.objects.filter(toUser = logged_user.username)

    nlist = []

    for x in notifications:
        nlist.append(x)

    session['notifications'] = nlist