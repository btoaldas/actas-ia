#!/usr/bin/env python
"""
Poblador corregido de datos realistas para el Municipio de Pastaza
Compatible con los campos reales de los modelos
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
from apps.auditoria.models import SistemaLogs


class PobladorMunicipioPastazaCorregido:
    """Poblador corregido de datos del Municipio de Pastaza"""
    
    def __init__(self):
        self.autoridades_municipales = {
            'alcalde': {
                'nombres': 'Segundo Germán',
                'apellidos': 'Flores Meza',
                'cargo': 'Alcalde',
                'email': 'alcalde@puyo.gob.ec'
            },
            'secretario_consejo': {
                'nombres': 'Danilo',
                'apellidos': 'Andrade',
                'cargo': 'Secretario de Consejo',
                'email': 'secretario.consejo@puyo.gob.ec'
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
                }
            ]
        }
        
        self.temas_sesiones = [
            'Ordenanza de Regulación del Comercio Ambulante en el Centro de Puyo',
            'Aprobación del Presupuesto Municipal 2025 - Segundo Semestre',
            'Creación del Parque Ecológico Río Pastaza',
            'Declaratoria de Emergencia Vial en el Sector Shell',
            'Reglamento de Turismo Comunitario Indígena',
            'Plan de Gestión de Residuos Sólidos Cantonal',
            'Aprobación de Convenio con Universidad Estatal Amazónica',
            'Regulación de Actividades Mineras en Territorio Cantonal',
            'Fortalecimiento del Sistema de Agua Potable Rural',
            'Creación de la Casa de la Cultura Amazónica',
            'Plan de Contingencia para Temporada Lluviosa 2025',
            'Reglamento de Construcciones Sostenibles'
        ]

    def crear_usuarios(self):
        """Crear usuarios para autoridades municipales"""
        print("🏛️ Creando usuarios de autoridades municipales...")
        
        usuarios_creados = []
        
        # Crear usuario para el Alcalde
        try:
            alcalde_user, created = User.objects.get_or_create(
                username='sflores',
                defaults={
                    'email': self.autoridades_municipales['alcalde']['email'],
                    'first_name': self.autoridades_municipales['alcalde']['nombres'],
                    'last_name': self.autoridades_municipales['alcalde']['apellidos'],
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                alcalde_user.set_password('Alcalde2025!')
                alcalde_user.save()
                usuarios_creados.append(f"✅ Alcalde: {alcalde_user.get_full_name()}")
            else:
                print(f"ℹ️ Usuario alcalde ya existe: {alcalde_user.get_full_name()}")
        except Exception as e:
            print(f"❌ Error creando alcalde: {str(e)[:50]}")

        # Crear usuario para el Secretario de Consejo  
        try:
            secretario_user, created = User.objects.get_or_create(
                username='dandrade',
                defaults={
                    'email': self.autoridades_municipales['secretario_consejo']['email'],
                    'first_name': self.autoridades_municipales['secretario_consejo']['nombres'],
                    'last_name': self.autoridades_municipales['secretario_consejo']['apellidos'],
                    'is_staff': True,
                    'is_active': True
                }
            )
            if created:
                secretario_user.set_password('Secretario2025!')
                secretario_user.save()
                usuarios_creados.append(f"✅ Secretario de Consejo: {secretario_user.get_full_name()}")
            else:
                print(f"ℹ️ Usuario secretario ya existe: {secretario_user.get_full_name()}")
        except Exception as e:
            print(f"❌ Error creando secretario: {str(e)[:50]}")

        # Crear usuarios para concejales
        for i, concejal in enumerate(self.autoridades_municipales['concejales']):
            try:
                username = f"concejal{i+1}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': concejal['email'],
                        'first_name': concejal['nombres'],
                        'last_name': concejal['apellidos'],
                        'is_active': True
                    }
                )
                if created:
                    user.set_password('Concejal2025!')
                    user.save()
                    usuarios_creados.append(f"✅ Concejal: {user.get_full_name()}")
            except Exception as e:
                print(f"❌ Error creando concejal {i+1}: {str(e)[:50]}")

        # Crear usuarios para funcionarios
        for i, funcionario in enumerate(self.autoridades_municipales['funcionarios']):
            try:
                username = f"funcionario{i+1}"
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': funcionario['email'],
                        'first_name': funcionario['nombres'],
                        'last_name': funcionario['apellidos'],
                        'is_staff': True,
                        'is_active': True
                    }
                )
                if created:
                    user.set_password('Funcionario2025!')
                    user.save()
                    usuarios_creados.append(f"✅ Funcionario: {user.get_full_name()}")
            except Exception as e:
                print(f"❌ Error creando funcionario {i+1}: {str(e)[:50]}")

        print(f"📊 Total usuarios nuevos creados: {len(usuarios_creados)}")
        for usuario in usuarios_creados[:5]:
            print(f"  {usuario}")
        
        return len(usuarios_creados)

    def crear_tipos_reunion(self):
        """Crear tipos de reunión con campos correctos"""
        print("📋 Creando tipos de reunión...")
        
        tipos_reunion = [
            {
                'nombre': 'Sesión Ordinaria',
                'descripcion': 'Sesión ordinaria del Concejo Municipal de Pastaza',
                'activo': True
            },
            {
                'nombre': 'Sesión Extraordinaria',
                'descripcion': 'Sesión extraordinaria por temas urgentes del cantón',
                'activo': True
            },
            {
                'nombre': 'Comisión Permanente',
                'descripcion': 'Reunión de comisión permanente especializada',
                'activo': True
            }
        ]
        
        tipos_creados = 0
        for tipo_data in tipos_reunion:
            try:
                tipo, created = TipoReunion.objects.get_or_create(
                    nombre=tipo_data['nombre'],
                    defaults=tipo_data
                )
                if created:
                    tipos_creados += 1
                    print(f"  ✅ {tipo.nombre}")
            except Exception as e:
                print(f"❌ Error creando tipo {tipo_data['nombre']}: {str(e)[:50]}")
        
        print(f"📊 Tipos de reunión creados: {tipos_creados}")
        return tipos_creados

    def crear_tipos_sesion(self):
        """Crear tipos de sesión con campos correctos"""
        print("📋 Creando tipos de sesión...")
        
        tipos_sesion = [
            {
                'nombre': 'Ordinaria',
                'descripcion': 'Sesión ordinaria mensual del Concejo Municipal',
                'color': '#007bff',
                'icono': 'fas fa-calendar-alt',
                'activo': True
            },
            {
                'nombre': 'Extraordinaria',
                'descripcion': 'Sesión extraordinaria por temas urgentes',
                'color': '#dc3545',
                'icono': 'fas fa-exclamation-triangle',
                'activo': True
            },
            {
                'nombre': 'Comisión',
                'descripcion': 'Reunión de comisión especializada',
                'color': '#6c757d',
                'icono': 'fas fa-users',
                'activo': True
            }
        ]
        
        tipos_creados = 0
        for tipo_data in tipos_sesion:
            try:
                tipo, created = TipoSesion.objects.get_or_create(
                    nombre=tipo_data['nombre'],
                    defaults=tipo_data
                )
                if created:
                    tipos_creados += 1
                    print(f"  ✅ {tipo.nombre}")
            except Exception as e:
                print(f"❌ Error creando tipo sesión {tipo_data['nombre']}: {str(e)[:50]}")
        
        print(f"📊 Tipos de sesión creados: {tipos_creados}")
        return tipos_creados

    def crear_estados_acta(self):
        """Crear estados de acta con campos correctos"""
        print("📋 Creando estados de acta...")
        
        estados = [
            {
                'nombre': 'Borrador',
                'descripcion': 'Acta en proceso de elaboración',
                'color': '#ffc107',
                'orden': 1,
                'activo': True
            },
            {
                'nombre': 'Revisión',
                'descripcion': 'Acta en proceso de revisión',
                'color': '#17a2b8',
                'orden': 2,
                'activo': True
            },
            {
                'nombre': 'Aprobada',
                'descripcion': 'Acta aprobada por el Concejo',
                'color': '#28a745',
                'orden': 3,
                'activo': True
            },
            {
                'nombre': 'Publicada',
                'descripcion': 'Acta publicada para acceso ciudadano',
                'color': '#007bff',
                'orden': 4,
                'activo': True
            }
        ]
        
        estados_creados = 0
        for estado_data in estados:
            try:
                estado, created = EstadoActa.objects.get_or_create(
                    nombre=estado_data['nombre'],
                    defaults=estado_data
                )
                if created:
                    estados_creados += 1
                    print(f"  ✅ {estado.nombre}")
            except Exception as e:
                print(f"❌ Error creando estado {estado_data['nombre']}: {str(e)[:50]}")
        
        print(f"📊 Estados de acta creados: {estados_creados}")
        return estados_creados

    def crear_actas_municipales(self):
        """Crear actas municipales realistas"""
        print("🏛️ Creando actas municipales del Concejo de Pastaza...")
        
        # Obtener objetos necesarios
        try:
            alcalde = User.objects.filter(username='sflores').first()
            secretario_consejo = User.objects.filter(username='dandrade').first()
            tipo_ordinaria = TipoSesion.objects.filter(nombre='Ordinaria').first()
            tipo_extraordinaria = TipoSesion.objects.filter(nombre='Extraordinaria').first()
            estado_publicada = EstadoActa.objects.filter(nombre='Publicada').first()
            estado_borrador = EstadoActa.objects.filter(nombre='Borrador').first()
            
            # Si no existe el secretario de consejo, usar el alcalde
            if not secretario_consejo:
                secretario_consejo = alcalde
            
            if not tipo_ordinaria or not estado_publicada or not alcalde:
                print("❌ Error: No se encontraron tipos de sesión, estados o usuarios")
                return 0
        except Exception as e:
            print(f"❌ Error obteniendo objetos necesarios: {str(e)}")
            return 0

        actas_creadas = 0
        fecha_base = datetime.now() - timedelta(days=180)
        
        for i, tema in enumerate(self.temas_sesiones):
            try:
                # Calcular fecha de sesión
                fecha_sesion = fecha_base + timedelta(days=i*15 + random.randint(-3, 3))
                
                # Determinar tipo y estado
                tipo_sesion = tipo_extraordinaria if 'Emergencia' in tema or 'Urgente' in tema else tipo_ordinaria
                estado = estado_publicada if random.choice([True, True, True, False]) else estado_borrador
                
                # Crear acta municipal con campos correctos
                acta = ActaMunicipal.objects.create(
                    numero_acta=f"ACTA-{2025}-{str(i+1).zfill(3)}",
                    numero_sesion=i+1,
                    titulo=tema,
                    fecha_sesion=fecha_sesion,
                    tipo_sesion=tipo_sesion,
                    estado=estado,
                    resumen=f"Sesión del Concejo Municipal de Pastaza sobre {tema.lower()}.",
                    contenido=self.generar_contenido_acta(tema, fecha_sesion),
                    orden_del_dia=f"1. Verificación del quórum\n2. {tema}\n3. Varios",
                    acuerdos=f"Se aprobó la propuesta relacionada con {tema.lower()}",
                    acceso='publico',
                    secretario=secretario_consejo,
                    presidente=alcalde,
                    asistentes='Alcalde Segundo Germán Flores Meza, Concejales presentes, Secretario de Consejo Danilo Andrade',
                    ausentes='Ninguno',
                    transcripcion_ia=True,
                    precision_ia=round(random.uniform(85.0, 95.0), 2),
                    tiempo_procesamiento=timedelta(seconds=random.randint(120, 300)),
                    palabras_clave=f"municipio, pastaza, {tema.split()[0].lower()}, concejo",
                    observaciones="Sesión desarrollada con normalidad según reglamento interno",
                    activo=True
                )
                
                # Crear procesamiento de audio asociado
                self.crear_procesamiento_audio_simple(acta)
                
                actas_creadas += 1
                print(f"  ✅ {acta.numero_acta}: {acta.titulo[:50]}...")
                
            except Exception as e:
                print(f"❌ Error creando acta {i+1}: {str(e)[:100]}")
                continue

        print(f"📊 Actas municipales creadas: {actas_creadas}")
        return actas_creadas

    def generar_contenido_acta(self, tema, fecha_sesion):
        """Generar contenido realista del acta"""
        return f"""
