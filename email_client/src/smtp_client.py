import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email_client.config import IMAP_SERVER_ADDR
from email_client.src.imap_client import obtener_mensaje_por_uid
from email_client.utils import decodificar_cabecera


def enviar_correo_smtp(smtp_server, email_addr, email_pass, destinatario, asunto, cuerpo, smtp_port=587):
    msg = MIMEMultipart()
    msg['From'] = email_addr
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(email_addr, email_pass)
        texto = msg.as_string()
        server.sendmail(email_addr, destinatario, texto)
        server.quit()
        print("Correo enviado exitosamente!")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def reenviar_correo_smtp(smtp_server, email_addr, email_pass, destinatario, uid_reenviar, smtp_port=587):
    """
       Obtiene un correo por UID, extrae su asunto y cuerpo, y lo reenvía.
       """
    print(f"Obteniendo correo con UID: {uid_reenviar.decode()}...")
    msg_original = obtener_mensaje_por_uid(IMAP_SERVER_ADDR, email_addr, email_pass, uid_reenviar)

    if not msg_original:
        print("No se pudo obtener el correo original. Abortando reenvío.")
        return

    # 1. Extraer y construir el nuevo asunto
    asunto_original = decodificar_cabecera(msg_original['Subject'])
    nuevo_asunto = f"Fwd: {asunto_original}"

    # 2. Extraer el cuerpo de texto plano del correo original
    cuerpo_original = ""
    if msg_original.is_multipart():
        for part in msg_original.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or 'utf-8'
                cuerpo_original = part.get_payload(decode=True).decode(charset, errors='replace')
                break  # Nos quedamos con la primera parte de texto plano
    else:
        # Si no es multipart, el cuerpo es el payload principal
        charset = msg_original.get_content_charset() or 'utf-8'
        cuerpo_original = msg_original.get_payload(decode=True).decode(charset, errors='replace')

    if not cuerpo_original:
        print("No se encontró un cuerpo de texto plano en el correo original.")
        return

    print(f"Reenviando a: {destinatario}...")
    enviar_correo_smtp(
        smtp_server=smtp_server,
        email_addr=email_addr,
        email_pass=email_pass,
        destinatario=destinatario,
        asunto=nuevo_asunto,
        cuerpo=cuerpo_original,
        smtp_port=smtp_port
    )


def responder_correo(smtp_server, email_addr, email_pass, uid_a_responder, respuesta):
    """
    Obtiene un correo por UID, prepara una respuesta y la envía
    utilizando tu función `enviar_correo_smtp`.
    """
    print(f"Obteniendo correo con UID: {uid_a_responder.decode()} para responder...")
    msg_original = obtener_mensaje_por_uid(uid_a_responder)

    if not msg_original:
        print("No se pudo obtener el correo original. Abortando respuesta.")
        return

    # 1. Extraer datos del correo original
    asunto_original = decodificar_cabecera(msg_original['Subject'])
    remitente_original_raw = decodificar_cabecera(msg_original['From'])

    match = re.search(r'<(.+?)>', remitente_original_raw)
    destinatario_respuesta = match.group(1) if match else remitente_original_raw

    nuevo_asunto = f"Re: {asunto_original}"

    # 2. Construir el cuerpo de la respuesta
    cuerpo_original = ""
    if msg_original.is_multipart():
        for part in msg_original.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or 'utf-8'
                cuerpo_original = part.get_payload(decode=True).decode(charset, errors='replace')
                break
    else:
        charset = msg_original.get_content_charset() or 'utf-8'
        cuerpo_original = msg_original.get_payload(decode=True).decode(charset, errors='replace')

    cuerpo_citado = "\n\n"
    cuerpo_citado += f"El {msg_original['Date']}, {remitente_original_raw} escribió:\n"
    cuerpo_citado += "\n".join([f"> {linea}" for linea in cuerpo_original.splitlines()])

    cuerpo_final_respuesta = respuesta + cuerpo_citado

    print(f"Preparando para enviar respuesta a {destinatario_respuesta}...")
    enviar_correo_smtp(
        smtp_server=smtp_server,
        email_addr=email_addr,
        email_pass=email_pass,
        destinatario=destinatario_respuesta,
        asunto=nuevo_asunto,
        cuerpo=cuerpo_final_respuesta
    )