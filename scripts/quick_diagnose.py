import subprocess
import os

print("=== DIAGNÓSTICO RÁPIDO DEL SISTEMA ===")

# Verificar estado inmediato de contenedores
try:
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    print("CONTENEDORES EJECUTÁNDOSE:")
    if "actas_web" in result.stdout:
        print("✅ actas_web está ejecutándose")
    else:
        print("❌ actas_web NO está ejecutándose")
    
    if "actas_postgres" in result.stdout:
        print("✅ actas_postgres está ejecutándose")
    else:
        print("❌ actas_postgres NO está ejecutándose")
        
    if "actas_redis" in result.stdout:
        print("✅ actas_redis está ejecutándose")
    else:
        print("❌ actas_redis NO está ejecutándose")
        
    print("\nESTADO COMPLETO:")
    print(result.stdout)
    
except Exception as e:
    print(f"Error: {e}")

# Si hay contenedores parados, intentar reiniciarlos
print("\n=== VERIFICANDO CONTENEDORES PARADOS ===")
try:
    result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True, cwd='c:/p/actas.ia')
    if "Exited" in result.stdout:
        print("⚠️ Hay contenedores parados:")
        lines = result.stdout.split('\n')
        for line in lines:
            if "Exited" in line:
                print(f"  📛 {line}")
    else:
        print("✅ No hay contenedores parados")
        
except Exception as e:
    print(f"Error: {e}")

print(f"\n=== EJECUTAR PARA DETALLES COMPLETOS ===")
print("python scripts/diagnose_system_crash.py")