import poplib
from email.parser import BytesParser
from email import policy

def abrir_sesion_pop3_ssl(pop3_server, email_addr, email_pass):
    pop3_ssl_session = poplib.POP3_SSL(pop3_server)
    pop3_ssl_session.user(email_addr)
    pop3_ssl_session.pass_(email_pass)

    return pop3_ssl_session

def leer_correos_pop3(pop3_session, cantidad):
    """Lee y descarga correos usando POP3."""
    try:
        num_messages = len(pop3_session.list()[1])
        print(f"Hay {num_messages} correos en el buzón.")

        for i in range(1, cantidad):
            asunto, cuerpo = obtener_correo_por_id(pop3_session, i)
            print(f"Correo {i}: Asunto - {asunto}")
            print(f"Cuerpo: {cuerpo[:150]}...")
            print("-" * 30)
    except Exception as e:
        print(f"Error al leer con POP3: {e}")

def obtener_correo_por_id(pop3_session, id):
    response, lines, octets = pop3_session.retr(id)

    msg_content = b'\n'.join(lines)
    parser = BytesParser(policy=policy.default)
    msg = parser.parsebytes(msg_content)

    asunto = msg['Subject']
    remitente = msg['From']
    cuerpo = ""
    for part in msg.walk():
        content_type = part.get_content_type()

        if content_type == 'text/plain':
            cuerpo = part.get_content()
            break

    return asunto, remitente, cuerpo

def eliminar_correo_pop3(pop_session, id):
    try:
        pop_session.dele(id)
        print(f"Correo con UID {id.decode()} borrado.")
        return True
    except Exception as e:
        print(f"Error al tratar de eliminar con IMAP: {e}")
        return False


