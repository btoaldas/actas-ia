import subprocess
import os

print("=== REINICIANDO SISTEMA ACTAS.IA ===")

# Primero verificar si docker-compose está funcionando
print("1. Verificando Docker Compose...")
try:
    result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    print(f"✅ Docker Compose: {result.stdout.strip()}")
except Exception as e:
    print(f"❌ Error con Docker Compose: {e}")
    print("Usando docker directamente...")

# Parar contenedores si están ejecutándose
print("\n2. Parando contenedores existentes...")
try:
    subprocess.run(['docker-compose', 'down'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("✅ Contenedores parados")
except Exception as e:
    print(f"⚠️ Error parando contenedores: {e}")

# Verificar archivo docker-compose.yml
print("\n3. Verificando archivos Docker...")
if os.path.exists('c:/p/actas.ia/docker-compose.yml'):
    print("✅ docker-compose.yml encontrado")
else:
    print("❌ docker-compose.yml NO encontrado")

# Intentar iniciar el sistema
print("\n4. Iniciando sistema...")
try:
    print("Ejecutando: docker-compose up -d")
    result = subprocess.run(['docker-compose', 'up', '-d'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    
    if result.returncode == 0:
        print("✅ Sistema iniciado exitosamente")
        print("Salida:", result.stdout)
    else:
        print("❌ Error iniciando sistema:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        
        # Intentar con --build si hay errores
        print("\nIntentando con --build...")
        result2 = subprocess.run(['docker-compose', 'up', '-d', '--build'], 
                               capture_output=True, text=True, cwd='c:/p/actas.ia')
        
        if result2.returncode == 0:
            print("✅ Sistema iniciado con --build")
        else:
            print("❌ Error persistente:")
            print("STDERR:", result2.stderr)
            
except Exception as e:
    print(f"❌ Error ejecutando docker-compose: {e}")

print("\n=== ESPERANDO INICIALIZACIÓN (60 segundos) ===")
import time
for i in range(6):
    print(f"⏳ {(i+1)*10} segundos...")
    time.sleep(10)

# Verificar estado final
print("\n5. Verificando estado final...")
try:
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("CONTENEDORES ACTIVOS:")
    print(result.stdout)
    
    # Verificar acceso web
    print("\n6. Verificando acceso web...")
    web_result = subprocess.run(['curl', '-I', 'http://localhost:8000'], 
                               capture_output=True, text=True, cwd='c:/p/actas.ia', timeout=10)
    
    if "200" in web_result.stdout:
        print("✅ Web accesible - Sistema funcionando")
    else:
        print("❌ Web no accesible:")
        print(web_result.stdout)
        
except Exception as e:
    print(f"Error en verificación final: {e}")

print("\n=== REINICIO COMPLETADO ===")
print("Si aún hay problemas, revisar logs con:")
print("docker logs actas_web")
print("docker logs actas_postgres")