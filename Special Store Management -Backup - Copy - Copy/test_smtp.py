from dotenv import load_dotenv
import os, ssl, smtplib

load_dotenv()  # loads .env in the same folder

print("EMAIL_USER:", os.getenv("EMAIL_USER"))
pw = os.getenv("EMAIL_PASSWORD") or ""
print("EMAIL_PASSWORD set:", bool(pw), "length:", len(pw))
print("SMTP_SERVER:", os.getenv("SMTP_SERVER"))
print("SMTP_PORT:", os.getenv("SMTP_PORT"))

smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
smtp_port = int(os.getenv("SMTP_PORT", 465))
smtp_user = os.getenv("EMAIL_USER")
smtp_pass = os.getenv("EMAIL_PASSWORD")

try:
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
        smtp.login(smtp_user, smtp_pass)
    print("SMTP login successful")
except Exception as e:
    print("SMTP login failed:", repr(e))