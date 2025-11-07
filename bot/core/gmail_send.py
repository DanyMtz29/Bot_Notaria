from __future__ import annotations
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from loguru import logger

# Permisos mínimos necesarios
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    creds = None
    token_path = "bot/config/token_gmail.pickle"
    creds_path = "bot/config/credenciales.json"

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, iniciar el flujo de autenticación
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError("⚠️ Falta el archivo credentials.json en bot/config/")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)
    return service

def send_email(to: str, subject: str, body_html: str, body_text: str | None = None):
    service = get_gmail_service()

    message = MIMEMultipart("alternative")
    message["to"] = to
    message["subject"] = subject

    if body_text:
        message.attach(MIMEText(body_text, "plain"))
    message.attach(MIMEText(body_html, "html"))

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        logger.success(f"✅ Correo enviado correctamente a {to}. ID: {sent['id']}")
        return sent
    except Exception as e:
        logger.error(f"❌ Error al enviar correo a {to}: {e}")
        return None
