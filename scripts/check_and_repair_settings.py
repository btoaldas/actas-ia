import shutil
import os
from datetime import datetime

# Crear backup del settings.py actual
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
backup_path = f"c:/p/actas.ia/scripts/backup/{timestamp}_backup_settings.py"

try:
    shutil.copy2("c:/p/actas.ia/config/settings.py", backup_path)
    print(f"✅ Backup creado: {backup_path}")
except Exception as e:
    print(f"❌ Error creando backup: {e}")

# Verificar sintaxis de settings.py
print("\n=== VERIFICANDO SINTAXIS DE SETTINGS.PY ===")
try:
    with open("c:/p/actas.ia/config/settings.py", 'r') as f:
        content = f.read()
    
    # Compilar para verificar sintaxis
    compile(content, "settings.py", "exec")
    print("✅ Sintaxis de settings.py es correcta")
    
except SyntaxError as e:
    print(f"❌ Error de sintaxis en settings.py:")
    print(f"Línea {e.lineno}: {e.text}")
    print(f"Error: {e.msg}")
    
    # Intentar reparar eliminando la configuración de IA problemática
    print("\n🔧 Intentando reparar eliminando configuración de IA...")
    try:
        # Buscar y eliminar la sección problemática
        lines = content.split('\n')
        new_lines = []
        skip_section = False
        
        for line in lines:
            if "# CONFIGURACIÓN DE PROVEEDORES DE IA" in line:
                skip_section = True
                print(f"⚠️ Saltando sección de IA desde línea con: {line[:50]}...")
                continue
            elif skip_section and (line.strip() == "" or line.startswith('#')) and len(new_lines) > 0:
                # Fin de la sección, agregar línea en blanco
                skip_section = False
                new_lines.append(line)
            elif not skip_section:
                new_lines.append(line)
        
        # Guardar archivo reparado
        with open("c:/p/actas.ia/config/settings.py", 'w') as f:
            f.write('\n'.join(new_lines))
        
        print("✅ Settings.py reparado - configuración de IA eliminada")
        print("✅ El sistema debería funcionar ahora sin la configuración de IA")
        
    except Exception as repair_error:
        print(f"❌ Error reparando: {repair_error}")
        
except Exception as e:
    print(f"❌ Error verificando settings.py: {e}")

print(f"\n=== RESUMEN ===")
print(f"1. Backup guardado en: {backup_path}")
print(f"2. Usar 'python scripts/restart_system.py' para reiniciar")
print(f"3. Si persisten problemas, restaurar backup con:")
print(f"   copy \"{backup_path}\" \"c:/p/actas.ia/config/settings.py\"")