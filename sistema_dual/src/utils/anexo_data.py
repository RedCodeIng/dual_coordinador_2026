from src.db_connection import get_supabase_client
from datetime import datetime

def get_anexo_5_1_data(student_id):
    """
    Recupera y formatea los datos necesarios para el Anexo 5.1
    basado en el ID del alumno.
    """
    supabase = get_supabase_client()
    
    # 1. Recuperar Alumno y Carrera
    res_alumno = supabase.table("alumnos").select("*, carreras(nombre)").eq("id", student_id).single().execute()
    alumno = res_alumno.data
    
    if not alumno:
        return None, "Alumno no encontrado"

    # 2. Recuperar Proyecto Dual (del periodo activo o el más reciente)
    res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", student_id).order("created_at", desc=True).limit(1).execute()
    
    if not res_proj.data:
        return None, "El alumno no tiene un proyecto dual registrado."
    
    proyecto = res_proj.data[0]
    ue = proyecto.get("unidades_economicas", {}) or {}
    mentor_ue_data = proyecto.get("mentores_ue", {}) or {}
    mentor_ie_data = proyecto.get("maestros", {}) or {}
    
    # 3. Recuperar Inscripciones (Asignaturas)
    res_insc = supabase.table("inscripciones_asignaturas").select("*, asignaturas(id, nombre, clave_asignatura)").eq("alumno_id", student_id).execute()
    inscripciones = res_insc.data
    
    # 4. Construir Listas de Competencias y Actividades
    competencias_list = []
    actividades_list = []
    
    for insc in inscripciones:
        asig = insc["asignaturas"]
        asig_id = asig["id"]
        asig_nombre = asig["nombre"]
        
        # Obtener Competencias de esta Asignatura
        res_comp = supabase.table("asignatura_competencias").select("*").eq("asignatura_id", asig_id).order("numero_competencia").execute()
        comps = res_comp.data
        
        for comp in comps:
            # Tabla 1: Competencia + Asignatura
            competencias_list.append({
                "competencia": comp["descripcion_competencia"],
                "asignatura": asig_nombre
            })
            
            # Obtener Actividades de esta Competencia
            # Usando la NUEVA tabla actividades_aprendizaje
            res_act = supabase.table("actividades_aprendizaje").select("*").eq("competencia_id", comp["id"]).execute()
            acts = res_act.data
            
            for act in acts:
                # Tabla 2: Detalles de Actividad
                # Formato de ponderación: Asegurar que se vea bonito (ej. "20%")
                pond = float(act["ponderacion"]) if act["ponderacion"] else 0
                
                actividades_list.append({
                    "actividad": act["descripcion_actividad"],
                    "horas": str(act["horas_dedicacion"]),
                    "evidencia": act["evidencia"],
                    "lugar": act["lugar"],
                    "ponderacion": f"{pond:.1f}%"
                })

    # 5. Formatear Contexto Final
    # Algunos campos calculados o estáticos por ahora
    fecha_inicio = datetime.fromisoformat(proyecto["fecha_inicio_convenio"]).strftime("%B %Y") if proyecto.get("fecha_inicio_convenio") else "Inicio"
    fecha_fin = datetime.fromisoformat(proyecto["fecha_fin_convenio"]).strftime("%B %Y") if proyecto.get("fecha_fin_convenio") else "Fin"
    
    context = {
        "nombre_proyecto": proyecto.get("nombre_proyecto", ""),
        "unidad_economica": ue.get("nombre_comercial", ""),
        "programa_educativo": alumno.get("carreras", {}).get("nombre", ""),
        # Estos campos suelen ser inputs manuales o estáticos del periodo, 
        # por ahora los dejamos con placeholders o valores por defecto.
        "num_estudiantes": "1", 
        "num_mentores_ue": "1",
        "num_mentores_academicos": "1",
        "periodos_vigencia": f"{fecha_inicio} - {fecha_fin}",
        "descripcion_proyecto": proyecto.get("descripcion_proyecto", ""),
        "horas_semanales": "40", # Valor estándar DUAL, podría ser campo en BD
        # Nuevas etiquetas
        "mentor_ue": mentor_ue_data.get("nombre_completo", "No Asignado"),
        "mentor_ie": mentor_ie_data.get("nombre_completo", "No Asignado"),
        
        # Nuevas etiquetas
        "mentor_ue": mentor_ue_data.get("nombre_completo", "No Asignado"),
        "mentor_ie": mentor_ie_data.get("nombre_completo", "No Asignado"),
        "fecha_generacion": datetime.today().strftime('%d/%m/%Y'),
        
        # Tablas dinámicas (Listas para docxtpl)
        "competencias_list": competencias_list,
        "actividades_list": actividades_list
    }
    
    return context, None

