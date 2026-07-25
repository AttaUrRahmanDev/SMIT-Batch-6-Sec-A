import requests, os

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")

url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

payload = {
    "messaging_product": "whatsapp",
    "to": "92XXXXXXXXXX",
    "type": "text",
    "text": {"body": "Hello! Test message from WhatsApp API"}
}

r = requests.post(url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}",
                                "Content-Type": "application/json"},
                  json=payload)

print(r.json())
