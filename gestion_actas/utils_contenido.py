"""
Utilidades para procesamiento y limpieza de contenido de actas
Maneja conversión entre HTML, texto plano y diferentes formatos
"""
import re
import html
from bs4 import BeautifulSoup
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)

def limpiar_contenido_html(contenido_html):
    """
    Limpia el contenido HTML eliminando tags innecesarios y extrayendo solo el contenido del body
    
    Args:
        contenido_html (str): Contenido HTML completo
        
    Returns:
        str: Contenido HTML limpio solo del body
    """
    try:
        if not contenido_html:
            return ""
            
        # Si no es HTML completo, devolver tal como está
        if not any(tag in contenido_html.lower() for tag in ['<html', '<body', '<head']):
            return contenido_html
        
        # Parsear el HTML
        soup = BeautifulSoup(contenido_html, 'html.parser')
        
        # Buscar el contenido del body
        body = soup.find('body')
        if body:
            # Extraer solo el contenido interno del body
            contenido_limpio = str(body.decode_contents())
        else:
            # Si no hay body, extraer todo el contenido sin html, head, body tags
            for tag in soup(['html', 'head', 'body']):
                tag.decompose()
            contenido_limpio = str(soup)
        
        # Limpiar espacios extra y líneas vacías
        contenido_limpio = re.sub(r'\n\s*\n\s*\n', '\n\n', contenido_limpio)
        contenido_limpio = contenido_limpio.strip()
        
        return contenido_limpio
        
    except Exception as e:
        logger.error(f"Error limpiando contenido HTML: {str(e)}")
        return strip_tags(contenido_html) if contenido_html else ""


def html_a_texto_formateado(contenido_html):
    """
    Convierte HTML a texto plano manteniendo formato de párrafos y títulos
    
    Args:
        contenido_html (str): Contenido HTML
        
    Returns:
        str: Texto plano formateado
    """
    try:
        if not contenido_html:
            return ""
        
        # Limpiar el HTML primero
        contenido_limpio = limpiar_contenido_html(contenido_html)
        
        # Parsear con BeautifulSoup para mejor manejo
        soup = BeautifulSoup(contenido_limpio, 'html.parser')
        
        # Reemplazar elementos específicos con formato de texto
        replacements = {
            'h1': lambda tag: f"\n{'=' * 60}\n{tag.get_text().upper()}\n{'=' * 60}\n",
            'h2': lambda tag: f"\n{'-' * 40}\n{tag.get_text().upper()}\n{'-' * 40}\n",
            'h3': lambda tag: f"\n### {tag.get_text()}\n",
            'h4': lambda tag: f"\n## {tag.get_text()}\n",
            'h5': lambda tag: f"\n# {tag.get_text()}\n",
            'h6': lambda tag: f"\n{tag.get_text()}\n",
            'p': lambda tag: f"\n{tag.get_text()}\n",
            'br': lambda tag: "\n",
            'hr': lambda tag: f"\n{'-' * 50}\n",
            'strong': lambda tag: f"**{tag.get_text()}**",
            'b': lambda tag: f"**{tag.get_text()}**",
            'em': lambda tag: f"*{tag.get_text()}*",
            'i': lambda tag: f"*{tag.get_text()}*",
            'li': lambda tag: f"• {tag.get_text()}\n",
            'ul': lambda tag: f"\n{chr(10).join(['• ' + li.get_text() for li in tag.find_all('li')])}\n",
            'ol': lambda tag: f"\n{chr(10).join([f'{i+1}. {li.get_text()}' for i, li in enumerate(tag.find_all('li'))])}\n",
        }
        
        # Aplicar reemplazos
        for tag_name, replacement_func in replacements.items():
            for tag in soup.find_all(tag_name):
                try:
                    new_text = replacement_func(tag)
                    tag.replace_with(new_text)
                except Exception:
                    tag.replace_with(tag.get_text())
        
        # Obtener texto final
        texto_final = soup.get_text()
        
        # Limpiar espacios extra y normalizar líneas
        texto_final = re.sub(r'\n\s*\n\s*\n', '\n\n', texto_final)
        texto_final = re.sub(r'[ \t]+', ' ', texto_final)
        texto_final = texto_final.strip()
        
        return texto_final
        
    except Exception as e:
        logger.error(f"Error convirtiendo HTML a texto: {str(e)}")
        return strip_tags(contenido_html) if contenido_html else ""


