# -*- coding: utf-8 -*-
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sender(recipients,title,content):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('hi.stranger.y@gmail.com', 'password')

    people = ""
    for item in recipients:
        # print('이메일 보내는중 :' + item['email'])
        people += item['email']
        people += ","

    msg = MIMEMultipart('alternative')

    # 송신자 설정
    msg['From'] = 'hi.stranger.y@gmail.com'
    # 수신자 설정 (복수는 콤마 구분이다.)
    msg['To'] = 'hi.stranger.y@gmail.com'
    # 참조 수신자 설정
    # msg['To'] = 'hi.stranger.y@gmail.com'
    # 숨은 참조 수신자 설정
    msg['Bcc'] = people
    # 메일 제목
    msg['Subject'] = title

    msg.attach(MIMEText(content, 'html'))
    server.send_message(msg)

    print('이메일 보내기 완료')
    server.quit()