ACTA DE SESIÓN DEL CONCEJO MUNICIPAL DEL CANTÓN PASTAZA

En la ciudad de Puyo, capital del cantón Pastaza, el {fecha_sesion.strftime('%d de %B de %Y')}, siendo las {fecha_sesion.strftime('%H:%M')} horas, se instaló la sesión del Concejo Municipal bajo la presidencia del señor Alcalde Segundo Germán Flores Meza.

TEMA PRINCIPAL: {tema}

DESARROLLO:
El señor Alcalde expone el tema principal relacionado con {tema.lower()}, destacando su importancia para el desarrollo sostenible del cantón Pastaza y el bienestar de los ciudadanos de Puyo y las parroquias rurales.

Los señores concejales participaron activamente en el debate, considerando especialmente el impacto en las comunidades indígenas Shuar y Achuar del territorio, así como en los colonos que habitan la región amazónica.

Se analizó la propuesta en el marco de las competencias municipales establecidas en el COOTAD y su alineación con el Plan de Desarrollo y Ordenamiento Territorial del cantón Pastaza.

RESOLUCIÓN:
Después del análisis correspondiente, el Concejo Municipal adoptó las decisiones necesarias, priorizando el desarrollo armónico entre la conservación del patrimonio natural amazónico y el progreso económico de la población.

