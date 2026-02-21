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
