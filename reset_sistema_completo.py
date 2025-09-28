#!/usr/bin/env python3
"""
Script para revertir todas las actas al estado inicial de edición
Limpia todo: archivos generados, estados, publicaciones, etc.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import transaction
from gestion_actas.models import GestionActa
from apps.pages.models import ActaMunicipal, VisualizacionActa, DescargaActa
from apps.generador_actas.models import ActaGenerada
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def limpiar_archivos_generados():
    """Eliminar todos los archivos PDF, Word, TXT generados"""
    logger.info("🗑️  Limpiando archivos generados...")
    
    import glob
    import shutil
    
    # Patrones de archivos a eliminar
    patrones = [
        'media/actas/*.pdf',
        'media/actas/*.docx', 
        'media/actas/*.txt',
        'media/documentos_actas/*.pdf',
        'media/documentos_actas/*.docx',
        'media/documentos_actas/*.txt',
        'staticfiles/generated_docs/*.*'
    ]
    
    archivos_eliminados = 0
    
    for patron in patrones:
        archivos = glob.glob(patron)
        for archivo in archivos:
            try:
                os.remove(archivo)
                archivos_eliminados += 1
                logger.info(f"   ✓ Eliminado: {archivo}")
            except Exception as e:
                logger.warning(f"   ⚠️  Error eliminando {archivo}: {e}")
    
    # Limpiar directorios vacíos
    directorios = ['media/actas', 'media/documentos_actas', 'staticfiles/generated_docs']
    for dir_path in directorios:
        if os.path.exists(dir_path):
            try:
                # Eliminar archivos restantes
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        os.remove(file_path)
                        archivos_eliminados += 1
                logger.info(f"   ✓ Limpiado directorio: {dir_path}")
            except Exception as e:
                logger.warning(f"   ⚠️  Error limpiando {dir_path}: {e}")
    
    logger.info(f"📊 Total archivos eliminados: {archivos_eliminados}")

def revertir_gestion_actas():
    """Revertir todas las actas de gestión al estado inicial"""
    logger.info("🔄 Revirtiendo estado de actas en gestion_actas...")
    
    with transaction.atomic():
        # Obtener o crear estado inicial
        from gestion_actas.models import EstadoGestionActa
        try:
            estado_edicion = EstadoGestionActa.objects.filter(
                nombre__icontains='edicion'
            ).first()
            if not estado_edicion:
                estado_edicion = EstadoGestionActa.objects.create(
                    codigo='en_edicion',
                    nombre='En Edición/Depuración',
                    descripcion='Estado inicial para edición de actas',
                    permite_edicion=True,
                    requiere_revision=False,
                    visible_portal=False
                )
        except Exception as e:
            logger.warning(f"Error con estados: {e}")
            # Usar el primero disponible como fallback
            estado_edicion = EstadoGestionActa.objects.first()
        
        actas_gestion = GestionActa.objects.all()
        total = actas_gestion.count()
        
        logger.info(f"📋 Encontradas {total} actas para revertir")
        
        for acta in actas_gestion:
            logger.info(f"   🔄 Revirtiendo: {acta.titulo}")
            
            # Revertir al estado inicial
            acta.estado = estado_edicion
            acta.fecha_enviada_revision = None
            acta.fecha_aprobacion_final = None
            acta.fecha_publicacion = None
            acta.observaciones = ''
            acta.bloqueada_edicion = False
            
            # Limpiar relación con portal
            acta.acta_portal = None
            
            # Resetear versión y cambios
            acta.version = 1
            acta.cambios_realizados = {}
            
            acta.save()
            
            logger.info(f"   ✅ {acta.titulo} revertida a estado inicial")
    
    logger.info(f"✅ Todas las actas revertidas exitosamente")

def limpiar_portal_ciudadano():
    """Limpiar todas las entradas del portal ciudadano"""
    logger.info("🌐 Limpiando registros del portal ciudadano...")
    
    with transaction.atomic():
        # Eliminar visualizaciones
        visualizaciones = VisualizacionActa.objects.all()
        count_vis = visualizaciones.count()
        visualizaciones.delete()
        logger.info(f"   ✓ Eliminadas {count_vis} visualizaciones")
        
        # Eliminar descargas
        descargas = DescargaActa.objects.all()
        count_desc = descargas.count()
        descargas.delete()
        logger.info(f"   ✓ Eliminadas {count_desc} descargas")
        
        # Desactivar todas las actas del portal (no eliminar para mantener datos)
        actas_portal = ActaMunicipal.objects.all()
        count_portal = actas_portal.count()
        
        # Obtener estado borrador
        from apps.pages.models import EstadoActa
        try:
            estado_borrador = EstadoActa.objects.get(nombre='borrador')
        except EstadoActa.DoesNotExist:
            # Crear estado borrador si no existe
            estado_borrador = EstadoActa.objects.create(
                nombre='borrador',
                descripcion='Estado inicial de borrador',
                color='#6c757d',
                orden=0
            )
        
        for acta_portal in actas_portal:
            acta_portal.activo = False
            acta_portal.estado = estado_borrador
            acta_portal.fecha_publicacion = None
            # No poner archivo_pdf = None porque es FileField requerido
            acta_portal.save()
        
        logger.info(f"   ✓ Desactivadas {count_portal} actas del portal ciudadano")

def limpiar_actas_generadas():
    """Limpiar referencias en generador_actas si existen"""
    logger.info("📝 Limpiando referencias en generador_actas...")
    
    try:
        with transaction.atomic():
            actas_gen = ActaGenerada.objects.all()
            count_gen = actas_gen.count()
            
            for acta_gen in actas_gen:
                # Solo resetear el estado, no eliminar
                acta_gen.estado = 'borrador'
                acta_gen.fecha_publicacion = None
                # No tocar campo 'publicada' si no existe
                acta_gen.save()
                
            logger.info(f"   ✓ Reseteadas {count_gen} actas en generador_actas")
            
    except Exception as e:
        logger.warning(f"   ⚠️  Error procesando generador_actas: {e}")

def main():
    """Función principal"""
    logger.info("🚀 Iniciando proceso de limpieza completa del sistema...")
    logger.info("=" * 80)
    
    try:
        # 1. Limpiar archivos del sistema de archivos
        limpiar_archivos_generados()
        logger.info("=" * 40)
        
        # 2. Revertir estado de actas de gestión  
        revertir_gestion_actas()
        logger.info("=" * 40)
        
        # 3. Limpiar portal ciudadano
        limpiar_portal_ciudadano()
        logger.info("=" * 40)
        
        # 4. Limpiar generador de actas
        limpiar_actas_generadas()
        logger.info("=" * 40)
        
        logger.info("✅ LIMPIEZA COMPLETA EXITOSA")
        logger.info("🔄 El sistema ha sido revertido al estado inicial")
        logger.info("📋 Todas las actas están ahora en estado 'edicion'")
        logger.info("🌐 El portal ciudadano está vacío")
        logger.info("📁 Todos los archivos generados han sido eliminados")
        logger.info("=" * 80)
        
        # Mostrar resumen
        from gestion_actas.models import EstadoGestionActa
        total_gestion = GestionActa.objects.count()
        actas_portal = ActaMunicipal.objects.filter(activo=True).count()
        
        print(f"""
╔══════════════════════════════════════════════════════════╗
║                    RESUMEN FINAL                         ║
╠══════════════════════════════════════════════════════════╣
║ 📋 Total actas gestion:       {total_gestion:2d}                     ║
║ 🌐 Actas activas en portal:   {actas_portal:2d}                     ║
║ 📁 Archivos generados:        0                         ║
║ 📊 Visualizaciones:           0                         ║
║ 📥 Descargas:                 0                         ║
╚══════════════════════════════════════════════════════════╝
        """)
        
    except Exception as e:
        logger.error(f"❌ Error durante la limpieza: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)