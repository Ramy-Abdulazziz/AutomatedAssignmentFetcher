import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json as js


def get_email_details():
    with open("AssignmentFetcher/Credentials/notification-details.json", "r") as details:

        details = js.load(details)

    email_details = details.get('email-details')
    sender = email_details.get('sender')
    password = email_details.get('pass')


    phone_details = details.get('phone-details')
    number = phone_details.get('number')

    receiver = f'{number}@tmomail.net'

    email_details = {'sender': sender,
                     "password": password, 'receiver': receiver}

    return email_details


def send_email():

    email_details = get_email_details()

    sender = email_details.get('sender')
    pswrd = email_details.get('password')
    receiver = email_details.get('receiver')

    subject = 'Assignment Fetching notification'
    body = "Assignment Fetching Script about to run - be ready to authenticate"

    msg = MIMEMultipart() 
    msg['From'] = sender 
    msg['To'] = receiver
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:    

        smtp_server.login(sender, pswrd)
        text = msg.as_string()
        smtp_server.sendmail(sender, receiver, text)
        smtp_server.quit()
