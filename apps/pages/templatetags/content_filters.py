from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def safe_html_content(value):
    """
    Filtro para renderizar contenido HTML de forma segura.
    Mantiene las etiquetas de formato básico y elimina las potencialmente peligrosas.
    """
    if not value:
        return ""
    
    # Lista de etiquetas HTML permitidas (seguras para contenido de actas)
    allowed_tags = [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',  # Títulos
        'p', 'br',  # Párrafos y saltos
        'strong', 'b', 'em', 'i', 'u',  # Formato de texto
        'ul', 'ol', 'li',  # Listas
        'table', 'thead', 'tbody', 'tr', 'th', 'td',  # Tablas
        'blockquote',  # Citas
        'hr',  # Líneas horizontales
        'div', 'span',  # Contenedores básicos
    ]
    
    # Patrón para encontrar etiquetas HTML
    tag_pattern = r'<(/?)([a-zA-Z]+)([^>]*)>'
    
    def clean_tag(match):
        closing = match.group(1)
        tag_name = match.group(2).lower()
        attributes = match.group(3)
        
        # Solo permitir etiquetas de la lista
        if tag_name in allowed_tags:
            # Para etiquetas permitidas, limpiar atributos peligrosos
            if attributes:
                # Eliminar atributos javascript y eventos
                attributes = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', '', attributes, flags=re.IGNORECASE)
                attributes = re.sub(r'javascript\s*:', '', attributes, flags=re.IGNORECASE)
                # Mantener solo atributos básicos como class, id, style (básico)
                safe_attrs = re.findall(r'(class|id|style|align|width|height)\s*=\s*["\'][^"\']*["\']', attributes, flags=re.IGNORECASE)
                attributes = ' ' + ' '.join(safe_attrs) if safe_attrs else ''
            
            return f'<{closing}{tag_name}{attributes}>'
        else:
            # Etiquetas no permitidas se eliminan pero se mantiene el contenido
            return ''
    
    # Limpiar las etiquetas
    cleaned_html = re.sub(tag_pattern, clean_tag, value)
    
    # Limpiar espacios múltiples y saltos de línea excesivos
    cleaned_html = re.sub(r'\n\s*\n', '\n', cleaned_html)
    cleaned_html = re.sub(r'<br\s*/?>\s*<br\s*/?>', '<br><br>', cleaned_html, flags=re.IGNORECASE)
    
    return mark_safe(cleaned_html)


@register.filter  
def strip_html_tags(value):
    """
    Filtro para eliminar completamente todas las etiquetas HTML.
    Útil para mostrar solo texto plano.
    """
    if not value:
        return ""
    
    # Eliminar todas las etiquetas HTML
    clean_text = re.sub(r'<[^>]+>', '', value)
    # Limpiar espacios múltiples
    clean_text = re.sub(r'\s+', ' ', clean_text)
    # Limpiar al inicio y final
    clean_text = clean_text.strip()
    
    return clean_text