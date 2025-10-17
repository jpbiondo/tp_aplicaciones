import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

IMAP_SERVER_ADDR = os.getenv("IMAP_SERVER_ADDR")
POP3_SERVER_ADDR = os.getenv("POP3_SERVER_ADDR")
SMTP_SERVER_ADDR = os.getenv("SMTP_SERVER_ADDR")

if not EMAIL_PASSWORD:
    raise ValueError("Error: La variable EMAIL_PASSWORD no está definida")