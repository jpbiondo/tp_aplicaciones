import base64
import configparser
import logging
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# Lee la configuración desde un archivo externo
config = configparser.ConfigParser()
config.read('config.ini')

SERVER_CONFIG = config['Server']
CREDENTIALS_CONFIG = config['Credentials']

PORT = int(SERVER_CONFIG.get('Port', 8080))
DOCUMENT_ROOT = SERVER_CONFIG.get('DocumentRoot', 'webroot')
USUARIO_VALIDO = CREDENTIALS_CONFIG.get('User', 'admin')
CONTRASENA_VALIDA = CREDENTIALS_CONFIG.get('Password', 'secret')

# Configura el sistema de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)


class CustomHTTP(BaseHTTPRequestHandler):
    def _autenticar(self):
        auth_header = self.headers.get('Authorization')
        if auth_header is None:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Acceso restringido a /private"')
            self.end_headers()
            self.wfile.write(b'{"error": "Falta header de autenticacion"}')
            return False
        if not auth_header.lower().startswith('basic '):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Esquema invalido"')
            self.end_headers()
            self.wfile.write(b'{"error": "Esquema de autenticacion debe ser Basic"}')
            return False
        try:
            credenciales_b64 = auth_header.split(' ')[1]
            credenciales_bytes = base64.b64decode(credenciales_b64)
            credenciales_str = credenciales_bytes.decode('utf-8')
            usuario, contrasena = credenciales_str.split(':', 1)
        except Exception:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Credenciales invalidas"')
            self.end_headers()
            self.wfile.write(b'{"error": "Credenciales mal formadas"}')
            return False
        if usuario == USUARIO_VALIDO and contrasena == CONTRASENA_VALIDA:
            logging.info(f"Usuario '{usuario}' autenticado correctamente para acceder a {self.path}")
            return True
        else:
            logging.warning(f"Intento de autenticacion fallido para el usuario '{usuario}'")
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'{"error": "Usuario o contrasena incorrectos"}')
            return False

    def do_GET(self):

        # Rutas /private/* -> Auth
        if self.path.startswith('/private/'):
            if not self._autenticar():
                return

        if self.path == '/':
            filepath = os.path.join(DOCUMENT_ROOT, 'index.html')
        else:
            # Elimina el '/' inicial para que os.path.join funcione correctamente
            filepath = os.path.join(DOCUMENT_ROOT, self.path.lstrip('/'))

        safe_document_root = os.path.abspath(DOCUMENT_ROOT)
        safe_filepath = os.path.abspath(filepath)

        # Anti-Path traversal
        if not safe_filepath.startswith(safe_document_root):
            logging.warning(f"Intento de acceso fuera del DocumentRoot bloqueado: {self.path}")
            self.send_error(403, "Acceso Prohibido")
            return

        # Sirve el archivo si existe
        if os.path.isfile(safe_filepath):
            try:
                with open(safe_filepath, 'rb') as f:
                    self.send_response(200)
                    # Adivina el tipo de contenido (MIME type)
                    mimetype, _ = mimetypes.guess_type(safe_filepath)
                    self.send_header('Content-type', mimetype or 'application/octet-stream')
                    self.end_headers()
                    self.wfile.write(f.read())
                logging.info(f"Sirviendo archivo: {safe_filepath}")
            except IOError:
                logging.error(f"No se pudo leer el archivo: {safe_filepath}")
                self.send_error(500, "Error Interno del Servidor")
        else:
            logging.info(f"Archivo no encontrado: {safe_filepath}")
            self.send_error(404, "Archivo No Encontrado")


if __name__ == "__main__":
    # Crea el directorio webroot si no existe
    if not os.path.exists(DOCUMENT_ROOT):
        os.makedirs(DOCUMENT_ROOT)
        logging.info(f"Directorio '{DOCUMENT_ROOT}' creado.")
        # Crea archivos de ejemplo para que el servidor funcione de inmediato
        with open(os.path.join(DOCUMENT_ROOT, "index.html"), "w") as f:
            f.write("<h1>Endpoint publico</h1><p><a href='/private/secret.html'>Ir a la seccion privada</a></p>")
        os.makedirs(os.path.join(DOCUMENT_ROOT, "private"))
        with open(os.path.join(DOCUMENT_ROOT, "private/secret.html"), "w") as f:
            f.write("<h1>Endpoint privado. Bienvenido Admin.</h1>")

    server = HTTPServer(("", PORT), CustomHTTP)
    logging.info(f"Servidor iniciado en http://localhost:{PORT}")
    logging.info(f"DocumentRoot configurado en: '{DOCUMENT_ROOT}'")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

    server.server_close()
    logging.info("Servidor detenido.")