import imaplib
import email

from email_client.utils import decodificar_cabecera


def leer_correos_imap_ssl(imap_server_addr, email_addr, email_pass):
    """Lee los correos de la bandeja de entrada usando IMAP de forma robusta."""
    try:
        mail = imaplib.IMAP4_SSL(imap_server_addr)
        mail.login(email_addr, email_pass)
        mail.select('inbox')

        # <-- CAMBIO: Usar UID para buscar y obtener identificadores permanentes
        status, messages = mail.uid('search', None, 'ALL')
        lista_uids = messages[0].split()

        # Analizar los últimos 5 correos
        for mail_uid in lista_uids[-5:]:
            # <-- CAMBIO: Usar UID para recuperar el correo
            status, data = mail.uid('fetch', mail_uid, '(RFC822)')
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    # <-- CAMBIO: Usar la función auxiliar para una decodificación segura
                    asunto = decodificar_cabecera(msg["Subject"])
                    remitente = decodificar_cabecera(msg["From"])
                    fecha = decodificar_cabecera(msg["Date"])

                    print(f"UID: {mail_uid.decode()}")
                    print(f"Asunto: {asunto}")
                    print(f"De: {remitente}")
                    print(f"Fecha: {fecha}")

                    # Extraer cuerpo del correo
                    cuerpo = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                try:
                                    # <-- CAMBIO: Usar el charset del correo para decodificar
                                    charset = part.get_content_charset() or 'utf-8'
                                    cuerpo = part.get_payload(decode=True).decode(charset, errors='replace')
                                    break  # Encontramos el texto plano, salimos del bucle
                                except Exception as e:
                                    # <-- CAMBIO: Manejo de errores específico
                                    print(f"  [Advertencia] No se pudo decodificar una parte: {e}")
                    else:
                        # <-- CAMBIO: Misma lógica de decodificación para correos simples
                        charset = msg.get_content_charset() or 'utf-8'
                        cuerpo = msg.get_payload(decode=True).decode(charset, errors='replace')

                    if cuerpo:
                        # Limpiamos saltos de línea para una vista previa más limpia
                        preview = ' '.join(cuerpo.splitlines())
                        print(f"Cuerpo: {preview[:150]}...")
                    else:
                        print("  (El correo no contiene una parte de texto plano legible)")

                    print("-" * 40)
        mail.logout()
    except Exception as e:
        print(f"Error al leer con IMAP: {e}")

def obtener_mensaje_por_uid(imap_server_addr, email_addr, email_pass, uid_buscar):
    try:
        mail = imaplib.IMAP4_SSL(imap_server_addr)
        mail.login(email_addr, email_pass)
        mail.select('inbox')

        # <-- CAMBIO: Usar UID para buscar y obtener identificadores permanentes
        status, data = mail.uid('fetch', uid_buscar, '(RFC822)')
        if status == 'OK':
            raw_email = data[0][1]
            mail.logout()
            return raw_email
        else:
            print("No se pudo encontrar el correo con ese UID.")
            mail.logout()
            return None
    except Exception as e:
        print(f"Error al buscar con IMAP: {e}")
        return None


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
