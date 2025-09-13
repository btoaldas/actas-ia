from django import template
from django.utils.safestring import mark_safe

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


@register.simple_tag
def celery_badge(task_id: str = None):
    """Devuelve un badge HTML (seguro) para el estado de una tarea Celery.
    Estados mapeados: pendiente, terminado, recibido, empezando, fallido, retirado.
    Si no hay task_id, no muestra nada.
    """
    if not task_id:
        return ''
    try:
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        state = (result.state or '').upper()
    except Exception:
        state = 'UNKNOWN'

    mapping = {
        'PENDING':  ('Pendiente', 'secondary', 'far fa-clock'),
        'RECEIVED': ('Recibido', 'info', 'fas fa-inbox'),
        'STARTED':  ('Empezando', 'warning', 'fas fa-play'),
        'RETRY':    ('Reintentando', 'warning', 'fas fa-redo'),
        'SUCCESS':  ('Terminado', 'success', 'fas fa-check'),
        'FAILURE':  ('Fallido', 'danger', 'fas fa-times'),
        'REVOKED':  ('Retirado', 'dark', 'fas fa-ban'),
    }
    label, css, icon = mapping.get(state, ('Desconocido', 'light', 'fas fa-question'))
    html = f'<span class="badge badge-{css}" title="{state}"><i class="{icon}"></i> {label}</span>'
    return mark_safe(html)


@register.simple_tag
def transcripcion_badge(transcripcion):
    """Muestra un badge compuesto con:
    - Estado de negocio (Transcripción): pendiente/en_proceso/transcribiendo/diarizando/procesando/completado/error/cancelado
    - Estado Celery (si existe task): PENDING/STARTED/RETRY/SUCCESS/FAILURE...
    - Progreso si está disponible (progreso_porcentaje)
    """
    try:
        estado = (getattr(transcripcion, 'estado', '') or '').lower()
    except Exception:
        estado = ''

    estado_map = {
        'pendiente':      ('Pendiente', 'secondary', 'far fa-clock'),
        'en_proceso':     ('En proceso', 'info', 'fas fa-spinner fa-spin'),
        'transcribiendo': ('Transcribiendo', 'primary', 'fas fa-keyboard'),
        'diarizando':     ('Diarizando', 'purple', 'fas fa-user-friends'),  # fallback a secondary si no hay purple
        'procesando':     ('Procesando', 'warning', 'fas fa-cogs'),
        'completado':     ('Completado', 'success', 'fas fa-check'),
        'error':          ('Error', 'danger', 'fas fa-times'),
        'cancelado':      ('Cancelado', 'dark', 'fas fa-ban'),
    }
    label, css, icon = estado_map.get(estado, ('Desconocido', 'light', 'fas fa-question'))
    # Ajustar css no estándar
    if css == 'purple':
        css = 'secondary'

    # Progreso
    progreso = None
    for attr in ('progreso_porcentaje', 'progreso'):
        val = getattr(transcripcion, attr, None)
        if isinstance(val, int) or isinstance(val, float):
            progreso = int(val)
            break

    # Celery state
    celery_state = None
    task_id = getattr(transcripcion, 'task_id_celery', None)
    if task_id:
        try:
            from celery.result import AsyncResult
            r = AsyncResult(task_id)
            celery_state = (r.state or '').upper()
        except Exception:
            celery_state = None

    # Construir HTML
    parts = []
    parts.append(f'<span class="badge badge-{css}" title="{label}"><i class="{icon}"></i> {label}</span>')
    if progreso is not None and 0 < progreso < 100:
        parts.append(f'<span class="badge badge-light ml-1">{progreso}%</span>')
    if celery_state and celery_state not in ('SUCCESS',):
        # Map simple para Celery
        c_map = {
            'PENDING':  ('secondary', 'far fa-clock'),
            'RECEIVED': ('info', 'fas fa-inbox'),
            'STARTED':  ('warning', 'fas fa-play'),
            'RETRY':    ('warning', 'fas fa-redo'),
            'FAILURE':  ('danger', 'fas fa-times'),
            'REVOKED':  ('dark', 'fas fa-ban'),
        }
        c_css, c_icon = c_map.get(celery_state, ('light', 'fas fa-question'))
        parts.append(f'<span class="badge badge-{c_css} ml-1" title="Celery: {celery_state}"><i class="{c_icon}"></i></span>')

    return mark_safe(' '.join(parts))
