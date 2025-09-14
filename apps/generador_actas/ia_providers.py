"""
Proveedores de IA para el módulo Generador de Actas
Implementaciones completas para todos los proveedores soportados
"""
import json
import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
import time

logger = logging.getLogger(__name__)


class BaseIAProvider(ABC):
    """Clase base para todos los proveedores de IA"""
    
    def __init__(self, config):
        """
        Inicializa el proveedor con la configuración
        
        Args:
            config: Instancia del modelo ProveedorIA
        """
        self.config = config
        self.configuracion = config.obtener_configuracion_completa()
        
    @abstractmethod
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa un prompt con el contexto dado
        
        Args:
            prompt: Prompt para enviar a la IA
            contexto: Contexto con datos adicionales
            
        Returns:
            Dict con respuesta, tokens usados y métricas
        """
        pass
    
    def validar_configuracion(self) -> Tuple[bool, str]:
        """
        Valida que la configuración del proveedor sea correcta
        
        Returns:
            (es_valida, mensaje_error)
        """
        if not self.configuracion.get('modelo'):
            return False, "Modelo no especificado"
        
        # Validar API key para proveedores que lo requieren
        if self.config.tipo in ['openai', 'anthropic', 'deepseek', 'google', 'groq', 'generic1', 'generic2']:
            if not self.configuracion.get('api_key'):
                return False, f"API Key requerida para {self.config.get_tipo_display()}"
        
        # Validar URL para proveedores locales
        if self.config.tipo in ['ollama', 'lmstudio']:
            if not self.configuracion.get('api_url'):
                return False, f"URL del servicio requerida para {self.config.get_tipo_display()}"
        
        return True, "Configuración válida"
    
    def test_conexion(self) -> Dict[str, Any]:
        """
        Prueba la conexión con el proveedor de IA
        
        Returns:
            Dict con resultado del test
        """
        try:
            prompt_test = (
                "Responde con un JSON válido indicando información REAL sobre ti mismo. "
                "Formato: {'tecnologia': 'ChatGPT/Claude/DeepSeek/etc', 'modelo': 'tu_modelo_real', "
                "'empresa': 'OpenAI/Anthropic/DeepSeek/etc', 'version': 'tu_version', "
                "'parametros': 'temperatura_max_tokens_etc', 'timestamp': '" + str(int(time.time())) + "'}. "
                "Usa TUS datos reales, no ejemplos."
            )
            
            start_time = time.time()
            resultado = self.procesar_prompt(prompt_test)
            end_time = time.time()
            
            return {
                "exito": True,
                "respuesta": resultado.get("respuesta", ""),
                "tokens_usados": resultado.get("tokens_usados", 0),
                "tiempo_respuesta": round(end_time - start_time, 2),
                "mensaje": "Conexión exitosa"
            }
            
        except Exception as e:
            logger.error(f"Error en test de conexión {self.config.nombre}: {str(e)}")
            return {
                "exito": False,
                "error": str(e),
                "mensaje": f"Error de conexión: {str(e)}"
            }
    
    def generar_respuesta(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Método de compatibilidad que mapea a procesar_prompt
        
        Args:
            prompt: Prompt para enviar a la IA
            contexto: Contexto con datos adicionales
            
        Returns:
            Dict con contenido, tokens_usados, modelo_usado y otras métricas
        """
        try:
            resultado = self.procesar_prompt(prompt, contexto)
            
            # Asegurar formato consistente
            return {
                "contenido": resultado.get("respuesta", resultado.get("contenido", "")),
                "response": resultado.get("respuesta", resultado.get("contenido", "")),
                "tokens_usados": resultado.get("tokens_usados", 0),
                "modelo_usado": resultado.get("modelo_usado", self.configuracion.get('modelo')),
                "finish_reason": resultado.get("finish_reason", ""),
                "tiempo_respuesta": resultado.get("tiempo_respuesta", 0),
                **resultado  # Incluir todos los campos originales
            }
        except Exception as e:
            logger.error(f"Error en generar_respuesta {self.config.nombre}: {str(e)}")
            raise Exception(f"Error generando respuesta: {str(e)}")
    
    def construir_mensaje_sistema(self) -> str:
        """Construye el mensaje del sistema para el chat"""
        mensaje_base = (
            "Eres un asistente especializado en redacción de actas municipales. "
            "Tu tarea es generar contenido formal, estructurado y preciso basado "
            "en transcripciones de reuniones. Mantén un tono oficial y usa "
            "terminología apropiada para documentos gubernamentales. "
            "IMPORTANTE: Siempre responde únicamente en formato JSON válido, "
            "sin explicaciones adicionales ni texto fuera del JSON."
        )
        
        # Agregar prompt global personalizado si existe
        if self.configuracion.get('prompt_sistema_global'):
            mensaje_base += f"\n\nInstrucciones adicionales: {self.configuracion['prompt_sistema_global']}"
        
        return mensaje_base


