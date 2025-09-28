from apps.generador_actas.models import ActaGenerada, EjecucionPlantilla, PlantillaActa, ProveedorIA
from apps.transcripcion.models import Transcripcion
from django.contrib.auth.models import User

# Obtener datos necesarios
acta = ActaGenerada.objects.get(id=4)
plantilla = acta.plantilla
proveedor = acta.proveedor_ia
# Para EjecucionPlantilla necesitamos ProcesamientoAudio, no Transcripcion
# Busquemos el ProcesamientoAudio relacionado con la transcripcion del acta
transcripcion_obj = acta.transcripcion
procesamiento_audio = transcripcion_obj.procesamiento_audio if hasattr(transcripcion_obj, 'procesamiento_audio') else None
usuario = User.objects.get(username='superadmin')

print(f'Acta: {acta.numero_acta}')
print(f'Transcripcion: {transcripcion_obj}')
print(f'Procesamiento Audio: {procesamiento_audio}')

# Verificar si ya existe una ejecución activa
ejecucion_existente = EjecucionPlantilla.objects.filter(
    plantilla=plantilla,
    usuario=usuario,
    estado__in=['iniciada', 'procesando_segmentos']
).first()

if ejecucion_existente:
    print(f'Ya existe ejecución: {ejecucion_existente.id}')
    ejecucion = ejecucion_existente
else:
    # Crear nueva ejecución
    ejecucion = EjecucionPlantilla.objects.create(
        nombre=f"Procesamiento para {acta.numero_acta}",
        plantilla=plantilla,
        usuario=usuario,
        transcripcion=procesamiento_audio,  # Usar el ProcesamientoAudio
        proveedor_ia_global=proveedor,
        variables_contexto={
            'acta_id': acta.pk,
            'numero_acta': acta.numero_acta,
            'fecha_sesion': acta.fecha_sesion.isoformat() if acta.fecha_sesion else None
        }
    )
    print(f'Nueva ejecución creada: {ejecucion.id}')

print(f'UUID de ejecución: {ejecucion.id}')
print(f'Estado: {ejecucion.estado}')
print(f'Plantilla: {ejecucion.plantilla.nombre}')
print(f'Proveedor IA: {ejecucion.proveedor_ia_global.nombre}')