def get_anexo_5_4_data(student_id):
    """
    Recupera y formatea los datos necesarios para el Anexo 5.4
    basado en el ID del alumno.
    """
    supabase = get_supabase_client()
    
    # 1. Recuperar Alumno y Carrera
    res_alumno = supabase.table("alumnos").select("*, carreras(nombre)").eq("id", student_id).single().execute()
    alumno = res_alumno.data
    if not alumno: return None, "Alumno no encontrado"

    # 2. Recuperar Proyecto Dual
    res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*), periodos(*)").eq("alumno_id", student_id).order("created_at", desc=True).limit(1).execute()
    if not res_proj.data: return None, "El alumno no tiene un proyecto dual registrado."
    
    proyecto = res_proj.data[0]
    ue = proyecto.get("unidades_economicas", {}) or {}
    mentor_ue = proyecto.get("mentores_ue", {}) or {}
    mentor_ie = proyecto.get("maestros", {}) or {}
    periodo = proyecto.get("periodos", {}) or {}
    
    import os
    from src.utils.pdf_generator_images import create_percentage_donut
    import tempfile
    
    # Generar gráfica temporal de logro
    final_grade = 0.0
    c_ue = proyecto.get('calificacion_ue')
    c_ie = proyecto.get('calificacion_ie')
    if c_ue is not None and c_ie is not None:
         final_grade = (float(c_ue) * 0.7) + (float(c_ie) * 0.3)
    
    chart_path = os.path.join(tempfile.gettempdir(), f"chart_54_{student_id}.png")
    # Donut expects percentage 0-100
    percentage = min(100, max(0, int(final_grade * 10)))
    create_percentage_donut(percentage, chart_path)
    
    # 3. Recuperar Inscripciones y Competencias
    res_insc = supabase.table("inscripciones_asignaturas").select("*, asignaturas(id, nombre, clave_asignatura)").eq("alumno_id", student_id).execute()
    inscripciones = res_insc.data
    
    lista_competencias = []
    lista_actividades = [] # For evaluation table
    
    consecutivo = 1
    for insc in inscripciones:
        asig = insc["asignaturas"]
        # Obtener Competencias
        res_comp = supabase.table("asignatura_competencias").select("*").eq("asignatura_id", asig["id"]).order("numero_competencia").execute()
        for comp in res_comp.data:
            # Obtener Actividades para marco/descripcion
            res_act = supabase.table("actividades_aprendizaje").select("*").eq("competencia_id", comp["id"]).execute()
            
            conocimientos = "\\n".join([f"- {a['descripcion_actividad']}" for a in res_act.data])
            desc_acts = "\\n".join([f"- Evidencia: {a['evidencia']} ({a['horas_dedicacion']}h)" for a in res_act.data])
            
            lista_competencias.append({
                "numero_consecutivo": consecutivo,
                "competencia_desarrollada": comp["descripcion_competencia"],
                "asignaturas_cubre": asig["nombre"],
                "conocimientos_teoricos": conocimientos if conocimientos else "Pendiente de registro",
                "descripcion_actividades": desc_acts if desc_acts else "Pendiente de registro"
            })
            
            # Formatear actividades para la tabla de evaluación
            acts = []
            for a in res_act.data:
                 acts.append({
                     "descripcion_actividad": a["descripcion_actividad"],
                     "evidencia": a["evidencia"],
                     "horas": a["horas_dedicacion"],
                     "p0": "", "p70": "", "p80": "", "p90": "X", "p100": "", # Mocking evaluation marks for now
                     "rec_ie": "", "rec_ue": ""
                 })
                 
            lista_actividades.append({
                "competencia_alcanzada": comp["descripcion_competencia"],
                "firma_y_fecha": f"{mentor_ue.get('nombre_completo', 'Mentor UE')}\\n{datetime.today().strftime('%d/%m/%Y')}",
                "actividades": acts
            })
            
            consecutivo += 1
            
    # Periodo text
    p_inicio = datetime.fromisoformat(periodo.get("fecha_inicio", "2026-01-01")).strftime("%B %Y")
    p_fin = datetime.fromisoformat(periodo.get("fecha_fin", "2026-06-01")).strftime("%B %Y")
            
    context = {
        "numero_reporte": 1,
        "fechas_periodo": f"{p_inicio} - {p_fin}",
        "nombre_proyecto": proyecto.get("nombre_proyecto", "No Definido"),
        "empresa": ue.get("nombre_comercial", "No Definida"),
        "institucion_educativa": "Tecnológico de Estudios Superiores de Ecatepec",
        "carrera": alumno.get("carreras", {}).get("nombre", ""),
        "nombre_alumno": f"{alumno['nombre']} {alumno['ap_paterno']}",
        "telefono_alumno": alumno.get("telefono", "No Registrado"),
        "mentor_ue": mentor_ue.get("nombre_completo", "No Asignado"),
        "telefono_mentorue": mentor_ue.get("telefono", "No Registrado"),
        "mentor_ie": mentor_ie.get("nombre_completo", "No Asignado"),
        "telefono_mentorie": mentor_ie.get("telefono", "No Registrado"),
        "fecha_elaboracion": datetime.today().strftime('%d/%m/%Y'),
        "grafica_promedio": f"IMAGE_PATH:{chart_path}" if os.path.exists(chart_path) else "",
        "lista_competencias": lista_competencias,
        "evaluaciones": lista_actividades
    }
    
    return context, None
