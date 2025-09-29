#!/usr/bin/env python
"""
Poblador completo de datos realistas para el Municipio de Pastaza
Genera información completa de autoridades, sesiones, audio, transcripciones y actas
Basado en información real del GAD Municipal del Cantón Pastaza
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta
from decimal import Decimal

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from apps.pages.models import (
    TipoSesion, EstadoActa, ActaMunicipal, 
    VisualizacionActa, DescargaActa
)
from apps.audio_processing.models import TipoReunion, ProcesamientoAudio
from apps.transcripcion.models import Transcripcion, ConfiguracionTranscripcion
from apps.auditoria.models import SistemaLogs
import json


class PobladorMunicipioPastaza:
    """Poblador de datos realistas del Municipio de Pastaza"""
    
    def __init__(self):
        self.autoridades_municipales = {
            'alcalde': {
                'nombres': 'Segundo Germán',
                'apellidos': 'Flores Meza',
                'cargo': 'Alcalde',
                'email': 'alcalde@puyo.gob.ec'
            },
            'concejales': [
                {
                    'nombres': 'Roosevelt Wilmer',
                    'apellidos': 'Gómez Arias',
                    'cargo': 'Concejal Principal',
                    'email': 'rgomez@puyo.gob.ec'
                },
                {
                    'nombres': 'Luis Fernando',
                    'apellidos': 'Guevara Pabón',
                    'cargo': 'Concejal Principal',
                    'email': 'lguevara@puyo.gob.ec'
                },
                {
                    'nombres': 'Mónica Gabriela',
                    'apellidos': 'Meza Bracho',
                    'cargo': 'Concejal Principal',
                    'email': 'mmeza@puyo.gob.ec'
                },
                {
                    'nombres': 'Jenny Judith',
                    'apellidos': 'Moncayo Peaza',
                    'cargo': 'Concejal Principal',
                    'email': 'jmoncayo@puyo.gob.ec'
                },
                {
                    'nombres': 'Laura Marisol',
                    'apellidos': 'Pérez Heredia',
                    'cargo': 'Concejal Principal',
                    'email': 'lperez@puyo.gob.ec'
                },
                {
                    'nombres': 'Iván Ramiro',
                    'apellidos': 'Rodríguez Villavicencio',
                    'cargo': 'Concejal Principal',
                    'email': 'irodriguez@puyo.gob.ec'
                },
                {
                    'nombres': 'Aníbal Homero',
                    'apellidos': 'Toscano Vargas',
                    'cargo': 'Concejal Principal',
                    'email': 'atoscano@puyo.gob.ec'
                }
            ],
            'funcionarios': [
                {
                    'nombres': 'María Elena',
                    'apellidos': 'Vásquez Castro',
                    'cargo': 'Secretaria General',
                    'email': 'secretaria@puyo.gob.ec'
                },
                {
                    'nombres': 'Carlos Eduardo',
                    'apellidos': 'Morales Rivadeneira',
                    'cargo': 'Director de Planificación',
                    'email': 'planificacion@puyo.gob.ec'
                },
                {
                    'nombres': 'Ana Cristina',
                    'apellidos': 'Salazar Mendoza',
                    'cargo': 'Directora Financiera',
                    'email': 'financiero@puyo.gob.ec'
                }
            ]
        }
        
        self.temas_sesiones = [
            {
                'titulo': 'Ordenanza de Regulación del Comercio Ambulante en el Centro de Puyo',
                'descripcion': 'Debate sobre la nueva normativa para regular el comercio informal en el centro histórico de la ciudad.',
                'tipo': 'ordinaria',
                'ordenanza': 'ORD-2025-001'
            },
            {
                'titulo': 'Aprobación del Presupuesto Municipal 2025 - Segundo Semestre',
                'descripcion': 'Análisis y aprobación del presupuesto participativo para el segundo semestre del año fiscal.',
                'tipo': 'ordinaria',
                'ordenanza': 'RES-2025-015'
            },
            {
                'titulo': 'Creación del Parque Ecológico Río Pastaza',
                'descripcion': 'Propuesta para la creación de un parque ecológico en las riberas del río Pastaza para conservación.',
                'tipo': 'extraordinaria',
                'ordenanza': 'ORD-2025-002'
            },
            {
                'titulo': 'Declaratoria de Emergencia Vial en el Sector Shell',
                'descripcion': 'Declaratoria de emergencia para reparación de la vía Shell-Mera por deslizamientos.',
                'tipo': 'extraordinaria',
                'ordenanza': 'RES-2025-016'
            },
            {
                'titulo': 'Reglamento de Turismo Comunitario Indígena',
                'descripcion': 'Normativa para fortalecer el turismo comunitario en las nacionalidades Shuar y Achuar.',
                'tipo': 'ordinaria',
                'ordenanza': 'ORD-2025-003'
            },
            {
                'titulo': 'Plan de Gestión de Residuos Sólidos Cantonal',
                'descripcion': 'Implementación del nuevo plan de manejo integral de residuos sólidos para todo el cantón.',
                'tipo': 'ordinaria',
                'ordenanza': 'RES-2025-017'
            },
            {
                'titulo': 'Aprobación de Convenio con Universidad Estatal Amazónica',
                'descripcion': 'Convenio de cooperación técnica y académica con la UEA para proyectos de desarrollo.',
                'tipo': 'ordinaria',
                'ordenanza': 'CON-2025-005'
            },
            {
                'titulo': 'Regulación de Actividades Mineras en Territorio Cantonal',
                'descripcion': 'Establecimiento de normativas para control de actividades mineras y protección ambiental.',
                'tipo': 'extraordinaria',
                'ordenanza': 'ORD-2025-004'
            },
            {
                'titulo': 'Fortalecimiento del Sistema de Agua Potable Rural',
                'descripcion': 'Proyecto de mejoramiento del servicio de agua potable para comunidades rurales del cantón.',
                'tipo': 'ordinaria',
                'ordenanza': 'RES-2025-018'
            },
            {
                'titulo': 'Creación de la Casa de la Cultura Amazónica',
                'descripcion': 'Establecimiento de espacio cultural para preservación y difusión de la cultura amazónica.',
                'tipo': 'ordinaria',
                'ordenanza': 'ORD-2025-005'
            },
            {
                'titulo': 'Plan de Contingencia para Temporada Lluviosa 2025',
                'descripcion': 'Medidas preventivas y de respuesta ante emergencias por precipitaciones extremas.',
                'tipo': 'extraordinaria',
                'ordenanza': 'RES-2025-019'
            },
            {
                'titulo': 'Reglamento de Construcciones Sostenibles',
                'descripcion': 'Normativa para promover construcciones eco-amigables y arquitectura bioclimática.',
                'tipo': 'ordinaria',
                'ordenanza': 'ORD-2025-006'
            }
        ]

    def crear_usuarios(self):
        """Crear usuarios para autoridades municipales"""
        print("🏛️ Creando usuarios de autoridades municipales...")
        
        usuarios_creados = []
        
        # Crear usuario para el Alcalde
        try:
            alcalde_user = User.objects.create_user(
                username='sflores',
                email=self.autoridades_municipales['alcalde']['email'],
                first_name=self.autoridades_municipales['alcalde']['nombres'],
                last_name=self.autoridades_municipales['alcalde']['apellidos'],
                is_staff=True,
                is_active=True
            )
            alcalde_user.set_password('Alcalde2025!')
            alcalde_user.save()
            usuarios_creados.append(f"✅ Alcalde: {alcalde_user.get_full_name()}")
        except:
            print("ℹ️ Usuario alcalde ya existe")

        # Crear usuarios para concejales
        for i, concejal in enumerate(self.autoridades_municipales['concejales']):
            try:
                username = f"concejal{i+1}"
                user = User.objects.create_user(
                    username=username,
                    email=concejal['email'],
                    first_name=concejal['nombres'],
                    last_name=concejal['apellidos'],
                    is_active=True
                )
                user.set_password('Concejal2025!')
                user.save()
                usuarios_creados.append(f"✅ Concejal: {user.get_full_name()}")
            except:
                print(f"ℹ️ Usuario {concejal['apellidos']} ya existe")

        # Crear usuarios para funcionarios
        for i, funcionario in enumerate(self.autoridades_municipales['funcionarios']):
            try:
                username = f"funcionario{i+1}"
                user = User.objects.create_user(
                    username=username,
                    email=funcionario['email'],
                    first_name=funcionario['nombres'],
                    last_name=funcionario['apellidos'],
                    is_staff=True,
                    is_active=True
                )
                user.set_password('Funcionario2025!')
                user.save()
                usuarios_creados.append(f"✅ Funcionario: {user.get_full_name()}")
            except:
                print(f"ℹ️ Usuario {funcionario['apellidos']} ya existe")

        print(f"📊 Total usuarios creados: {len(usuarios_creados)}")
        for usuario in usuarios_creados[:5]:  # Mostrar solo los primeros 5
            print(f"  {usuario}")
        
        return len(usuarios_creados)

    def crear_tipos_reunion(self):
        """Crear tipos de reunión municipales"""
        print("📋 Creando tipos de reunión...")
        
        tipos_reunion = [
            {
                'nombre': 'Sesión Ordinaria',
                'descripcion': 'Sesión ordinaria del Concejo Municipal de Pastaza',
                'requiere_quorum': True,
                'es_publica': True
            },
            {
                'nombre': 'Sesión Extraordinaria',
                'descripcion': 'Sesión extraordinaria por temas urgentes del cantón',
                'requiere_quorum': True,
                'es_publica': True
            },
            {
                'nombre': 'Comisión Permanente',
                'descripcion': 'Reunión de comisión permanente especializada',
                'requiere_quorum': False,
                'es_publica': False
            },
            {
                'nombre': 'Mesa de Trabajo',
                'descripcion': 'Mesa técnica de trabajo con funcionarios municipales',
                'requiere_quorum': False,
                'es_publica': False
            }
        ]
        
        tipos_creados = 0
        for tipo_data in tipos_reunion:
            tipo, created = TipoReunion.objects.get_or_create(
                nombre=tipo_data['nombre'],
                defaults=tipo_data
            )
            if created:
                tipos_creados += 1
                print(f"  ✅ {tipo.nombre}")
        
        print(f"📊 Tipos de reunión creados: {tipos_creados}")
        return tipos_creados

    def crear_sesiones_municipales(self):
        """Crear sesiones municipales realistas"""
        print("🏛️ Creando sesiones municipales del Concejo de Pastaza...")
        
        # Obtener usuarios y tipos
        alcalde = User.objects.filter(username='sflores').first()
        secretaria = User.objects.filter(first_name='María Elena').first()
        tipo_ordinaria = TipoReunion.objects.filter(nombre='Sesión Ordinaria').first()
        tipo_extraordinaria = TipoReunion.objects.filter(nombre='Sesión Extraordinaria').first()
        
        if not alcalde or not tipo_ordinaria:
            print("❌ Error: No se encontraron usuarios o tipos de reunión necesarios")
            return 0

        sesiones_creadas = 0
        fecha_base = datetime.now() - timedelta(days=180)  # Empezar hace 6 meses
        
        for i, tema in enumerate(self.temas_sesiones):
            # Calcular fecha de sesión (cada 15 días aproximadamente)
            fecha_sesion = fecha_base + timedelta(days=i*15 + random.randint(-3, 3))
            
            # Determinar tipo de sesión
            tipo_reunion = tipo_extraordinaria if tema['tipo'] == 'extraordinaria' else tipo_ordinaria
            
            # Crear acta municipal
            acta = ActaMunicipal.objects.create(
                numero_acta=f"ACTA-{2025}-{str(i+1).zfill(3)}",
                fecha_sesion=fecha_sesion,
                tipo_sesion=tipo_reunion,
                titulo=tema['titulo'],
                descripcion_breve=tema['descripcion'],
                ubicacion='Salón de Sesiones del GAD Municipal - Puyo, Pastaza',
                presidida_por=alcalde,
                secretario_acta=secretaria or alcalde,
                estado='publicada' if random.choice([True, True, True, False]) else 'borrador',
                es_publica=True,
                acceso_publico='publico',
                confidencial=False,
                metadata_adicional={
                    'ordenanza_numero': tema.get('ordenanza', ''),
                    'ciudad': 'Puyo',
                    'canton': 'Pastaza',
                    'provincia': 'Pastaza',
                    'region': 'Amazónica',
                    'quorum_minimo': 5,
                    'duracion_estimada': random.randint(120, 240)
                }
            )
            
            # Crear participantes (autoridades municipales)
            self.crear_participantes_sesion(acta)
            
            # Crear procesamiento de audio
            self.crear_procesamiento_audio(acta)
            
            # Crear transcripción
            self.crear_transcripcion_completa(acta)
            
            sesiones_creadas += 1
            print(f"  ✅ {acta.numero_acta}: {acta.titulo[:50]}...")

        print(f"📊 Sesiones municipales creadas: {sesiones_creadas}")
        return sesiones_creadas

    def crear_participantes_sesion(self, acta):
        """Crear participantes para una sesión"""
        # Alcalde siempre presente
        alcalde = User.objects.filter(username='sflores').first()
        if alcalde:
            ParticipanteReunion.objects.create(
                acta=acta,
                nombre_completo=f"{alcalde.first_name} {alcalde.last_name}",
                cargo='Alcalde del GAD Municipal del Cantón Pastaza',
                rol_participacion='presidente',
                presente=True,
                observaciones='Preside la sesión'
            )

        # Concejales (entre 5-7 presentes)
        concejales_usuarios = User.objects.filter(username__startswith='concejal')
        num_presentes = random.randint(5, min(7, concejales_usuarios.count()))
        
        for user in concejales_usuarios[:num_presentes]:
            ParticipanteReunion.objects.create(
                acta=acta,
                nombre_completo=f"{user.first_name} {user.last_name}",
                cargo='Concejal Principal',
                rol_participacion='concejal',
                presente=True,
                observaciones='Participación activa en el debate'
            )

        # Funcionarios municipales
        funcionarios = User.objects.filter(username__startswith='funcionario')
        for user in funcionarios[:2]:  # Máximo 2 funcionarios por sesión
            ParticipanteReunion.objects.create(
                acta=acta,
                nombre_completo=f"{user.first_name} {user.last_name}",
                cargo=random.choice(['Secretario General', 'Director de Planificación', 'Director Financiero']),
                rol_participacion='funcionario',
                presente=True,
                observaciones='Soporte técnico y administrativo'
            )

    def crear_procesamiento_audio(self, acta):
        """Crear registro de procesamiento de audio para la sesión"""
        estados_posibles = ['completado', 'procesando', 'error', 'pendiente']
        estado = random.choices(
            estados_posibles, 
            weights=[70, 10, 5, 15]  # 70% completado, 10% procesando, etc.
        )[0]
        
        procesamiento = ProcesamientoAudio.objects.create(
            tipo_reunion=acta.tipo_sesion,
            titulo=f"Audio - {acta.titulo}",
            descripcion=f"Grabación de la sesión municipal {acta.numero_acta}",
            estado=estado,
            fecha_inicio=acta.fecha_sesion,
            fecha_completado=acta.fecha_sesion + timedelta(hours=2) if estado == 'completado' else None,
            duracion_original=random.randint(7200, 14400),  # Entre 2-4 horas
            ubicacion=acta.ubicacion,
            participantes_detallados=[
                {
                    'nombre': 'Segundo Germán Flores Meza',
                    'cargo': 'Alcalde',
                    'tiempo_participacion': random.randint(1800, 3600)
                },
                {
                    'nombre': 'Roosevelt Wilmer Gómez Arias',
                    'cargo': 'Concejal Principal',
                    'tiempo_participacion': random.randint(600, 1800)
                },
                {
                    'nombre': 'Luis Fernando Guevara Pabón',
                    'cargo': 'Concejal Principal',
                    'tiempo_participacion': random.randint(600, 1800)
                }
            ],
            metadatos_originales={
                'formato': 'mp3',
                'bitrate': 128,
                'sample_rate': 44100,
                'canales': 2,
                'dispositivo_grabacion': 'Sistema de Audio Municipal',
                'ubicacion_grabacion': 'Salón de Sesiones'
            },
            metadatos_procesamiento={
                'snr_promedio': round(random.uniform(15.0, 25.0), 2),
                'nivel_ruido': round(random.uniform(0.1, 0.3), 3),
                'modelo_transcripcion': 'whisper-large-v3',
                'modelo_diarizacion': 'pyannote-v3',
                'tiempo_procesamiento': random.randint(300, 900)
            } if estado == 'completado' else {},
            confidencial=False,
            acta_generada=acta if estado == 'completado' else None
        )
        
        return procesamiento

    def crear_transcripcion_completa(self, acta):
        """Crear transcripción completa para la sesión"""
        procesamiento = ProcesamientoAudio.objects.filter(acta_generada=acta).first()
        
        if not procesamiento or procesamiento.estado != 'completado':
            return None

        # Contenido realista de sesión municipal
        contenido_sesion = self.generar_contenido_sesion_municipal(acta)
        
        transcripcion = TranscripcionCompleta.objects.create(
            procesamiento_audio=procesamiento,
            acta_municipal=acta,
            texto_completo=contenido_sesion['texto_completo'],
            total_speakers=len(contenido_sesion['speakers']),
            duracion_total=procesamiento.duracion_original,
            estado='completada',
            fecha_inicio=acta.fecha_sesion,
            fecha_completado=acta.fecha_sesion + timedelta(hours=1),
            metadatos_diarizacion={
                'speakers_identificados': contenido_sesion['speakers'],
                'intervalos_silencio': random.randint(15, 35),
                'confianza_promedio': round(random.uniform(0.85, 0.95), 3),
                'modelo_utilizado': 'pyannote-v3',
                'tiempo_procesamiento': random.randint(180, 600)
            },
            metadatos_correccion={
                'errores_corregidos': random.randint(5, 25),
                'palabras_agregadas': random.randint(10, 50),
                'nivel_confianza': round(random.uniform(0.9, 0.98), 3),
                'revisor': 'Sistema Automático IA',
                'fecha_revision': acta.fecha_sesion + timedelta(minutes=30)
            }
        )
        
        # Crear segmentos de transcripción
        self.crear_segmentos_transcripcion(transcripcion, contenido_sesion)
        
        return transcripcion

    def generar_contenido_sesion_municipal(self, acta):
        """Generar contenido realista de sesión municipal"""
        
        speakers = [
            'Alcalde Segundo Flores Meza',
            'Concejal Roosevelt Gómez',
            'Concejal Luis Guevara',
            'Concejal Mónica Meza',
            'Secretaria General',
            'Director de Planificación'
        ]
        
        texto_completo = f"""
