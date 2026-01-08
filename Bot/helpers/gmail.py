#Imports independientes
import os, base64, pickle
import base64
import pickle

#Imports gmail
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.base import MIMEBase
from email import encoders

#Imports mios
from Bot.helpers.logs import registrar_log
from Bot.constantes.rutas import RUTA_CREDENCIALES

# Permisos mínimos necesarios
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def get_gmail_service():
    creds = None
    token_path = os.path.join(RUTA_CREDENCIALES, "token_gmail.pickle")
    creds_path = os.path.join(RUTA_CREDENCIALES, "credenciales.json")

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    # Si no hay credenciales válidas, iniciar el flujo de autenticación
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(creds_path):
                raise FileNotFoundError("Falta el archivo credentials.json en bot/config/")
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)

    service = build("gmail", "v1", credentials=creds)
    return service

def enviar_gmail(carpeta_logs: str, to: str, subject: str, body_html: str, body_text: str | None = None, ruta_excel: str | None = None):
    service = get_gmail_service()

    # Cambiamos a "mixed" para permitir adjuntos
    message = MIMEMultipart("mixed")
    message["to"] = to
    message["subject"] = subject

    # Crear la parte de texto (HTML y Plano)
    msg_body = MIMEMultipart("alternative")
    if body_text:
        msg_body.attach(MIMEText(body_text, "plain"))
    msg_body.attach(MIMEText(body_html, "html"))
    
    # Adjuntamos el cuerpo al mensaje principal
    message.attach(msg_body)

    # --- LÓGICA PARA ADJUNTAR EL EXCEL ---
    if ruta_excel and os.path.exists(ruta_excel):
        try:
            with open(ruta_excel, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            
            # Codificamos en base64 para el envío
            encoders.encode_base64(part)
            
            # Le ponemos el nombre al archivo que verá el cliente
            nombre_archivo = os.path.basename(ruta_excel)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={nombre_archivo}",
            )
            message.attach(part)
        except Exception as e:
            registrar_log(carpeta_logs, f"Error al leer el archivo para adjuntar: {e}", "ERROR")

    # Codificar mensaje completo
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        sent = service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        registrar_log(carpeta_logs, f"Correo enviado correctamente a {to}. ID: {sent['id']}", "SUCCESS")
        return sent
    except Exception as e:
        registrar_log(carpeta_logs, f"Error al enviar correo a {to}: {e}", "ERROR")
        return None