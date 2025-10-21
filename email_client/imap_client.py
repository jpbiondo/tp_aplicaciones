import imaplib
from email.parser import BytesParser
from email import policy


def abrir_sesion_imap_ssl(imap_server_addr, email_addr, email_pass):
    imap_ssl_session = imaplib.IMAP4_SSL(imap_server_addr)
    imap_ssl_session.login(email_addr, email_pass)
    return imap_ssl_session

def leer_correos_imap_ssl(imap_session, cantidad):
    """Lee los correos de la bandeja de entrada usando IMAP de forma robusta."""
    try:
        imap_session.select('inbox')

        # <-- CAMBIO: Usar UID para buscar y obtener identificadores permanentes
        status, messages = imap_session.uid('search', None, 'ALL')
        lista_uids = messages[0].split()

        # Analizar los últimos 5 correos
        for mail_uid in lista_uids[-cantidad:]:
            asunto, remitente, fecha, cuerpo = obtener_mensaje_por_uid(imap_session, mail_uid)

            print(f"UID: {mail_uid.decode()}")
            print(f"Asunto: {asunto}")
            print(f"De: {remitente}")
            print(f"Fecha: {fecha}")
            print(f"Cuerpo: {cuerpo[:150]}...")
            print("-" * 30)
    except Exception as e:
        print(f"Error al leer con IMAP: {e}")

def obtener_mensaje_por_uid(imap_session, uid_buscar):
    imap_session.select('inbox')
    parser = BytesParser(policy=policy.default)
    status, data = imap_session.uid('fetch', uid_buscar, '(RFC822)')
    for response_part in data:
        if isinstance(response_part, tuple):
            msg = parser.parsebytes(response_part[1])

            asunto = msg["Subject"]
            remitente = msg["From"]
            fecha = msg["Date"]
            cuerpo = ""

            for part in msg.walk():
                content_type = part.get_content_type()

                if content_type == 'text/plain':
                    cuerpo = part.get_content()
                    break

            return asunto, remitente, fecha, cuerpo


def eliminar_correo_imap_ssl(imap_server_addr, email_addr, email_pass, uid_correo_eliminar):
    try:
        mail = imaplib.IMAP4_SSL(imap_server_addr)
        mail.login(email_addr, email_pass)
        mail.uid('store', uid_correo_eliminar, '+FLAGS', '\\DELETED')
        mail.expunge()
        mail.logout()
        print(f"Correo con UID {uid_correo_eliminar.decode()} borrado.")
        return True
    except Exception as e:
        print(f"Error al tratar de eliminar con IMAP: {e}")
        return False