SESIÓN {acta.tipo_sesion.nombre.upper()} DEL CONCEJO MUNICIPAL DE PASTAZA
{acta.numero_acta} - {acta.fecha_sesion.strftime('%d de %B de %Y')}

ALCALDE FLORES MEZA: Buenos días, señores concejales y funcionarios municipales. Se declara instalada la sesión {acta.tipo_sesion.nombre.lower()} del Concejo Municipal del Cantón Pastaza, siendo las {acta.fecha_sesion.strftime('%H:%M')} horas del día {acta.fecha_sesion.strftime('%d de %B de %Y')}.

Verificamos el quórum reglamentario con la presencia de los señores concejales y procederemos con el orden del día establecido.

SECRETARIA GENERAL: Señor Alcalde, se registra la asistencia de los concejales presentes y se da lectura al orden del día de la presente sesión.

PUNTO PRINCIPAL: {acta.titulo}

ALCALDE FLORES MEZA: Señores concejales, el tema central de nuestra sesión de hoy es {acta.titulo.lower()}. {acta.descripcion_breve}

Esta iniciativa es fundamental para el desarrollo sostenible de nuestro cantón Pastaza y beneficiará directamente a los ciudadanos de Puyo y las parroquias rurales.

CONCEJAL GÓMEZ ARIAS: Señor Alcalde, considero que esta propuesta merece un análisis detallado. El cantón Pastaza, ubicado en el corazón de la Amazonía ecuatoriana, requiere políticas que respeten nuestro patrimonio natural y cultural.

