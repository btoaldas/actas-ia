"""
Script para crear estados iniciales de gestión de actas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion_actas.models import EstadoGestionActa, ConfiguracionExportacion

def crear_estados_iniciales():
    """Crear estados iniciales de gestión de actas"""
    
    estados_data = [
        {
            'codigo': 'generada',
            'nombre': 'Acta Generada',
            'descripcion': 'Acta recién generada por IA, lista para depuración',
            'color': '#17a2b8',
            'orden': 1,
            'permite_edicion': True,
            'requiere_revision': False,
            'visible_portal': False
        },
        {
            'codigo': 'en_edicion',
            'nombre': 'En Edición/Depuración',
            'descripcion': 'Acta siendo editada y mejorada por el usuario',
            'color': '#ffc107',
            'orden': 2,
            'permite_edicion': True,
            'requiere_revision': False,
            'visible_portal': False
        },
        {
            'codigo': 'enviada_revision',
            'nombre': 'Enviada para Revisión',
            'descripcion': 'Acta enviada al proceso de revisión, edición bloqueada',
            'color': '#fd7e14',
            'orden': 3,
            'permite_edicion': False,
            'requiere_revision': True,
            'visible_portal': False
        },
        {
            'codigo': 'en_revision',
            'nombre': 'En Proceso de Revisión',
            'descripcion': 'Acta siendo revisada por los usuarios asignados',
            'color': '#6f42c1',
            'orden': 4,
            'permite_edicion': False,
            'requiere_revision': True,
            'visible_portal': False
        },
        {
            'codigo': 'aprobada',
            'nombre': 'Aprobada por Revisores',
            'descripcion': 'Acta aprobada por todos los revisores requeridos',
            'color': '#28a745',
            'orden': 5,
            'permite_edicion': False,
            'requiere_revision': False,
            'visible_portal': False
        },
        {
            'codigo': 'rechazada',
            'nombre': 'Rechazada',
            'descripcion': 'Acta rechazada por los revisores, requiere correcciones',
            'color': '#dc3545',
            'orden': 6,
            'permite_edicion': True,
            'requiere_revision': False,
            'visible_portal': False
        },
        {
            'codigo': 'lista_publicacion',
            'nombre': 'Lista para Publicación',
            'descripcion': 'Acta aprobada, lista para ser publicada en el portal',
            'color': '#20c997',
            'orden': 7,
            'permite_edicion': False,
            'requiere_revision': False,
            'visible_portal': False
        },
        {
            'codigo': 'publicada',
            'nombre': 'Publicada en Portal',
            'descripcion': 'Acta publicada en el portal ciudadano, visible públicamente',
            'color': '#007bff',
            'orden': 8,
            'permite_edicion': False,
            'requiere_revision': False,
            'visible_portal': True
        },
        {
            'codigo': 'archivada',
            'nombre': 'Archivada',
            'descripcion': 'Acta archivada, fuera del flujo activo',
            'color': '#6c757d',
            'orden': 9,
            'permite_edicion': False,
            'requiere_revision': False,
            'visible_portal': True
        }
    ]
    
    print("🔧 Creando estados de gestión de actas...")
    created_count = 0
    
    for estado_data in estados_data:
        estado, created = EstadoGestionActa.objects.get_or_create(
            codigo=estado_data['codigo'],
            defaults=estado_data
        )
        
        if created:
            print(f"✅ Creado: {estado.nombre}")
            created_count += 1
        else:
            print(f"⚠️  Ya existe: {estado.nombre}")
    
    print(f"\n🎯 Estados creados: {created_count}/{len(estados_data)}")


def crear_configuracion_exportacion():
    """Crear configuración por defecto de exportación"""
    
    config_data = {
        'pdf_header_enabled': True,
        'pdf_footer_enabled': True,
        'pdf_watermark': 'GOBIERNO MUNICIPAL DE PASTAZA',
        'pdf_template': 'oficial',
        'word_template_path': '',
        'word_styles_enabled': True,
        'txt_encoding': 'utf-8',
        'txt_line_endings': 'lf',
        'incluir_metadatos': True,
        'incluir_firma_digital': False,
        'activa': True
    }
    
    print("\n📄 Creando configuración de exportación...")
    
    # Desactivar configuraciones existentes
    ConfiguracionExportacion.objects.filter(activa=True).update(activa=False)
    
    config, created = ConfiguracionExportacion.objects.get_or_create(
        activa=True,
        defaults=config_data
    )
    
    if created:
        print("✅ Configuración de exportación creada")
    else:
        print("⚠️  Ya existe configuración activa")


if __name__ == "__main__":
    print("🚀 Inicializando datos de Gestión de Actas\n")
    
    try:
        crear_estados_iniciales()
        crear_configuracion_exportacion()
        
        print("\n🎉 ¡Inicialización completada exitosamente!")
        print("\n📋 Próximos pasos:")
        print("1. Acceder al admin de Django para revisar los estados")
        print("2. Comenzar a usar el sistema de gestión de actas")
        print("3. Configurar usuarios con permisos de revisión")
        
    except Exception as e:
        print(f"\n❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()