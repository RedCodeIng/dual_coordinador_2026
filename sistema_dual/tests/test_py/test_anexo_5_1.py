import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.docs_generator import generate_document

def test_anexo_5_1():
    template_name = "Anexo_5.1_Plan_de_Formacion.docx"
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'output'))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, f"Generado_{template_name}")
    
    # Datos de prueba simulando un caso real
    context = {
        # Datos Generales
        "nombre_proyecto": "Implementación de Sistema ERP",
        "unidad_economica": "Tech Solutions S.A. de C.V.",
        "programa_educativo": "Ingeniería en Desarrollo de Software",
        "num_estudiantes": "1",
        "num_mentores_ue": "1",
        "num_mentores_academicos": "1",
        "periodos_vigencia": "Enero - abril 2024",
        "descripcion_proyecto": "Desarrollo e implementación de módulos de inventario y facturación para el sistema ERP interno de la empresa.",
        "horas_semanales": "30",
        "dia_visita": "Viernes",
        
        # Tabla 1: Competencias y Asignaturas
        "competencias_list": [
            {"competencia": "Desarrollar aplicaciones web", "asignatura": "Programación Web"},
            {"competencia": "Diseñar bases de datos relacionales", "asignatura": "Base de Datos"},
            {"competencia": "Gestionar proyectos de software", "asignatura": "Administración de Proyectos"}
        ],
        
        # Tabla 2: Actividades
        "actividades_list": [
            {
                "actividad": "Análisis de requerimientos",
                "horas": "20",
                "evidencia": "Documento de alcance",
                "lugar": "Oficina Central",
                "ponderacion": "10%"
            },
            {
                "actividad": "Diseño de base de datos",
                "horas": "40",
                "evidencia": "Diagrama E-R",
                "lugar": "Oficina Central",
                "ponderacion": "20%"
            },
            {
                "actividad": "Codificación de módulos",
                "horas": "100",
                "evidencia": "Código fuente en Git",
                "lugar": "Oficina Central",
                "ponderacion": "50%"
            },
            {
                "actividad": "Pruebas unitarias",
                "horas": "40",
                "evidencia": "Reporte de pruebas",
                "lugar": "Oficina Central",
                "ponderacion": "20%"
            }
        ]
    }
    
    print(f"Generando {template_name} con datos de prueba...")
    success, message = generate_document(template_name, output_path, context)
    
    if success:
        print(f"✅ Documento generado exitosamente.")
        print(f"Archivo guardado en: {output_path}")
    else:
        print(f"❌ Error al generar documento: {message}")

if __name__ == "__main__":
    test_anexo_5_1()
