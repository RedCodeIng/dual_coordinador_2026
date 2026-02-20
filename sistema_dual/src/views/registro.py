
import streamlit as st
from datetime import date, datetime
from src.utils.helpers import calculate_age
from src.db_connection import get_supabase_client
from src.utils.db_actions import create_student_transaction

def render_registro():
    st.title("Inscripción al Modelo DUAL")
    supabase = get_supabase_client()
    
    # 0. Check Status (Prevent Re-registration)
    request_user = st.session_state.get("user", {})
    matricula = request_user.get("matricula", "")
    
    # Simple check: if student exists and status is NOT 'Pre-registro'
    # In a real app we might fetch the status from DB if session is stale
    # But let's assume session 'user' has recent data or we fetch it:
    if matricula:
        res = supabase.table("alumnos").select("estatus").eq("matricula", matricula).execute()
        if res.data:
            estatus = res.data[0]["estatus"]
            if estatus in ["Registrado", "Activo", "Baja"]:
                st.warning(f"Tu estatus actual es: {estatus}")
                st.info("Ya te encuentras registrado en el sistema. No es necesario volver a llenar el formulario.")
                return 

    # Wizard Progress
    step = st.session_state.get("registro_step", 1)
    st.progress(step / 4)
    
    if step == 1:
        st.subheader("Paso 1: Datos Personales")
        
        curp = request_user.get("curp", "")
        
        with st.form("personal_data"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Matrícula", value=matricula, disabled=True)
                nombre = st.text_input("Nombre(s)")
                ap_paterno = st.text_input("Apellido Paterno")
                ap_materno = st.text_input("Apellido Materno")
                genero = st.selectbox("Género", ["Hombre", "Mujer", "Otro"])
                estado_civil = st.selectbox("Estado Civil", ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"])

            with col2:
                st.text_input("CURP", value=curp)
                nss = st.text_input("NSS")
                
                min_dob = date(1950, 1, 1)
                max_dob = date(2010, 12, 31)
                default_dob = date(2000, 1, 1)
                fecha_nac = st.date_input("Fecha de Nacimiento", value=default_dob, min_value=min_dob, max_value=max_dob)
                
                if fecha_nac:
                    edad = calculate_age(fecha_nac)
                    st.info(f"Edad calculada {edad} años")
                
                email_inst = st.text_input("Correo Institucional")
                email_pers = st.text_input("Correo Personal")
                telefono = st.text_input("Teléfono")

            carrera = st.selectbox("Carrera", ["Ingeniería en Sistemas Computacionales", "Ingeniería Industrial", "Ingeniería Mecánica"])
            semestre = st.selectbox("Semestre", ["6", "7", "8", "9"])
            
            submitted = st.form_submit_button("Siguiente >")
            if submitted:
                 # Update user dict in session state with form data
                request_user.update({
                    "nombre": nombre, "ap_paterno": ap_paterno, "ap_materno": ap_materno,
                    "curp": curp, "nss": nss, "fecha_nacimiento": str(fecha_nac),
                    "genero": genero, "estado_civil": estado_civil,
                    "email_institucional": email_inst, "email_personal": email_pers, "telefono": telefono,
                    "carrera": carrera, "semestre": semestre
                })
                st.session_state["user"] = request_user
                st.session_state["registro_step"] = 2
                st.rerun()

    elif step == 2:
        st.subheader("Paso 2: Datos del Proyecto")
        
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
            nombre_proyecto = st.text_input("Nombre del Proyecto")
            descripcion_proyecto = st.text_area("Descripción del Proyecto")
            fecha_inicio = st.date_input("Fecha Inicio Convenio", value=date.today())
            fecha_fin = st.date_input("Fecha Fin Convenio", value=date.today())

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior"):
             st.session_state["registro_step"] = 1
             st.rerun()
             
        if col_nav2.button("Siguiente >"):
             st.session_state["project_data"] = {
                 "ue_id": ue_id,
                 "mentor_ue_id": mentor_id,
                 "nombre_proyecto": nombre_proyecto,
                 "descripcion_proyecto": descripcion_proyecto,
                 "fecha_inicio": str(fecha_inicio),
                 "fecha_fin": str(fecha_fin),
                 "ue_name": selected_ue_name, # Storing names for summary
                 "mentor_ue_name": selected_mentor_name
             }
             st.session_state["registro_step"] = 3
             st.rerun()

    elif step == 3:
        st.subheader("Paso 3: Carga Académica")
        st.info("Agrega las materias que cursarás en modalidad DUAL.")
        
        # Initialize subjects list
        if "subjects_data" not in st.session_state:
            st.session_state["subjects_data"] = []
            
        # Fetch Catalogues
        res_subjects = supabase.table("asignaturas").select("id, nombre, clave_asignatura").execute()
        subjects = res_subjects.data if res_subjects.data else []
        subject_options = {f"{s['clave_asignatura']} - {s['nombre']}": s["id"] for s in subjects}
        
        res_teachers = supabase.table("maestros").select("id, nombre_completo, es_mentor_ie").execute()
        teachers = res_teachers.data if res_teachers.data else []
        teacher_options = {t["nombre_completo"]: t["id"] for t in teachers}

        # Add form
        with st.form("add_subject"):
            c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
            with c1:
                sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()))
            with c2:
                sel_teacher_name = st.selectbox("Maestro (Docente)", list(teacher_options.keys()))
            with c3:
                grupo = st.text_input("Grupo", value="8101")
            with c4:
                st.write("Parciales:")
                p1 = st.checkbox("P1", value=True)
                p2 = st.checkbox("P2", value=True)
                p3 = st.checkbox("P3", value=True)
            
            submitted_subj = st.form_submit_button("Agregar Materia")
            if submitted_subj:
                st.session_state["subjects_data"].append({
                    "asignatura_id": subject_options[sel_subj_name],
                    "maestro_id": teacher_options[sel_teacher_name],
                    "grupo": grupo,
                    "asignatura_name": sel_subj_name, # For display
                    "maestro_name": sel_teacher_name,
                    "p1": p1, "p2": p2, "p3": p3
                })
                st.success("Materia agregada.")

        # Show Added Table
        if st.session_state["subjects_data"]:
            st.write("Materias Agregadas:")
            for idx, item in enumerate(st.session_state["subjects_data"]):
                st.text(f"{idx+1}. {item['asignatura_name']} with {item['maestro_name']} (Gpo: {item['grupo']})")
            
            if st.button("Limpiar Lista"):
                st.session_state["subjects_data"] = []
                st.rerun()

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior"):
             st.session_state["registro_step"] = 2
             st.rerun()
        if col_nav2.button("Finalizar y Revisar >"):
             st.session_state["registro_step"] = 4
             st.rerun()

    elif step == 4:
        st.subheader("Confirmación")
        
        user = st.session_state.get("user", {})
        proj = st.session_state.get("project_data", {})
        subjs = st.session_state.get("subjects_data", [])
        
        with st.expander("Ver Resumen", expanded=True):
            st.write(f"**Alumno:** {user.get('nombre')} {user.get('ap_paterno')}")
            st.write(f"**Proyecto:** {proj.get('nombre_proyecto')} en {proj.get('ue_name')}")
            st.write(f"**Materias:** {len(subjs)}")

        if st.button("Confirmar Inscripción"):
            with st.spinner("Registrando..."):
                # Call REAL Transaction
                success, msg = create_student_transaction(user, proj, subjs)
                
                if success:
                    st.balloons()
                    st.success("¡Inscripción Exitosa!")
                    # Email
                    from src.utils.email_sender import send_confirmation_email
                    send_confirmation_email(user.get("email_personal", "test@example.com"), user.get("nombre"))
                    st.session_state["registro_complete"] = True
                else:
                    st.error(f"Error: {msg}")
