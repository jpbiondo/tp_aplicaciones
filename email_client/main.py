from email_client.src.imap_client import leer_correos_imap_ssl, eliminar_correo_imap_ssl
from email_client.src.smtp_client import reenviar_correo_smtp, responder_correo
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER_ADDR, SMTP_SERVER_ADDR

def opcion_valida(opcion):
    return 1 <= opcion <= 3

leer_correos_imap_ssl(IMAP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD)

while(1):
    opcion = int(input("[Sistema] Seleccione una opción:\n[1] Reenviar correo\n[2] Responder correo\n[3] Seleccionar correo\n[4] Buscar correo\n"))
    if opcion_valida(opcion):
        break
    print("[Error] La opción ingresada debe estar ente 1 y 3")

# Reenviar correo
if opcion == 1:
    uid_correo = input("[Sistema] Ingrese ID del correo que desee reenviar: ")
    destinatario = input("[Sistema] Ingrese correo del destinatario: ")
    reenviar_correo_smtp(SMTP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD, destinatario, uid_correo)

# Responder
elif opcion == 2:
    uid_correo = input("[Sistema] Ingrese ID del correo que desee eliminar: ")
    cuerpo = input("[Sistema] Ingrese cuerpo del correo que desea enviar: ")
    responder_correo(SMTP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD, uid_correo, cuerpo)

# Eliminar
elif opcion == 3:
    uid_correo_eliminar = input("[Sistema] Ingrese ID del correo que desee eliminar: ")
    eliminar_correo_imap_ssl(IMAP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD, uid_correo_eliminar)


# enviar_correo_smtp("smtp.gmail.com", EMAIL_ADDRESS, EMAIL_PASSWORD, "escppscentral@gmail.com", "Buenas tardes", "Hola buenas tardes")
