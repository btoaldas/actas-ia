#!/usr/bin/env python
"""
Script de validación para el módulo de segmentos de plantilla
Prueba todas las funcionalidades implementadas
"""
import os
import sys
import django
import requests
import json
from datetime import datetime

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.generador_actas.models import SegmentoPlantilla, ProveedorIA
from apps.generador_actas.forms import SegmentoPlantillaForm, PruebaSegmentoForm

User = get_user_model()

class ValidadorSegmentos:
    def __init__(self):
        self.errores = []
        self.exitos = []
        self.base_url = "http://localhost:8000"
        
    def log_exito(self, mensaje):
        self.exitos.append(f"✅ {mensaje}")
        print(f"✅ {mensaje}")
        
    def log_error(self, mensaje):
        self.errores.append(f"❌ {mensaje}")
        print(f"❌ {mensaje}")
        
    def test_modelo_segmento(self):
        """Probar funcionalidades del modelo SegmentoPlantilla"""
        print("\n🧪 Probando modelo SegmentoPlantilla...")
        
        try:
            # Crear usuario de prueba si no existe
            user, created = User.objects.get_or_create(
                username='test_segmentos',
                defaults={'email': 'test@example.com'}
            )
            
            # Crear proveedor IA de prueba
            proveedor, created = ProveedorIA.objects.get_or_create(
                nombre='OpenAI Test',
                defaults={
                    'tipo': 'openai',
                    'activo': True,
                    'configuracion': {'model': 'gpt-3.5-turbo'},
                    'usuario_creacion': user
                }
            )
            
            # Crear segmento estático
            segmento_estatico = SegmentoPlantilla.objects.create(
                codigo='TEST_ESTATICO_001',
                nombre='Encabezado de Prueba',
                descripcion='Segmento estático para pruebas',
                categoria='encabezado',
                tipo='estatico',
                variables_personalizadas={
                    'municipio': 'Pastaza',
                    'fecha_default': '2025-01-15'
                },
                usuario_creacion=user
            )
            
            # Crear segmento dinámico
            segmento_dinamico = SegmentoPlantilla.objects.create(
                codigo='TEST_DINAMICO_001',
                nombre='Desarrollo con IA',
                descripcion='Segmento dinámico para pruebas',
                categoria='desarrollo',
                tipo='dinamico',
                prompt_ia='Genera un resumen de los temas tratados en la reunión: {temas_tratados}',
                proveedor_ia=proveedor,
                estructura_json={
                    'resumen': 'string',
                    'puntos_clave': ['array']
                },
                variables_personalizadas={
                    'max_palabras': 200,
                    'incluir_decisiones': True
                },
                usuario_creacion=user
            )
            
            # Probar propiedades del modelo
            assert segmento_estatico.es_dinamico == False
            assert segmento_dinamico.es_dinamico == True
            assert segmento_dinamico.tiene_prompt == True
            assert segmento_dinamico.esta_configurado == True
            
            # Probar variables disponibles
            variables = segmento_estatico.variables_disponibles
            assert 'fecha_actual' in variables
            assert 'participantes' in variables
            assert 'municipio' in variables
            
            # Probar JSON completo para IA
            datos_contexto = {
                'temas_tratados': ['Presupuesto 2025', 'Obras públicas'],
                'participantes': ['Juan Pérez', 'María García']
            }
            json_completo = segmento_dinamico.generar_json_completo(datos_contexto)
            assert 'segmento_info' in json_completo
            assert 'prompt' in json_completo
            assert 'datos_contexto' in json_completo
            
            # Probar actualización de métricas
            segmento_dinamico.actualizar_metricas_uso(
                tiempo_procesamiento=2.5,
                resultado_prueba='Prueba exitosa'
            )
            assert segmento_dinamico.total_usos == 1
            assert segmento_dinamico.tiempo_promedio_procesamiento == 2.5
            
            self.log_exito("Modelo SegmentoPlantilla funciona correctamente")
            
        except Exception as e:
            self.log_error(f"Error en modelo SegmentoPlantilla: {str(e)}")
    
    def test_formularios(self):
        """Probar formularios de segmentos"""
        print("\n📝 Probando formularios...")
        
        try:
            # Probar formulario de creación
            form_data = {
                'codigo': 'TEST_FORM_001',
                'nombre': 'Segmento de Formulario',
                'descripcion': 'Prueba de formulario',
                'categoria': 'otros',
                'tipo': 'estatico',
                'orden_defecto': 10,
                'reutilizable': True,
                'obligatorio': False,
                'activo': True,
                'variables_personalizadas': '{"test": "value"}',
                'estructura_json': '{"campo": "valor"}',
                'componentes': '{"texto": "contenido"}',
                'parametros_entrada': '["param1", "param2"]'
            }
            
            form = SegmentoPlantillaForm(data=form_data)
            if not form.is_valid():
                raise Exception(f"Errores en formulario: {form.errors}")
            
            # Probar formulario con tipo dinámico
            user = User.objects.first()
            proveedor = ProveedorIA.objects.filter(activo=True).first()
            if proveedor:
                form_data_dinamico = form_data.copy()
                form_data_dinamico.update({
                    'codigo': 'TEST_FORM_002',
                    'tipo': 'dinamico',
                    'prompt_ia': 'Procesa este contenido: {contenido}',
                    'proveedor_ia': proveedor.pk
                })
                
                form_dinamico = SegmentoPlantillaForm(data=form_data_dinamico)
                if not form_dinamico.is_valid():
                    raise Exception(f"Errores en formulario dinámico: {form_dinamico.errors}")
            
            # Probar formulario de prueba
            if SegmentoPlantilla.objects.exists():
                segmento = SegmentoPlantilla.objects.first()
                prueba_data = {
                    'segmento': segmento.pk,
                    'datos_contexto': '{"test": "data"}',
                    'usar_celery': False,
                    'incluir_metricas': True
                }
                
                prueba_form = PruebaSegmentoForm(data=prueba_data)
                if not prueba_form.is_valid():
                    raise Exception(f"Errores en formulario de prueba: {prueba_form.errors}")
            
            self.log_exito("Formularios funcionan correctamente")
            
        except Exception as e:
            self.log_error(f"Error en formularios: {str(e)}")
    
    def test_urls_dashboard(self):
        """Probar URLs del dashboard y navegación"""
        print("\n🌐 Probando URLs y navegación...")
        
        try:
            # URLs principales que deben estar disponibles
            urls_importantes = [
                '/admin/',  # Django admin
                '/generador_actas/',  # Dashboard principal
                '/generador_actas/segmentos/',  # Dashboard segmentos
                '/generador_actas/segmentos/lista/',  # Lista segmentos
                '/generador_actas/segmentos/crear/',  # Crear segmento
                '/generador_actas/segmentos/probar/',  # Probar segmentos
            ]
            
            for url in urls_importantes:
                try:
                    response = requests.get(f"{self.base_url}{url}", timeout=10)
                    if response.status_code in [200, 302]:  # 302 para redirects de login
                        self.log_exito(f"URL accesible: {url}")
                    else:
                        self.log_error(f"URL no accesible: {url} (Status: {response.status_code})")
                except requests.exceptions.RequestException as e:
                    self.log_error(f"Error conectando a {url}: {str(e)}")
            
        except Exception as e:
            self.log_error(f"Error probando URLs: {str(e)}")
    
    def test_variables_comunes(self):
        """Probar sistema de variables comunes"""
        print("\n🔧 Probando sistema de variables...")
        
        try:
            variables_comunes = SegmentoPlantilla.obtener_variables_comunes()
            
            # Verificar que existen las variables esperadas
            variables_esperadas = [
                'fecha', 'participantes', 'lugar', 'hora_inicio', 
                'numero_acta', 'tipo_reunion', 'decisiones'
            ]
            
            for var in variables_esperadas:
                if var not in variables_comunes:
                    raise Exception(f"Variable común faltante: {var}")
                
                var_info = variables_comunes[var]
                if 'tipo' not in var_info or 'descripcion' not in var_info:
                    raise Exception(f"Info incompleta para variable: {var}")
            
            self.log_exito("Sistema de variables comunes funciona correctamente")
            
        except Exception as e:
            self.log_error(f"Error en variables comunes: {str(e)}")
    
    def test_admin_interface(self):
        """Probar interfaz de Django admin"""
        print("\n👑 Probando interfaz de admin...")
        
        try:
            from django.contrib import admin
            from apps.generador_actas.admin import SegmentoPlantillaAdmin
            
            # Verificar que el admin está registrado
            if SegmentoPlantilla not in admin.site._registry:
                raise Exception("SegmentoPlantilla no está registrado en admin")
            
            admin_class = admin.site._registry[SegmentoPlantilla]
            
            # Verificar configuración del admin
            required_attrs = [
                'list_display', 'list_filter', 'search_fields',
                'readonly_fields', 'fieldsets', 'actions'
            ]
            
            for attr in required_attrs:
                if not hasattr(admin_class, attr):
                    raise Exception(f"Admin falta atributo: {attr}")
            
            # Verificar acciones personalizadas
            expected_actions = [
                'marcar_activo', 'marcar_inactivo', 
                'resetear_metricas', 'probar_segmento'
            ]
            
            for action in expected_actions:
                if not hasattr(admin_class, action):
                    raise Exception(f"Admin falta acción: {action}")
            
            self.log_exito("Interfaz de admin configurada correctamente")
            
        except Exception as e:
            self.log_error(f"Error en admin interface: {str(e)}")
    
    def test_integridad_datos(self):
        """Probar integridad y consistencia de datos"""
        print("\n🔍 Probando integridad de datos...")
        
        try:
            # Verificar que no hay segmentos dinámicos sin proveedor IA
            segmentos_problematicos = SegmentoPlantilla.objects.filter(
                tipo__in=['dinamico', 'hibrido'],
                proveedor_ia__isnull=True
            )
            
            if segmentos_problematicos.exists():
                self.log_error(f"Encontrados {segmentos_problematicos.count()} segmentos dinámicos sin proveedor IA")
            else:
                self.log_exito("No hay segmentos dinámicos sin proveedor IA")
            
            # Verificar códigos únicos
            codigos_duplicados = SegmentoPlantilla.objects.values('codigo').annotate(
                count=django.db.models.Count('codigo')
            ).filter(count__gt=1)
            
            if codigos_duplicados.exists():
                self.log_error(f"Encontrados códigos duplicados: {list(codigos_duplicados)}")
            else:
                self.log_exito("Todos los códigos de segmentos son únicos")
            
            # Verificar JSON válido en campos JSON
            for segmento in SegmentoPlantilla.objects.all():
                try:
                    if segmento.variables_personalizadas:
                        json.loads(json.dumps(segmento.variables_personalizadas))
                    if segmento.estructura_json:
                        json.loads(json.dumps(segmento.estructura_json))
                    if segmento.componentes:
                        json.loads(json.dumps(segmento.componentes))
                except Exception as e:
                    self.log_error(f"JSON inválido en segmento {segmento.codigo}: {str(e)}")
                    return
            
            self.log_exito("Todos los campos JSON son válidos")
            
        except Exception as e:
            self.log_error(f"Error verificando integridad: {str(e)}")
    
    def generar_reporte(self):
        """Generar reporte final de la validación"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE VALIDACIÓN")
        print("="*60)
        
        print(f"\n✅ ÉXITOS ({len(self.exitos)}):")
        for exito in self.exitos:
            print(f"  {exito}")
        
        if self.errores:
            print(f"\n❌ ERRORES ({len(self.errores)}):")
            for error in self.errores:
                print(f"  {error}")
        
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"  - Total segmentos: {SegmentoPlantilla.objects.count()}")
        print(f"  - Segmentos activos: {SegmentoPlantilla.objects.filter(activo=True).count()}")
        print(f"  - Segmentos dinámicos: {SegmentoPlantilla.objects.filter(tipo='dinamico').count()}")
        print(f"  - Segmentos estáticos: {SegmentoPlantilla.objects.filter(tipo='estatico').count()}")
        print(f"  - Proveedores IA: {ProveedorIA.objects.filter(activo=True).count()}")
        
        total_pruebas = len(self.exitos) + len(self.errores)
        porcentaje_exito = (len(self.exitos) / total_pruebas * 100) if total_pruebas > 0 else 0
        
        print(f"\n🎯 RESULTADO GENERAL:")
        print(f"  - Porcentaje de éxito: {porcentaje_exito:.1f}%")
        
        if porcentaje_exito >= 90:
            print("  - Estado: ✅ EXCELENTE")
        elif porcentaje_exito >= 70:
            print("  - Estado: ⚠️ BUENO (algunos problemas menores)")
        else:
            print("  - Estado: ❌ REQUIERE ATENCIÓN")
        
        return len(self.errores) == 0
    
    def ejecutar_validacion_completa(self):
        """Ejecutar todas las pruebas"""
        print("🚀 Iniciando validación completa del módulo de segmentos...")
        print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Ejecutar todas las pruebas
        self.test_modelo_segmento()
        self.test_formularios()
        self.test_urls_dashboard()
        self.test_variables_comunes()
        self.test_admin_interface()
        self.test_integridad_datos()
        
        # Generar reporte
        return self.generar_reporte()

if __name__ == "__main__":
    validador = ValidadorSegmentos()
    exito = validador.ejecutar_validacion_completa()
    
    # Código de salida para scripts automatizados
    sys.exit(0 if exito else 1)