CONCEJAL GUEVARA PABÓN: Estoy de acuerdo con el colega Gómez. Debemos considerar el impacto en las comunidades indígenas Shuar y Achuar de nuestro territorio, así como en los colonos que han hecho de Pastaza su hogar.

CONCEJAL MEZA BRACHO: Señor Alcalde, me parece importante destacar que cualquier decisión debe estar alineada con los objetivos del Plan de Desarrollo y Ordenamiento Territorial del cantón Pastaza 2020-2025.

DIRECTOR DE PLANIFICACIÓN: Señores concejales, desde el aspecto técnico podemos confirmar que la propuesta cumple con la normativa vigente y está enmarcada en las competencias municipales establecidas en el COOTAD.

ALCALDE FLORES MEZA: Agradezco las intervenciones de los señores concejales. Esta administración municipal mantiene el compromiso de trabajar por el bienestar de todos los pastacenses, promoviendo el desarrollo armónico entre la conservación ambiental y el progreso económico.

CONCEJAL RODRÍGUEZ VILLAVICENCIO: Solicito que se incluya en el proyecto las medidas de mitigación ambiental correspondientes, considerando que Pastaza es una provincia eminentemente ecológica.

CONCEJAL PÉREZ HEREDIA: Apoyo la moción del colega Rodríguez. Además, sugiero que se establezcan mecanismos de participación ciudadana para que la comunidad pueda expresar sus opiniones.

