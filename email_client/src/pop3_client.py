import poplib
import email
from email.header import decode_header

def leer_correos_pop3(pop3_server, email_addr, email_pass):
    """Lee y descarga correos usando POP3."""
    try:
        server = poplib.POP3_SSL(pop3_server)
        server.user(email_addr)
        server.pass_(email_pass)

        num_messages = len(server.list()[1])
        print(f"Hay {num_messages} correos en el buzón.")

        for i in range(1, 10):
            # retr() recupera el mensaje completo
            response, lines, octets = server.retr(i)

            msg_content = b'\n'.join(lines)
            msg = email.message_from_bytes(msg_content)

            # --- SECCIÓN CORREGIDA ---
            asunto_completo = []
            for fragmento, codificacion in decode_header(msg['subject']):
                if isinstance(fragmento, bytes):
                    # Si la codificación no está especificada, intentamos con las más comunes
                    if codificacion is None:
                        try:
                            asunto_completo.append(fragmento.decode('utf-8'))
                        except UnicodeDecodeError:
                            # Fallback a latin-1 si utf-8 falla
                            asunto_completo.append(fragmento.decode('iso-8859-1', errors='replace'))
                    else:
                        try:
                            asunto_completo.append(fragmento.decode(codificacion, errors='replace'))
                        except LookupError:  # Si la codificación es desconocida
                            asunto_completo.append(fragmento.decode('iso-8859-1', errors='replace'))
                else:
                    # Si ya es un string, simplemente lo añadimos
                    asunto_completo.append(fragmento)

            asunto = "".join(asunto_completo)
            # --- FIN DE LA SECCIÓN CORREGIDA ---

            # ... (dentro del bucle for, después de decodificar el asunto) ...

            cuerpo = ""
            # 1. Comprobar si el correo es multipart
            if msg.is_multipart():
                # 2. Iterar sobre las partes del correo
                for part in msg.walk():
                    # Buscamos la primera parte que sea de texto plano
                    if part.get_content_type() == 'text/plain':
                        try:
                            # 3. Obtenemos los bytes del cuerpo y los decodificamos
                            cuerpo_bytes = part.get_payload(decode=True)

                            # Obtenemos la codificación de esta parte
                            charset = part.get_content_charset()

                            # Si no especifica una, usamos utf-8 como fallback
                            if charset is None:
                                charset = 'utf-8'

                            cuerpo = cuerpo_bytes.decode(charset, errors='replace')
                            # Una vez que encontramos el texto plano, salimos del bucle
                            break
                        except Exception as e:
                            print(f"  No se pudo decodificar una parte del cuerpo: {e}")
                            cuerpo = "Error al decodificar el cuerpo."
            else:
                # 4. Si no es multipart, es un correo simple
                try:
                    cuerpo_bytes = msg.get_payload(decode=True)
                    charset = msg.get_content_charset()
                    if charset is None:
                        charset = 'utf-8'
                    cuerpo = cuerpo_bytes.decode(charset, errors='replace')
                except Exception as e:
                    print(f"  No se pudo decodificar el cuerpo del correo simple: {e}")
                    cuerpo = "Error al decodificar el cuerpo."

            # Imprimimos el asunto y una vista previa del cuerpo
            print(f"Correo {i}: Asunto - {asunto}")
            print(f"Cuerpo: {cuerpo[:250]}...")  # Muestra los primeros 250 caracteres
            print("-" * 30)

        server.quit()
    except Exception as e:
        print(f"Error al leer con POP3: {e}")

