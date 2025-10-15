import socketserver, http.server
from handler import LearningHTTPRequestHandler
from config import CONFIG, CONFIG_LOCK
import logging


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

def run_server(host: str, port: int):
    with CONFIG_LOCK:
        cfg = CONFIG.copy()
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, LearningHTTPRequestHandler)
    sa = httpd.socket.getsockname()
    logger.info("Serving HTTP on %s port %d (DocumentRoot: %s) ...", sa[0], sa[1], cfg.get('document_root'))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received, exiting.')
        httpd.server_close()
