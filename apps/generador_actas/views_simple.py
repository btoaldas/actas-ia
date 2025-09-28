from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.generador_actas.models import SegmentoPlantilla, PlantillaActa, ConfiguracionSegmento
from apps.generador_actas.forms import PlantillaBasicaForm

@login_required
def crear_plantilla_simple(request):
    """Vista simple para crear plantillas sin problemas de contexto"""
    
    if request.method == 'POST':
        form = PlantillaBasicaForm(request.POST)
        if form.is_valid():
            plantilla = form.save(commit=False)
            plantilla.usuario_creacion = request.user
            plantilla.save()
            
            # Procesar segmentos seleccionados
            segmentos_seleccionados = request.POST.getlist('segmentos_seleccionados')
            segmentos_creados = 0
            
            for segmento_id in segmentos_seleccionados:
                try:
                    segmento = SegmentoPlantilla.objects.get(id=segmento_id)
                    orden = request.POST.get(f'orden_{segmento_id}', 1)
                    obligatorio = request.POST.get(f'obligatorio_{segmento_id}') == 'on'
                    
                    ConfiguracionSegmento.objects.create(
                        plantilla=plantilla,
                        segmento=segmento,
                        orden=int(orden),
                        obligatorio=obligatorio
                    )
                    segmentos_creados += 1
                except Exception as e:
                    print(f'Error procesando segmento {segmento_id}: {e}')
            
            messages.success(
                request, 
                f'✅ Plantilla "{plantilla.nombre}" creada con {segmentos_creados} segmentos.'
            )
            return redirect('generador_actas:plantillas_lista')
    else:
        form = PlantillaBasicaForm()
    
    # Obtener segmentos disponibles
    segmentos_disponibles = SegmentoPlantilla.objects.filter(activo=True).order_by('categoria', 'nombre')
    
    context = {
        'form': form,
        'segmentos_disponibles': segmentos_disponibles,
        'page_title': 'Nueva Plantilla',
        'breadcrumbs': [
            {'title': 'Generador Actas', 'url': '/generador-actas/'},
            {'title': 'Plantillas', 'url': '/generador-actas/plantillas/'},
            {'title': 'Nueva', 'url': ''}
        ]
    }
    
    return render(request, 'generador_actas/plantillas/crear_funcional.html', context)