def generar_texto_acta_formateado(acta_portal):
    """
    Genera el contenido de texto formateado completo de un acta
    
    Args:
        acta_portal: Instancia de ActaMunicipal
        
    Returns:
        str: Contenido completo de la acta en texto formateado
    """
    try:
        contenido_texto = f"""
{'=' * 80}
ACTA DE SESIÓN MUNICIPAL
MUNICIPIO DE PASTAZA - ECUADOR
{'=' * 80}

INFORMACIÓN GENERAL:
{'-' * 40}
• Número de Acta: {acta_portal.numero_acta}
• Título: {acta_portal.titulo}
• Fecha de Sesión: {acta_portal.fecha_sesion.strftime('%d de %B de %Y')}
• Tipo de Sesión: {acta_portal.tipo_sesion.nombre if acta_portal.tipo_sesion else 'No especificado'}
• Fecha de Publicación: {acta_portal.fecha_publicacion.strftime('%d de %B de %Y') if acta_portal.fecha_publicacion else 'No disponible'}

DATOS DE LA SESIÓN:
{'-' * 40}
• Presidente: {acta_portal.presidente or 'No especificado'}
• Secretario: {acta_portal.secretario.get_full_name() if acta_portal.secretario else 'No especificado'}
• Estado: {acta_portal.estado.nombre if acta_portal.estado else 'No especificado'}

RESUMEN EJECUTIVO:
{'-' * 40}
{acta_portal.resumen or 'Sin resumen disponible'}

ORDEN DEL DÍA:
{'-' * 40}
{html_a_texto_formateado(acta_portal.orden_del_dia) if acta_portal.orden_del_dia else 'Sin orden del día especificado'}

DESARROLLO DE LA SESIÓN:
{'-' * 40}
{html_a_texto_formateado(acta_portal.contenido) if acta_portal.contenido else 'Sin contenido disponible'}

ACUERDOS Y RESOLUCIONES:
{'-' * 40}
{html_a_texto_formateado(acta_portal.acuerdos) if acta_portal.acuerdos else 'Sin acuerdos registrados'}

PARTICIPANTES:
{'-' * 40}
• Asistentes: {acta_portal.asistentes or 'No especificado'}

INFORMACIÓN ADICIONAL:
{'-' * 40}
• Palabras Clave: {acta_portal.palabras_clave or 'No especificadas'}
• Observaciones: {html_a_texto_formateado(acta_portal.observaciones) if acta_portal.observaciones else 'Sin observaciones'}

{'=' * 80}
Documento generado automáticamente por el Sistema de Actas Municipales
Municipio de Pastaza - Ecuador
Fecha de generación: {acta_portal.fecha_publicacion.strftime('%d de %B de %Y a las %H:%M:%S') if acta_portal.fecha_publicacion else 'No disponible'}
{'=' * 80}
        """.strip()
        
        return contenido_texto
        
    except Exception as e:
        logger.error(f"Error generando texto formateado del acta: {str(e)}")
        return f"Error al generar el contenido del acta: {str(e)}"


def generar_html_acta_limpio(acta_portal):
    """
    Genera HTML limpio y bien formateado para la visualización del acta
    
    Args:
        acta_portal: Instancia de ActaMunicipal
        
    Returns:
        str: HTML limpio para visualización
    """
    try:
        # Limpiar contenidos HTML
        contenido_limpio = limpiar_contenido_html(acta_portal.contenido) if acta_portal.contenido else 'Sin contenido disponible'
        orden_dia_limpio = limpiar_contenido_html(acta_portal.orden_del_dia) if acta_portal.orden_del_dia else 'Sin orden del día'
        acuerdos_limpio = limpiar_contenido_html(acta_portal.acuerdos) if acta_portal.acuerdos else 'Sin acuerdos'
        observaciones_limpio = limpiar_contenido_html(acta_portal.observaciones) if acta_portal.observaciones else 'Sin observaciones'
        
        return {
            'contenido': contenido_limpio,
            'orden_del_dia': orden_dia_limpio,
            'acuerdos': acuerdos_limpio,
            'observaciones': observaciones_limpio,
        }
        
    except Exception as e:
        logger.error(f"Error generando HTML limpio: {str(e)}")
        return {
            'contenido': 'Error al procesar contenido',
            'orden_del_dia': 'Error al procesar orden del día',
            'acuerdos': 'Error al procesar acuerdos',
            'observaciones': 'Error al procesar observaciones',
        }


def validar_contenido_acta(acta_portal):
    """
    Valida que el acta tenga contenido mínimo necesario
    
    Args:
        acta_portal: Instancia de ActaMunicipal
        
    Returns:
        dict: Resultado de validación con errores si los hay
    """
    errores = []
    advertencias = []
    
    # Validaciones básicas
    if not acta_portal.titulo:
        errores.append("Título del acta requerido")
    
    if not acta_portal.numero_acta:
        errores.append("Número del acta requerido")
        
    if not acta_portal.fecha_sesion:
        errores.append("Fecha de sesión requerida")
    
    # Validaciones de contenido
    if not acta_portal.contenido or len(strip_tags(acta_portal.contenido).strip()) < 50:
        advertencias.append("Contenido del acta muy corto o vacío")
    
    if not acta_portal.resumen or len(acta_portal.resumen.strip()) < 20:
        advertencias.append("Resumen del acta muy corto o vacío")
        
    return {
        'valida': len(errores) == 0,
        'errores': errores,
        'advertencias': advertencias
    }