import time
import subprocess
import os

print("=== VERIFICANDO ESTADO DEL SISTEMA ===")

# Verificar estado de los contenedores
print("1. Verificando estado de contenedores...")
try:
    result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("CONTENEDORES:")
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
except Exception as e:
    print(f"Error verificando contenedores: {e}")

print("\n" + "="*60)
print("Esperando 60 segundos antes de revisar logs...")
time.sleep(60)

print("\n=== REVISANDO LOGS DEL CONTENEDOR WEB ===")
try:
    result = subprocess.run(['docker', 'logs', '--tail=30', 'actas_web'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("LOGS WEB (últimas 30 líneas):")
    print(result.stdout)
    if result.stderr:
        print("STDERR WEB:", result.stderr)
except Exception as e:
    print(f"Error obteniendo logs web: {e}")

print("\n=== REVISANDO LOGS DE POSTGRES ===")
try:
    result = subprocess.run(['docker', 'logs', '--tail=15', 'actas_postgres'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("LOGS POSTGRES (últimas 15 líneas):")
    print(result.stdout)
    if result.stderr:
        print("STDERR POSTGRES:", result.stderr)
except Exception as e:
    print(f"Error obteniendo logs postgres: {e}")

print("\n=== REVISANDO LOGS DE REDIS ===")
try:
    result = subprocess.run(['docker', 'logs', '--tail=10', 'actas_redis'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("LOGS REDIS (últimas 10 líneas):")
    print(result.stdout)
    if result.stderr:
        print("STDERR REDIS:", result.stderr)
except Exception as e:
    print(f"Error obteniendo logs redis: {e}")

print("\n=== VERIFICANDO ACCESO WEB ===")
try:
    result = subprocess.run(['curl', '-I', 'http://localhost:8000'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia', timeout=10)
    if "200 OK" in result.stdout:
        print("✅ Web accesible - HTTP 200 OK")
    elif "500" in result.stdout:
        print("❌ Error interno del servidor - HTTP 500")
    elif "502" in result.stdout or "503" in result.stdout:
        print("❌ Servicio no disponible - HTTP 502/503")
    else:
        print("⚠️ Respuesta inesperada:")
        print(result.stdout)
except subprocess.TimeoutExpired:
    print("❌ Timeout - El servidor no responde")
except Exception as e:
    print(f"❌ Error accediendo a la web: {e}")

print("\n=== DIAGNÓSTICO COMPLETADO ===")
print("Si los contenedores están parados, necesitaremos reiniciarlos.")
print("Si hay errores en los logs, se identificarán para corregirlos.")