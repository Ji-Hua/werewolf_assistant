from threading import Thread

from flask import render_template, current_app
from flask_mail import Message

from app import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(
        current_app._get_current_object(), msg)).start()


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    print(current_app.config)
    send_email('[烂柯游艺社] 重置密码',
               sender=current_app.config['MAIL_USERNAME'],
               recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))