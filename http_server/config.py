import json, os, threading

DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 8080,
    "document_root": os.path.abspath("www"),
    "log_file": "http_learning_server.log",
    # users: username -> password (plain text for simplicity)
    "users": {
        "admin": "adminpass"
    },
    # protected_dirs are paths relative to document_root that require auth
    "protected_dirs": [
        "protected"
    ],
    # admin path credentials (separate admin user could be enforced)
    "admin_user": "admin",
    "admin_pass": "adminpass"
}

CONFIG_PATH = "config.json"
CONFIG_LOCK = threading.Lock()


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = json.load(f)
            # normalize document_root to absolute
            cfg["document_root"] = os.path.abspath(cfg.get("document_root", DEFAULT_CONFIG["document_root"]))
            return cfg
    else:
        # write default
        os.makedirs(DEFAULT_CONFIG["document_root"], exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)