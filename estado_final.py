from apps.generador_actas.models import ActaGenerada

acta = ActaGenerada.objects.get(id=4)
print(f'Estado DB: {acta.estado}')
print(f'Progreso DB: {acta.progreso}')
print(f'Mensaje error: {acta.mensajes_error}')

ultimo_evento = acta.historial_cambios[-1]
print(f'Último evento: {ultimo_evento.get("evento")} - Progreso: {ultimo_evento.get("progreso")}')