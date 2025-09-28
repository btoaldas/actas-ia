from apps.generador_actas.models import ActaGenerada

acta = ActaGenerada.objects.get(id=4)
transcripcion = acta.transcripcion

print(f'Transcripcion: {transcripcion}')
print(f'Tipo: {type(transcripcion)}')

# Ver algunos atributos del modelo
attrs = [attr for attr in dir(transcripcion) if not attr.startswith('_') and not callable(getattr(transcripcion, attr))]
print(f'Atributos: {attrs[:10]}')  # Solo primeros 10

# Verificar específicamente el nombre/título
if hasattr(transcripcion, 'nombre'):
    print(f'Nombre: {transcripcion.nombre}')
if hasattr(transcripcion, 'titulo'):
    print(f'Titulo: {transcripcion.titulo}')
if hasattr(transcripcion, 'descripcion'):
    print(f'Descripcion: {transcripcion.descripcion}')