# --- Función auxiliar para decodificar cabeceras de forma robusta ---
from email.header import decode_header


def decodificar_cabecera(cabecera):
    """Decodifica correctamente las cabeceras de correo (Asunto, De, Para)."""
    partes_decodificadas = []
    for fragmento, codificacion in decode_header(cabecera):
        if isinstance(fragmento, bytes):
            try:
                # Si la codificación es None o inválida, intenta con fallbacks comunes
                partes_decodificadas.append(fragmento.decode(codificacion or 'utf-8', errors='replace'))
            except (UnicodeDecodeError, LookupError):
                partes_decodificadas.append(fragmento.decode('iso-8859-1', errors='replace'))
        else:
            partes_decodificadas.append(fragmento)
    return "".join(partes_decodificadas)
