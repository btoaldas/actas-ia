"""
Context processor para manejar botones dinámicos "Anterior" y "Siguiente" en el header
"""

import re

# Reglas de navegación con soporte a botones anterior y siguiente
STEP_RULES = [
    # Centro de Audio
    (re.compile(r'^/audio/$'), {
        'previous': None,  # No hay paso anterior
        'next': {
            'show': True,
            'text': 'SIGUIENTE: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-audio'
        }
    }),

    # Lista de Audios
    (re.compile(r'^/audio/lista/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: CENTRO DE AUDIO',
            'url': '/audio/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-audio'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-audio'
        }
    }),

    # Detalle de Audio
    (re.compile(r'^/audio/detalle/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE AUDIOS',
            'url': '/audio/lista/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-audio'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-audio'
        }
    }),

    # Transcripciones
    (re.compile(r'^/transcripcion/audios/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: CENTRO DE AUDIO',
            'url': '/audio/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-transcription'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ACTAS GENERADAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-transcription'
        }
    }),

    # Generador de Actas
    (re.compile(r'^/generador-actas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-actas'
        },
        'next': None  # No hay paso siguiente (final del flujo)
    }),

    # Portal Ciudadano (opcional)
    (re.compile(r'^/portal-ciudadano/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: ACTAS GENERADAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-portal'
        },
        'next': None  # No hay paso siguiente
    }),
]


def step_buttons_context(request):
    """
    Devuelve configuración de botones "Anterior" y "Siguiente" según la ruta actual
    """
    current_path = request.path
    step_config = {'previous': {'show': False}, 'next': {'show': False}}

    for pattern, config in STEP_RULES:
        if pattern.match(current_path):
            step_config = config
            break

    return {
        'previous_step_button': step_config.get('previous', {'show': False}),
        'next_step_button': step_config.get('next', {'show': False}),
    }
