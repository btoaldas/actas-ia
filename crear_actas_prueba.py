"""
Script para crear datos de prueba para el sistema de gestión de actas
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from gestion_actas.models import GestionActa, EstadoGestionActa
from django.contrib.auth.models import User

def crear_acta_prueba():
    """Crear un acta de prueba para el sistema de gestión"""
    
    print("🔧 Creando acta de prueba para gestión...")
    
    # Buscar un usuario para asignar como creador
    try:
        usuario = User.objects.filter(is_superuser=True).first()
        if not usuario:
            usuario = User.objects.first()
            
        if not usuario:
            print("❌ No hay usuarios en el sistema. Crear un usuario primero.")
            return
            
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        return
    
    # Obtener estado inicial
    try:
        estado_generada = EstadoGestionActa.objects.get(codigo='generada')
    except EstadoGestionActa.DoesNotExist:
        print("❌ Estados no encontrados. Ejecutar inicializar_gestion_actas.py primero.")
        return
    
    # Contenido HTML de ejemplo para el acta
    contenido_html_ejemplo = """
    <h1>ACTA DE SESIÓN ORDINARIA N° 001-2025</h1>
    
    <h2>I. INFORMACIÓN GENERAL</h2>
    <p><strong>Fecha:</strong> Lunes, 06 de enero de 2025</p>
    <p><strong>Hora de inicio:</strong> 09:00 AM</p>
    <p><strong>Lugar:</strong> Sala de Sesiones del Gobierno Municipal de Pastaza</p>
    <p><strong>Presidente de sesión:</strong> Sr. Alcalde Municipal</p>
    
    <h2>II. ASISTENCIA</h2>
    <p><strong>Presentes:</strong></p>
    <ul>
        <li>Sr. Alcalde Municipal - Presidente</li>
        <li>Concejal María González - Vicepresidenta</li>
        <li>Concejal Juan Pérez - Vocal</li>
        <li>Concejal Ana Rodríguez - Vocal</li>
        <li>Secretario Municipal - Dr. Carlos López</li>
    </ul>
    
    <p><strong>Ausentes justificados:</strong> Ninguno</p>
    
    <h2>III. ORDEN DEL DÍA</h2>
    <ol>
        <li>Verificación del quórum</li>
        <li>Lectura y aprobación del acta anterior</li>
        <li>Informe del Alcalde</li>
        <li>Aprobación del presupuesto municipal 2025</li>
        <li>Proyectos de ordenanzas municipales</li>
        <li>Varios</li>
    </ol>
    
    <h2>IV. DESARROLLO DE LA SESIÓN</h2>
    
    <h3>1. Verificación del quórum</h3>
    <p>El Sr. Alcalde verifica la asistencia y declara la existencia del quórum reglamentario 
    con la presencia de 5 miembros del Concejo Municipal.</p>
    
    <h3>2. Lectura y aprobación del acta anterior</h3>
    <p>Se procede a la lectura del acta de la sesión anterior. El Concejal Juan Pérez 
    solicita una corrección menor en el punto 3 del acta anterior. Se aprueba el acta 
    con la corrección solicitada por unanimidad.</p>
    
    <h3>3. Informe del Alcalde</h3>
    <p>El Sr. Alcalde presenta el informe mensual de actividades, destacando:</p>
    <ul>
        <li>Avance del proyecto de mejoramiento vial en 85%</li>
        <li>Inauguración del centro de salud comunitario</li>
        <li>Gestiones para el proyecto de agua potable</li>
        <li>Coordinaciones con el gobierno provincial para proyectos conjuntos</li>
    </ul>
    
    <h3>4. Aprobación del presupuesto municipal 2025</h3>
    <p>La Directora Financiera presenta el proyecto de presupuesto para el año 2025, 
    con un monto total de $2,850,000. Se detallan las partidas principales:</p>
    <ul>
        <li><strong>Gastos corrientes:</strong> $1,200,000 (42.1%)</li>
        <li><strong>Inversión pública:</strong> $1,400,000 (49.1%)</li>
        <li><strong>Deuda pública:</strong> $250,000 (8.8%)</li>
    </ul>
    
    <p>Después de la discusión correspondiente, se aprueba el presupuesto por unanimidad.</p>
    
    <h3>5. Proyectos de ordenanzas municipales</h3>
    <p>Se presentan para primer debate dos proyectos de ordenanzas:</p>
    <ol>
        <li><strong>Ordenanza de protección ambiental:</strong> Aprobada para primer debate</li>
        <li><strong>Ordenanza de comercio en vía pública:</strong> Se solicitan ajustes y se posterga</li>
    </ol>
    
    <h3>6. Varios</h3>
    <ul>
        <li>La Concejal Ana Rodríguez solicita información sobre el mantenimiento de parques</li>
        <li>El Concejal Juan Pérez propone crear una comisión para el seguimiento de obras</li>
        <li>Se programa sesión extraordinaria para el 15 de enero</li>
    </ul>
    
    <h2>V. RESOLUCIONES ADOPTADAS</h2>
    <ol>
        <li><strong>RESOLUCIÓN N° 001-2025:</strong> Aprobar el acta de la sesión anterior con las correcciones solicitadas.</li>
        <li><strong>RESOLUCIÓN N° 002-2025:</strong> Aprobar el presupuesto municipal para el año 2025 por un monto de $2,850,000.</li>
        <li><strong>RESOLUCIÓN N° 003-2025:</strong> Aprobar en primer debate la ordenanza de protección ambiental.</li>
        <li><strong>RESOLUCIÓN N° 004-2025:</strong> Convocar a sesión extraordinaria para el 15 de enero de 2025.</li>
    </ol>
    
    <h2>VI. CLAUSURA</h2>
    <p>No habiendo más asuntos que tratar, el Sr. Alcalde declara clausurada la sesión 
    siendo las 12:30 PM del mismo día.</p>
    
    <hr>
    
    <div style="margin-top: 40px;">
        <table style="width: 100%;">
            <tr>
                <td style="text-align: center; width: 50%;">
                    <strong>Sr. Alcalde Municipal</strong><br>
                    Presidente de Sesión<br><br>
                    _____________________
                </td>
                <td style="text-align: center; width: 50%;">
                    <strong>Dr. Carlos López</strong><br>
                    Secretario Municipal<br><br>
                    _____________________
                </td>
            </tr>
        </table>
    </div>
    """
    
    # Crear el acta
    try:
        acta = GestionActa.objects.create(
            contenido_editado=contenido_html_ejemplo.strip(),
            estado=estado_generada,
            usuario_editor=usuario,
            observaciones="Acta de prueba creada automáticamente para demostración del sistema de gestión.",
            cambios_realizados={
                "tipo_sesion": "ordinaria",
                "numero_acta": "001-2025",
                "duracion_sesion": "3.5 horas",
                "total_asistentes": 5,
                "resoluciones_aprobadas": 4,
                "creada_por_demo": True
            }
        )
        
        print(f"✅ Acta creada exitosamente:")
        print(f"   - ID: #{acta.pk}")
        print(f"   - Estado: {acta.estado.nombre}")
        print(f"   - Creador: {acta.usuario_editor.username}")
        print(f"   - Palabras aproximadas: {len(acta.contenido_editado.split())}")
        
        return acta
        
    except Exception as e:
        print(f"❌ Error creando acta: {e}")
        import traceback
        traceback.print_exc()
        return None


def crear_actas_adicionales():
    """Crear actas adicionales con diferentes estados"""
    
    print("\n🔧 Creando actas adicionales...")
    
    try:
        usuario = User.objects.filter(is_superuser=True).first() or User.objects.first()
        
        # Estados disponibles
        estados = {
            'en_edicion': EstadoGestionActa.objects.get(codigo='en_edicion'),
            'enviada_revision': EstadoGestionActa.objects.get(codigo='enviada_revision'),
            'aprobada': EstadoGestionActa.objects.get(codigo='aprobada'),
        }
        
        actas_adicionales = [
            {
                'titulo': 'Acta de Sesión Extraordinaria N° 002-2025 - Proyecto Vial',
                'estado': 'en_edicion',
                'contenido': '<h1>Acta de Sesión Extraordinaria</h1><p>Contenido en desarrollo...</p>'
            },
            {
                'titulo': 'Acta de Sesión Ordinaria N° 003-2025 - Presupuesto Participativo',
                'estado': 'enviada_revision',
                'contenido': '<h1>Presupuesto Participativo</h1><p>Sesión dedicada a la presentación de proyectos ciudadanos...</p>'
            },
            {
                'titulo': 'Acta de Sesión de Emergencia - Respuesta COVID-19',
                'estado': 'aprobada',
                'contenido': '<h1>Medidas de Emergencia Sanitaria</h1><p>Acta aprobada con medidas urgentes...</p>'
            }
        ]
        
        for data in actas_adicionales:
            acta = GestionActa.objects.create(
                contenido_editado=data['contenido'],
                estado=estados[data['estado']],
                usuario_editor=usuario,
                observaciones=f"Acta de ejemplo en estado {data['estado']}",
                cambios_realizados={'demo': True, 'estado_inicial': data['estado']}
            )
            
            print(f"   ✅ Acta #{acta.pk} -> {acta.estado.nombre}")
            
    except Exception as e:
        print(f"❌ Error creando actas adicionales: {e}")


if __name__ == "__main__":
    print("🚀 Creando datos de prueba para Gestión de Actas\n")
    
    try:
        # Verificar que los estados existen
        if not EstadoGestionActa.objects.exists():
            print("❌ No hay estados de gestión. Ejecutar inicializar_gestion_actas.py primero.")
            exit(1)
        
        # Crear acta principal
        acta_principal = crear_acta_prueba()
        
        if acta_principal:
            # Crear actas adicionales
            crear_actas_adicionales()
            
            print(f"\n🎉 ¡Datos de prueba creados exitosamente!")
            print(f"\n📋 Próximos pasos:")
            print(f"1. Acceder a http://localhost:8000/gestion-actas/")
            print(f"2. Ver el listado de actas disponibles")
            print(f"3. Abrir el editor de actas para la edición")
            print(f"4. Probar el flujo de revisión y aprobación")
        
    except Exception as e:
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()