class OpenAIProvider(BaseIAProvider):
    """Proveedor para OpenAI GPT"""
    
    def __init__(self, config):
        super().__init__(config)
        try:
            import openai
            import httpx
            
            # Crear cliente HTTP personalizado para evitar problemas de proxies
            http_client = httpx.Client(
                timeout=self.configuracion.get('timeout', 60)
            )
            
            # Crear cliente OpenAI con http_client personalizado
            self.client = openai.OpenAI(
                api_key=self.configuracion['api_key'],
                http_client=http_client
            )
        except ImportError as e:
            raise ImportError(f"La librería requerida no está instalada: {str(e)}")
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            messages = [
                {"role": "system", "content": self.construir_mensaje_sistema()},
                {"role": "user", "content": prompt}
            ]
            
            # Agregar contexto si existe
            if contexto:
                context_msg = f"Contexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages.insert(-1, {"role": "user", "content": context_msg})
            
            response = self.client.chat.completions.create(
                model=self.configuracion['modelo'],
                messages=messages,
                temperature=self.configuracion['temperatura'],
                max_tokens=self.configuracion['max_tokens'],
                **self.configuracion.get('configuracion_adicional', {})
            )
            
            return {
                "respuesta": response.choices[0].message.content,
                "tokens_usados": response.usage.total_tokens if response.usage else 0,
                "modelo_usado": response.model,
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error OpenAI: {str(e)}")
            raise


class AnthropicProvider(BaseIAProvider):
    """Proveedor para Anthropic Claude"""
    
    def __init__(self, config):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=self.configuracion['api_key'],
                base_url=self.configuracion.get('api_url'),
                timeout=self.configuracion.get('timeout', 60)
            )
        except ImportError:
            raise ImportError("La librería 'anthropic' no está instalada. Ejecute: pip install anthropic")
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            # Construir mensaje completo
            mensaje_completo = prompt
            if contexto:
                context_str = f"\n\nContexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                mensaje_completo += context_str
            
            response = self.client.messages.create(
                model=self.configuracion['modelo'],
                max_tokens=self.configuracion['max_tokens'],
                temperature=self.configuracion['temperatura'],
                system=self.construir_mensaje_sistema(),
                messages=[
                    {"role": "user", "content": mensaje_completo}
                ],
                **self.configuracion.get('configuracion_adicional', {})
            )
            
            return {
                "respuesta": response.content[0].text,
                "tokens_usados": response.usage.input_tokens + response.usage.output_tokens,
                "modelo_usado": response.model,
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error Anthropic: {str(e)}")
            raise


class DeepSeekProvider(BaseIAProvider):
    """Proveedor para DeepSeek"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/chat/completions"
            
            messages = [
                {"role": "system", "content": self.construir_mensaje_sistema()},
                {"role": "user", "content": prompt}
            ]
            
            if contexto:
                context_msg = f"Contexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages.insert(-1, {"role": "user", "content": context_msg})
            
            headers = {
                "Authorization": f"Bearer {self.configuracion['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.configuracion['modelo'],
                "messages": messages,
                "temperature": self.configuracion['temperatura'],
                "max_tokens": self.configuracion['max_tokens'],
                **self.configuracion.get('configuracion_adicional', {})
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['choices'][0]['message']['content'],
                "tokens_usados": result.get('usage', {}).get('total_tokens', 0),
                "modelo_usado": result.get('model', self.configuracion['modelo']),
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error DeepSeek: {str(e)}")
            raise


class GoogleGeminiProvider(BaseIAProvider):
    """Proveedor para Google Gemini"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/models/{self.configuracion['modelo']}:generateContent"
            
            # Construir mensaje completo
            mensaje_completo = f"{self.construir_mensaje_sistema()}\n\n{prompt}"
            if contexto:
                context_str = f"\n\nContexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                mensaje_completo += context_str
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {"text": mensaje_completo}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": self.configuracion['temperatura'],
                    "maxOutputTokens": self.configuracion['max_tokens'],
                    **self.configuracion.get('configuracion_adicional', {})
                }
            }
            
            params = {"key": self.configuracion['api_key']}
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                params=params,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['candidates'][0]['content']['parts'][0]['text'],
                "tokens_usados": result.get('usageMetadata', {}).get('totalTokenCount', 0),
                "modelo_usado": self.configuracion['modelo'],
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error Google Gemini: {str(e)}")
            raise


