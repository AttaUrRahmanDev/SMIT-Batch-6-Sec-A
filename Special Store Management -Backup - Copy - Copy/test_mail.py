import os
import smtplib, ssl
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL_USER")
PASS = os.getenv("EMAIL_PASSWORD")

print("USER:", EMAIL)
print("PASS:", PASS)

msg = EmailMessage()
msg['Subject'] = "SMTP TEST"
msg['From'] = EMAIL
msg['To'] = EMAIL
msg.set_content("SMTP test email")

context = ssl.create_default_context()
with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
    smtp.login(EMAIL, PASS)
    smtp.send_message(msg)

print("SUCCESS!")
