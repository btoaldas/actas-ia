from apps.generador_actas.models import PlantillaActa, ConfiguracionSegmento

plantilla = PlantillaActa.objects.get(id=5)
configs = ConfiguracionSegmento.objects.filter(plantilla=plantilla)

print(f'Plantilla: {plantilla.nombre}')
print(f'Configuraciones: {configs.count()}')

for c in configs:
    print(f'  - {c.segmento.nombre} (orden: {c.orden})')