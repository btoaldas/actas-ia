from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
from .models import ActaMunicipal
import os

@receiver(pre_save, sender=ActaMunicipal)
def generar_estructura_directorios(sender, instance, **kwargs):
    """
    Genera automáticamente la estructura de directorios cuando se crea/actualiza un acta
    """
    if instance.fecha_sesion and not instance.archivo_pdf:
        # Solo crear estructura si no tiene PDF asignado
        fecha = instance.fecha_sesion
        pdf_dir = os.path.join(
            settings.MEDIA_ROOT,
            'repositorio',
            str(fecha.year),
            f'{fecha.month:02d}',
            f'{fecha.day:02d}',
            f'{fecha.hour:02d}'
        )
        
        # Crear directorios si no existen
        try:
            os.makedirs(pdf_dir, exist_ok=True)
            print(f"📁 Directorio creado: {pdf_dir}")
        except Exception as e:
            print(f"❌ Error creando directorio: {e}")

@receiver(post_save, sender=ActaMunicipal)
def acta_publicada_signal(sender, instance, created, **kwargs):
    """
    Ejecuta acciones automáticas cuando se publica una nueva acta
    """
    if created:
        print(f"📋 Nueva acta creada: {instance.numero_acta}")
        
        # Si el acta se crea ya en estado publicado, generar PDF automáticamente
        if instance.estado and instance.estado.nombre == 'publicada' and not instance.archivo_pdf:
            from django.core.management import call_command
            try:
                # Llamar al comando para generar PDF solo para esta acta
                print(f"🔄 Generando PDF automáticamente para {instance.numero_acta}")
                # Aquí podrías llamar a una función específica para generar el PDF
                generar_pdf_para_acta(instance)
            except Exception as e:
                print(f"❌ Error generando PDF automático: {e}")
    
    elif hasattr(instance, '_state') and instance._state.db:
        # Verificar si cambió a estado publicado
        try:
            acta_anterior = ActaMunicipal.objects.get(pk=instance.pk)
            if (acta_anterior.estado.nombre != 'publicada' and 
                instance.estado and instance.estado.nombre == 'publicada' and 
                not instance.archivo_pdf):
                print(f"📝 Acta {instance.numero_acta} cambió a estado publicado")
                # Generar PDF automáticamente
                generar_pdf_para_acta(instance)
        except ActaMunicipal.DoesNotExist:
            pass
        except Exception as e:
            print(f"❌ Error en signal de publicación: {e}")

def generar_pdf_para_acta(acta):
    """
    Genera PDF específico para una sola acta
    """
    try:
        from datetime import datetime
        
        # Generar contenido del PDF
        pdf_content = generar_contenido_pdf_acta(acta)
        
        # Crear estructura de directorios
        fecha = acta.fecha_sesion or datetime.now()
        pdf_dir = os.path.join(
            settings.MEDIA_ROOT,
            'repositorio',
            str(fecha.year),
            f'{fecha.month:02d}',
            f'{fecha.day:02d}',
            f'{fecha.hour:02d}'
        )
        
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Crear archivo PDF
        filename = f'{acta.numero_acta}.pdf'
        pdf_path = os.path.join(pdf_dir, filename)
        
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(pdf_content)
        
        # Actualizar el modelo
        relative_path = f'repositorio/{fecha.year}/{fecha.month:02d}/{fecha.day:02d}/{fecha.hour:02d}/{filename}'
        acta.archivo_pdf = relative_path
        acta.save(update_fields=['archivo_pdf'])
        
        print(f"✅ PDF generado automáticamente: {acta.numero_acta}")
        
    except Exception as e:
        print(f"❌ Error generando PDF para {acta.numero_acta}: {e}")

def generar_contenido_pdf_acta(acta):
    """
    Genera el contenido del PDF para una acta específica
    """
    pdf_content = f'''%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources << /Font << /F1 5 0 R >> >>
>>
endobj

4 0 obj
<<
/Length 1500
>>
stream
BT
/F1 16 Tf
50 750 Td
(MUNICIPIO DE PASTAZA) Tj
0 -30 Td
/F1 14 Tf
(ACTA DE SESION MUNICIPAL) Tj
0 -40 Td
/F1 12 Tf
(Numero: {acta.numero_acta}) Tj
0 -20 Td
(Fecha: {acta.fecha_sesion.strftime("%d/%m/%Y %H:%M") if acta.fecha_sesion else "No definida"}) Tj
0 -20 Td
(Tipo: {acta.tipo_sesion.get_nombre_display() if acta.tipo_sesion else "No definido"}) Tj
0 -20 Td
(Estado: {acta.estado.get_nombre_display() if acta.estado else "No definido"}) Tj
0 -40 Td
/F1 14 Tf
(TITULO: {acta.titulo[:50]}) Tj
0 -30 Td
/F1 10 Tf
(Presidente: {acta.presidente}) Tj
0 -15 Td
(Secretario: {acta.secretario.get_full_name() if acta.secretario else "No asignado"}) Tj
0 -30 Td
/F1 12 Tf
(RESUMEN:) Tj
0 -20 Td
/F1 10 Tf
({acta.resumen[:200] if acta.resumen else "Sin resumen disponible"}) Tj
0 -30 Td
/F1 8 Tf
(Documento generado automaticamente) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000109 00000 n 
0000000203 00000 n 
0000001800 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
1870
%%EOF'''
    
    return pdf_content
