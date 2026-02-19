
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
                fecha_nac = st.date_input("Fecha de Nacimiento", value=default_dob, min_value=min_dob, max_value=max_dob)
                
                edad = calculate_age(fecha_nac)
                st.info(f"Edad calculada: {edad} años")
                
                email_inst = st.text_input("Correo Institucional", value=st.session_state["coord_student_data"].get("email_institucional", ""))
                email_pers = st.text_input("Correo Personal", value=st.session_state["coord_student_data"].get("email_personal", ""))
                telefono = st.text_input("Teléfono", value=st.session_state["coord_student_data"].get("telefono", ""))

            st.markdown("---")
            st.subheader("Datos Académicos")
            col_aca1, col_aca2 = st.columns(2)
            
            # Context
            selected_career_name = st.session_state.get("selected_career_name", "")
            selected_career_id = st.session_state.get("selected_career_id", None)
            
            with col_aca1:
                if selected_career_name:
                    st.text_input("Carrera", value=selected_career_name, disabled=True)
                    # We will use the session ID
                else:
                    # Fallback if no context (shouldn't happen with new logic, but safe to handle)
                    st.error("Error: No se ha seleccionado una carrera en el contexto.")
                    
            with col_aca2:
                semestre = st.selectbox("Semestre", ["6", "7", "8", "9"])
            
            submitted = st.form_submit_button("Siguiente >")
            if submitted:
                if not matricula or not curp or not nombre or not ap_paterno:
                     st.error("Matrícula, CURP y Nombre son obligatorios para iniciar el registro.")
                elif not selected_career_id:
                     st.error("Error crítico: No se identificó el ID de la carrera.")
                else:
                    st.session_state["coord_student_data"].update({
                        "matricula": matricula, "curp": curp,
                        "nombre": nombre, "ap_paterno": ap_paterno, "ap_materno": ap_materno,
                        "nss": nss, "fecha_nacimiento": fecha_nac,
                        "genero": genero, "estado_civil": estado_civil,
                        "email_institucional": email_inst, "email_personal": email_pers, "telefono": telefono,
                        "carrera_id": selected_career_id, # Store ID
                        "carrera": selected_career_name, # Store Name for display
                        "semestre": semestre
                    })
                    st.session_state["coord_reg_step"] = 2
                    st.rerun()

    elif step == 2:
        st.subheader("Paso 2: Datos del Proyecto DUAL")
        
        # Load Companies
        res_ue = supabase.table("unidades_economicas").select("id, nombre_comercial").execute()
        ues = res_ue.data if res_ue.data else []
        ue_options = {ue["nombre_comercial"]: ue["id"] for ue in ues}
        
        # FIX: UE Selection outside form
        col_ue_sel, col_dummy = st.columns(2)
        with col_ue_sel:
             selected_ue_name = st.selectbox("Seleccionar Unidad Económica", list(ue_options.keys()) if ues else ["No disponible"], key="coord_ue_selector")
             ue_id = ue_options.get(selected_ue_name)

        mentors = []
        if ue_id:
            res_mentors = supabase.table("mentores_ue").select("id, nombre_completo").eq("ue_id", ue_id).execute()
            mentors = res_mentors.data
        
        mentor_options = {m["nombre_completo"]: m["id"] for m in mentors}

        with st.form("coord_project_details"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                 selected_mentor_name = st.selectbox("Mentor UE (Industrial)", list(mentor_options.keys()) if mentors else ["No hay mentores registrados"])
                 mentor_id = mentor_options.get(selected_mentor_name)
                 
                 nombre_proyecto = st.text_input("Nombre del Proyecto")
            
            with col_p2:
                 fecha_inicio = st.date_input("Fecha Inicio Convenio", value=date.today())
                 fecha_fin = st.date_input("Fecha Fin Convenio", value=date.today())
            
            descripcion_proyecto = st.text_area("Descripción del Proyecto")

            submitted_proj = st.form_submit_button("Siguiente >")
            
            if submitted_proj:
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
                          "fecha_inicio": fecha_inicio,
                          "fecha_fin": fecha_fin,
                          "ue_name": selected_ue_name,
                          "mentor_ue_name": selected_mentor_name
                      }
                      st.session_state["coord_reg_step"] = 3
                      st.rerun()

        if st.button("< Anterior"):
             st.session_state["coord_reg_step"] = 1
             st.rerun()

    elif step == 3:
        st.subheader("Paso 3: Carga Académica")
        
        res_period = supabase.table("periodos").select("*").eq("activo", True).execute()
        period_name = res_period.data[0]["nombre"] if res_period.data else "No Definido"
        st.info(f"Periodo Activo: {period_name}")
        
        if "coord_subjects_data" not in st.session_state:
            st.session_state["coord_subjects_data"] = []
            
        # Context
        selected_career_id = st.session_state.get("selected_career_id", None)
            
        # Fetch Subjects Filtered
        query = supabase.table("asignaturas").select("id, nombre, clave_asignatura")
        if selected_career_id:
            query = query.eq("carrera_id", selected_career_id)
        
        res_subjects = query.execute()
        subjects = res_subjects.data if res_subjects.data else []
        subject_options = {f"{s['clave_asignatura']} - {s['nombre']}": s["id"] for s in subjects}

        # FIX: Removed st.form, added filtering
        st.markdown("##### Agregar Asignatura")
        
        c1, c2 = st.columns(2)
        with c1:
            sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()) if subjects else ["No hay asignaturas"])
            subject_id = subject_options.get(sel_subj_name)
            grupo = st.text_input("Grupo (Ej. 8101)")
            
        with c2:
            # Filter Teachers
            filtered_teachers = []
            if subject_id:
                res_rels = supabase.table("rel_maestros_asignaturas").select("maestro_id").eq("asignatura_id", subject_id).execute()
                teacher_ids = [r["maestro_id"] for r in res_rels.data] if res_rels.data else []
                if teacher_ids:
                    res_teachers = supabase.table("maestros").select("id, clave_maestro, nombre_completo").in_("id", teacher_ids).execute()
                    filtered_teachers = res_teachers.data if res_teachers.data else []
            
            # Display Clave - Name
            if filtered_teachers:
                teacher_options = {f"{t['clave_maestro']} - {t['nombre_completo']}": t["id"] for t in filtered_teachers}
            else:
                 teacher_options = {}

            sel_teacher_name = st.selectbox(
                "Maestro (Docente)", 
                list(teacher_options.keys()) if teacher_options else ["No hay maestros asignados"]
            )
            
            st.write("Parciales a Cursar:")
            col_chk1, col_chk2, col_chk3 = st.columns(3)
            with col_chk1: p1 = st.checkbox("Parcial 1", value=True)
            with col_chk2: p2 = st.checkbox("Parcial 2", value=True)
            with col_chk3: p3 = st.checkbox("Parcial 3", value=True)
            
        if st.button("Agregar Materia"):
             if not grupo:
                  st.error("Ingrese el grupo.")
             elif not sel_teacher_name or "No hay maestros" in sel_teacher_name:
                  st.error("Seleccione un maestro válido.")
             else:
                  st.session_state["coord_subjects_data"].append({
                      "asignatura_id": subject_id,
                      "maestro_id": teacher_options[sel_teacher_name],
                      "grupo": grupo,
                      "asignatura_name": sel_subj_name, 
                      "maestro_name": sel_teacher_name,
                      "p1": p1, "p2": p2, "p3": p3
                  })
                  st.success("Materia agregada.")

        # Show Added Table
        if st.session_state["coord_subjects_data"]:
            st.markdown("##### Materias Inscritas")
            for idx, item in enumerate(st.session_state["coord_subjects_data"]):
                with st.container():
                     cols = st.columns([3, 3, 1, 3])
                     cols[0].write(f"**{item['asignatura_name']}**")
                     cols[1].write(f"{item['maestro_name']}")
                     cols[2].write(f"Gpo: {item['grupo']}")
                     partials = []
                     if item['p1']: partials.append("P1")
                     if item['p2']: partials.append("P2")
                     if item['p3']: partials.append("P3")
                     cols[3].write(f"Eval: {', '.join(partials)}")
            
            if st.button("Limpiar Lista"):
                st.session_state["coord_subjects_data"] = []
                st.rerun()

        col_nav1, col_nav2 = st.columns([1, 1])
        if col_nav1.button("< Anterior"):
             st.session_state["coord_reg_step"] = 2
             st.rerun()
        if col_nav2.button("Finalizar y Registrar >"):
             if not st.session_state["coord_subjects_data"]:
                  st.error("Debe inscribir al menos una materia.")
             else:
                  st.session_state["coord_reg_step"] = 4
                  st.rerun()

    elif step == 4:
        st.subheader("Resumen y Confirmación")
        
        user = st.session_state.get("coord_student_data", {})
        proj = st.session_state.get("coord_project_data", {})
        subjs = st.session_state.get("coord_subjects_data", [])
        
        # FIX: UI Summary
        with st.expander("Datos Personales", expanded=False):
             c1, c2, c3 = st.columns(3)
             c1.markdown(f"**Nombre:** {user.get('nombre')} {user.get('ap_paterno')} {user.get('ap_materno')}")
             c1.markdown(f"**Matrícula:** {user.get('matricula')}")
             c2.markdown(f"**CURP:** {user.get('curp')}")
             c2.markdown(f"**NSS:** {user.get('nss')}")
             c3.markdown(f"**Email:** {user.get('email_institucional')}")
             
        with st.expander("Datos del Proyecto", expanded=True):
             st.markdown(f"**Empresa:** {proj.get('ue_name')}")
             st.markdown(f"**Proyecto:** {proj.get('nombre_proyecto')}")
             st.markdown(f"**Mentor:** {proj.get('mentor_ue_name')}")
             
        with st.expander("Carga Académica", expanded=True):
             st.markdown("| Asignatura | Maestro | Grupo |")
             st.markdown("| --- | --- | --- |")
             for s in subjs:
                  st.markdown(f"| {s['asignatura_name']} | {s['maestro_name']} | {s['grupo']} |")

        if st.button("Confirmar y Guardar Registro"):
            with st.spinner("Guardando registro en sistema..."):
                success, msg = create_student_transaction(user, proj, subjs)
                
                if success:
                    st.balloons()
                    st.success("¡Alumno registrado exitosamente!")
                    try:
                        from src.utils.email_sender import send_confirmation_email
                        
                        email_data = {
                            "nombre": f"{user.get('nombre')} {user.get('ap_paterno')}",
                            "matricula": user.get("matricula"),
                            "carrera": user.get("carrera"),
                            "proyecto": proj.get("nombre_proyecto"),
                            "ue": proj.get("ue_name"),
                            "fecha_inicio": proj.get("fecha_inicio")
                        }
                        
                        send_confirmation_email(user.get("email_personal"), email_data)
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
