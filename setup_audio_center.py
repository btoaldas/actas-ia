#!/usr/bin/env python
"""
Script para configurar el Centro de Audio con datos de ejemplo
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/app')  # Ruta dentro del contenedor
django.setup()

from apps.audio_processing.models import TipoReunion, ProcesamientoAudio
from django.contrib.auth.models import User

def main():
    print("🎯 Configurando Centro de Audio...")
    
    # 1. Verificar tipos de reunión
    print("\n📋 Verificando tipos de reunión...")
    tipos_count = TipoReunion.objects.count()
    print(f"Total tipos de reunión: {tipos_count}")
    
    if tipos_count > 0:
        print("Tipos de reunión disponibles:")
        for tipo in TipoReunion.objects.all():
            print(f"  - {tipo.nombre}: {tipo.descripcion}")
    else:
        print("⚠️  No hay tipos de reunión. Creando algunos básicos...")
        tipos_basicos = [
            ("Reunión de Equipo", "Reuniones regulares de equipos de trabajo"),
            ("Junta Directiva", "Reuniones del consejo o junta directiva"),
            ("Entrevista", "Entrevistas de trabajo o evaluación"),
            ("Conferencia", "Conferencias, webinars o presentaciones"),
            ("Sesión de Brainstorming", "Sesiones de lluvia de ideas o creatividad"),
            ("Sesión de Concejo", "Sesiones municipales del concejo"),
            ("Audiencia Pública", "Audiencias públicas municipales"),
            ("Reunión Comunitaria", "Reuniones con la comunidad"),
        ]
        
        for nombre, descripcion in tipos_basicos:
            tipo, created = TipoReunion.objects.get_or_create(
                nombre=nombre,
                defaults={'descripcion': descripcion, 'activo': True}
            )
            if created:
                print(f"  ✅ Creado: {nombre}")
            else:
                print(f"  📝 Ya existe: {nombre}")
    
    # 2. Verificar usuarios
    print("\n👥 Verificando usuarios...")
    users_count = User.objects.count()
    print(f"Total usuarios: {users_count}")
    
    # 3. Verificar procesamientos
    print("\n🎙️ Verificando procesamientos de audio...")
    procesamientos_count = ProcesamientoAudio.objects.count()
    print(f"Total procesamientos: {procesamientos_count}")
    
    # 4. Mostrar estadísticas
    print("\n📊 Estadísticas del sistema:")
    from django.db.models import Count, Q
    
    stats = ProcesamientoAudio.objects.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(estado='completado')),
        processing=Count('id', filter=Q(estado__in=['pendiente', 'procesando', 'transcribiendo'])),
        error=Count('id', filter=Q(estado='error'))
    )
    
    print(f"  - Total: {stats['total'] or 0}")
    print(f"  - Completados: {stats['completed'] or 0}")
    print(f"  - En proceso: {stats['processing'] or 0}")
    print(f"  - Con errores: {stats['error'] or 0}")
    
    print("\n✅ ¡Centro de Audio configurado correctamente!")
    print("\n🌐 Puedes acceder en: http://localhost/audio/")
    print("🎯 O desde el menú: Audio & Transcripción > Centro de Audio")

if __name__ == "__main__":
    main()
