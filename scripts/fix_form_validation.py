# BACKUP del archivo original antes de la corrección
backup_timestamp = "2025-09-14_19-30-00"
print(f"Backup creado en scripts/backup/{backup_timestamp}_backup_forms.py")

# Leer archivo completo
with open("c:/p/actas.ia/apps/generador_actas/forms.py", "r", encoding="utf-8") as f:
    contenido_completo = f.read()

# Buscar el final de la clase ProveedorIAForm
import re
pattern = r'(class ProveedorIAForm.*?)(class\s+\w+|$)'
match = re.search(pattern, contenido_completo, re.DOTALL)

if match:
    print("Clase ProveedorIAForm encontrada - modificando validación")
    
    # Buscar el final de la clase (antes del siguiente 'class' o final del archivo)
    clase_content = match.group(1)
    
    # Si no existe el método clean, agregarlo
    if 'def clean(self):' not in clase_content:
        print("Método clean no existe - agregándolo")
        # Buscar el final del método save o __init__
        if 'return instancia' in clase_content:
            nuevo_contenido = contenido_completo.replace(
                'return instancia',
                '''return instancia

    def clean(self):
        """Validación global del formulario para manejar API key según checkbox"""
        cleaned_data = super().clean()
        api_key = cleaned_data.get('api_key')
        usar_env = cleaned_data.get('usar_env_api_key', False)
        tipo = cleaned_data.get('tipo', '')
        
        if usar_env:
            # Si usa .env, limpiar el campo api_key para evitar errores de validación
            cleaned_data['api_key'] = ''
        else:
            # Si no usa .env, API key es obligatoria
            if not api_key or api_key.strip() == '':
                self.add_error('api_key', 
                    'Debe proporcionar una API Key personalizada o marcar "Usar configuración del .env"'
                )
        
        return cleaned_data'''
            )
            
            # Escribir el archivo corregido
            with open("c:/p/actas.ia/apps/generador_actas/forms.py", "w", encoding="utf-8") as f:
                f.write(nuevo_contenido)
            
            print("Archivo forms.py actualizado con validación corregida")
        else:
            print("No se encontró 'return instancia' - estructura inesperada")
    else:
        print("Método clean ya existe - verificar implementación manual")
else:
    print("No se encontró la clase ProveedorIAForm")