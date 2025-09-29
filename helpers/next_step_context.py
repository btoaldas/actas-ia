"""
Context processor para manejar botones dinámicos "Anterior" y "Siguiente" en el header
"""

import re

# Reglas de navegación con soporte a botones anterior y siguiente - FLUJO COMPLETO DE LA APLICACIÓN
STEP_RULES = [
    # 1. MÓDULO DE AUDIO - CENTRO DE AUDIO (Inicio del flujo)
    (re.compile(r'^/audio/$'), {
        'previous': None,  # No hay paso anterior (inicio del flujo)
        'next': {
            'show': True,
            'text': 'SIGUIENTE: LISTA DE AUDIOS',
            'url': '/audio/lista/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-audio'
        }
    }),

    # 2. MÓDULO DE AUDIO - LISTA DE AUDIOS
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

    # 3. MÓDULO DE AUDIO - DETALLE DE AUDIO
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

    # 4. MÓDULO DE TRANSCRIPCIÓN - LISTA DE AUDIOS PARA TRANSCRIBIR
    (re.compile(r'^/transcripcion/audios/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE AUDIOS',
            'url': '/audio/lista/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-transcription'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: CREAR ACTAS',
            'url': '/generador-actas/actas/crear/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-transcription'
        }
    }),

    # 5. MÓDULO DE TRANSCRIPCIÓN - DETALLE DE TRANSCRIPCIÓN
    (re.compile(r'^/transcripcion/detalle/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-transcription'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: PLANTILLAS DE ACTAS',
            'url': '/admin/generador_actas/plantillaacta/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-transcription'
        }
    }),

    # 6. MÓDULO DE TRANSCRIPCIÓN - PROCESO DE TRANSCRIPCIÓN
    (re.compile(r'^/transcripcion/proceso/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-transcription'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: GENERAR ACTA',
            'url': '/generador-actas/actas/crear/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-transcription'
        }
    }),

    # 7. MÓDULO DE PLANTILLAS - GESTIÓN DE PLANTILLAS
    (re.compile(r'^/admin/generador_actas/plantillaacta/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-templates'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ACTAS GENERADAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-templates'
        }
    }),

    # 8. MÓDULO DE PLANTILLAS - DETALLE/EDICIÓN DE PLANTILLA
    (re.compile(r'^/admin/generador_actas/plantillaacta/\d+/change/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE PLANTILLAS',
            'url': '/admin/generador_actas/plantillaacta/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-templates'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ACTAS GENERADAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-templates'
        }
    }),

    # 9. MÓDULO GENERADOR - CREAR ACTA
    (re.compile(r'^/generador-actas/actas/crear/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-generator'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: LISTA DE ACTAS',
            'url': '/generador-actas/actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-generator'
        }
    }),

    # 10. MÓDULO GENERADOR - LISTA DE ACTAS
    (re.compile(r'^/generador-actas/actas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: TRANSCRIPCIONES',
            'url': '/transcripcion/audios/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-generator'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: DASHBOARD REVISIÓN',
            'url': '/gestion-actas/dashboard-revision/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-generator'
        }
    }),

    # 11. MÓDULO GENERADOR - DETALLE DE ACTA ESPECÍFICA
    (re.compile(r'^/generador-actas/actas/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE ACTAS',
            'url': '/generador-actas/actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-generator'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: GESTIÓN DE ACTAS',
            'url': '/gestion-actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-generator'
        }
    }),

    # 12. MÓDULO GESTIÓN - DASHBOARD REVISIÓN
    (re.compile(r'^/gestion-actas/dashboard-revision/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE ACTAS',
            'url': '/generador-actas/actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-management'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: GESTIÓN DE ACTAS',
            'url': '/gestion-actas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-management'
        }
    }),

    # 13. MÓDULO GESTIÓN - GESTIÓN DE ACTAS
    (re.compile(r'^/gestion-actas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE ACTAS',
            'url': '/generador-actas/actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-management'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: DASHBOARD REVISIÓN',
            'url': '/gestion-actas/dashboard-revision/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-management'
        }
    }),

    # 15. MÓDULO GENERADOR - LISTA DE ACTAS GENERADAS (Regla original)
    (re.compile(r'^/generador-actas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: PLANTILLAS DE ACTAS',
            'url': '/admin/generador_actas/plantillaacta/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-generator'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: GESTIÓN DE ACTAS',
            'url': '/admin/generador_actas/actagenerada/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-generator'
        }
    }),

    # 16. MÓDULO GENERADOR - DETALLE DE ACTA GENERADA
    (re.compile(r'^/generador-actas/detalle/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE ACTAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-generator'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: GESTIÓN DE ACTAS',
            'url': '/admin/generador_actas/actagenerada/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-generator'
        }
    }),

    # 17. MÓDULO DE GESTIÓN - ACTAS GENERADAS (Admin)
    (re.compile(r'^/admin/generador_actas/actagenerada/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: ACTAS GENERADAS',
            'url': '/generador-actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-management'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: REVISIÓN Y APROBACIÓN',
            'url': '/admin/generador_actas/actagenerada/?estado__exact=borrador',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-management'
        }
    }),

    # 18. MÓDULO DE GESTIÓN - DETALLE/EDICIÓN DE ACTA
    (re.compile(r'^/admin/generador_actas/actagenerada/\d+/change/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: LISTA DE GESTIÓN',
            'url': '/admin/generador_actas/actagenerada/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-management'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: REVISIÓN Y APROBACIÓN',
            'url': '/admin/generador_actas/actagenerada/?estado__exact=borrador',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-management'
        }
    }),

    # 19. MÓDULO DE REVISIÓN - ACTAS EN BORRADOR
    (re.compile(r'^/admin/generador_actas/actagenerada/\?estado__exact=borrador$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: GESTIÓN DE ACTAS',
            'url': '/admin/generador_actas/actagenerada/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-review'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: PORTAL CIUDADANO',
            'url': '/portal-ciudadano/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-review'
        }
    }),

    # 20. PORTAL CIUDADANO - VISTA PRINCIPAL (Final del flujo principal)
    (re.compile(r'^/portal-ciudadano/$'), {
        'previous': {
            'show': True,
            'text': 'LOGIN',
            'url': '/accounts/login/',
            'icon': 'fas fa-sign-in-alt',
            'class': 'nav-btn-prev-portal'
        },
        'next': None  # Final del flujo principal
    }),

    # 21. PORTAL CIUDADANO - ACTAS PUBLICADAS
    (re.compile(r'^/portal-ciudadano/actas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: PORTAL PRINCIPAL',
            'url': '/portal-ciudadano/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-portal'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ACTAS POR REUNIÓN',
            'url': '/portal-ciudadano/actas-por-reunion/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-portal'
        }
    }),

    # 22. PORTAL CIUDADANO - ACTAS POR TIPO DE REUNIÓN
    (re.compile(r'^/portal-ciudadano/actas-por-reunion/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: ACTAS PUBLICADAS',
            'url': '/portal-ciudadano/actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-portal'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ESTADÍSTICAS',
            'url': '/portal-ciudadano/estadisticas/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-portal'
        }
    }),

    # 23. PORTAL CIUDADANO - ESTADÍSTICAS
    (re.compile(r'^/portal-ciudadano/estadisticas/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: ACTAS POR REUNIÓN',
            'url': '/portal-ciudadano/actas-por-reunion/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-portal'
        },
        'next': None  # Final del flujo del portal
    }),

    # 24. PORTAL CIUDADANO - DETALLE DE ACTA
    (re.compile(r'^/portal-ciudadano/acta/\d+/$'), {
        'previous': {
            'show': True,
            'text': 'ANTERIOR: ACTAS PUBLICADAS',
            'url': '/portal-ciudadano/actas/',
            'icon': 'fas fa-arrow-left',
            'class': 'nav-btn-prev-portal'
        },
        'next': {
            'show': True,
            'text': 'SIGUIENTE: ACTAS POR REUNIÓN',
            'url': '/portal-ciudadano/actas-por-reunion/',
            'icon': 'fas fa-arrow-right',
            'class': 'nav-btn-next-portal'
        }
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
