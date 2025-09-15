import subprocess
import os

# Verificar logs del contenedor web
print("=== LOGS DEL CONTENEDOR WEB (últimas 20 líneas) ===")
try:
    result = subprocess.run(['docker', 'logs', '--tail=20', 'actas_web'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
except Exception as e:
    print(f"Error ejecutando docker logs: {e}")

print("\n=== VERIFICACIÓN SINTAXIS PYTHON ===")
try:
    result = subprocess.run(['docker', 'exec', 'actas_web', 'python', '-m', 'py_compile', '/app/apps/generador_actas/forms.py'], 
                          capture_output=True, text=True, cwd='c:/p/actas.ia')
    if result.returncode == 0:
        print("✅ forms.py - Sintaxis correcta")
    else:
        print("❌ forms.py - Error de sintaxis:")
        print(result.stderr)
except Exception as e:
    print(f"Error verificando sintaxis: {e}")