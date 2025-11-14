import ftplib
from ftplib import FTP
import os

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 21

print("+ Para comenzar ingrese host y puerto del servidor FTP.")

ftp_host = input("Ingrese HOST (default: 127.0.0.1): ")
if len(ftp_host) == 0:
    ftp_host = DEFAULT_HOST

ftp_port = input(f"Ingrese PORT({ftp_host}:({DEFAULT_PORT})):")
ftp_port = DEFAULT_PORT if len(ftp_port) == 0 else int(ftp_port)

print(f"+ Intentando ingresar al servidor {ftp_host}:{ftp_port}")

ftp = FTP()
print(ftp.connect(ftp_host, ftp_port))

try:
    ftp.retrlines('LIST')
except ftplib.error_perm as auth_err:
    print(auth_err)
    user = input(f'Usuario ({ftp_host}:{ftp_port}): ')
    passwrd = input(f'Contraseña: ')
    try:
        print(ftp.login(user, passwrd))
    except ftplib.error_perm as invalid_cred_err:
        print(invalid_cred_err)
        ftp.close()
        exit()


def handle_ftp_commnd(ftp_commnd):
    # Separar comando y argumentos correctamente
    parts = ftp_commnd.strip().split(maxsplit=1)

    if len(parts) == 0:
        return

    commnd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else None

    try:
        if commnd == 'ls' or commnd == 'dir':
            # Listar archivos/directorios
            path = args if args else ''
            ftp.retrlines(f'LIST {path}')

        elif commnd == 'pwd':
            # Mostrar directorio actual
            print(ftp.pwd())

        elif commnd == 'cd' or commnd == 'cwd':
            # Cambiar directorio
            if args:
                print(ftp.cwd(args))
            else:
                print("Error: Debe especificar un directorio")

        elif commnd == 'get':
            # Descargar archivo
            if args:
                filename = args
                with open(filename, 'wb') as local_file:
                    ftp.retrbinary(f'RETR {filename}', local_file.write)
                print(f"Archivo '{filename}' descargado correctamente")
            else:
                print("Error: Debe especificar un archivo para descargar")

        elif commnd == 'put':
            # Subir archivo
            if args:
                filename = args
                if os.path.exists(filename):
                    with open(filename, 'rb') as local_file:
                        print(ftp.storbinary(f'STOR {filename}', local_file))
                else:
                    print(f"Error: El archivo '{filename}' no existe localmente")
            else:
                print("Error: Debe especificar un archivo para subir")

        elif commnd == 'delete' or commnd == 'del':
            # Eliminar archivo
            if args:
                print(ftp.delete(args))
            else:
                print("Error: Debe especificar un archivo para eliminar")

        elif commnd == 'mkdir':
            # Crear directorio
            if args:
                print(ftp.mkd(args))
            else:
                print("Error: Debe especificar un nombre de directorio")

        elif commnd == 'rmdir':
            # Eliminar directorio
            if args:
                print(ftp.rmd(args))
            else:
                print("Error: Debe especificar un directorio para eliminar")

        elif commnd == 'rename':
            # Renombrar archivo/directorio
            if args and ' ' in args:
                old_name, new_name = args.split(maxsplit=1)
                print(ftp.rename(old_name, new_name))
            else:
                print("Error: Uso: rename <nombre_actual> <nombre_nuevo>")

        elif commnd == 'help':
            # Mostrar ayuda
            print("\nComandos disponibles:")
            print("  ls/dir [ruta]          - Listar archivos")
            print("  pwd                    - Mostrar directorio actual")
            print("  cd/cwd <directorio>    - Cambiar directorio")
            print("  get <archivo>          - Descargar archivo")
            print("  put <archivo>          - Subir archivo")
            print("  delete/del <archivo>   - Eliminar archivo")
            print("  mkdir <directorio>     - Crear directorio")
            print("  rmdir <directorio>     - Eliminar directorio")
            print("  rename <viejo> <nuevo> - Renombrar archivo/directorio")
            print("  quit/exit              - Salir\n")

        elif commnd == 'quit' or commnd == 'exit':
            print("Cerrando conexión FTP...")
            ftp.quit()
            exit()

        else:
            print(f"Comando '{commnd}' no válido. Escriba 'help' para ver comandos disponibles")

    except ftplib.error_perm as e:
        print(f"Error de permisos: {e}")
    except ftplib.error_temp as e:
        print(f"Error temporal: {e}")
    except Exception as e:
        print(f"Error: {e}")


print("\nConexión establecida. Escriba 'help' para ver comandos disponibles.\n")

while True:
    try:
        ftp_cmmnd = input("ftp> ")
        handle_ftp_commnd(ftp_cmmnd)
    except KeyboardInterrupt:
        print("\n\nCerrando conexión...")
        ftp.quit()
        break