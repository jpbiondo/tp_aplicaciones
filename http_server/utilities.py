# utilities.py
import os
import base64
from typing import Optional, Tuple


def is_safe_path(base_path: str, path: str) -> bool:
    """Verifica que la ruta 'path' esté dentro de 'base_path'."""
    real_base = os.path.realpath(base_path)
    real_target = os.path.realpath(os.path.join(base_path, path))
    return real_target.startswith(real_base)

def decode_basic_auth(header_value: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Decodifica un header 'Authorization: Basic ...' y devuelve (usuario, contraseña).
    Si no puede decodificar o no es Basic, devuelve (None, None).
    """
    if not header_value:
        return None, None

    parts = header_value.split()
    if len(parts) != 2:
        return None, None

    scheme, token = parts
    if scheme.lower() != "basic":
        return None, None

    try:
        # token es base64 de "usuario:contraseña"
        decoded_bytes = base64.b64decode(token, validate=True)
        decoded = decoded_bytes.decode("utf-8", errors="strict")
    except (base64.binascii.Error, UnicodeDecodeError):
        return None, None

    if ":" not in decoded:
        return None, None

    user, pw = decoded.split(":", 1)
    return user, pw