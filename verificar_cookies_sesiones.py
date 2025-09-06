#!/usr/bin/env python3
"""
Script de Verificación - Sistema de Cookies y Sesiones
Sistema de Actas Municipales

Este script verifica que todos los componentes del sistema de cookies
y sesiones están funcionando correctamente.
"""

import os
import sys
import django
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

class CookieSessionVerifier:
    def __init__(self):
        self.client = Client()
        self.errors = []
        self.warnings = []
        self.success = []
        
    def log_result(self, test_name, status, message):
        """Registra el resultado de una prueba"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "SUCCESS":
            self.success.append(f"✅ [{timestamp}] {test_name}: {message}")
            print(f"✅ {test_name}: {message}")
        elif status == "WARNING":
            self.warnings.append(f"⚠️ [{timestamp}] {test_name}: {message}")
            print(f"⚠️ {test_name}: {message}")
        else:
            self.errors.append(f"❌ [{timestamp}] {test_name}: {message}")
            print(f"❌ {test_name}: {message}")
    
    def verify_django_settings(self):
        """Verifica la configuración de Django"""
        print("\n🔧 VERIFICANDO CONFIGURACIÓN DE DJANGO...")
        
        # Verificar configuración de sesiones
        try:
            assert hasattr(settings, 'SESSION_ENGINE'), "SESSION_ENGINE no configurado"
            assert settings.SESSION_COOKIE_NAME == 'actas_sessionid', f"SESSION_COOKIE_NAME incorrecto: {settings.SESSION_COOKIE_NAME}"
            assert settings.SESSION_COOKIE_AGE == 7200, f"SESSION_COOKIE_AGE incorrecto: {settings.SESSION_COOKIE_AGE}"
            assert settings.SESSION_SAVE_EVERY_REQUEST == True, "SESSION_SAVE_EVERY_REQUEST debe ser True"
            self.log_result("Configuración de Sesiones", "SUCCESS", "Todas las configuraciones son correctas")
        except AssertionError as e:
            self.log_result("Configuración de Sesiones", "ERROR", str(e))
        
        # Verificar configuración CSRF
        try:
            assert settings.CSRF_COOKIE_NAME == 'actas_csrftoken', f"CSRF_COOKIE_NAME incorrecto: {settings.CSRF_COOKIE_NAME}"
            assert settings.CSRF_USE_SESSIONS == True, "CSRF_USE_SESSIONS debe ser True"
            self.log_result("Configuración CSRF", "SUCCESS", "Configuración CSRF correcta")
        except AssertionError as e:
            self.log_result("Configuración CSRF", "ERROR", str(e))
        
        # Verificar middleware
        try:
            middleware_list = settings.MIDDLEWARE
            assert 'apps.auditoria.session_middleware.AdvancedSessionMiddleware' in middleware_list, "Middleware personalizado no encontrado"
            self.log_result("Middleware Personalizado", "SUCCESS", "AdvancedSessionMiddleware está configurado")
        except AssertionError as e:
            self.log_result("Middleware Personalizado", "ERROR", str(e))
    
    def verify_database_structure(self):
        """Verifica la estructura de la base de datos"""
        print("\n🗄️ VERIFICANDO BASE DE DATOS...")
        
        try:
            # Verificar tabla de sesiones
            session_count = Session.objects.count()
            self.log_result("Tabla de Sesiones", "SUCCESS", f"Tabla django_session accesible ({session_count} sesiones)")
            
            # Verificar sesiones activas
            active_sessions = Session.objects.filter(expire_date__gt=datetime.now())
            self.log_result("Sesiones Activas", "SUCCESS", f"{active_sessions.count()} sesiones activas encontradas")
            
        except Exception as e:
            self.log_result("Base de Datos", "ERROR", f"Error accediendo a la base de datos: {e}")
    
    def verify_templates(self):
        """Verifica que los templates existen"""
        print("\n📄 VERIFICANDO TEMPLATES...")
        
        templates_to_check = [
            'templates/auditoria/widgets/cookie_notification.html',
            'templates/auditoria/widgets/session_debug_widget.html',
            'templates/layouts/base.html',
            'templates/accounts/login.html'
        ]
        
        for template_path in templates_to_check:
            full_path = Path(template_path)
            if full_path.exists():
                self.log_result(f"Template {template_path}", "SUCCESS", "Archivo encontrado")
            else:
                self.log_result(f"Template {template_path}", "ERROR", "Archivo no encontrado")
    
    def verify_urls(self):
        """Verifica que las URLs están configuradas"""
        print("\n🌐 VERIFICANDO URLs...")
        
        urls_to_check = [
            'auditoria:session_debug_api',
            'auditoria:clear_session_data',
            'auditoria:log_frontend_activity'
        ]
        
        for url_name in urls_to_check:
            try:
                url = reverse(url_name)
                self.log_result(f"URL {url_name}", "SUCCESS", f"URL encontrada: {url}")
            except Exception as e:
                self.log_result(f"URL {url_name}", "ERROR", f"URL no encontrada: {e}")
    
    def test_session_creation(self):
        """Prueba la creación de sesiones"""
        print("\n🧪 PROBANDO CREACIÓN DE SESIONES...")
        
        try:
            # Simular visita a la página principal
            response = self.client.get('/')
            
            # Verificar que se crearon las cookies
            if 'actas_sessionid' in response.cookies:
                self.log_result("Creación de Cookie de Sesión", "SUCCESS", "Cookie actas_sessionid creada")
            else:
                self.log_result("Creación de Cookie de Sesión", "ERROR", "Cookie actas_sessionid no creada")
            
            if 'actas_csrftoken' in response.cookies:
                self.log_result("Creación de Cookie CSRF", "SUCCESS", "Cookie actas_csrftoken creada")
            else:
                self.log_result("Creación de Cookie CSRF", "ERROR", "Cookie actas_csrftoken no creada")
            
        except Exception as e:
            self.log_result("Test de Sesión", "ERROR", f"Error en test de sesión: {e}")
    
    def test_debug_apis(self):
        """Prueba las APIs de debug"""
        print("\n🔍 PROBANDO APIs DE DEBUG...")
        
        # Crear un superusuario para las pruebas
        try:
            user, created = User.objects.get_or_create(
                username='test_admin',
                defaults={'is_superuser': True, 'is_staff': True}
            )
            if created:
                user.set_password('test_password')
                user.save()
            
            # Iniciar sesión
            self.client.login(username='test_admin', password='test_password')
            
            # Probar API de debug de sesión
            response = self.client.get(reverse('auditoria:session_debug_api'))
            if response.status_code == 200:
                self.log_result("API Session Debug", "SUCCESS", "API responde correctamente")
            else:
                self.log_result("API Session Debug", "ERROR", f"API respondió con código {response.status_code}")
            
            # Probar API de log de actividad frontend
            response = self.client.post(
                reverse('auditoria:log_frontend_activity'),
                {'action': 'test', 'data': {'test': True}},
                content_type='application/json'
            )
            if response.status_code == 200:
                self.log_result("API Log Frontend", "SUCCESS", "API de logging funciona")
            else:
                self.log_result("API Log Frontend", "ERROR", f"API de logging falló con código {response.status_code}")
            
        except Exception as e:
            self.log_result("APIs Debug", "ERROR", f"Error probando APIs: {e}")
    
    def verify_file_structure(self):
        """Verifica la estructura de archivos"""
        print("\n📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS...")
        
        required_files = [
            'apps/auditoria/session_middleware.py',
            'apps/auditoria/debug_views.py',
            'docs/COOKIES_Y_SESIONES.md',
            'docs/GUIA_USUARIO_COOKIES.md'
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.log_result(f"Archivo {file_path}", "SUCCESS", "Archivo existe")
            else:
                self.log_result(f"Archivo {file_path}", "ERROR", "Archivo no encontrado")
    
    def check_security_settings(self):
        """Verifica configuraciones de seguridad"""
        print("\n🔒 VERIFICANDO CONFIGURACIONES DE SEGURIDAD...")
        
        security_checks = [
            ('SESSION_COOKIE_HTTPONLY', True, "Las cookies de sesión están protegidas contra XSS"),
            ('CSRF_COOKIE_HTTPONLY', False, "El token CSRF es accesible para JavaScript (correcto)"),
            ('SESSION_COOKIE_SAMESITE', 'Lax', "Configuración SameSite correcta"),
            ('SESSION_EXPIRE_AT_BROWSER_CLOSE', True, "Las sesiones expiran al cerrar navegador")
        ]
        
        for setting_name, expected_value, message in security_checks:
            try:
                actual_value = getattr(settings, setting_name)
                if actual_value == expected_value:
                    self.log_result(f"Seguridad {setting_name}", "SUCCESS", message)
                else:
                    self.log_result(f"Seguridad {setting_name}", "WARNING", 
                                  f"Valor actual: {actual_value}, esperado: {expected_value}")
            except AttributeError:
                self.log_result(f"Seguridad {setting_name}", "WARNING", f"Configuración {setting_name} no encontrada")
    
    def generate_report(self):
        """Genera un reporte final"""
        print("\n" + "="*60)
        print("📊 REPORTE FINAL DE VERIFICACIÓN")
        print("="*60)
        
        print(f"\n✅ ÉXITOS: {len(self.success)}")
        for success in self.success[-5:]:  # Mostrar últimos 5
            print(f"   {success}")
        if len(self.success) > 5:
            print(f"   ... y {len(self.success) - 5} más")
        
        print(f"\n⚠️ ADVERTENCIAS: {len(self.warnings)}")
        for warning in self.warnings:
            print(f"   {warning}")
        
        print(f"\n❌ ERRORES: {len(self.errors)}")
        for error in self.errors:
            print(f"   {error}")
        
        # Evaluación general
        total_tests = len(self.success) + len(self.warnings) + len(self.errors)
        success_rate = (len(self.success) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 TASA DE ÉXITO: {success_rate:.1f}%")
        
        if len(self.errors) == 0 and len(self.warnings) <= 2:
            print("🎉 SISTEMA COMPLETAMENTE FUNCIONAL")
            return True
        elif len(self.errors) == 0:
            print("⚠️ SISTEMA FUNCIONAL CON ADVERTENCIAS MENORES")
            return True
        else:
            print("❌ SISTEMA REQUIERE CORRECCIONES")
            return False
    
    def run_all_tests(self):
        """Ejecuta todas las verificaciones"""
        print("🚀 INICIANDO VERIFICACIÓN DEL SISTEMA DE COOKIES Y SESIONES")
        print("=" * 60)
        
        self.verify_django_settings()
        self.verify_database_structure()
        self.verify_templates()
        self.verify_urls()
        self.verify_file_structure()
        self.check_security_settings()
        self.test_session_creation()
        self.test_debug_apis()
        
        return self.generate_report()

def main():
    """Función principal"""
    verifier = CookieSessionVerifier()
    
    try:
        success = verifier.run_all_tests()
        
        # Guardar reporte en archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"verificacion_cookies_sesiones_{timestamp}.log"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("REPORTE DE VERIFICACIÓN - SISTEMA DE COOKIES Y SESIONES\n")
            f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("ÉXITOS:\n")
            for success in verifier.success:
                f.write(f"{success}\n")
            
            f.write("\nADVERTENCIAS:\n")
            for warning in verifier.warnings:
                f.write(f"{warning}\n")
            
            f.write("\nERRORES:\n")
            for error in verifier.errors:
                f.write(f"{error}\n")
        
        print(f"\n📝 Reporte guardado en: {report_file}")
        
        if success:
            print("\n🎉 ¡VERIFICACIÓN COMPLETADA CON ÉXITO!")
            print("El sistema de cookies y sesiones está funcionando correctamente.")
            sys.exit(0)
        else:
            print("\n⚠️ VERIFICACIÓN COMPLETADA CON ERRORES")
            print("Revisa los errores reportados y corrige antes de continuar.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN LA VERIFICACIÓN: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
