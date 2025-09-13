from django import template

register = template.Library()


@register.filter(name='speaker_label')
def speaker_label(info):
    """Devuelve una etiqueta amigable para un hablante.
    Acepta dicts o strings. Prioriza: nombre, nombre_completo, nombre_real, y si no existe, intenta
    combinar nombre + apellidos; como último recurso, str(info).
    """
    try:
        if isinstance(info, str):
            return info
        if isinstance(info, dict):
            # Prioridades de campos esperados en distintas fuentes
            for key in ('nombre', 'nombre_completo', 'nombre_real'):
                val = info.get(key)
                if val:
                    return val
            # Intento de combinación nombre + apellidos
            nombre = info.get('nombre')
            apellidos = info.get('apellidos')
            if nombre and apellidos:
                return f"{nombre} {apellidos}".strip()
        # Fallback
        return str(info)
    except Exception:
        return str(info)