ALCALDE FLORES MEZA: Se toma nota de las observaciones y sugerencias de los señores concejales. Sometemos a votación la propuesta con las modificaciones sugeridas.

SECRETARIA GENERAL: Se procede a la votación nominal.

[VOTACIÓN REGISTRADA]

ALCALDE FLORES MEZA: Con el resultado de la votación, se aprueba la propuesta por mayoría. Se dispone la elaboración del documento final para su promulgación y publicación.

No habiendo más temas que tratar, se da por terminada la sesión siendo las {(acta.fecha_sesion + timedelta(hours=2, minutes=30)).strftime('%H:%M')} horas del mismo día.

Elaborado por: María Elena Vásquez Castro - Secretaria General
Revisado por: Segundo Germán Flores Meza - Alcalde
"""
        
        return {
            'texto_completo': texto_completo.strip(),
            'speakers': speakers
        }

    def crear_segmentos_transcripcion(self, transcripcion, contenido):
        """Crear segmentos individuales de la transcripción"""
        # Dividir el texto en párrafos/segmentos
        parrafos = [p.strip() for p in contenido['texto_completo'].split('\n\n') if p.strip()]
        
        tiempo_actual = 0
        for i, parrafo in enumerate(parrafos[:20]):  # Máximo 20 segmentos
            if not parrafo or len(parrafo) < 10:
                continue
                
            # Estimar duración del segmento (aprox 3 palabras por segundo)
            palabras = len(parrafo.split())
            duracion = max(10, palabras // 3)  # Mínimo 10 segundos
            
            # Identificar speaker
            speaker_identificado = 'SPEAKER_00'
            for j, speaker in enumerate(contenido['speakers']):
                if any(name.upper() in parrafo.upper() for name in speaker.split()):
                    speaker_identificado = f'SPEAKER_{j:02d}'
                    break
            
            SegmentoTranscripcion.objects.create(
                transcripcion=transcripcion,
                numero_segmento=i + 1,
                tiempo_inicio=tiempo_actual,
                tiempo_fin=tiempo_actual + duracion,
                speaker_id=speaker_identificado,
                speaker_label=random.choice(contenido['speakers']),
                texto_original=parrafo,
                texto_corregido=parrafo,  # En demo, asumimos que ya está corregido
                confianza=round(random.uniform(0.85, 0.98), 3),
                editado=False,
                timestamp_edicion=None
            )
            
            tiempo_actual += duracion + random.randint(1, 5)  # Pausa entre segmentos

    def crear_auditorias(self):
        """Crear registros de auditoría para actividades municipales"""
        print("🔍 Creando registros de auditoría...")
        
        usuarios = User.objects.all()
        actividades = [
            'Creación de sesión municipal',
            'Aprobación de acta',
            'Procesamiento de audio completado',
            'Transcripción revisada',
            'Publicación de acta',
            'Consulta de información pública',
            'Modificación de ordenanza',
            'Acceso a portal transparencia'
        ]
        
        auditorias_creadas = 0
        fecha_base = datetime.now() - timedelta(days=90)
        
        for i in range(50):  # 50 registros de auditoría
            fecha_actividad = fecha_base + timedelta(days=random.randint(0, 90))
            
            LogActividad.objects.create(
                usuario=random.choice(usuarios),
                accion=random.choice(actividades),
                modelo_afectado='ActaMunicipal',
                objeto_id=random.randint(1, 12),
                descripcion=f"Actividad municipal registrada desde el sistema de actas",
                ip_address=f"10.0.{random.randint(1,50)}.{random.randint(1,200)}",
                user_agent='Mozilla/5.0 (Sistema Municipal Pastaza)',
                timestamp=fecha_actividad,
                metadata_adicional={
                    'modulo': 'actas_municipales',
                    'canton': 'Pastaza',
                    'ubicacion': 'Puyo'
                }
            )
            auditorias_creadas += 1
            
        print(f"📊 Registros de auditoría creados: {auditorias_creadas}")
        return auditorias_creadas

    def crear_permisos_publicacion(self):
        """Crear permisos de publicación para transparencia"""
        print("🔓 Configurando permisos de publicación...")
        
        actas = ActaMunicipal.objects.filter(estado='publicada')
        permisos_creados = 0
        
        for acta in actas:
            permiso, created = PermisoPublicacion.objects.get_or_create(
                acta=acta,
                defaults={
                    'tipo_acceso': 'publico',
                    'fecha_publicacion': acta.fecha_sesion + timedelta(days=7),
                    'publicado_por': acta.presidida_por,
                    'motivo_publicacion': 'Transparencia y acceso a información pública municipal',
                    'observaciones': 'Publicación automática según LOTAIP'
                }
            )
            if created:
                permisos_creados += 1
                
        print(f"📊 Permisos de publicación creados: {permisos_creados}")
        return permisos_creados

    def ejecutar_poblado_completo(self):
        """Ejecutar todo el proceso de poblado de datos"""
        print("🚀 INICIANDO POBLADO COMPLETO DEL MUNICIPIO DE PASTAZA")
        print("=" * 60)
        
        resultados = {}
        
        try:
            resultados['usuarios'] = self.crear_usuarios()
            resultados['tipos_reunion'] = self.crear_tipos_reunion()
            resultados['sesiones'] = self.crear_sesiones_municipales()
            resultados['auditorias'] = self.crear_auditorias()
            resultados['permisos'] = self.crear_permisos_publicacion()
            
            print("\n" + "=" * 60)
            print("✅ POBLADO COMPLETADO EXITOSAMENTE")
            print("=" * 60)
            print(f"👥 Usuarios creados: {resultados['usuarios']}")
            print(f"📋 Tipos de reunión: {resultados['tipos_reunion']}")
            print(f"🏛️ Sesiones municipales: {resultados['sesiones']}")
            print(f"🔍 Registros de auditoría: {resultados['auditorias']}")
            print(f"🔓 Permisos de publicación: {resultados['permisos']}")
            print("\n🎉 El sistema está listo con datos realistas del Municipio de Pastaza!")
            print("🌐 Sitio web: https://puyo.gob.ec/")
            print("📱 Facebook: https://www.facebook.com/GADMPastaza")
            
        except Exception as e:
            print(f"❌ Error durante el poblado: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return resultados


if __name__ == '__main__':
    poblador = PobladorMunicipioPastaza()
    resultados = poblador.ejecutar_poblado_completo()