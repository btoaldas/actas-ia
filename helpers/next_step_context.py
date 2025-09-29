"""
Context processor para manejar el botón dinámico "Siguiente Paso" en el header
"""

import re

# Definir reglas como lista de tuplas (regex, config)
NEXT_STEP_RULES = [
    # Centro de Audio -> Transcripciones
    (re.compile(r'^/audio/$'), {
        'show': True,
        'text': 'SIGUIENTE: TRANSCRIPCIONES',
        'url': '/transcripcion/audios/',
        'icon': 'fas fa-arrow-right',
        'class': 'nav-btn-next-audio'
    }),

    # Cualquier detalle de audio, ej: /audio/detalle/20/2/
    (re.compile(r'^/audio/detalle/\d+/$'), {
        'show': True,
        'text': 'SIGUIENTE: TRANSCRIPCIONES',
        'url': '/transcripcion/audios/',
        'icon': 'fas fa-arrow-right',
        'class': 'nav-btn-next-audio'
    }),
    #/audio/lista/
    (re.compile(r'^/audio/lista/$'), {
        'show': True,
        'text': 'SIGUIENTE: TRANSCRIPCIONES',
        'url': '/transcripcion/audios/',
        'icon': 'fas fa-arrow-right',
        'class': 'nav-btn-next-audio'
    }),

    # Ejemplo adicional (futuro): Transcripciones -> Actas
    (re.compile(r'^/transcripcion/audios/$'), {
        'show': True,
        'text': 'SIGUIENTE: ACTAS GENERADAS',
        'url': '/generador-actas/',
        'icon': 'fas fa-arrow-right',
        'class': 'nav-btn-next-transcription'
    }),
]

def next_step_button_context(request):
    """
    Determina qué botón "Siguiente Paso" mostrar basado en la página actual
    """
    current_path = request.path
    next_step = {'show': False}

    for pattern, config in NEXT_STEP_RULES:
        if pattern.match(current_path):
            next_step = config
            break

    return {
        'next_step_button': next_step
    }
