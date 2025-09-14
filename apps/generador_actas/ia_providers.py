"""
Proveedores de IA para el módulo Generador de Actas
Incluye implementaciones para OpenAI, DeepSeek, Ollama y factory pattern
"""
import json
import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from django.conf import settings

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
        self.modelo = config.modelo
        self.temperatura = config.temperatura
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout
        self.configuracion_adicional = config.configuracion_adicional
    
    @abstractmethod
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa un prompt con el contexto dado
        
        Args:
            prompt: Prompt para enviar a la IA
            contexto: Contexto con datos de la transcripción
            
        Returns:
            Respuesta de la IA como string
        """
        pass
    
    def formatear_contexto(self, contexto: Dict[str, Any]) -> str:
        """
        Formatea el contexto para incluir en el prompt
        
        Args:
            contexto: Diccionario con datos de contexto
            
        Returns:
            String JSON formateado
        """
        try:
            return json.dumps(contexto, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Error formateando contexto: {e}")
            return str(contexto)
    
    def construir_mensaje_sistema(self) -> str:
        """Construye el mensaje del sistema para el chat"""
        return (
            "Eres un asistente especializado en redacción de actas municipales. "
            "Tu tarea es generar contenido formal, estructurado y preciso basado "
            "en transcripciones de reuniones. Mantén un tono oficial y usa "
            "terminología apropiada para documentos gubernamentales."
        )
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """
        Valida que la configuración del proveedor sea correcta
        
        Returns:
            (es_valida, mensaje_error)
        """
        if not self.modelo:
            return False, "Modelo no especificado"
        return True, ""


class OpenAIProvider(BaseIAProvider):
    """Proveedor para OpenAI GPT"""
    
    def __init__(self, config):
        super().__init__(config)
        try:
            import openai
            self.client = openai.OpenAI(
                api_key=config.api_key,
                base_url=config.api_url if config.api_url else None,
                timeout=config.timeout
            )
        except ImportError:
            raise ImportError("La librería 'openai' no está instalada. Ejecute: pip install openai")
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para OpenAI"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_key:
            return False, "API Key de OpenAI no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa el prompt usando OpenAI
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción
            
        Returns:
            Respuesta de OpenAI
        """
        try:
            # Determinar si necesita respuesta JSON
            response_format = None
            if any(keyword in prompt.lower() for keyword in ['json', 'formato json', 'estructura']):
                response_format = {"type": "json_object"}
            
            messages = [
                {
                    "role": "system",
                    "content": self.construir_mensaje_sistema()
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nContexto de la reunión:\n{self.formatear_contexto(contexto)}"
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.modelo,
                messages=messages,
                temperature=self.temperatura,
                max_tokens=self.max_tokens,
                response_format=response_format,
                **self.configuracion_adicional
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error en OpenAI: {str(e)}")
            raise Exception(f"Error procesando con OpenAI: {str(e)}")


class DeepSeekProvider(BaseIAProvider):
    """Proveedor para DeepSeek"""
    
    def validar_configuracion(self) -> tuple[bool, str]:
        """Validación específica para DeepSeek"""
        base_valid, base_msg = super().validar_configuracion()
        if not base_valid:
            return False, base_msg
        
        if not self.config.api_key:
            return False, "API Key de DeepSeek no configurada"
        
        return True, ""
    
    def procesar_prompt(self, prompt: str, contexto: Dict[str, Any]) -> str:
        """
        Procesa el prompt usando DeepSeek
        
        Args:
            prompt: Prompt del segmento
            contexto: Datos de la transcripción
            
        Returns:
            Respuesta de DeepSeek
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
                        "content": f"{prompt}\n\nContexto de la reunión:\n{self.formatear_contexto(contexto)}"
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
            
            return result['choices'][0]['message']['content']
            
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
        'deepseek': DeepSeekProvider,
        'anthropic': AnthropicProvider,
        'ollama': OllamaProvider,
        'google': GoogleProvider
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