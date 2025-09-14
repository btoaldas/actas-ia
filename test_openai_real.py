from apps.generador_actas.models import ProveedorIA
from apps.generador_actas.ia_providers import get_ia_provider
import json

# Obtener el proveedor OpenAI
proveedor = ProveedorIA.objects.get(nombre='OpenAI Producción')
print(f"🔍 Probando proveedor: {proveedor.nombre}")
print(f"🔧 Tipo: {proveedor.tipo}")
print(f"🔑 API Key: {proveedor.api_key[:20]}...")
print(f"🤖 Modelo: {proveedor.modelo}")

# Crear instancia del proveedor
provider = get_ia_provider(proveedor)
print(f"✅ Proveedor creado: {provider.__class__.__name__}")

# Probar conexión
prompt = 'Responde solo con JSON: {"mensaje": "Conexión exitosa", "proveedor": "OpenAI", "modelo": "gpt-4o-mini", "test": "ok"}'

try:
    print("🚀 Enviando prueba de conexión...")
    resultado = provider.generar_respuesta(prompt)
    print(f"✅ Respuesta recibida:")
    print(f"📄 Contenido: {resultado['contenido']}")
    print(f"📊 Tokens usados: {resultado.get('tokens_usados', 'N/A')}")
    print(f"⏱️ Tiempo: {resultado.get('tiempo_respuesta', 'N/A')}")
    
    # Verificar que sea JSON válido
    try:
        json_data = json.loads(resultado['contenido'])
        print("✅ JSON válido:")
        print(json.dumps(json_data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("❌ La respuesta no es JSON válido")
        
except Exception as e:
    print(f"❌ Error en la prueba: {str(e)}")
    print(f"🔍 Tipo de error: {type(e).__name__}")