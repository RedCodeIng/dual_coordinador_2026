
import streamlit as st
from datetime import date, datetime
from src.utils.helpers import calculate_age
from src.db_connection import get_supabase_client
from src.utils.db_actions import create_student_transaction

def render_registro_coordinador():
    st.header("Alta de Alumno (Modalidad Coordinador)")
    st.info("Utilice este formulario para registrar manualmente a un alumno en el sistema DUAL.")
    
    supabase = get_supabase_client()
    
    # State management for Coordinator's form
    if "coord_reg_step" not in st.session_state:
        st.session_state["coord_reg_step"] = 1
        st.session_state["coord_student_data"] = {}
        st.session_state["coord_project_data"] = {}
        st.session_state["coord_subjects_data"] = []

    step = st.session_state["coord_reg_step"]
    
    # Progress
    st.progress(step / 4)
    
    if step == 1:
        st.subheader("Paso 1: Datos Personales del Alumno")
        
        with st.form("coord_personal_data"):
            col1, col2 = st.columns(2)
            with col1:
                matricula = st.text_input("Matrícula", value=st.session_state["coord_student_data"].get("matricula", ""))
                nombre = st.text_input("Nombre(s)", value=st.session_state["coord_student_data"].get("nombre", ""))
                ap_paterno = st.text_input("Apellido Paterno", value=st.session_state["coord_student_data"].get("ap_paterno", ""))
                ap_materno = st.text_input("Apellido Materno", value=st.session_state["coord_student_data"].get("ap_materno", ""))
                genero = st.selectbox("Género", ["Hombre", "Mujer", "Otro"])
                estado_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"])

            with col2:
                curp = st.text_input("CURP", value=st.session_state["coord_student_data"].get("curp", ""))
                nss = st.text_input("Número de Seguridad Social (NSS)", value=st.session_state["coord_student_data"].get("nss", ""))
                
                # FIX: Date Range 1950-2020
                min_dob = date(1950, 1, 1)
                max_dob = date(2020, 12, 31)
                default_dob = date(2000, 1, 1)
                
                prev_dob = st.session_state["coord_student_data"].get("fecha_nacimiento")
                if isinstance(prev_dob, str):
                    try: prev_dob = datetime.strptime(prev_dob, "%Y-%m-%d").date()
                    except: prev_dob = default_dob
                
                fecha_nac = st.date_input("Fecha de Nacimiento", value=prev_dob if prev_dob else default_dob, min_value=min_dob, max_value=max_dob)
                
                edad = calculate_age(fecha_nac)
                st.info(f"Edad calculada: {edad} años")
                
                tipo_ingreso_opts = ["Nuevo Ingreso", "Reinscripción"]
                tipo_ingreso = st.selectbox("Tipo de Ingreso", tipo_ingreso_opts, index=tipo_ingreso_opts.index(st.session_state["coord_student_data"].get("tipo_ingreso", "Nuevo Ingreso")))
                
                email_inst = st.text_input("Correo Institucional", value=st.session_state["coord_student_data"].get("email_institucional", ""))
                email_pers = st.text_input("Correo Personal", value=st.session_state["coord_student_data"].get("email_personal", ""))
                telefono = st.text_input("Teléfono", value=st.session_state["coord_student_data"].get("telefono", ""))

            carrera = st.selectbox("Carrera", ["Ingeniería en Sistemas Computacionales", "Ingeniería Industrial", "Ingeniería Mecánica"])
            semestre = st.selectbox("Semestre", ["6", "7", "8", "9"])
            ultimo_semestre_convenio = st.checkbox("¿Es su último semestre de convenio (Por egresar/cerrar expediente)?", value=st.session_state["coord_student_data"].get("ultimo_semestre_convenio", False))
            
            submitted = st.form_submit_button("Siguiente >")
            if submitted:
                if not matricula or not curp or not nombre or not ap_paterno:
                     st.error("Matrícula, CURP y Nombre son obligatorios para iniciar el registro.")
                else:
                    st.session_state["coord_student_data"].update({
                        "matricula": matricula, "curp": curp,
                        "nombre": nombre, "ap_paterno": ap_paterno, "ap_materno": ap_materno,
                        "nss": nss, "fecha_nacimiento": str(fecha_nac),
                        "genero": genero, "estado_civil": estado_civil,
                        "email_institucional": email_inst, "email_personal": email_pers, "telefono": telefono,
                        "carrera": carrera,
                        "semestre": semestre,
                        "tipo_ingreso": tipo_ingreso,
                        "ultimo_semestre_convenio": ultimo_semestre_convenio
                    })
                    st.session_state["coord_reg_step"] = 2
                    st.rerun()

    elif step == 2:
        st.subheader("Paso 2: Datos del Proyecto DUAL")
        
        # Load Companies
        res_ue = supabase.table("unidades_economicas").select("id, nombre_comercial").execute()
        ues = res_ue.data if res_ue.data else []
        ue_options = {ue["nombre_comercial"]: ue["id"] for ue in ues}
        
        col_proj1, col_proj2 = st.columns(2)
        
        with col_proj1:
            selected_ue_name = st.selectbox("Unidad Económica", list(ue_options.keys()) if ues else ["No hay empresas registradas"])
            ue_id = ue_options.get(selected_ue_name)
            
            # Load Mentors for selected UE
            mentors = []
            if ue_id:
                res_mentors = supabase.table("mentores_ue").select("id, nombre_completo").eq("ue_id", ue_id).execute()
                mentors = res_mentors.data
            
            mentor_options = {m["nombre_completo"]: m["id"] for m in mentors}
            selected_mentor_name = st.selectbox("Mentor Industrial (Mentor UE)", list(mentor_options.keys()) if mentors else ["No hay mentores registrados"])
            mentor_id = mentor_options.get(selected_mentor_name)

        with col_proj2:
            nombre_proyecto = st.text_input("Nombre del Proyecto", value=st.session_state.get("coord_project_data", {}).get("nombre_proyecto", ""))
            descripcion_proyecto = st.text_area("Descripción del Proyecto", value=st.session_state.get("coord_project_data", {}).get("descripcion_proyecto", ""))
            marco_teorico = st.text_area("Marco Teórico / Justificación", value=st.session_state.get("coord_project_data", {}).get("marco_teorico", ""))
            
            prev_start = st.session_state.get("coord_project_data", {}).get("fecha_inicio", str(date.today()))
            prev_end = st.session_state.get("coord_project_data", {}).get("fecha_fin", str(date.today()))
            
            try: prev_start = datetime.strptime(prev_start, "%Y-%m-%d").date()
            except: prev_start = date.today()
            try: prev_end = datetime.strptime(prev_end, "%Y-%m-%d").date()
            except: prev_end = date.today()

            fecha_inicio = st.date_input("Fecha Inicio Convenio", value=prev_start)
            fecha_fin = st.date_input("Fecha Fin Convenio", value=prev_end)

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior"):
             st.session_state["coord_reg_step"] = 1
             st.rerun()
             
        if col_nav2.button("Siguiente >"):
             if not nombre_proyecto or not ue_id:
                  st.error("Nombre del proyecto y Empresa son obligatorios.")
             elif not mentor_id:
                  st.error("Debe seleccionar un Mentor UE (Industrial).")
             else:
                 st.session_state["coord_project_data"] = {
                     "ue_id": ue_id,
                     "mentor_ue_id": mentor_id,
                     "nombre_proyecto": nombre_proyecto,
                     "descripcion_proyecto": descripcion_proyecto,
                     "marco_teorico": marco_teorico,
                     "fecha_inicio": str(fecha_inicio),
                     "fecha_fin": str(fecha_fin),
                     "ue_name": selected_ue_name,
                     "mentor_ue_name": selected_mentor_name
                 }
                 st.session_state["coord_reg_step"] = 3
                 st.rerun()

    elif step == 3:
        st.subheader("Paso 3: Carga Académica")
        st.info("Agrega las materias que el alumno cursará en modalidad DUAL.")
        
        if "coord_subjects_data" not in st.session_state:
            st.session_state["coord_subjects_data"] = []
            
        # Fetch Catalogues
        res_subjects = supabase.table("asignaturas").select("id, nombre, clave_asignatura").execute()
        subjects = res_subjects.data if res_subjects.data else []
        subject_options = {f"{s['clave_asignatura']} - {s['nombre']}": s["id"] for s in subjects}
        
        res_teachers = supabase.table("maestros").select("id, nombre_completo, es_mentor_ie").execute()
        teachers = res_teachers.data if res_teachers.data else []
        teacher_options = {t["nombre_completo"]: t["id"] for t in teachers}

        # Add form
        with st.form("coord_add_subject"):
            c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
            with c1:
                sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()) if subjects else ["No hay asignaturas"])
                subject_id = subject_options.get(sel_subj_name)
            with c2:
                sel_teacher_name = st.selectbox("Maestro (Docente)", list(teacher_options.keys()) if teachers else ["No hay maestros"])
                teacher_id = teacher_options.get(sel_teacher_name)
            with c3:
                grupo = st.text_input("Grupo", value="8101")
                actividades = st.text_area("Actividades que desarrollará el alumno en relación a esta materia", help="Descripción breve de lo que hará en la empresa que sirva para evaluar.")
            with c4:
                st.write("Parciales:")
                p1 = st.checkbox("P1", value=True)
                p2 = st.checkbox("P2", value=True)
                p3 = st.checkbox("P3", value=True)
            
            submitted_subj = st.form_submit_button("Agregar Materia")
            if submitted_subj:
                if not subject_id or not teacher_id:
                     st.error("Debe seleccionar una materia y un maestro.")
                else:
                    st.session_state["coord_subjects_data"].append({
                        "asignatura_id": subject_id,
                        "maestro_id": teacher_id,
                        "grupo": grupo,
                        "asignatura_name": sel_subj_name, 
                        "maestro_name": sel_teacher_name,
                        "actividades": actividades,
                        "p1": p1, "p2": p2, "p3": p3
                    })
                    st.success("Materia agregada.")

        # Show Added Table
        if st.session_state["coord_subjects_data"]:
            st.write("Materias Agregadas:")
            for idx, item in enumerate(st.session_state["coord_subjects_data"]):
                st.text(f"{idx+1}. {item['asignatura_name']} with {item['maestro_name']} (Gpo: {item['grupo']})")
            
            if st.button("Limpiar Lista"):
                st.session_state["coord_subjects_data"] = []
                st.rerun()

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior"):
             st.session_state["coord_reg_step"] = 2
             st.rerun()
        if col_nav2.button("Finalizar y Revisar >"):
             st.session_state["coord_reg_step"] = 4
             st.rerun()

    elif step == 4:
        st.subheader("Resumen y Confirmación")
        
        user = st.session_state.get("coord_student_data", {})
        proj = st.session_state.get("coord_project_data", {})
        subjs = st.session_state.get("coord_subjects_data", [])
        
        with st.expander("Ver Resumen", expanded=True):
            st.write(f"**Alumno:** {user.get('nombre')} {user.get('ap_paterno')} {user.get('ap_materno')}")
            st.write(f"**Proyecto:** {proj.get('nombre_proyecto')} en {proj.get('ue_name')}")
            st.write(f"**Materias:** {len(subjs)}")

        if st.button("Confirmar y Guardar Registro"):
            with st.spinner("Guardando registro en sistema..."):
                success, msg = create_student_transaction(user, proj, subjs)
                
                if success:
                    st.balloons()
                    st.success("¡Alumno registrado exitosamente!")
                    try:
                        from src.utils.email_sender import send_confirmation_email
                        send_confirmation_email(user.get("email_personal", "test@example.com"), user.get("nombre"))
                        st.info("Correo enviado al alumno.")
                    except:
                        pass
                    
                    if st.button("Registrar Otro Alumno"):
                        st.session_state["coord_reg_step"] = 1
                        st.session_state["coord_student_data"] = {}
                        st.session_state["coord_project_data"] = {}
                        st.session_state["coord_subjects_data"] = []
                        st.rerun()
                else:
                    st.error(f"Error al guardar: {msg}")
        
        if st.button("< Corregir"):
             st.session_state["coord_reg_step"] = 3
             st.rerun()