class OllamaProvider(BaseIAProvider):
    """Proveedor para Ollama (Local)"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/api/generate"
            
            # Construir mensaje completo
            mensaje_completo = f"{self.construir_mensaje_sistema()}\n\n{prompt}"
            if contexto:
                context_str = f"\n\nContexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                mensaje_completo += context_str
            
            data = {
                "model": self.configuracion['modelo'],
                "prompt": mensaje_completo,
                "stream": False,
                "options": {
                    "temperature": self.configuracion['temperatura'],
                    "num_predict": self.configuracion['max_tokens'],
                    **self.configuracion.get('configuracion_adicional', {})
                }
            }
            
            response = requests.post(
                url, 
                json=data,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['response'],
                "tokens_usados": result.get('eval_count', 0) + result.get('prompt_eval_count', 0),
                "modelo_usado": self.configuracion['modelo'],
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error Ollama: {str(e)}")
            raise


class LMStudioProvider(BaseIAProvider):
    """Proveedor para LM Studio (Local)"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/v1/chat/completions"
            
            messages = [
                {"role": "system", "content": self.construir_mensaje_sistema()},
                {"role": "user", "content": prompt}
            ]
            
            if contexto:
                context_msg = f"Contexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages.insert(-1, {"role": "user", "content": context_msg})
            
            data = {
                "model": self.configuracion['modelo'],
                "messages": messages,
                "temperature": self.configuracion['temperatura'],
                "max_tokens": self.configuracion['max_tokens'],
                **self.configuracion.get('configuracion_adicional', {})
            }
            
            response = requests.post(
                url, 
                json=data,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['choices'][0]['message']['content'],
                "tokens_usados": result.get('usage', {}).get('total_tokens', 0),
                "modelo_usado": result.get('model', self.configuracion['modelo']),
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error LM Studio: {str(e)}")
            raise


class GroqProvider(BaseIAProvider):
    """Proveedor para Groq"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/chat/completions"
            
            messages = [
                {"role": "system", "content": self.construir_mensaje_sistema()},
                {"role": "user", "content": prompt}
            ]
            
            if contexto:
                context_msg = f"Contexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages.insert(-1, {"role": "user", "content": context_msg})
            
            headers = {
                "Authorization": f"Bearer {self.configuracion['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.configuracion['modelo'],
                "messages": messages,
                "temperature": self.configuracion['temperatura'],
                "max_tokens": self.configuracion['max_tokens'],
                **self.configuracion.get('configuracion_adicional', {})
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['choices'][0]['message']['content'],
                "tokens_usados": result.get('usage', {}).get('total_tokens', 0),
                "modelo_usado": result.get('model', self.configuracion['modelo']),
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error Groq: {str(e)}")
            raise


class GenericProvider(BaseIAProvider):
    """Proveedor genérico compatible con OpenAI API"""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            url = f"{self.configuracion['api_url']}/chat/completions"
            
            messages = [
                {"role": "system", "content": self.construir_mensaje_sistema()},
                {"role": "user", "content": prompt}
            ]
            
            if contexto:
                context_msg = f"Contexto adicional:\n{json.dumps(contexto, ensure_ascii=False, indent=2)}"
                messages.insert(-1, {"role": "user", "content": context_msg})
            
            headers = {
                "Authorization": f"Bearer {self.configuracion['api_key']}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.configuracion['modelo'],
                "messages": messages,
                "temperature": self.configuracion['temperatura'],
                "max_tokens": self.configuracion['max_tokens'],
                **self.configuracion.get('configuracion_adicional', {})
            }
            
            response = requests.post(
                url, 
                headers=headers, 
                json=data,
                timeout=self.configuracion.get('timeout', 60)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "respuesta": result['choices'][0]['message']['content'],
                "tokens_usados": result.get('usage', {}).get('total_tokens', 0),
                "modelo_usado": result.get('model', self.configuracion['modelo']),
                "exito": True
            }
            
        except Exception as e:
            logger.error(f"Error Proveedor Genérico: {str(e)}")
            raise


# Factory function combinada en línea 792


class DeepSeekProvider(BaseIAProvider):
    """Proveedor para DeepSeek"""
    
    def __init__(self, config):
        super().__init__(config)
        # Propiedades específicas de DeepSeek
        self.modelo = self.configuracion.get('modelo', 'deepseek-chat')
        self.temperatura = self.configuracion.get('temperatura', 0.7)
        self.max_tokens = self.configuracion.get('max_tokens', 1000)
        self.timeout = self.configuracion.get('timeout', 60)
        self.configuracion_adicional = self.configuracion.get('configuracion_adicional', {})
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para DeepSeek"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_key:
            return False, "API Key de DeepSeek no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa el prompt usando DeepSeek
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción (opcional)
            
        Returns:
            Dict con respuesta, tokens y métricas
        """
        try:
            url = self.config.api_url or "https://api.deepseek.com/v1/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.modelo,
                "messages": [
                    {
                        "role": "system",
                        "content": self.construir_mensaje_sistema()
                    },
                    {
                        "role": "user", 
                        "content": f"{prompt}" + (f"\n\nContexto de la reunión:\n{self.formatear_contexto(contexto)}" if contexto else "")
                    }
                ],
                "temperature": self.temperatura,
                "max_tokens": self.max_tokens,
                "stream": False,
                **self.configuracion_adicional
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception("Respuesta inválida de DeepSeek")
            
            # Devolver formato consistente
            return {
                "respuesta": result['choices'][0]['message']['content'],
                "tokens_usados": result.get('usage', {}).get('total_tokens', 0),
                "modelo_usado": result.get('model', self.modelo),
                "finish_reason": result['choices'][0].get('finish_reason', '')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con DeepSeek: {str(e)}")
            raise Exception(f"Error de conexión con DeepSeek: {str(e)}")
        except Exception as e:
            logger.error(f"Error en DeepSeek: {str(e)}")
            raise Exception(f"Error procesando con DeepSeek: {str(e)}")


class AnthropicProvider(BaseIAProvider):
    """Proveedor para Anthropic Claude"""
    
    def __init__(self, config):
        super().__init__(config)
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=config.api_key,
                base_url=config.api_url if config.api_url else None,
                timeout=config.timeout
            )
        except ImportError:
            raise ImportError("La librería 'anthropic' no está instalada. Ejecute: pip install anthropic")
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para Anthropic"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_key:
            return False, "API Key de Anthropic no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa el prompt usando Anthropic Claude
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción
            
        Returns:
            Respuesta de Claude
        """
        try:
            message = self.client.messages.create(
                model=self.modelo,
                max_tokens=self.max_tokens,
                temperature=self.temperatura,
                system=self.construir_mensaje_sistema(),
                messages=[
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nContexto de la reunión:\n{self.formatear_contexto(contexto)}"
                    }
                ],
                **self.configuracion_adicional
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Error en Anthropic: {str(e)}")
            raise Exception(f"Error procesando con Anthropic: {str(e)}")


class OllamaProvider(BaseIAProvider):
    """Proveedor para Ollama (modelos locales)"""
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para Ollama"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_url:
            return False, "URL de Ollama no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa el prompt usando Ollama
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción
            
        Returns:
            Respuesta de Ollama
        """
        try:
            url = f"{self.config.api_url.rstrip('/')}/api/generate"
            
            # Construir prompt completo para Ollama
            prompt_completo = f"""
{self.construir_mensaje_sistema()}

Tarea: {prompt}

Contexto de la reunión:
{self.formatear_contexto(contexto)}

Respuesta:"""
            
            data = {
                "model": self.modelo,
                "prompt": prompt_completo,
                "temperature": self.temperatura,
                "num_predict": self.max_tokens,
                "stream": False,
                **self.configuracion_adicional
            }
            
            response = requests.post(
                url,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'response' not in result:
                raise Exception("Respuesta inválida de Ollama")
            
            return result['response']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con Ollama: {str(e)}")
            raise Exception(f"Error de conexión con Ollama: {str(e)}")
        except Exception as e:
            logger.error(f"Error en Ollama: {str(e)}")
            raise Exception(f"Error procesando con Ollama: {str(e)}")


class GoogleProvider(BaseIAProvider):
    """Proveedor para Google Gemini"""
    
    def __init__(self, config):
        super().__init__(config)
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.api_key)
            self.model = genai.GenerativeModel(config.modelo)
        except ImportError:
            raise ImportError("La librería 'google-generativeai' no está instalada. Ejecute: pip install google-generativeai")
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para Google"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_key:
            return False, "API Key de Google no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa el prompt usando Google Gemini
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción
            
        Returns:
            Respuesta de Gemini
        """
        try:
            prompt_completo = f"""
{self.construir_mensaje_sistema()}

Tarea: {prompt}

Contexto de la reunión:
{self.formatear_contexto(contexto)}"""
            
            response = self.model.generate_content(
                prompt_completo,
                generation_config={
                    'temperature': self.temperatura,
                    'max_output_tokens': self.max_tokens,
                    **self.configuracion_adicional
                }
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Error en Google Gemini: {str(e)}")
            raise Exception(f"Error procesando con Google Gemini: {str(e)}")


# Factory para crear proveedores
def get_ia_provider(proveedor_config) -> BaseIAProvider:
    """
    Factory para obtener el proveedor de IA correcto
    
    Args:
        proveedor_config: Instancia del modelo ProveedorIA
        
    Returns:
        Instancia del proveedor correspondiente
        
    Raises:
        ValueError: Si el tipo de proveedor no es soportado
        Exception: Si hay errores de configuración
    """
    providers = {
        'openai': OpenAIProvider,
        'anthropic': AnthropicProvider,
        'deepseek': DeepSeekProvider,
        'google': GoogleGeminiProvider,
        'ollama': OllamaProvider,
        'lmstudio': LMStudioProvider,
        'groq': GroqProvider,
        'generic1': GenericProvider,
        'generic2': GenericProvider,
    }
    
    provider_class = providers.get(proveedor_config.tipo)
    if not provider_class:
        raise ValueError(f"Proveedor no soportado: {proveedor_config.tipo}")
    
    # Crear instancia del proveedor
    try:
        provider = provider_class(proveedor_config)
        
        # Validar configuración
        is_valid, error_msg = provider.validar_configuracion()
        if not is_valid:
            raise Exception(f"Configuración inválida para {proveedor_config.nombre}: {error_msg}")
        
        return provider
        
    except ImportError as e:
        raise Exception(f"Dependencia faltante para {proveedor_config.tipo}: {str(e)}")
    except Exception as e:
        logger.error(f"Error creando proveedor {proveedor_config.tipo}: {str(e)}")
        raise


def probar_proveedor(proveedor_config, prompt_prueba: str = None) -> Dict[str, Any]:
    """
    Prueba un proveedor de IA con un prompt simple
    
    Args:
        proveedor_config: Instancia del modelo ProveedorIA
        prompt_prueba: Prompt personalizado para la prueba
        
    Returns:
        Diccionario con resultado de la prueba
    """
    if not prompt_prueba:
        prompt_prueba = "Responde brevemente: ¿Cuál es la capital de Ecuador?"
    
    contexto_prueba = {
        "tipo_prueba": "configuracion",
        "timestamp": "2025-09-13",
        "mensaje": "Esta es una prueba de configuración del proveedor IA"
    }
    
    try:
        provider = get_ia_provider(proveedor_config)
        respuesta = provider.procesar_prompt(prompt_prueba, contexto_prueba)
        
        return {
            'exito': True,
            'respuesta': respuesta,
            'mensaje': 'Proveedor configurado correctamente'
        }
        
    except Exception as e:
        return {
            'exito': False,
            'respuesta': None,
            'mensaje': str(e)
        }


def obtener_proveedores_disponibles():
    """
    Obtiene lista de proveedores disponibles según las dependencias instaladas
    
    Returns:
        Lista de tipos de proveedores disponibles
    """
    disponibles = []
    
    # Verificar OpenAI
    try:
        import openai
        disponibles.append('openai')
    except ImportError:
        pass
    
    # Verificar Anthropic
    try:
        import anthropic
        disponibles.append('anthropic')
    except ImportError:
        pass
    
    # Verificar Google
    try:
        import google.generativeai
        disponibles.append('google')
    except ImportError:
        pass
    
    # DeepSeek y Ollama no necesitan librerías especiales
    disponibles.extend(['deepseek', 'ollama'])
    
    return disponibles