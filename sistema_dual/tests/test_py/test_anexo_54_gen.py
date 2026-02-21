import os
from datetime import datetime
from src.utils.pdf_generator_images import create_percentage_donut
from src.utils.pdf_generator_docx import generate_pdf_from_docx

def test_generation():
    # 1. Build mock evaluations array first to calculate the correct percentage
    evaluaciones = [
        {
            "competencia_alcanzada": "Desarrollo Frontend",
            "firma_y_fecha": "Carlos Mendoza\n20/10/2026",
            "actividades": [
                {
                    "descripcion_actividad": "Crear UI de Login",
                    "evidencia": "Repositorio Git",
                    "horas": 15,
                    "p0": "", "p70": "", "p80": "", "p90": "X", "p100": "",
                    "rec_ie": "", "rec_ue": ""
                },
                {
                    "descripcion_actividad": "Consumir API REST",
                    "evidencia": "Código Punteado",
                    "horas": 25,
                    "p0": "", "p70": "", "p80": "X", "p90": "", "p100": "",
                    "rec_ie": "", "rec_ue": ""
                }
            ]
        },
        {
            "competencia_alcanzada": "Desarrollo Backend",
            "firma_y_fecha": "Carlos Mendoza\n20/10/2026",
            "actividades": [
                {
                    "descripcion_actividad": "Diseñar Esquema SQL",
                    "evidencia": "Diagrama E-R",
                    "horas": 10,
                    "p0": "", "p70": "", "p80": "", "p90": "", "p100": "X",
                    "rec_ie": "", "rec_ue": ""
                }
            ]
        }
    ]
    
    # 2. Calculate dynamic average
    total_val = 0
    total_items = 0
    for ev in evaluaciones:
        for act in ev["actividades"]:
            if act.get("p100"): total_val += 100
            elif act.get("p90"): total_val += 90
            elif act.get("p80"): total_val += 80
            elif act.get("p70"): total_val += 70
            total_items += 1
            
    promedio = int(total_val / total_items) if total_items > 0 else 0

    # 3. Generate chart
    chart_path = "test_chart.png"
    create_percentage_donut(promedio, chart_path)
    
    # 4. Build mock context
    context = {
        "numero_reporte": 1,
        "fechas_periodo": "Octubre 2026",
        "nombre_proyecto": "Sistema Web DUAL",
        "empresa": "TechCorp SA de CV",
        "institucion_educativa": "Tecnológico de Estudios Superiores de Ecatepec",
        "carrera": "Ingeniería en Sistemas Computacionales",
        "nombre_alumno": "Juan Pérez",
        "telefono_alumno": "55 1234 5678",
        "mentor_ue": "Ing. Carlos Mendoza",
        "telefono_mentorue": "55 8765 4321",
        "mentor_ie": "Mtro. Luis Vargas",
        "telefono_mentorie": "55 9999 8888",
        "fecha_elaboracion": datetime.now().strftime("%d/%m/%Y"),
        "grafica_promedio": f"IMAGE_PATH:{chart_path}",
        "evaluaciones": evaluaciones
    }
    
    # Tabla 2
    context["lista_competencias"] = [
        {
            "numero_consecutivo": 1,
            "competencia_desarrollada": "Desarrollo Frontend",
            "asignaturas_cubre": "Ingeniería de Software",
            "conocimientos_teoricos": "Conceptos de UI/UX, manipulación del DOM, frameworks de JavaScript (React/Vue).",
            "descripcion_actividades": "Creación de vistas maestras y consumo de APIs."
        },
        {
            "numero_consecutivo": 2,
            "competencia_desarrollada": "Desarrollo Backend",
            "asignaturas_cubre": "Bases de Datos Avanzadas",
            "conocimientos_teoricos": "Principios REST, bases de datos relacionales, normalización y SQL.",
            "descripcion_actividades": "Diseño del modelo entidad-relación y programación de end-points."
        }
    ]
    

    
    template_path = os.path.join("src", "templates", "docs", "Anexo_5.4_Reporte_de_Actividades.docx")
    output_path = "Test_Anexo_5.4.pdf"
    
    print("Generating from template:", template_path)
    res, msg = generate_pdf_from_docx("Anexo_5.4_Reporte_de_Actividades.docx", context, output_path, template_path=template_path)
    print(msg)
    
if __name__ == "__main__":
    test_generation()
