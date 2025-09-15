import time
import subprocess

print("Esperando 60 segundos antes de verificar logs...")
time.sleep(60)

print("\n=== VERIFICANDO LOGS DEL CONTENEDOR WEB ===")
try:
    result = subprocess.run(['docker', 'logs', '--tail=20', 'actas_web'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
except Exception as e:
    print(f"Error: {e}")

print("\n=== VERIFICANDO SINTAXIS DE SETTINGS.PY ===")
try:
    result = subprocess.run(['docker', 'exec', 'actas_web', 'python', '-c', 
                           'import config.settings; print("✅ Settings.py OK")'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("❌ Error en settings.py:")
        print(result.stderr)
except Exception as e:
    print(f"Error: {e}")

print("\n=== PROBANDO ACCESO AL FORMULARIO ===")
try:
    result = subprocess.run(['curl', '-I', 'http://localhost:8000/generador-actas/proveedores/crear/'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    if "200 OK" in result.stdout:
        print("✅ Formulario accesible")
    else:
        print("❌ Problema de acceso al formulario")
        print(result.stdout)
except Exception as e:
    print(f"Error: {e}")