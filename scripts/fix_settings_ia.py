# Corregir las definiciones de variables usando os.environ.get en lugar de env()

# Buscar y reemplazar cada línea individualmente
import re

# Leer el contenido del archivo
with open('c:/p/actas.ia/config/settings.py', 'r') as f:
    content = f.read()

# Reemplazar todas las ocurrencias de env() por os.environ.get()
content = content.replace("OPENAI_API_KEY = env('OPENAI_API_KEY', default='')", "OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')")
content = content.replace("OPENAI_API_URL = env('OPENAI_API_URL', default='https://api.openai.com/v1/chat/completions')", "OPENAI_API_URL = os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')")
content = content.replace("OPENAI_DEFAULT_MODEL = env('OPENAI_DEFAULT_MODEL', default='gpt-4o-mini')", "OPENAI_DEFAULT_MODEL = os.environ.get('OPENAI_DEFAULT_MODEL', 'gpt-4o-mini')")
content = content.replace("OPENAI_DEFAULT_TEMPERATURE = env.float('OPENAI_DEFAULT_TEMPERATURE', default=0.7)", "OPENAI_DEFAULT_TEMPERATURE = float(os.environ.get('OPENAI_DEFAULT_TEMPERATURE', '0.7'))")
content = content.replace("OPENAI_DEFAULT_MAX_TOKENS = env.int('OPENAI_DEFAULT_MAX_TOKENS', default=4000)", "OPENAI_DEFAULT_MAX_TOKENS = int(os.environ.get('OPENAI_DEFAULT_MAX_TOKENS', '4000'))")

# Continuar con las demás configuraciones...
content = content.replace("DEEPSEEK_API_KEY = env('DEEPSEEK_API_KEY', default='')", "DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')")
content = content.replace("DEEPSEEK_API_URL = env('DEEPSEEK_API_URL', default='https://api.deepseek.com/v1/chat/completions')", "DEEPSEEK_API_URL = os.environ.get('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1/chat/completions')")
content = content.replace("DEEPSEEK_DEFAULT_MODEL = env('DEEPSEEK_DEFAULT_MODEL', default='deepseek-chat')", "DEEPSEEK_DEFAULT_MODEL = os.environ.get('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')")
content = content.replace("DEEPSEEK_DEFAULT_TEMPERATURE = env.float('DEEPSEEK_DEFAULT_TEMPERATURE', default=0.7)", "DEEPSEEK_DEFAULT_TEMPERATURE = float(os.environ.get('DEEPSEEK_DEFAULT_TEMPERATURE', '0.7'))")
content = content.replace("DEEPSEEK_DEFAULT_MAX_TOKENS = env.int('DEEPSEEK_DEFAULT_MAX_TOKENS', default=4000)", "DEEPSEEK_DEFAULT_MAX_TOKENS = int(os.environ.get('DEEPSEEK_DEFAULT_MAX_TOKENS', '4000'))")

# Continuar con todas las configuraciones usando regex para ser más eficiente
patterns = [
    (r"= env\('([^']+)', default='([^']*)'\)", r"= os.environ.get('\1', '\2')"),
    (r"= env\.float\('([^']+)', default=([^)]+)\)", r"= float(os.environ.get('\1', '\2'))"),
    (r"= env\.int\('([^']+)', default=([^)]+)\)", r"= int(os.environ.get('\1', '\2'))"),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

# Guardar el archivo corregido
with open('c:/p/actas.ia/config/settings.py', 'w') as f:
    f.write(content)

print("✅ Configuración de settings.py actualizada correctamente")