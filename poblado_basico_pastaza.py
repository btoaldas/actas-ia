#!/usr/bin/env python
"""
Script simplificado para poblar con datos básicos del Municipio de Pastaza
Solo usando campos que sabemos que funcionan
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from apps.pages.models import TipoSesion, EstadoActa, ActaMunicipal
from apps.audio_processing.models import TipoReunion, ProcesamientoAudio


def poblado_basico_pastaza():
    """Poblado básico y funcional para el Municipio de Pastaza"""
    print("🚀 POBLADO BÁSICO DEL MUNICIPIO DE PASTAZA")
    print("🌍 GAD Municipal del Cantón Pastaza - Puyo, Ecuador")
    print("=" * 65)
    
    # Crear tipos básicos si no existen
    print("📋 Configurando tipos básicos...")
    
    tipo_ordinaria, _ = TipoSesion.objects.get_or_create(
        nombre='Ordinaria',
        defaults={
            'descripcion': 'Sesión ordinaria del Concejo Municipal',
            'color': '#007bff',
            'icono': 'fas fa-calendar-alt',
            'activo': True
        }
    )
    
    estado_publicada, _ = EstadoActa.objects.get_or_create(
        nombre='Publicada',
        defaults={
            'descripcion': 'Acta publicada para acceso ciudadano',
            'color': '#28a745',
            'orden': 4,
            'activo': True
        }
    )
    
    # Obtener usuario alcalde
    alcalde = User.objects.filter(username='sflores').first()
    if not alcalde:
        print("❌ No se encontró el usuario alcalde")
        return
    
    # Temas de sesiones del Municipio de Pastaza
    temas_pastaza = [
        'Ordenanza de Regulación del Comercio Ambulante en el Centro de Puyo',
        'Aprobación del Presupuesto Municipal 2025 - Segundo Semestre',
        'Creación del Parque Ecológico Río Pastaza',
        'Declaratoria de Emergencia Vial en el Sector Shell',
        'Reglamento de Turismo Comunitario Indígena Shuar y Achuar',
        'Plan de Gestión de Residuos Sólidos Cantonal',
        'Convenio con Universidad Estatal Amazónica UEA',
        'Regulación de Actividades Mineras en Territorio Cantonal',
        'Fortalecimiento del Sistema de Agua Potable Rural',
        'Creación de la Casa de la Cultura Amazónica',
        'Plan de Contingencia para Temporada Lluviosa 2025',
        'Reglamento de Construcciones Sostenibles en Puyo'
    ]
    
    print("🏛️ Creando actas municipales...")
    actas_creadas = 0
    fecha_base = datetime.now() - timedelta(days=180)
    
    for i, tema in enumerate(temas_pastaza):
        try:
            fecha_sesion = fecha_base + timedelta(days=i*15)
            
            # Crear solo con campos básicos que sabemos que funcionan
            acta = ActaMunicipal.objects.create(
                numero_acta=f"ACTA-PASTAZA-{2025}-{str(i+1).zfill(3)}",
                numero_sesion=i+1,
                titulo=tema,
                fecha_sesion=timezone.make_aware(fecha_sesion),
                tipo_sesion=tipo_ordinaria,
                estado=estado_publicada,
                resumen=f"Sesión del Concejo Municipal de Pastaza sobre {tema.lower()}. "
                       f"Importante para el desarrollo del cantón en la región amazónica.",
                contenido=f"""
ACTA DE SESIÓN DEL CONCEJO MUNICIPAL DEL CANTÓN PASTAZA

En la ciudad de Puyo, capital del cantón Pastaza, el {fecha_sesion.strftime('%d de %B de %Y')}, 
se desarrolló sesión del Concejo Municipal bajo la presidencia del señor Alcalde 
Segundo Germán Flores Meza.

TEMA: {tema}

El Concejo Municipal analizó la propuesta considerando el impacto en las comunidades 
del cantón Pastaza, incluyendo las parroquias urbanas y rurales, así como las 
nacionalidades indígenas Shuar y Achuar presentes en el territorio amazónico.

Se adoptaron las decisiones pertinentes en el marco de las competencias municipales 
establecidas en el COOTAD para el bienestar de los ciudadanos pastacenses.

Elaborada por: Secretaría General del GAD Municipal
Revisada por: Alcaldía del Cantón Pastaza
""",
                acceso='publico',
                secretario=alcalde,
                presidente=alcalde,
                activo=True
            )
            
            actas_creadas += 1
            print(f"  ✅ {acta.numero_acta}: {tema[:60]}...")
            
        except Exception as e:
            print(f"❌ Error creando acta {i+1}: {str(e)[:100]}")
            continue
    
    print(f"📊 Actas municipales creadas: {actas_creadas}")
    
    # Crear algunos procesamientos de audio básicos
    print("🎵 Creando procesamientos de audio...")
    
    tipo_reunion, _ = TipoReunion.objects.get_or_create(
        nombre='Sesión Municipal',
        defaults={
            'descripcion': 'Sesión del Concejo Municipal de Pastaza',
            'activo': True
        }
    )
    
    audio_creados = 0
    actas = ActaMunicipal.objects.all()[:5]  # Solo las primeras 5
    
    for acta in actas:
        try:
            ProcesamientoAudio.objects.create(
                tipo_reunion=tipo_reunion,
                titulo=f"Audio - {acta.titulo[:50]}",
                descripcion=f"Grabación de la sesión {acta.numero_acta}",
                estado='completado',
                fecha_inicio=acta.fecha_sesion,
                fecha_completado=acta.fecha_sesion + timedelta(hours=2),
                duracion_original=random.randint(7200, 14400),
                participantes_detallados=[
                    {
                        'nombre': 'Segundo Germán Flores Meza',
                        'cargo': 'Alcalde del Cantón Pastaza'
                    }
                ],
                metadatos_originales={'formato': 'mp3', 'calidad': 'alta'},
                metadatos_procesamiento={'modelo': 'whisper-v3'},
                confidencial=False
            )
            audio_creados += 1
        except Exception as e:
            print(f"❌ Error creando audio para {acta.numero_acta}: {str(e)[:50]}")
            continue
    
    print(f"📊 Procesamientos de audio creados: {audio_creados}")
    
    print("\n" + "=" * 65)
    print("✅ POBLADO BÁSICO COMPLETADO EXITOSAMENTE")
    print("=" * 65)
    print(f"🏛️ Actas municipales: {actas_creadas}")
    print(f"🎵 Procesamientos de audio: {audio_creados}")
    print("\n🎉 EL SISTEMA TIENE DATOS REALISTAS DEL MUNICIPIO DE PASTAZA!")
    print("🏛️ Alcalde: Segundo Germán Flores Meza")
    print("🌍 Ubicación: Puyo, Cantón Pastaza, Región Amazónica")
    print("🌐 Web: https://puyo.gob.ec/")
    print("📱 Facebook: https://www.facebook.com/GADMPastaza")
    
    return {
        'actas': actas_creadas,
        'audio': audio_creados
    }


if __name__ == '__main__':
    resultado = poblado_basico_pastaza()