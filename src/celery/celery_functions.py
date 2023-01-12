"""""""""""""""""""""""""""""""""""""""""""""""""CELERY  FUNCTIONS"""""""""""""""""""""""""""""""""""""""""""""""""""""""

from app import celery, db
from flask import session, render_template
from src.database.models import Otp
import datetime
import pytz
import random
import os
import pdfkit
from sendgrid import SendGridAPIClient 
from twilio.rest import Client
from sendgrid.helpers.mail import Mail 
from dotenv import load_dotenv

load_dotenv()


"""Smaple Celery task to check celery performation"""
@celery.task(name='app.add_together')
def add_together(a, b):
    print('In Celery TAsk')
    return a + b

"""CELERY  Tasks"""


"""Task to send OTP on User's phone number"""
@celery.task(name='app.send_sms')
def send_otp(phone,otp):

    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    client = Client(account_sid, auth_token)
    message = client.messages.create(
                    body="Hello! Your otp for registration is - " + str(otp),
                    from_="+16086022741",
                    to ='+91' + str(phone)
                )


"""Task to send OTP on User's Email ID"""
@celery.task(name='app.send_mail')
def send_mail(email,otp):
    sg = SendGridAPIClient("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")
    message = Mail(
                    from_email="kartik.lavkush@unthinkable.co",
                    to_emails= email,
                    subject='OTP Verification Code ',
                    html_content = "Your OTP for reset password - " + str(otp)
                    )
            
    session['response'] = str(otp)
    sg.send(message)


"""Task to generate PDF of Uesr profile details"""
@celery.task(name='app.make_pdf')
def make_pdf(result,pdf):
    path_wkhtmltopdf = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    random_no = random.randrange(000000,999999)
    file_name = f"info_{str(random_no)}.pdf"
    
    html = render_template('index.html',result = result)
    
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    save_pdf = f'D:\one more pdf/{file_name}'


"""Celery task to delete expired OTPs"""
@celery.task(name = 'app.delete_expired_otp')
def delete_expired_otp():
    exp_otp = Otp.query.filter(Otp.expiry<datetime.datetime.utcnow(pytz.timezone('Asia/Kolkata'))).all()
    # if exp_otp:
    #     current_time =  datetime.now(pytz.timezone('Asia/Kolkata'))   
    #     expire_time = Otp.expiry
    #     if (current_time > expire_time):
    for otp in exp_otp:
        db.session.delete(otp)
        db.session.commit()