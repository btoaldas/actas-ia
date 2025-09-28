from apps.generador_actas.models import ActaGenerada, EjecucionPlantilla

# Verificar acta 4
acta = ActaGenerada.objects.get(id=4)
print(f'Acta: {acta.numero_acta}')
print(f'Plantilla: {acta.plantilla}')

# Verificar ejecuciones para esta acta
ejecuciones = EjecucionPlantilla.objects.filter(acta_generada=acta)
print(f'Ejecuciones para acta 4: {ejecuciones.count()}')
for e in ejecuciones:
    print(f'  ID: {e.id}, Estado: {e.estado}')

# Mostrar todas las ejecuciones
print('\nTodas las ejecuciones:')
for e in EjecucionPlantilla.objects.all():
    print(f'ID: {e.id}, Acta: {e.acta_generada.id if e.acta_generada else "None"}, Estado: {e.estado}')