from django.core.management.base import BaseCommand
from apps.pages.models import ActaMunicipal
from django.conf import settings
import os
from datetime import datetime
import random

class Command(BaseCommand):
    help = 'Generar PDFs de ejemplo para las actas municipales existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Generar PDFs para todas las actas',
        )

    def handle(self, *args, **options):
        self.stdout.write('📄 Generando PDFs de ejemplo para actas municipales...')
        
        # Obtener actas sin PDF o todas si se especifica --all
        if options['all']:
            actas = ActaMunicipal.objects.all()
        else:
            actas = ActaMunicipal.objects.filter(archivo_pdf='')
        
        if not actas.exists():
            self.stdout.write(self.style.WARNING('No hay actas para procesar'))
            return
        
        self.stdout.write(f'Procesando {actas.count()} actas...')
        
        for acta in actas:
            try:
                # Generar contenido del PDF
                pdf_content = self.generate_pdf_content(acta)
                
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
                
                # Crear directorios si no existen
                os.makedirs(pdf_dir, exist_ok=True)
                
                # Nombre del archivo
                filename = f'{acta.numero_acta}.pdf'
                pdf_path = os.path.join(pdf_dir, filename)
                
                # Escribir archivo PDF
                with open(pdf_path, 'w', encoding='utf-8') as f:
                    f.write(pdf_content)
                
                # Actualizar el modelo con la ruta relativa
                relative_path = f'repositorio/{fecha.year}/{fecha.month:02d}/{fecha.day:02d}/{fecha.hour:02d}/{filename}'
                acta.archivo_pdf = relative_path
                acta.save()
                
                self.stdout.write(f'✅ PDF creado: {acta.numero_acta}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error creando PDF para {acta.numero_acta}: {e}')
                )
        
        self.stdout.write(self.style.SUCCESS(f'🎉 Proceso completado! PDFs generados: {actas.count()}'))

    def generate_pdf_content(self, acta):
        """Genera contenido PDF realista para un acta municipal"""
        
        # Contenido base del PDF con formato básico
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
/Length 2000
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
(TITULO: {acta.titulo[:60]}) Tj
0 -30 Td
/F1 10 Tf
(Presidente: {acta.presidente}) Tj
0 -15 Td
(Secretario: {acta.secretario.get_full_name() if acta.secretario else "No asignado"}) Tj
0 -30 Td
/F1 12 Tf
(RESUMEN EJECUTIVO:) Tj
0 -20 Td
/F1 10 Tf
'''

        # Agregar resumen línea por línea
        if acta.resumen:
            resumen_lines = acta.resumen[:800].replace('\n', ' ').split('. ')
            for i, line in enumerate(resumen_lines[:8]):
                if line.strip():
                    pdf_content += f'({line.strip()[:70]}.) Tj\n0 -15 Td\n'
        
        pdf_content += '''
0 -20 Td
/F1 12 Tf
(ORDEN DEL DIA:) Tj
0 -20 Td
/F1 10 Tf
'''
        
        # Agregar orden del día o contenido genérico
        if acta.orden_del_dia:
            orden_lines = acta.orden_del_dia[:400].replace('\n', ' ').split('. ')
            for line in orden_lines[:5]:
                if line.strip():
                    pdf_content += f'(- {line.strip()[:60]}) Tj\n0 -15 Td\n'
        else:
            agenda_items = [
                "1. Verificacion del quorum",
                "2. Lectura y aprobacion del acta anterior", 
                "3. Informes de comisiones",
                "4. Asuntos varios",
                "5. Clausura de la sesion"
            ]
            for item in agenda_items:
                pdf_content += f'({item}) Tj\n0 -15 Td\n'
        
        pdf_content += '''
0 -30 Td
/F1 12 Tf
(PARTICIPANTES:) Tj
0 -20 Td
/F1 10 Tf
'''
        
        # Agregar participantes
        if acta.asistentes:
            participantes = acta.asistentes[:300].replace('\n', ', ')
            pdf_content += f'(Asistentes: {participantes[:70]}) Tj\n0 -15 Td\n'
        
        if acta.ausentes:
            ausentes = acta.ausentes[:200].replace('\n', ', ')
            pdf_content += f'(Ausentes: {ausentes[:70]}) Tj\n0 -15 Td\n'
        
        # Agregar información de IA si existe
        if acta.transcripcion_ia and acta.precision_ia:
            pdf_content += f'''
0 -20 Td
/F1 8 Tf
(Documento procesado con IA - Precision: {acta.precision_ia}%) Tj
'''
        
        # Cerrar el PDF
        pdf_content += '''
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
0000002300 00000 n 
trailer
<< /Size 6 /Root 1 0 R >>
startxref
2370
%%EOF'''
        
        return pdf_content