La presente acta se elabora en cumplimiento de las disposiciones legales vigentes y del reglamento interno del Concejo Municipal del Cantón Pastaza.

Elaborada por: Danilo Andrade - Secretario de Consejo
Revisada por: Segundo Germán Flores Meza - Alcalde del Cantón Pastaza
"""

    def crear_procesamiento_audio_simple(self, acta):
        """Crear procesamiento de audio simple para el acta"""
        try:
            tipo_reunion = TipoReunion.objects.first()
            if not tipo_reunion:
                return None
                
            estados_posibles = ['completado', 'procesando', 'pendiente']
            estado = random.choices(estados_posibles, weights=[70, 15, 15])[0]
            
            procesamiento = ProcesamientoAudio.objects.create(
                tipo_reunion=tipo_reunion,
                titulo=f"Audio - {acta.titulo}",
                descripcion=f"Grabación de la sesión municipal {acta.numero_acta}",
                estado=estado,
                fecha_inicio=acta.fecha_sesion,
                fecha_completado=acta.fecha_sesion + timedelta(hours=2) if estado == 'completado' else None,
                duracion_original=random.randint(7200, 14400),
                participantes_detallados=[
                    {
                        'nombre': 'Segundo Germán Flores Meza',
                        'cargo': 'Alcalde',
                        'participacion': 'Alta'
                    },
                    {
                        'nombre': 'Danilo Andrade',
                        'cargo': 'Secretario de Consejo',
                        'participacion': 'Media'
                    }
                ],
                metadatos_originales={
                    'formato': 'mp3',
                    'duracion': random.randint(7200, 14400),
                    'ubicacion_grabacion': 'Salón de Sesiones'
                },
                metadatos_procesamiento={
                    'snr_promedio': round(random.uniform(15.0, 25.0), 2),
                    'modelo_transcripcion': 'whisper-large-v3'
                } if estado == 'completado' else {},
                confidencial=False
            )
            
            return procesamiento
            
        except Exception as e:
            print(f"❌ Error creando procesamiento audio: {str(e)[:100]}")
            return None

    def crear_logs_auditoria(self):
        """Crear logs de auditoría con campos correctos"""
        print("🔍 Creando registros de auditoría...")
        
        categorias = ['actas', 'audio', 'transcripcion', 'sistema']
        subcategorias = ['creacion', 'edicion', 'consulta', 'publicacion']
        
        logs_creados = 0
        for i in range(25):
            try:
                SistemaLogs.objects.create(
                    timestamp=timezone.now() - timedelta(days=random.randint(1, 30)),
                    nivel='INFO',
                    categoria=random.choice(categorias),
                    subcategoria=random.choice(subcategorias),
                    usuario_id=1,
                    session_id=f'session_{random.randint(1000, 9999)}',
                    ip_address=f"10.0.1.{random.randint(1, 100)}",
                    user_agent='Mozilla/5.0 (Sistema Municipal Pastaza)',
                    mensaje=f"Actividad municipal registrada en el sistema #{i+1}",
                    datos_extra={'municipio': 'Pastaza', 'ubicacion': 'Puyo'},
                    modulo='actas_municipales',
                    url_solicitada=f'/actas/{random.randint(1, 12)}/',
                    metodo_http='GET',
                    tiempo_respuesta_ms=random.randint(100, 500),
                    codigo_respuesta=200
                )
                logs_creados += 1
                if i < 5:  # Mostrar solo los primeros 5
                    print(f"  ✅ Log {i+1}: Actividad municipal registrada")
            except Exception as e:
                print(f"❌ Error creando log {i+1}: {str(e)[:50]}")
                continue
                
        print(f"📊 Logs de auditoría creados: {logs_creados}")
        return logs_creados

    def ejecutar_poblado_completo(self):
        """Ejecutar todo el proceso de poblado de datos"""
        print("🚀 INICIANDO POBLADO COMPLETO DEL MUNICIPIO DE PASTAZA")
        print("🌍 GAD Municipal del Cantón Pastaza - Puyo, Ecuador")
        print("=" * 65)
        
        resultados = {}
        
        try:
            resultados['usuarios'] = self.crear_usuarios()
            resultados['tipos_reunion'] = self.crear_tipos_reunion()
            resultados['tipos_sesion'] = self.crear_tipos_sesion()
            resultados['estados_acta'] = self.crear_estados_acta()
            resultados['actas'] = self.crear_actas_municipales()
            resultados['logs'] = self.crear_logs_auditoria()
            
            print("\n" + "=" * 65)
            print("✅ POBLADO COMPLETADO EXITOSAMENTE")
            print("=" * 65)
            print(f"👥 Usuarios nuevos creados: {resultados['usuarios']}")
            print(f"📋 Tipos de reunión: {resultados['tipos_reunion']}")
            print(f"📋 Tipos de sesión: {resultados['tipos_sesion']}")
            print(f"📊 Estados de acta: {resultados['estados_acta']}")
            print(f"🏛️ Actas municipales: {resultados['actas']}")
            print(f"🔍 Logs de auditoría: {resultados['logs']}")
            print("\n🎉 EL SISTEMA ESTÁ LISTO CON DATOS REALISTAS!")
            print("🏛️ Municipio: GAD Municipal del Cantón Pastaza")
            print("🌐 Sitio web: https://puyo.gob.ec/")
            print("📱 Facebook: https://www.facebook.com/GADMPastaza")
            print("🌳 Región: Amazónica Ecuatoriana")
            
        except Exception as e:
            print(f"❌ Error durante el poblado: {str(e)}")
            import traceback
            traceback.print_exc()
            
        return resultados


if __name__ == '__main__':
    poblador = PobladorMunicipioPastazaCorregido()
    resultados = poblador.ejecutar_poblado_completo()