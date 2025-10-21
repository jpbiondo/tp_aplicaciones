from poplib import POP3

from email_client.config import POP3_SERVER_ADDR, SMTP_SERVER_ADDR
from email_client.pop3_client import leer_correos_pop3, abrir_sesion_pop3_ssl
from email_client.imap_client import leer_correos_imap_ssl, eliminar_correo_imap_ssl, abrir_sesion_imap_ssl
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER_ADDR

def opcion_valida_correo(opcion):
    return 1 <= opcion <= 3

def opcion_valida_protocolo(opcion):
    return 1 <= opcion <= 2

def abrir_sesion(protocolo):
    assert protocolo in [1, 2], f"'{protocolo}' no es un valor válido"

    if protocolo == 1:
        return abrir_sesion_imap_ssl(IMAP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD)
    return abrir_sesion_pop3_ssl(POP3_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD)

def leer_correos(sesion, cantidad):
    if isinstance(sesion, POP3):
        leer_correos_pop3(sesion, cantidad)
        return
    leer_correos_imap_ssl(sesion, cantidad)

def reenviar_correo(sesion):
    uid_correo = input("[Sistema] Ingrese ID del correo que desee reenviar: ")
    destinatario = input("[Sistema] Ingrese correo del destinatario: ")
    return

def responder_correo(sesion):
    return

def eliminar_correo(sesion):
    return

opcion_protocolo = 1
opcion_correo = 1

while(1):
    opcion_protocolo = int(input("[Sistema] Seleccione un protocolo para buscar, leer y eliminar mensajes:\n[1] IMAP\n[2] POP3\n"))
    if opcion_valida_protocolo(opcion_protocolo):
        break
    print("[Error] La opción ingresada debe ser 1 o 2")

sesion = abrir_sesion(opcion_protocolo)
leer_correos(sesion, 5)

while(1):
    opcion_correo = int(input("[Sistema] Seleccione una opción:\n[1] Reenviar correo\n[2] Responder correo\n[3] Eliminar correo\n[4] Buscar correo\n"))
    if opcion_valida_correo(opcion_correo):
        break
    print("[Error] La opción ingresada debe estar ente 1 y 3")

# Reenviar correo
if opcion_correo == 1:
    reenviar_correo(sesion)

# Responder
elif opcion_correo == 2:
    responder_correo(sesion)

# Eliminar
elif opcion_correo == 3:
    eliminar_correo(sesion)
