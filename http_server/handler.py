import http.server
import os
import urllib.parse
from config import CONFIG, CONFIG_LOCK, load_config, save_config

class LearningHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "HTTPLearning/0.1"

    def log_message(self, format, *args):
        # Override to use logger
        logger.info("%s - %s" % (self.address_string(), format % args))

    def do_HEAD(self):
        self._handle_request(head_only=True)

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def _handle_request(self, head_only=False):
        # Reload config under lock to pick up runtime changes
        with CONFIG_LOCK:
            cfg = CONFIG.copy()

        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path

        # Admin endpoints
        if path.startswith('/admin'):
            return self._handle_admin(path, head_only, cfg)

        # map path to filesystem
        try:
            fs_path = self.translate_path(path, cfg["document_root"])  # absolute path
        except Exception as e:
            logger.exception("Error translating path")
            self.send_error(400, "Bad request")
            return

        # Security: ensure path is inside document_root
        if not is_path_within(fs_path, cfg["document_root"]):
            logger.warning("Blocked path outside document_root: %s", fs_path)
            self.send_error(403, "Access denied")
            return

        # Check protected dirs
        rel = os.path.relpath(fs_path, cfg["document_root"]) if os.path.exists(fs_path) else os.path.relpath(os.path.dirname(fs_path), cfg["document_root"])
        for protected in cfg.get("protected_dirs", []):
            # Normalise
            protected_norm = os.path.normpath(protected)
            # If rel starts with protected_norm -> requires auth
            if rel == protected_norm or rel.startswith(protected_norm + os.sep):
                if not self.check_auth_for_user(cfg):
                    self.require_auth()
                    return
                break

        # If path is a directory, look for index.html
        if os.path.isdir(fs_path):
            index = os.path.join(fs_path, "index.html")
            if os.path.exists(index):
                fs_path = index
            else:
                # For security, do not allow directory listing; return 403
                self.send_error(403, "Directory listing denied")
                return

        # Now serve file if exists
        if not os.path.exists(fs_path) or not os.path.isfile(fs_path):
            self.send_error(404, "File not found")
            return

        try:
            ctype = self.guess_type(fs_path)
            fs = open(fs_path, 'rb')
            try:
                fs_stat = os.fstat(fs.fileno())
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", str(fs_stat.st_size))
                self.end_headers()
                if not head_only:
                    self.wfile.write(fs.read())
                logger.info("Served %s %s %s", self.client_address, self.command, fs_path)
            finally:
                fs.close()
        except Exception as e:
            logger.exception("Error serving file")
            self.send_error(500, "Internal server error")

    # -------------------- Admin handling --------------------
    def _handle_admin(self, path, head_only, cfg):
        # Only allow admin if configured admin_user/admin_pass are present
        auth_header = self.headers.get('Authorization')
        user, pw = parse_basic_auth(auth_header) if auth_header else (None, None)
        if user != cfg.get('admin_user') or pw != cfg.get('admin_pass'):
            self.require_auth(realm='Admin Area')
            return

        if self.command == 'GET':
            # show simple config page
            html = self._render_admin_page(cfg)
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html.encode('utf-8'))))
            self.end_headers()
            if not head_only:
                self.wfile.write(html.encode('utf-8'))
            return

        elif self.command == 'POST':
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode('utf-8')
            params = urllib.parse.parse_qs(body)
            updated = False
            # accept only a few keys for safety
            allowed_keys = ['host', 'port', 'document_root', 'admin_user', 'admin_pass']
            global CONFIG
            with CONFIG_LOCK:
                for k in allowed_keys:
                    if k in params:
                        val = params[k][0]
                        if k == 'port':
                            val = int(val)
                        cfg[k] = val
                        updated = True
                if updated:
                    # persist and reload
                    save_config(cfg)
                    # update global CONFIG
                    CONFIG = load_config()
            # respond
            self.send_response(303)
            self.send_header('Location', '/admin')
            self.end_headers()
            return

        else:
            self.send_error(405, 'Method not allowed')
            return

    def _render_admin_page(self, cfg):
        # Minimal admin html
        protected_html = '<ul>' + ''.join(f'<li>{p}</li>' for p in cfg.get('protected_dirs', [])) + '</ul>'
        users_html = '<ul>' + ''.join(f'<li>{u}</li>' for u in cfg.get('users', {}).keys()) + '</ul>'
        html = f"""
        <html>
        <head><meta charset='utf-8'><title>Admin - HTTP Learning Server</title></head>
        <body>
          <h1>Admin</h1>
          <h2>Configuration</h2>
          <form method='post' action='/admin'>
            Host: <input name='host' value='{cfg.get('host')}'/><br/>
            Port: <input name='port' value='{cfg.get('port')}'/><br/>
            Document root: <input name='document_root' value='{cfg.get('document_root')}' size='60'/><br/>
            Admin user: <input name='admin_user' value='{cfg.get('admin_user')}'/><br/>
            Admin pass: <input name='admin_pass' value='{cfg.get('admin_pass')}'/><br/>
            <input type='submit' value='Save'/>
          </form>
          <h2>Protected directories</h2>
          {protected_html}
          <h2>Users</h2>
          {users_html}
          <p>To add users or change protected dirs edit <code>config.json</code> directly or extend this admin UI.</p>
        </body>
        </html>
        """
        return html

    # -------------------- Auth helpers --------------------
    def require_auth(self, realm='Protected'):
        self.send_response(401)
        self.send_header('WWW-Authenticate', f'Basic realm="{realm}"')
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(b'401 Authentication required')

    def check_auth_for_user(self, cfg) -> bool:
        # Check Authorization header against cfg['users']
        auth = self.headers.get('Authorization')
        user, pw = parse_basic_auth(auth) if auth else (None, None)
        if not user:
            return False
        users = cfg.get('users', {})
        expected = users.get(user)
        if expected is None:
            return False
        return pw == expected

    # -------------------- Filesystem helpers --------------------
    def translate_path(self, path, document_root):
        # Adapted from http.server.SimpleHTTPRequestHandler.translate_path
        # Prevent path traversal by normalizing and joining to document_root
        path = posixpath.normpath(urllib.parse.unquote(path))
        words = [w for w in path.split('/') if w]
        path = document_root
        for word in words:
            # don't allow going up
            if os.path.dirname(word) or word in (os.curdir, os.pardir):
                # suspicious path
                raise Exception("Suspicious path component")
            path = os.path.join(path, word)
        return os.path.abspath(path)

    def guess_type(self, path):
        import mimetypes
        base, ext = os.path.splitext(path)
        if ext in mimetypes.types_map:
            return mimetypes.types_map[ext]
        return 'application/octet-stream'