from apps.generador_actas.models import ActaGenerada
import json

acta = ActaGenerada.objects.get(id=4)
print(f'Total entradas historial: {len(acta.historial_cambios)}')
print('\n=== ÚLTIMAS 5 ENTRADAS DEL HISTORIAL ===')

for h in acta.historial_cambios[-5:]:
    timestamp = h.get('timestamp', 'No timestamp')
    evento = h.get('evento', 'No evento')
    descripcion = h.get('descripcion', 'No descripcion')
    progreso = h.get('progreso', 'No progreso')
    print(f'{timestamp}: {evento} - {descripcion} (progreso: {progreso})')