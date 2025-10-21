from poplib import POP3

from email_client.config import POP3_SERVER_ADDR, SMTP_SERVER_ADDR
from email_client.pop3_client import leer_correos_pop3, abrir_sesion_pop3_ssl, eliminar_correo_pop3
from email_client.imap_client import leer_correos_imap_ssl, eliminar_correo_imap_ssl, abrir_sesion_imap_ssl
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, IMAP_SERVER_ADDR
from email_client.smtp_client import responder_correo_pop3_smtp, responder_correo_imap_smtp, reenviar_correo_pop3_smtp, \
    reenviar_correo_imap_smtp, abrir_sesion_smtp

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

def reenviar_correo(sesion_mua, sesion_smtp):
    id_reenviar = input("[Sistema] Ingrese ID del correo que desee reenviar: ")
    destinatario = input("[Sistema] Ingrese correo del destinatario: ")
    if isinstance(sesion_mua, POP3):
        reenviar_correo_pop3_smtp(sesion_smtp, sesion_mua, EMAIL_ADDRESS, destinatario, id_reenviar)
        return

    reenviar_correo_imap_smtp(sesion_smtp, sesion_mua, EMAIL_ADDRESS, destinatario, id_reenviar)

def responder_correo(sesion_mua, sesion_smtp):
    id_responder = input("[Sistema] Ingrese ID del correo que desee eliminar: ")
    cuerpo = input("[Sistema] Ingrese cuerpo del mensaje: ")

    if isinstance(sesion_mua, POP3):
        responder_correo_pop3_smtp(sesion_mua, sesion_smtp, EMAIL_ADDRESS, id_responder, cuerpo)
        return
    responder_correo_imap_smtp(sesion_mua, sesion_smtp, EMAIL_ADDRESS, id_responder, cuerpo)


def eliminar_correo(sesion):
    id_eliminar = input("[Sistema] Ingrese ID del correo que desee eliminar: ")
    if isinstance(sesion, POP3):
        eliminar_correo_pop3(sesion, id_eliminar)
        return
    eliminar_correo_imap_ssl(sesion, id_eliminar)

if __name__ == 'main':
    opcion_protocolo = 1
    opcion_correo = 1

    while 1:
        opcion_protocolo = int(input("[Sistema] Seleccione un protocolo para buscar, leer y eliminar mensajes:\n[1] IMAP\n[2] POP3\n"))
        if opcion_protocolo in [1, 2]:
            break
        print("[Error] La opción ingresada debe ser 1 o 2")

    sesion = abrir_sesion(opcion_protocolo)
    sesion_smtp = abrir_sesion_smtp(SMTP_SERVER_ADDR, EMAIL_ADDRESS, EMAIL_PASSWORD)

    leer_correos(sesion, 5)

    while 1:
        opcion_correo = int(input("[Sistema] Seleccione una opción:\n[1] Reenviar correo\n[2] Responder correo\n[3] Eliminar correo\n[4] Buscar correo\n"))
        if opcion_correo [1, 2, 3]:
            break
        print("[Error] La opción ingresada debe estar ente 1 y 3")

    if opcion_correo == 1:
        reenviar_correo(sesion, sesion_smtp)
    elif opcion_correo == 2:
        responder_correo(sesion, sesion_smtp)
    elif opcion_correo == 3:
        eliminar_correo(sesion)
