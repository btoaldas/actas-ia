#!/usr/bin/env python
"""
Script para analizar información rica de actas
"""
import os
import django
import sys

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion_actas.models import GestionActa
from apps.generador_actas.models import ActaGenerada

# Obtener una acta importada con toda su información
gestion = GestionActa.objects.filter(acta_generada__isnull=False).first()

if not gestion:
    print("No se encontraron gestiones con actas generadas")
    exit()

acta = gestion.acta_generada
transcripcion = acta.transcripcion
procesamiento = transcripcion.procesamiento_audio

print('=== INFORMACIÓN COMPLETA DE ACTA ===')
print(f'ID Gestión: {gestion.pk}')
print(f'Título: {acta.titulo}')
print(f'Número: {acta.numero_acta}')
print(f'Estado original: {acta.estado}')
print(f'Fecha sesión: {acta.fecha_sesion}')
print(f'Usuario creación: {acta.usuario_creacion.username}')

print('\n=== INFORMACIÓN DE PROCESAMIENTO ===')
print(f'Tipo reunión: {procesamiento.tipo_reunion.nombre if procesamiento.tipo_reunion else "N/A"}')
print(f'Participantes: {procesamiento.participantes[:100] if procesamiento.participantes else "N/A"}...')
print(f'Participantes detallados: {len(procesamiento.participantes_detallados) if procesamiento.participantes_detallados else 0} personas')
print(f'Ubicación: {procesamiento.ubicacion or "N/A"}')
print(f'Duración: {procesamiento.duracion_seg or "N/A"} segundos')
print(f'Confidencial: {procesamiento.confidencial}')
print(f'Etiquetas: {procesamiento.etiquetas or "N/A"}')

print('\n=== INFORMACIÓN DE TRANSCRIPCIÓN ===')
print(f'Hablantes detectados: {transcripcion.numero_hablantes}')
print(f'Palabras totales: {transcripcion.palabras_totales}')
print(f'Confianza promedio: {transcripcion.confianza_promedio}')
print(f'Segmentos: {transcripcion.numero_segmentos}')

print('\n=== PLANTILLA Y PROVEEDOR ===')  
print(f'Plantilla: {acta.plantilla.nombre}')
print(f'Proveedor IA: {acta.proveedor_ia.nombre}')

print('\n=== MÉTRICAS DE PROCESAMIENTO ===')
if acta.metricas_procesamiento:
    for key, value in acta.metricas_procesamiento.items():
        print(f'  {key}: {value}')
else:
    print('  Sin métricas disponibles')

print('\n=== METADATOS ===')
if acta.metadatos:
    for key, value in acta.metadatos.items():
        print(f'  {key}: {value}')
else:
    print('  Sin metadatos disponibles')