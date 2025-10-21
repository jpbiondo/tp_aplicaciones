import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from email_client.imap_client import obtener_mensaje_por_uid
from email_client.pop3_client import obtener_correo_por_id


def abrir_sesion_smtp(smtp_server, email_addr, email_pass,  smtp_port=587):
    smtp_session = smtplib.SMTP(smtp_server, smtp_port)
    smtp_session.ehlo()
    smtp_session.starttls()
    smtp_session.login(email_addr, email_pass)
    return smtp_session


def enviar_correo_smtp(smtp_session, emisor, destinatario, asunto, cuerpo):
    msg = MIMEMultipart()
    msg['From'] = emisor
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        texto = msg.as_string()
        smtp_session.sendmail(emisor, destinatario, texto)
        print("Correo enviado exitosamente!")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def reenviar_correo_imap_smtp(smtp_session, imap_session, emisor, destinatario, uid_reenviar):
    """
    Obtiene un correo por UID, extrae su asunto y cuerpo, y lo reenvía.
    """
    try:
        print(f"Obteniendo correo con UID: {uid_reenviar.decode()}...")
        asunto, remitente, fecha, cuerpo = obtener_mensaje_por_uid(imap_session, uid_reenviar)

        nuevo_asunto = f"Fwd: {asunto}"

        print(f"Reenviando a: {destinatario}...")
        enviar_correo_smtp(
            smtp_session,
            emisor,
            destinatario,
            nuevo_asunto,
            cuerpo,
        )
    except Exception as e:
        print(f"Error al enviar correo: {e}")


def reenviar_correo_pop3_smtp(smtp_session, pop3_session, emisor, destinatario, id_reenviar):
    """
    Obtiene un correo por UID, extrae su asunto y cuerpo, y lo reenvía.
    """
    try:
        print(f"Obteniendo correo con UID: {id_reenviar.decode()}...")
        asunto, remitente, cuerpo = obtener_correo_por_id(pop3_session, id_reenviar)

        nuevo_asunto = f"Fwd: {asunto}"

        print(f"Reenviando a: {destinatario}...")
        enviar_correo_smtp(
            smtp_session,
            emisor,
            destinatario,
            nuevo_asunto,
            cuerpo,
        )
    except Exception as e:
        print(f"Error al enviar correo: {e}")


def responder_correo_imap_smtp(smtp_session, imap_session, emisor, uid_a_responder, respuesta):
    """
    Obtiene un correo por UID, prepara una respuesta y la envía
    utilizando tu función `enviar_correo_smtp`.
    """
    try:
        print(f"Obteniendo correo con UID: {uid_a_responder.decode()} para responder...")
        asunto, remitente, fecha, cuerpo = obtener_mensaje_por_uid(imap_session, uid_a_responder)

        match = re.search(r'<(.+?)>', remitente)
        destinatario_respuesta = match.group(1) if match else remitente

        nuevo_asunto = f"Re: {asunto}"


        cuerpo_citado = "\n\n"
        cuerpo_citado += f"El {fecha}, {remitente} escribió:\n"
        cuerpo_citado += "\n".join([f"> {linea}" for linea in cuerpo.splitlines()])

        cuerpo_final_respuesta = respuesta + cuerpo_citado

        print(f"Preparando para enviar respuesta a {destinatario_respuesta}...")
        enviar_correo_smtp(
            smtp_session,
            emisor,
            remitente,
            asunto,
            cuerpo
        )
    except Exception as e:
        print(f"Error al enviar correo: {e}")


def responder_correo_pop3_smtp(smtp_session, pop3_session, emisor, id_responder, respuesta):
    """
    Obtiene un correo por UID, prepara una respuesta y la envía
    utilizando tu función `enviar_correo_smtp`.
    """
    try:
        print(f"Obteniendo correo con UID: {id_responder.decode()} para responder...")
        asunto, remitente, fecha, cuerpo = obtener_correo_por_id(pop3_session, id_responder)

        match = re.search(r'<(.+?)>', remitente)
        destinatario_respuesta = match.group(1) if match else remitente

        nuevo_asunto = f"Re: {asunto}"

        cuerpo_citado = "\n\n"
        cuerpo_citado += f"El {fecha}, {remitente} escribió:\n"
        cuerpo_citado += "\n".join([f"> {linea}" for linea in cuerpo.splitlines()])

        cuerpo_final_respuesta = respuesta + cuerpo_citado

        print(f"Preparando para enviar respuesta a {destinatario_respuesta}...")
        enviar_correo_smtp(
            smtp_session,
            emisor,
            remitente,
            asunto,
            cuerpo
        )
    except Exception as e:
        print(f"Error al enviar correo: {e}")