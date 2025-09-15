#!/usr/bin/env python3
"""
Script de emergencia para corregir el error en settings.py
que está impidiendo que Django inicie
"""

import re

def fix_settings_file():
    """Corregir todas las referencias a env() en settings.py"""
    
    settings_path = 'c:/p/actas.ia/config/settings.py'
    
    try:
        # Leer el archivo
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("📁 Archivo settings.py leído")
        
        # Backup
        backup_path = settings_path + '.backup.emergency'
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 Backup creado: {backup_path}")
        
        # Reemplazar todas las instancias de env() por os.environ.get()
        
        # Patrón 1: env('VAR', default='value') → os.environ.get('VAR', 'value')
        content = re.sub(
            r"env\('([^']+)',\s*default='([^']*)'\)",
            r"os.environ.get('\1', '\2')",
            content
        )
        
        # Patrón 2: env('VAR', default="value") → os.environ.get('VAR', "value")
        content = re.sub(
            r'env\(\'([^\']+)\',\s*default="([^"]*)"\)',
            r'os.environ.get(\'\1\', "\2")',
            content
        )
        
        # Patrón 3: env.float('VAR', default=0.7) → float(os.environ.get('VAR', '0.7'))
        content = re.sub(
            r"env\.float\('([^']+)',\s*default=([^)]+)\)",
            r"float(os.environ.get('\1', '\2'))",
            content
        )
        
        # Patrón 4: env.int('VAR', default=123) → int(os.environ.get('VAR', '123'))
        content = re.sub(
            r"env\.int\('([^']+)',\s*default=([^)]+)\)",
            r"int(os.environ.get('\1', '\2'))",
            content
        )
        
        # Patrón 5: env.bool('VAR', default=True) → os.environ.get('VAR', 'True').lower() == 'true'
        content = re.sub(
            r"env\.bool\('([^']+)',\s*default=([^)]+)\)",
            r"os.environ.get('\1', '\2').lower() == 'true'",
            content
        )
        
        print("🔧 Reemplazos realizados:")
        print("   - env('VAR', default='value') → os.environ.get('VAR', 'value')")
        print("   - env.float('VAR', default=X) → float(os.environ.get('VAR', 'X'))")
        print("   - env.int('VAR', default=X) → int(os.environ.get('VAR', 'X'))")
        print("   - env.bool('VAR', default=X) → os.environ.get('VAR', 'X').lower() == 'true'")
        
        # Escribir el archivo corregido
        with open(settings_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("✅ Archivo settings.py corregido")
        print("🔄 Django debería poder iniciar ahora")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚨 === CORRECCIÓN DE EMERGENCIA DE SETTINGS.PY ===")
    if fix_settings_file():
        print("\n✅ CORRECCIÓN COMPLETADA")
        print("🔄 El contenedor debería reiniciarse automáticamente")
        print("⏱️ Espera 30-60 segundos y verifica: http://localhost:8000")
    else:
        print("\n❌ CORRECCIÓN FALLÓ")
        print("🔧 Restaurar manualmente desde el backup")