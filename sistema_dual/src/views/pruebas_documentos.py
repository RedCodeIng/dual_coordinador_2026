import streamlit as st
import os
import random
from datetime import datetime
from src.db_connection import get_supabase_client
from src.utils.anexo_data import get_anexo_5_1_data
from src.utils.pdf_generator_docx import generate_pdf_from_docx
from src.utils.pdf_generator_images import create_percentage_donut

def get_random_eligible_student():
    supabase = get_supabase_client()
    # Find active projects with assignments
    res_proj = supabase.table("proyectos_dual").select("alumno_id, ue_id, mentor_ie_id").execute()
    if not res_proj.data:
        return None
    
    # Filter those that have an enterprise assigned
    eligible = [p["alumno_id"] for p in res_proj.data if p.get("ue_id")]
    if not eligible:
        # Fallback to any project
        eligible = [p["alumno_id"] for p in res_proj.data]
        
    random_id = random.choice(eligible)
    
    # Get student info
    res_student = supabase.table("alumnos").select("*").eq("id", random_id).single().execute()
    return res_student.data

def render_pruebas_documentos():
    st.header("Pruebas de Generación de Documentos")
    st.info("Esta sección utilza datos de alumnos reales al azar (que cuentan con proyecto y unidad económica) para probar el formato visual y estructural de los PDFs generados.")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Anexo 5.1", 
        "📄 Anexo 5.4", 
        "📄 Anexo 5.5", 
        "✉️ Carta Mentor IE", 
        "📝 Acta Materias",
        "🛠️ Entorno MOCK"
    ])
    
    with tab1:
        st.subheader("Anexo 5.1 - Plan de Formación")
        fmt_5_1 = st.radio("Formato", ["PDF", "Word (DOCX)"], key="fmt_5_1", horizontal=True)
        if st.button("Generar Prueba Anexo 5.1", use_container_width=True):
            with st.spinner("Seleccionando alumno al azar y compilando..."):
                student = get_random_eligible_student()
                if not student:
                    st.error("No hay alumnos con proyectos registrados en la BD para probar.")
                else:
                    data, msg = get_anexo_5_1_data(student["id"])
                    if not data:
                        st.warning(f"Alumno {student['matricula']} tiene datos incompletos. Usando fallback...")
                        data = {
                            "nombre_proyecto": "PROYECTO DE PRUEBA DUAL",
                            "unidad_economica": "EMPRESA DE PRUEBA S.A. DE C.V.",
                            "programa_educativo": "INGENIERÍA",
                            "num_estudiantes": "1", 
                            "num_mentores_ue": "1",
                            "num_mentores_academicos": "1",
                            "periodos_vigencia": "Enero - Diciembre 2026",
                            "descripcion_proyecto": "Prueba automática.",
                            "horas_semanales": "40",
                            "mentor_ue": "Ing. Mentor",
                            "mentor_ie": "Mtro. Maestro",
                            "fecha_generacion": datetime.now().strftime('%d/%m/%Y'),
                            "competencias_list": [],
                            "actividades_list": []
                        }
                    import tempfile
                    out_dir = tempfile.gettempdir()
                    
                    pdf_path = os.path.join(out_dir, f"Prueba_Anexo_5.1_{student['matricula']}.pdf")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", "Anexo_5.1_Plan_de_Formacion.docx")
                    
                    to_pdf_5_1 = (fmt_5_1 == "PDF")
                    success, result_msg = generate_pdf_from_docx("Anexo_5.1_Plan_de_Formacion.docx", data, pdf_path, template_path, to_pdf_5_1)
                    
                    if success:
                        st.success("¡Documento generado!")
                        active_path = pdf_path if to_pdf_5_1 else pdf_path.replace('.pdf', '.docx')
                        st.session_state["test_5_1_path"] = active_path
                    else:
                        st.error(f"Error: {result_msg}")
                        
        if st.session_state.get("test_5_1_path") and os.path.exists(st.session_state["test_5_1_path"]):
            active_path = st.session_state["test_5_1_path"]
            with open(active_path, "rb") as f:
                st.download_button("⬇️ Descargar Anexo 5.1", f.read(), os.path.basename(active_path), key="dl_5_1")

    with tab2:
        st.subheader("Anexo 5.4 - Reporte de Actividades")
        fmt_5_4 = st.radio("Formato", ["PDF", "Word (DOCX)"], key="fmt_5_4", horizontal=True)
        if st.button("Generar Prueba Anexo 5.4", use_container_width=True):
            with st.spinner("Seleccionando alumno e insertando gráficas..."):
                student = get_random_eligible_student()
                if student:
                    supabase = get_supabase_client()
                    res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", student["id"]).limit(1).execute()
                    proj = res_proj.data[0] if res_proj.data else {}
                    chart_path = os.path.join(os.path.dirname(__file__), "test_chart_temp.png")
                    create_percentage_donut(85, chart_path) # Dummy 85%
                    
                    context = {
                        "numero_reporte": 1,
                        "fechas_periodo": "Prueba",
                        "nombre_proyecto": proj.get("nombre_proyecto", "PROYECTO TEST"),
                        "empresa": proj.get("unidades_economicas", {}).get("nombre_comercial", "EMPRESA TEST"),
                        "institucion_educativa": "TESE",
                        "carrera": "Carrera Test",
                        "nombre_alumno": f"{student['nombre']} {student['ap_paterno']}",
                        "mentor_ue": proj.get("mentores_ue", {}).get("nombre_completo", "Mentor UE"),
                        "mentor_ie": proj.get("maestros", {}).get("nombre_completo", "Mentor IE"),
                        "grafica_promedio": f"IMAGE_PATH:{chart_path}",
                        "evaluaciones": [],
                        "lista_competencias": []
                    }
                    
                    import tempfile
                    out_dir = tempfile.gettempdir()
                    pdf_path = os.path.join(out_dir, f"Prueba_Anexo_5.4_{student['matricula']}.pdf")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", "Anexo_5.4_Reporte_de_Actividades.docx")
                    to_pdf_5_4 = (fmt_5_4 == "PDF")
                    success, result_msg = generate_pdf_from_docx("Anexo_5.4_Reporte_de_Actividades.docx", context, pdf_path, template_path, to_pdf_5_4)
                    if os.path.exists(chart_path): os.remove(chart_path)
                    if success:
                        st.success("¡Documento generado!")
                        active_path = pdf_path if to_pdf_5_4 else pdf_path.replace('.pdf', '.docx')
                        st.session_state["test_5_4_path"] = active_path
                    else: st.error(result_msg)
                    
        if st.session_state.get("test_5_4_path") and os.path.exists(st.session_state["test_5_4_path"]):
            active_path = st.session_state["test_5_4_path"]
            with open(active_path, "rb") as f:
                st.download_button("⬇️ Descargar Anexo 5.4", f.read(), os.path.basename(active_path), key="dl_5_4")

    # Reusable function for the new generic mock documents
    def generate_generic_mock(tab_obj, template_file, out_prefix, format_choice, gen_btn_key, dl_btn_key):
        with tab_obj:
            st.subheader(out_prefix.replace('_', ' '))
            fmt = st.radio("Formato", ["PDF", "Word (DOCX)"], key=f"fmt_{gen_btn_key}", horizontal=True)
            if st.button(f"Generar {out_prefix.replace('_', ' ')}", use_container_width=True, key=gen_btn_key):
                with st.spinner("Generando..."):
                    student = get_random_eligible_student()
                    if student:
                        supabase = get_supabase_client()
                        res_proj = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", student["id"]).limit(1).execute()
                        proj = res_proj.data[0] if res_proj.data else {}
                        
                        # Generic mock context
                        context = {
                            "alumno_nombre": f"{student['nombre']} {student['ap_paterno']}",
                            "alumno_matricula": student['matricula'],
                            "empresa_nombre": proj.get("unidades_economicas", {}).get("nombre_comercial", "EMPRESA MOCK") if proj.get("unidades_economicas") else "EMPRESA MOCK",
                            "mentor_ie_nombre": proj.get("maestros", {}).get("nombre_completo", "MENTOR IE MOCK") if proj.get("maestros") else "MENTOR IE MOCK",
                            "mentor_ue_nombre": proj.get("mentores_ue", {}).get("nombre_completo", "MENTOR UE MOCK") if proj.get("mentores_ue") else "MENTOR UE MOCK",
                            "materia_nombre": "Materia de Prueba",
                            "calificacion": "9.5",
                            "fecha_actual": datetime.now().strftime('%d/%m/%Y'),
                            "proyecto_nombre": proj.get("nombre_proyecto", "PROYECTO MOCK")
                        }
                        
                        import tempfile
                        out_dir = tempfile.gettempdir()
                        pdf_path = os.path.join(out_dir, f"Prueba_{out_prefix}_{student['matricula']}.pdf")
                        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", template_file)
                        
                        to_pdf = (fmt == "PDF")
                        success, result_msg = generate_pdf_from_docx(template_file, context, pdf_path, template_path, to_pdf)
                        
                        if success:
                            st.success("¡Documento generado!")
                            active_path = pdf_path if to_pdf else pdf_path.replace('.pdf', '.docx')
                            st.session_state[f"test_{gen_btn_key}_path"] = active_path
                        else:
                            st.error(f"Error: {result_msg}")
                            
            if st.session_state.get(f"test_{gen_btn_key}_path") and os.path.exists(st.session_state[f"test_{gen_btn_key}_path"]):
                active_path = st.session_state[f"test_{gen_btn_key}_path"]
                with open(active_path, "rb") as f:
                    st.download_button(f"⬇️ Descargar {out_prefix}", f.read(), os.path.basename(active_path), key=dl_btn_key)

    generate_generic_mock(tab3, "Anexo_5.5_Seguimiento_Modificado.docx", "Anexo_5.5", fmt_5_1, "btn_gen_55", "dl_btn_55")
    generate_generic_mock(tab4, "Carta_Asignacion_Mentor_IE.docx", "Carta_Mentor_IE", fmt_5_1, "btn_gen_carta", "dl_btn_carta")
    generate_generic_mock(tab5, "Acta_Calificaciones_Materia.docx", "Acta_Calificaciones", fmt_5_1, "btn_gen_acta", "dl_btn_acta")

    with tab6:
        st.subheader("Entorno de Pruebas (Ciclo Completo DUAL)")
        st.info("Utiliza esta herramienta para inyectar un alumno falso con un proyecto e inscripciones falsas utilizando las Unidades Económicas y Maestros ya existentes en el sistema. Esto te permite recorrer todo el sistema como Estudiante o como Mentor sin arruinar datos reales.")
        
        st.markdown("""
        ### Pasos para probar el sistema
        1. Presiona **Instalar Universo MOCK** abajo.
        2. Ve al **Control de Fases** -> **Fase 2** y Asígnale un *Mentor Institucional (MOCK Maestro)* a los alumnos MOCK. (Te llegará un correo con sus contraseñas).
        3. Cierra sesión y **Entra como uno de los alumnos** (Matrícula: `MOCK-ALU-1` : `MOCK-ALU-1`). Llena sus datos y ve a sus documentos.
        4. Inicia sesión como el **Mentor UE** o **Mentor IE** (con la contraseña que te llegó) y evalúa al alumno para recibir los PDF finales.
        """)
        
        def purge_mock_universe(supa):
            # Because of CASCADE, deleting masters/UE deletes projects/enrolls.
            supa.table("alumnos").delete().like("matricula", "MOCK-%").execute()
            supa.table("mentores_ue").delete().like("nombre_completo", "MOCK %").execute()
            supa.table("unidades_economicas").delete().like("rfc", "MOCK-%").execute()
            supa.table("maestros").delete().like("clave_maestro", "MOCK-%").execute()
            # Subjects are deleted explicitly last.
            supa.table("asignaturas").delete().like("clave_asignatura", "MOCK-%").execute()

        col_mock1, col_mock2 = st.columns(2)
        
        with col_mock1:
            if st.button("🚀 Instalar Universo MOCK", use_container_width=True):
                with st.spinner("Inyectando 16 entidades... (Tardará unos segundos)"):
                    try:
                        supabase = get_supabase_client()
                        
                        # Verify prerequisites
                        res_p = supabase.table("periodos").select("id").eq("activo", True).execute()
                        if not res_p.data:
                            st.error("No hay ningún periodo activo. No se puede construir el universo.")
                        else:
                            periodo_id = res_p.data[0]['id']
                            
                            res_c = supabase.table("carreras").select("id").limit(1).execute()
                            if not res_c.data:
                                st.error("No hay carreras registradas. No se puede construir el universo.")
                            else:
                                carrera_id = res_c.data[0]['id']
                                
                                # Clean potential previous mocks
                                purge_mock_universe(supabase)
                                
                                tgt_email = "jairyanez44@gmail.com"
                                
                                # 1. Generate 3 Asignaturas
                                asig_data = [
                                    {"clave_asignatura": "MOCK-ASIG-1", "nombre": "MOCK Arquitectura Software", "semestre": 6, "carrera_id": carrera_id},
                                    {"clave_asignatura": "MOCK-ASIG-2", "nombre": "MOCK Desarrollo Distribuido", "semestre": 7, "carrera_id": carrera_id},
                                    {"clave_asignatura": "MOCK-ASIG-3", "nombre": "MOCK Gestión de Equipos", "semestre": 8, "carrera_id": carrera_id}
                                ]
                                res_asig = supabase.table("asignaturas").insert(asig_data).execute()
                                asig_ids = [a['id'] for a in res_asig.data]
                                
                                # 2. Generate 5 Maestros
                                mae_data = [
                                    {"clave_maestro": f"MOCK-MAE-{i}", "nombre_completo": f"MOCK Maestro {i}", "email_institucional": tgt_email, "es_mentor_ie": True, "carrera_id": carrera_id}
                                    for i in range(1, 6)
                                ]
                                res_mae = supabase.table("maestros").insert(mae_data).execute()
                                mae_ids = [m['id'] for m in res_mae.data]
                                
                                # 3. Generate 2 UEs
                                ue_data = [
                                    {"nombre_comercial": "MOCK Tech Corporation", "rfc": "MOCK-RFC-1"},
                                    {"nombre_comercial": "MOCK Innova Labs", "rfc": "MOCK-RFC-2"}
                                ]
                                res_ue = supabase.table("unidades_economicas").insert(ue_data).execute()
                                ue_ids = [u['id'] for u in res_ue.data]
                                
                                # 4. Generate 3 Mentores UE (1 for UE1, 2 for UE2)
                                mue_data = [
                                    {"ue_id": ue_ids[0], "nombre_completo": "MOCK Mentor Ejecutivo 1", "email": tgt_email},
                                    {"ue_id": ue_ids[1], "nombre_completo": "MOCK Mentor Ejecutivo 2", "email": tgt_email},
                                    {"ue_id": ue_ids[1], "nombre_completo": "MOCK Mentor Asociado 3", "email": tgt_email}
                                ]
                                res_mue = supabase.table("mentores_ue").insert(mue_data).execute()
                                mue_ids = [m['id'] for m in res_mue.data]
                                
                                # 5. Generate 3 Alumnos
                                alu_data = [
                                    {
                                        "carrera_id": carrera_id,
                                        "matricula": f"MOCK-ALU-{i}",
                                        "curp": f"MOCK1234567890123{i}",
                                        "nombre": f"MOCK Estudiante {i}",
                                        "ap_paterno": "Prueba",
                                        "ap_materno": "Mock",
                                        "email_institucional": tgt_email,
                                        "email_personal": tgt_email,
                                        "semestre": str(6 + (i % 3)),
                                        "tipo_ingreso": "Nuevo Ingreso",
                                        "ultimo_semestre_convenio": False,
                                        "estatus": "Activo"
                                    } for i in range(1, 4)
                                ]
                                res_alu = supabase.table("alumnos").insert(alu_data).execute()
                                alu_ids = [a['id'] for a in res_alu.data]
                                
                                st.success("¡Universo MOCK Inyectado! (3 Asignaturas, 5 Maestros, 2 UEs, 3 Mentores UE, 3 Alumnos). Todos usarán el correo proporcionado para pruebas de Fases.")
                    except Exception as e:
                        st.error(f"Error insertando: {e}")
        
        with col_mock2:
            if st.button("🗑️ Purgar Universo MOCK", use_container_width=True):
                with st.spinner("Borrando todo rastro de los Mocks..."):
                    try:
                        supabase = get_supabase_client()
                        purge_mock_universe(supabase)
                        st.success("Toda la información falsa (Alumnos, UEs, Maestros, Materias) ha sido desintegrada.")
                    except Exception as e:
                        st.error(f"Error borrando: {e}")

        st.divider()
        st.subheader("Descarga de Manuales del Sistema")
        st.info("Obtén las versiones en PDF de los manuales del sistema. Puedes modificar los archivos .docx originales en la carpeta `templates/docs` y el sistema generará el PDF actualizado al vuelo.")
        
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            if st.button("📄 Generar PDF: Manual de Usuario", use_container_width=True):
                with st.spinner("Convirtiendo a PDF..."):
                    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "output")
                    os.makedirs(out_dir, exist_ok=True)
                    pdf_path = os.path.join(out_dir, "Manual_Usuario_Sistema_DUAL.pdf")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "docs", "Manual_Usuario_Sistema_DUAL.docx")
                    
                    success, msg = generate_pdf_from_docx("Manual_Usuario_Sistema_DUAL.docx", {}, pdf_path, template_path, True)
                    if success:
                        st.session_state["path_manual_usr"] = pdf_path
                        st.success("Manual listo para descargar.")
                    else:
                        st.error(f"Error generando: {msg}")
                        
            if st.session_state.get("path_manual_usr") and os.path.exists(st.session_state["path_manual_usr"]):
                with open(st.session_state["path_manual_usr"], "rb") as f:
                    st.download_button("⬇️ Descargar Manual de Usuario (PDF)", f.read(), "Manual_Usuario_Sistema_DUAL.pdf", key="dl_usr")
                    
        with col_man2:
            if st.button("⚙️ Generar PDF: Manual Técnico", use_container_width=True):
                with st.spinner("Convirtiendo a PDF..."):
                    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "output")
                    os.makedirs(out_dir, exist_ok=True)
                    pdf_path = os.path.join(out_dir, "Manual_Tecnico_Sistema_DUAL.pdf")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "docs", "Manual_Tecnico_Sistema_DUAL.docx")
                    
                    success, msg = generate_pdf_from_docx("Manual_Tecnico_Sistema_DUAL.docx", {}, pdf_path, template_path, True)
                    if success:
                        st.session_state["path_manual_tec"] = pdf_path
                        st.success("Manual listo para descargar.")
                    else:
                        st.error(f"Error generando: {msg}")
                        
            if st.session_state.get("path_manual_tec") and os.path.exists(st.session_state["path_manual_tec"]):
                with open(st.session_state["path_manual_tec"], "rb") as f:
                    st.download_button("⬇️ Descargar Manual Técnico (PDF)", f.read(), "Manual_Tecnico_Sistema_DUAL.pdf", key="dl_tec")
