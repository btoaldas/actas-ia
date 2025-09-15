# Esperar 60 segundos antes de verificar logs
import time
import os

print("Esperando 60 segundos antes de verificar los logs del contenedor...")
time.sleep(60)

print("Verificando logs del contenedor web:")
os.system("docker logs --tail=20 actas_web")