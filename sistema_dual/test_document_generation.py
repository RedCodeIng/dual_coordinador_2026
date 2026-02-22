import os
import sys
from datetime import datetime
import json

# Add current folder (sistema_dual) to Python path so absolute imports work
sys.path.append(os.path.dirname(__file__))

from src.utils.pdf_generator_docx import generate_pdf_from_docx
from src.utils.pdf_generator_images import create_percentage_donut

def test_generate_anexo_51():
    print("Test: Generando Anexo 5.1...")
    
    # Dummy Context matching what doc_generator expects
    context_51 = {
        "nombre_proyecto": "PROYECTO MOCK DUAL",
        "unidad_economica": "CODECRAFTERS INC S.A. DE C.V.",
        "programa_educativo": "INGENIERÍA EN SISTEMAS COMPUTACIONALES",
        "num_estudiantes": "1", 
        "num_mentores_ue": "1",
        "num_mentores_academicos": "1",
        "periodos_vigencia": "Enero 2026 - Agosto 2026",
        "descripcion_proyecto": "Desarrollo de una plataforma web en React y Node.js para la gestión de inventarios y logística interna.",
        "horas_semanales": "40",
        "mentor_ue": "Ing. Carlos Mendoza (Líder Técnico)",
        "mentor_ie": "Mtro. Luis Gómez (Docente Asignado)",
        "fecha_generacion": datetime.now().strftime('%d/%m/%Y'),
        "competencias_list": [
            {"competencia": "Desarrollo Frontend con React", "asignatura": "Programación Web"},
            {"competencia": "Diseño de APIs REST", "asignatura": "Taller de Ingeniería de Software"}
        ],
        "actividades_list": [
            {"actividad": "Crear componentes de React", "horas": "80", "evidencia": "Repositorio Git", "lugar": "Home Office", "ponderacion": "50.0%"},
            {"actividad": "Conectar endpoints Node.js", "horas": "40", "evidencia": "Postman Collection", "lugar": "Oficina", "ponderacion": "50.0%"}
        ]
    }
    
    template_path = os.path.join(os.path.dirname(__file__), "src", "templates", "docs", "Anexo_5.1_Plan_de_Formacion.docx")
    output_path = os.path.join(os.path.dirname(__file__), "test_dummy_Anexo_5.1.pdf") # coordinator generates pdfs usually, lets try pdf
    
    success, msg = generate_pdf_from_docx("Anexo_5.1_Plan_de_Formacion.docx", context_51, output_path, template_path=template_path, to_pdf=False)
    if success:
         print(f"✅ Anexo 5.1 generado con éxito en: {output_path.replace('.pdf', '.docx')}")
    else:
         print(f"❌ Error al generar Anexo 5.1: {msg}")

def test_generate_anexo_54():
    print("\nTest: Generando Anexo 5.4...")
    
    # Create Donut Chart
    chart_path = os.path.join(os.path.dirname(__file__), "tmp_dummy_chart.png")
    create_percentage_donut(85, chart_path)
    
    context_54 = {
        "numero_reporte": 1,
        "fechas_periodo": "Enero 2026",
        "nombre_proyecto": "Plataforma de Inventarios TESE",
        "empresa": "Tech Corp SA de CV",
        "institucion_educativa": "Tecnológico de Estudios Superiores de Ecatepec",
        "carrera": "Ingeniería en Sistemas Computacionales",
        "nombre_alumno": "Juan Pérez López",
        "telefono_alumno": "55 8765 4321",
        "mentor_ue": "Ing. Sofía Martínez",
        "telefono_mentorue": "55 1234 5678",
        "mentor_ie": "Mtro. Luis Gómez",
        "telefono_mentorie": "55 9876 5432",
        "fecha_elaboracion": datetime.now().strftime("%d/%m/%Y"),
        "grafica_promedio": f"IMAGE_PATH:{chart_path}",
        "lista_competencias": [
            {
                "numero_consecutivo": 1, 
                "competencia_desarrollada": "Desarrollo Frontend", 
                "asignaturas_cubre": "Desarrollo Web",
                "conocimientos_teoricos": "Principios de React, Virtual DOM, Hooks, Estado Global con Redux y Context API.",
                "descripcion_actividades": "Se desarrollaron componentes reutilizables para el panel de control, aplicando estilos CSS Modules y Tailwind. Se integró la paleta de colores oficial de la empresa."
            },
            {
                "numero_consecutivo": 2, 
                "competencia_desarrollada": "Diseño de Base de Datos", 
                "asignaturas_cubre": "Bases de Datos Avanzadas",
                "conocimientos_teoricos": "Normalización SQL, Índices y Optimizaciones en PostgreSQL, Migraciones con Prisma ORM.",
                "descripcion_actividades": "Se diseñó el esquema relacional para los productos y envíos. Se crearon los scripts de migración y se pobló la base de datos con información de prueba."
            }
        ],
        "evaluaciones": [
            {
               "competencia_alcanzada": "Desarrollo Frontend",
               "firma_y_fecha": f"Ing. Sofía Martínez\n{datetime.now().strftime('%d/%m/%Y')}",
               "actividades": [
                   {"descripcion_actividad": "Crear UI con React", "evidencia": "GitHub Repo", "horas": 40, "p0": "", "p70": "", "p80": "", "p90": "X", "p100": "", "rec_ie": "", "rec_ue": ""},
                   {"descripcion_actividad": "Integrar API REST", "evidencia": "Insomnia Export", "horas": 20, "p0": "", "p70": "", "p80": "X", "p90": "", "p100": "", "rec_ie": "", "rec_ue": ""}
               ]
            }
        ]
    }
    
    template_path = os.path.join(os.path.dirname(__file__), "src", "templates", "docs", "Anexo_5.4_Reporte_de_Actividades.docx")
    
    import copy
    
    # Generate DOCX
    output_path_docx = os.path.join(os.path.dirname(__file__), "test_dummy_Anexo_5.4_raw.pdf")
    success_docx, msg_docx = generate_pdf_from_docx("Anexo_5.4_Reporte_de_Actividades.docx", copy.deepcopy(context_54), output_path_docx, template_path=template_path, to_pdf=False)
    if success_docx:
         print(f"✅ Anexo 5.4 (DOCX) generado con éxito en: {output_path_docx.replace('.pdf', '.docx')}")
    else:
         print(f"❌ Error al generar Anexo 5.4 (DOCX): {msg_docx}")
         
    # Generate PDF
    output_path_pdf = os.path.join(os.path.dirname(__file__), "test_dummy_Anexo_5.4.pdf")
    success_pdf, msg_pdf = generate_pdf_from_docx("Anexo_5.4_Reporte_de_Actividades.docx", copy.deepcopy(context_54), output_path_pdf, template_path=template_path, to_pdf=True)
    if success_pdf:
         print(f"✅ Anexo 5.4 (PDF) generado con éxito en: {output_path_pdf}")
    else:
         print(f"❌ Error al generar Anexo 5.4 (PDF): {msg_pdf}")

if __name__ == "__main__":
    test_generate_anexo_51()
    test_generate_anexo_54()
