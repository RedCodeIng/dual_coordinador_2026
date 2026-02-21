# Force Reload
import streamlit as st
import pandas as pd
import os
import re
from src.db_connection import get_supabase_client
from src.views.registro_coordinador import render_registro_coordinador
from src.utils.helpers import sanitize_input
from src.utils.anexo_data import get_anexo_5_1_data
from src.utils.pdf_generator_docx import generate_pdf_from_docx
from src.utils.email_sender import send_document_email

def render_alumnos():
    """
    Render the Student Management view with tabs for Listing and Registration.
    """
    st.subheader("Gestión de Alumnos")
    
    # Handle view mode
    if "view_student_id" not in st.session_state:
        st.session_state["view_student_id"] = None
        
    if st.session_state["view_student_id"]:
        # DETAIL VIEW (EXPEDIENTE)
        student_id = st.session_state["view_student_id"]
        
        # Load Student Data
        supabase = get_supabase_client()
        res = supabase.table("alumnos").select("*").eq("id", student_id).execute()
        
        if not res.data:
            st.error("Error al cargar el alumno.")
            if st.button("Volver"):
                st.session_state["view_student_id"] = None
                st.rerun()
            return
            
        student = res.data[0]
        
        c_header, c_back = st.columns([8, 2])
        c_header.markdown(f"### Expediente: {student['nombre']} {student['ap_paterno']} {student['ap_materno']}")
        if c_back.button("Volver al Listado", use_container_width=True):
            st.session_state["view_student_id"] = None
            st.rerun()
            
        # Tabs for different sections of the file
        tab_personal, tab_project, tab_academic, tab_docs, tab_admin = st.tabs(["Datos Personales", "Proyecto DUAL", "Historial Académico", "Documentos", "Administración"])
        
        with tab_personal:
            st.markdown("##### Información General")
            with st.form("edit_personal_info"):
                st.info("Edición de Datos del Alumno")
                c_names1, c_names2, c_names3 = st.columns(3)
                new_nombre = c_names1.text_input("Nombre(s)", value=student['nombre'])
                new_ap_paterno = c_names2.text_input("Apellido Paterno", value=student['ap_paterno'])
                new_ap_materno = c_names3.text_input("Apellido Materno", value=student['ap_materno'])

                cp1, cp2 = st.columns(2)
                # Keep identifiers disabled (Keys)
                cp1.text_input("Matrícula", value=student['matricula'], disabled=True)
                cp1.text_input("CURP", value=student['curp'], disabled=True)
                
                # Editable fields
                new_nss = cp1.text_input("NSS", value=student.get('nss', ''))
                
                # Dates & Status
                # Safe casting for date
                def safe_date(d_str):
                    if not d_str: return None
                    try: return pd.to_datetime(d_str).date()
                    except: return None

                current_dob = safe_date(student.get('fecha_nacimiento'))
                new_dob = cp2.date_input("Fecha de Nacimiento", value=current_dob if current_dob else None)
                
                # Enums
                current_gender = student.get('genero')
                gender_opts = ["Hombre", "Mujer", "Otro"]
                idx_g = gender_opts.index(current_gender) if current_gender in gender_opts else 0
                new_gender = cp2.selectbox("Género", gender_opts, index=idx_g)
                
                current_ec = student.get('estado_civil')
                ec_opts = ["Soltero/a", "Casado/a", "Divorciado/a", "Viudo/a"]
                idx_ec = ec_opts.index(current_ec) if current_ec in ec_opts else 0
                new_ec = cp1.selectbox("Estado Civil", ec_opts, index=idx_ec)

                st.markdown("---")
                st.markdown("###### Información de Contacto")
                cc1, cc2 = st.columns(2)
                new_email_inst = cc1.text_input("Correo Institucional", value=student.get('email_institucional', ''))
                new_email_pers = cc2.text_input("Correo Personal", value=student.get('email_personal', ''))
                new_tel = cc1.text_input("Teléfono", value=student.get('telefono', ''))
                
                if st.form_submit_button("Guardar Cambios Personales"):
                    # Sanitize
                    new_nombre = sanitize_input(new_nombre).strip()
                    new_ap_paterno = sanitize_input(new_ap_paterno).strip()
                    new_ap_materno = sanitize_input(new_ap_materno).strip()
                    new_nss = sanitize_input(new_nss).strip()
                    new_email_inst = sanitize_input(new_email_inst).strip()
                    new_email_pers = sanitize_input(new_email_pers).strip()
                    new_tel = sanitize_input(new_tel).strip()
                    
                    try:
                        supabase.table("alumnos").update({
                            "nombre": new_nombre,
                            "ap_paterno": new_ap_paterno,
                            "ap_materno": new_ap_materno,
                            "fecha_nacimiento": new_dob.isoformat() if new_dob else None,
                            "genero": new_gender,
                            "estado_civil": new_ec,
                            "nss": new_nss,
                            "email_institucional": new_email_inst,
                            "email_personal": new_email_pers,
                            "telefono": new_tel
                        }).eq("id", student_id).execute()
                        st.success("Información actualizada exitosamente.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")

        with tab_project:
            st.markdown("##### Información del Proyecto")
            
            # Load Project Data
            res_proj = supabase.table("proyectos_dual").select(
                "*, unidades_economicas(nombre_comercial), mentores_ue(nombre_completo, cargo, email), maestros(nombre_completo)"
            ).eq("alumno_id", student_id).execute()
            
            if res_proj.data:
                proj = res_proj.data[0]
                ue_name = proj.get('unidades_economicas', {}).get('nombre_comercial', 'N/A')
                mentor_ue = proj.get('mentores_ue', {})
                mentor_ie_name = (proj.get("maestros") or {}).get("nombre_completo", "Sin Asignar")
                
                # PROJECT EDIT FORM
                with st.form("edit_project_form"):
                    st.info(f"Editando Proyecto: {proj.get('nombre_proyecto')}")
                    
                    new_proj_name = st.text_input("Nombre del Proyecto", value=proj.get('nombre_proyecto', ''))
                    
                    # DATE VALIDATION LOGIC
                    c_d1, c_d2 = st.columns(2)
                    
                    def safe_date_proj(d_str):
                        if not d_str: return None
                        try: return pd.to_datetime(d_str).date()
                        except: return None
                        
                    current_start = safe_date_proj(proj.get('fecha_inicio_convenio'))
                    current_end = safe_date_proj(proj.get('fecha_fin_convenio'))
                    
                    new_start = c_d1.date_input("Fecha Inicio Convenio", value=current_start if current_start else None)
                    new_end = c_d2.date_input("Fecha Fin Convenio", value=current_end if current_end else None)
                    
                    # Validation Display (Visual feedback before submit)
                    if new_start and new_end:
                        if new_start == new_end:
                            st.error("⚠️ La fecha de inicio y fin no pueden ser iguales.")
                        else:
                            delta = new_end - new_start
                            days = delta.days
                            if 360 <= days <= 370: # Approx 1 year
                                st.success(f"Duración: {days} días (Aprox. 1 Año) ✅")
                            else:
                                st.warning(f"⚠️ **Atención:** La duración del convenio es de {days} días. (No es 1 año exacto). Verifique si esto es intencional.")

                    new_desc = st.text_area("Descripción del Proyecto", value=proj.get('descripcion_proyecto', ''), height=150)
                    new_marco_teorico = st.text_area("Marco Teórico / Justificación", value=proj.get('marco_teorico', ''), height=150)
                    
                    st.markdown(f"**Empresa (Solo lectura):** {ue_name}")
                    st.markdown("**Mentor Industrial (UE) (Solo lectura):**")
                    if mentor_ue:
                         st.caption(f"{mentor_ue.get('nombre_completo')} - {mentor_ue.get('email')}")
                    else:
                         st.caption("Sin Mentor UE asignado")

                    if st.form_submit_button("Actualizar Datos del Proyecto"):
                        # Sanitize
                        new_proj_name = sanitize_input(new_proj_name).strip()
                        new_desc = sanitize_input(new_desc).strip()
                        new_marco_teorico = sanitize_input(new_marco_teorico).strip()
                        
                        if not new_proj_name:
                             st.error("El nombre del proyecto es obligatorio.")
                        elif not new_start or not new_end:
                             st.error("Las fechas son obligatorias.")
                        elif new_start == new_end:
                             st.error("Las fechas no pueden ser iguales.")
                        elif new_start > new_end:
                             st.error("La fecha de inicio no puede ser posterior a la fecha fin.")
                        else:
                            try:
                                supabase.table("proyectos_dual").update({
                                    "nombre_proyecto": new_proj_name,
                                    "descripcion_proyecto": new_desc,
                                    "marco_teorico": new_marco_teorico,
                                    "fecha_inicio_convenio": new_start.isoformat(),
                                    "fecha_fin_convenio": new_end.isoformat()
                                }).eq("id", proj['id']).execute()
                                st.success("Proyecto actualizado exitosamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al actualizar proyecto: {e}")

                st.divider()
                
                c_mentors_col, c_dummy = st.columns([1,1])
                with c_mentors_col:
                    st.markdown("**Mentor Académico (IE):**")
                    st.write(f"Actual: **{mentor_ie_name}**")
                    
                    st.markdown("###### Asignar Mentor IE")
                    
                    # Manual Assignment (Outside form to allow independent interaction)
                    res_teachers = supabase.table("maestros").select("id, nombre_completo, email_institucional").eq("es_mentor_ie", True).execute()
                    if res_teachers.data:
                        # Find by name, keep teacher dict payload
                        teacher_opts = {t['nombre_completo']: t for t in res_teachers.data}
                        selected_new_mentor = st.selectbox("Seleccionar Manualmente", list(teacher_opts.keys()), index=None, placeholder="Seleccione un docente...")
                        
                        enviar_credenciales = st.checkbox("Generar y Enviar Credenciales de Acceso", help="Creará una contraseña temporal y se la enviará al maestro para ingresar al portal IE.", value=True)
                        
                        if st.button("Guardar Asignación Manual"):
                            if selected_new_mentor:
                                new_mentor_id = teacher_opts[selected_new_mentor]['id']
                                mentor_email = teacher_opts[selected_new_mentor].get('email_institucional')
                                
                                supabase.table("proyectos_dual").update({"mentor_ie_id": new_mentor_id}).eq("id", proj['id']).execute()
                                st.success("Mentor Académico actualizado.")
                                
                                if enviar_credenciales and mentor_email:
                                    import random, string, hashlib
                                    raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                                    hashed_pw = hashlib.sha256(raw_password.encode()).hexdigest()
                                    
                                    # Update password in DB
                                    supabase.table("maestros").update({"password_hash": hashed_pw}).eq("id", new_mentor_id).execute()
                                    
                                    # Send Email
                                    from src.utils.notifications import send_email
                                    ctx = {
                                        "title": "Credenciales de Acceso - Mentor IE (DUAL)",
                                        "message": f"""<p>Estimado/a Maestro/a <strong>{selected_new_mentor}</strong>,</p>
                                        <p>Se le ha asignado como <strong>Mentor Académico (IE)</strong> de un alumno del programa Educación DUAL.</p>
                                        <p>Con estas credenciales podrá acceder al portal del Modelo Dual para revisar a sus alumnos asignados y evaluarlos:</p>
                                        <ul><li><strong>Usuario/Correo:</strong> {mentor_email}</li><li><strong>Contraseña Temporal:</strong> {raw_password}</li></ul>
                                        <p>La coordinación le indicará las fechas para ingresar a realizar las evaluaciones.</p>
                                        """
                                    }
                                    success, emsg = send_email(mentor_email, "Credenciales de Acceso - Sistema DUAL", "base_notification.html", ctx)
                                    if success:
                                        st.success(f"Credenciales enviadas a {mentor_email}.")
                                    else:
                                        st.error(f"Mentor actualizado pero falló el correo: {emsg}")
                                
                                st.rerun()
                            else:
                                st.error("Seleccione un docente.")
                    else:
                        st.warning("No hay docentes registrados como Mentores IE.")
                    
                    # Automatic Assignment Button
                        success, msg = assign_mentors_round_robin()
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                        
            else:
                st.warning("El alumno no tiene un Proyecto DUAL activo registrado.")
                st.markdown("###### Registrar Proyecto DUAL")
                
                # Fetch available UEs
                res_ue = supabase.table("unidades_economicas").select("id, nombre_comercial").execute()
                ues = res_ue.data if res_ue.data else []
                ue_options = {ue["nombre_comercial"]: ue["id"] for ue in ues}
                
                with st.form("coord_create_project_form"):
                    col_proj1, col_proj2 = st.columns(2)
                    with col_proj1:
                        selected_ue_name = st.selectbox("Unidad Económica", list(ue_options.keys()) if ues else ["No hay empresas registradas"])
                        ue_id = ue_options.get(selected_ue_name) if ues else None
                        
                        mentors = []
                        if ue_id:
                            res_mentors = supabase.table("mentores_ue").select("id, nombre_completo").eq("ue_id", ue_id).execute()
                            mentors = res_mentors.data
                        
                        mentor_options = {m["nombre_completo"]: m["id"] for m in mentors}
                        selected_mentor_name = st.selectbox("Mentor Industrial (Mentor UE)", list(mentor_options.keys()) if mentors else ["No hay mentores registrados"])
                        mentor_id = mentor_options.get(selected_mentor_name) if mentors else None

                    with col_proj2:
                        nombre_proyecto = st.text_input("Nombre del Proyecto")
                        c_d1, c_d2 = st.columns(2)
                        fecha_inicio = c_d1.date_input("Fecha Inicio Convenio", value=pd.to_datetime("today").date())
                        fecha_fin = c_d2.date_input("Fecha Fin Convenio", value=pd.to_datetime("today").date())
                    
                    descripcion_proyecto = st.text_area("Descripción del Proyecto")
                    marco_teorico = st.text_area("Marco Teórico / Justificación")
                    
                    if st.form_submit_button("Crear Proyecto y Asignar al Alumno", use_container_width=True):
                        from src.utils.db_actions import get_active_period_id
                        periodo_id = get_active_period_id()
                        if not periodo_id:
                            st.error("No hay un periodo activo para vincular el proyecto.")
                        elif not nombre_proyecto or not ue_id or not mentor_id:
                            st.error("Empresa, Mentor y Nombre de Proyecto son obligatorios.")
                        elif fecha_inicio >= fecha_fin:
                            st.error("La fecha de inicio debe ser menor a la fecha fin.")
                        else:
                            try:
                                supabase.table("proyectos_dual").insert({
                                    "alumno_id": student_id,
                                    "periodo_id": periodo_id,
                                    "ue_id": ue_id,
                                    "mentor_ue_id": mentor_id,
                                    "nombre_proyecto": sanitize_input(nombre_proyecto),
                                    "descripcion_proyecto": sanitize_input(descripcion_proyecto),
                                    "marco_teorico": sanitize_input(marco_teorico),
                                    "fecha_inicio_convenio": fecha_inicio.isoformat(),
                                    "fecha_fin_convenio": fecha_fin.isoformat()
                                }).execute()
                                st.success("Proyecto registrado exitosamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al registrar proyecto: {e}")

        with tab_academic:
            st.markdown("##### Carga Académica")
            
            # Need to fetch enrolled subjects: inscripciones_asignaturas joined with asignaturas and maestros
            try:
                res_insc = supabase.table("inscripciones_asignaturas").select(
                    "id, *, asignaturas(clave_asignatura, nombre, semestre), maestros(nombre_completo)"
                ).eq("alumno_id", student_id).execute()
                
                enrolled_subjects = res_insc.data if res_insc.data else []
                
                if enrolled_subjects:
                    data_rows = []
                    for item in enrolled_subjects:
                        asign = item.get('asignaturas', {})
                        docente = item.get('maestros', {})
                        data_rows.append({
                            "Clave": asign.get('clave_asignatura'),
                            "Asignatura": asign.get('nombre'),
                            "Semestre": asign.get('semestre'),
                            "Grupo": item.get('grupo'),
                            "Docente": docente.get('nombre_completo', 'Sin Asignar'),
                            "P1": "✅" if item.get('parcial_1') else "⬜",
                            "P2": "✅" if item.get('parcial_2') else "⬜",
                            "P3": "✅" if item.get('parcial_3') else "⬜"
                        })
                    st.dataframe(pd.DataFrame(data_rows), use_container_width=True)
                    
                    st.markdown("###### Desglose de Calificaciones y Actividades DUAL")
                    
                    # Fetch project scores
                    res_p = supabase.table("proyectos_dual").select("calificacion_ue, calificacion_ie").eq("alumno_id", student_id).order("created_at", desc=True).limit(1).execute()
                    if res_p.data:
                         p_data = res_p.data[0]
                         c_ue = p_data.get("calificacion_ue")
                         c_ie = p_data.get("calificacion_ie")
                         
                         sc1, sc2 = st.columns(2)
                         sc1.metric("Promedio Mentor Industrial (UE)", f"{c_ue}%" if c_ue is not None else "No evaluado")
                         sc2.metric("Promedio Mentor Académico (IE)", f"{c_ie}%" if c_ie is not None else "No evaluado")
                         
                         if c_ue is not None and c_ie is not None:
                              total = (float(c_ue) * 0.7) + (float(c_ie) * 0.3)
                              st.info(f"**Calificación Final Ponderada (Modelo DUAL):** {total:.2f}%")

                    # Fetch Activities for the enrolled subjects
                    asig_ids = [item["asignatura_id"] for item in enrolled_subjects]
                    if asig_ids:
                         res_comp = supabase.table("asignatura_competencias").select("*, asignaturas(nombre)").in_("asignatura_id", asig_ids).execute()
                         if res_comp.data:
                              comps = res_comp.data
                              comp_ids = [c["id"] for c in comps]
                              res_act = supabase.table("actividades_aprendizaje").select("*").in_("competencia_id", comp_ids).execute()
                              acts = res_act.data if res_act.data else []
                              
                              for s in enrolled_subjects:
                                   asig_nombre = s.get('asignaturas', {}).get('nombre')
                                   s_comps = [c for c in comps if c["asignatura_id"] == s["asignatura_id"]]
                                   if s_comps:
                                        with st.expander(f"📚 {asig_nombre} - Actividades a Desarrollar"):
                                             for c in s_comps:
                                                  st.markdown(f"**Competencia:** {c['descripcion_competencia']}")
                                                  c_acts = [a for a in acts if a["competencia_id"] == c["id"]]
                                                  if c_acts:
                                                       df_acts = pd.DataFrame([{
                                                            "Actividad": a['descripcion_actividad'],
                                                            "Horas": a['horas_dedicacion'],
                                                            "Evidencia": a['evidencia']
                                                       } for a in c_acts])
                                                       st.dataframe(df_acts, use_container_width=True, hide_index=True)
                                                  else:
                                                       st.caption("No hay actividades registradas en esta competencia.")
                                                  st.divider()
                    
                    st.markdown("###### Dar de Baja Materia")
                    del_options = {f"{item.get('asignaturas', {}).get('nombre')} (Grupo {item.get('grupo')})": item["id"] for item in enrolled_subjects}
                    
                    col_del1, col_del2 = st.columns([3, 1])
                    materia_a_borrar = col_del1.selectbox("Seleccionar materia a eliminar", list(del_options.keys()), key="del_mat_select")
                    if col_del2.button("Eliminar Seleccionada", type="secondary", use_container_width=True):
                         id_to_delete = del_options[materia_a_borrar]
                         supabase.table("inscripciones_asignaturas").delete().eq("id", id_to_delete).execute()
                         st.success(f"Materia '{materia_a_borrar}' dada de baja.")
                         st.rerun()
                else:
                    st.info("No hay asignaturas inscritas.")
                    
                st.divider()
                st.markdown("###### Agregar Nueva Asignatura")
                
                c_filter1, c_filter2 = st.columns(2)
                with c_filter1:
                    sem_options = ["Todos", "6", "7", "8", "9"]
                    current_sem = student.get("semestre", "6")
                    default_index = sem_options.index(str(current_sem)) if str(current_sem) in sem_options else 0
                    selected_sem_filter = st.selectbox("Filtrar Materias por Semestre", sem_options, index=default_index, key="filt_sem")

                query = supabase.table("asignaturas").select("id, nombre, clave_asignatura, semestre")
                if student.get("carrera_id"):
                     query = query.eq("carrera_id", student.get("carrera_id"))
                
                if selected_sem_filter != "Todos":
                    query = query.eq("semestre", selected_sem_filter)

                res_subjects = query.execute()
                subjects = res_subjects.data if res_subjects.data else []
                subject_options = {f"{s['clave_asignatura']} - {s['nombre']} (Sem {s['semestre']})": s["id"] for s in subjects}

                with st.form("add_subject_form"):
                    c1, c2 = st.columns(2)
                    with c1:
                        sel_subj_name = st.selectbox("Asignatura", list(subject_options.keys()) if subjects else ["No hay asignaturas en este semestre"])
                        subject_id = subject_options.get(sel_subj_name) if subject_options and sel_subj_name else None
                        
                        grupo = st.text_input("Grupo (Ej. 8101)")
                        
                    with c2:
                        filtered_teachers = []
                        if subject_id:
                            res_rels = supabase.table("rel_maestros_asignaturas").select("maestro_id").eq("asignatura_id", subject_id).execute()
                            teacher_ids = [r["maestro_id"] for r in res_rels.data] if res_rels.data else []
                            
                            if teacher_ids:
                                res_teachers = supabase.table("maestros").select("id, clave_maestro, nombre_completo").in_("id", teacher_ids).execute()
                                filtered_teachers = res_teachers.data if res_teachers.data else []
                        
                        teacher_options = {}
                        if filtered_teachers:
                            for t in filtered_teachers:
                                raw_name = t['nombre_completo']
                                clean_name = re.sub(r'\s*\([^)]*\)', '', raw_name).strip()
                                teacher_options[f"{t['clave_maestro']} - {clean_name}"] = t["id"]

                        sel_teacher_name = st.selectbox(
                            "Maestro (Docente)", 
                            list(teacher_options.keys()) if teacher_options else ["No hay maestros asignados a esta materia"]
                        )
                        teacher_id = teacher_options.get(sel_teacher_name) if teacher_options and sel_teacher_name else None
                        
                        st.write("Parciales a Cursar:")
                        col_chk1, col_chk2, col_chk3 = st.columns(3)
                        with col_chk1: p1 = st.checkbox("Parcial 1", value=True)
                        with col_chk2: p2 = st.checkbox("Parcial 2", value=True)
                        with col_chk3: p3 = st.checkbox("Parcial 3", value=True)
                        
                    submitted = st.form_submit_button("Agregar y Guardar Materia")
                    
                    if submitted:
                         grupo = grupo.strip()
                         if not subject_id:
                             st.error("Por favor selecciona una materia válida.")
                         elif not grupo:
                             st.error("El grupo es obligatorio.")
                         elif not teacher_id:
                             st.error("La materia debe tener un docente seleccionado.")
                         else:
                             try:
                                 # Prevent adding duplicates
                                 check_dup = supabase.table("inscripciones_asignaturas").select("id").eq("alumno_id", student_id).eq("asignatura_id", subject_id).execute()
                                 if check_dup.data:
                                      st.error("El alumno ya está reinscrito en esta materia.")
                                 else:
                                      supabase.table("inscripciones_asignaturas").insert({
                                          "alumno_id": student_id,
                                          "asignatura_id": subject_id,
                                          "maestro_id": teacher_id,
                                          "grupo": grupo,
                                          "parcial_1": p1,
                                          "parcial_2": p2,
                                          "parcial_3": p3
                                      }).execute()
                                      st.success("Materia agregada exitosamente.")
                                      st.rerun()
                             except Exception as e:
                                 st.error(f"Error al agregar materia: {e}")
            except Exception as e:
                st.error(f"Error al cargar carga académica: {e}")

        with tab_docs:
            st.markdown("##### Generación de Documentos DUAL")
            st.info("Aquí puedes generar manualmente los documentos oficiales para este alumno o enviarlos por correo.")
            
            # Validar requisitos del alumno para generar documentos
            res_reqs = supabase.table("proyectos_dual").select("*, unidades_economicas(*), mentores_ue(*), maestros(*)").eq("alumno_id", student_id).order("created_at", desc=True).limit(1).execute()
            reqs = res_reqs.data[0] if res_reqs.data else {}
            has_project_and_ue = bool(reqs.get('ue_id') and reqs.get('mentor_ue_id'))
            has_mentor_ie = bool(reqs.get('mentor_ie_id'))
            has_all_reqs = has_project_and_ue and has_mentor_ie

            # Prepare generic context map for 5.4, 5.5, Carta, Acta
            ue = reqs.get("unidades_economicas", {}) or {}
            mentor_ue = reqs.get("mentores_ue", {}) or {}
            mentor_ie = reqs.get("maestros", {}) or {}
            
            from datetime import datetime
            
            # Simple context map for generic docs
            generic_context = {
                "alumno_nombre": f"{student.get('nombre')} {student.get('ap_paterno')} {student.get('ap_materno', '')}".strip(),
                "alumno_matricula": student.get('matricula'),
                "alumno_carrera": student.get('carrera', 'N/A'),
                "alumno_semestre": str(student.get('semestre', 'N/A')),
                "empresa_nombre": ue.get('nombre_comercial', 'N/A'),
                "empresa_rfc": ue.get('rfc', 'N/A'),
                "empresa_direccion": ue.get('direccion_fiscal', 'N/A'),
                "empresa_representante": ue.get('nombre_titular', 'N/A'),
                "empresa_cargo_representante": ue.get('cargo_titular', 'N/A'),
                "mentor_ue_nombre": mentor_ue.get('nombre_completo', 'N/A'),
                "mentor_ue_cargo": mentor_ue.get('cargo', 'N/A'),
                "mentor_ue_email": mentor_ue.get('email', 'N/A'),
                "mentor_ue_telefono": mentor_ue.get('telefono', 'N/A'),
                "mentor_ie_nombre": mentor_ie.get('nombre_completo', 'N/A'),
                "proyecto_nombre": reqs.get('nombre_proyecto', 'N/A'),
                "proyecto_fecha_inicio": str(reqs.get('fecha_inicio_convenio', 'N/A')),
                "proyecto_fecha_fin": str(reqs.get('fecha_fin_convenio', 'N/A')),
                "materia_nombre": "Asignaturas Modelo DUAL",
                "calificacion": "100", # Demostrativo
                "fecha_actual": datetime.now().strftime('%d/%m/%Y'),
                
                # Context overrides for 5.4 format block
                "numero_reporte": 1,
                "fechas_periodo": str(reqs.get('fecha_inicio_convenio', 'N/A')),
                "empresa": ue.get('nombre_comercial', 'N/A'),
                "institucion_educativa": "TESE",
                "carrera": student.get('carrera', 'N/A'),
                "nombre_alumno": f"{student.get('nombre')} {student.get('ap_paterno')}",
            }

            st.markdown("---")
            import tempfile
            out_dir = tempfile.gettempdir()
            
            def render_coordinator_doc_card(title, desc, req_met, disabled_msg, btn_key, dl_key, filename, template_tgt, is_anexo_5_1=False):
                st.markdown(f"**{title}**")
                st.write(desc)
                
                if not req_met:
                    st.error(disabled_msg)
                else:
                    st.success("✅ Este anexo o documento ya es posible generarlo completo.")
                    
                path_base = os.path.join(out_dir, f"{filename}_{student['matricula']}")
                pdf_path = f"{path_base}.pdf"
                docx_path = f"{path_base}.docx"
                
                fmt_options = ["PDF", "Word (DOCX)"]
                fmt_indiv = st.radio("Formato de Documento", fmt_options, key=f"fmt_{btn_key}", horizontal=True)

                if st.button(f"Generar {title.split('-')[0].strip('📄✉️📝 ')}", key=btn_key, disabled=not req_met):
                    to_pdf = (fmt_indiv == "PDF")
                    with st.spinner("Compilando..."):
                        if is_anexo_5_1:
                            ctx_data, msg_err = get_anexo_5_1_data(student_id)
                        else:
                            ctx_data, msg_err = generic_context, None
                        
                        if msg_err and is_anexo_5_1:
                            st.error(f"Error recuperando datos: {msg_err}")
                        else:
                            base_project_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                            t_path = os.path.join(base_project_dir, "sistema_dual", "src", "templates", "docs", template_tgt)
                            
                            succ, msg_gen = generate_pdf_from_docx(template_tgt, ctx_data, pdf_path, t_path, to_pdf)
                            if succ:
                                st.session_state[f"active_fmt_{btn_key}"] = "PDF" if to_pdf else "DOCX"
                                st.success(f"{title} generado exitosamente.")
                                st.rerun()
                            else:
                                st.error(msg_gen)
                                
                file_exists = os.path.exists(pdf_path) or os.path.exists(docx_path)
                if file_exists:
                    pref_fmt = st.session_state.get(f"active_fmt_{btn_key}", "Word (DOCX)" if is_cloud else "PDF")
                    a_path = pdf_path if pref_fmt == "PDF" and os.path.exists(pdf_path) else docx_path
                    if not os.path.exists(a_path): 
                        a_path = pdf_path if os.path.exists(pdf_path) else docx_path
                        
                    is_pdf_file = a_path.endswith('.pdf')
                    st.info(f"📄 Listo: {os.path.basename(a_path)}")
                    
                    c_dl, c_mail = st.columns([1, 1])
                    with open(a_path, "rb") as f:
                        c_dl.download_button(
                            label=f"⬇️ Descargar {title.split('-')[0].strip('📄✉️📝 ')}",
                            data=f.read(),
                            file_name=os.path.basename(a_path),
                            mime="application/pdf" if is_pdf_file else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            type="primary",
                            use_container_width=True,
                            key=dl_key
                        )
                        
                    if c_mail.button(f"📧 Enviar al Alumno", key=f"mail_{btn_key}", use_container_width=True):
                        target_email = student.get('email_institucional') or student.get('email_personal')
                        if not target_email:
                            st.error("El alumno no tiene un correo registrado.")
                        else:
                            with st.spinner("Enviando correo..."):
                                success_mail = send_document_email(
                                    to_email=target_email,
                                    student_name=f"{student.get('nombre')} {student.get('ap_paterno')}",
                                    document_name=title.split('-')[0].strip('📄✉️📝 '),
                                    file_path=a_path
                                )
                                if success_mail:
                                    st.success("Documento enviado exitosamente.")
                                else:
                                    st.error("Error al enviar el correo. Verifica las credenciales del servidor SMTP general.")
                                
                st.markdown("---")

            # 1. Anexo 5.1
            render_coordinator_doc_card(
                "📄 Anexo 5.1 - Plan de Formación DUAL", "Contiene el acuerdo inicial, datos de la empresa y lista de materias.",
                has_project_and_ue, "🛑 Aún no tiene la información completa (Empresa/Mentor UE).",
                "btn_51", "dl_51", "Anexo_5.1", "Anexo_5.1_Plan_de_Formacion.docx", is_anexo_5_1=True
            )
            
            # 2. Anexo 5.4
            render_coordinator_doc_card(
                "📄 Anexo 5.4 - Reporte de Actividades", "Formato oficial para reportes.",
                has_all_reqs, "🛑 Requiere Mentor Institucional asignado además de Empresa.",
                "btn_54", "dl_54", "Anexo_5.4", "Anexo_5.4_Reporte_de_Actividades.docx"
            )

            # 3. Anexo 5.5
            render_coordinator_doc_card(
                "📄 Anexo 5.5 - Evaluación Final", "Concentrado final y seguimiento global del modelo DUAL.",
                has_all_reqs, "🛑 Requiere tener Mentor IE, Mentor UE y Proyecto Asignados.",
                "btn_55", "dl_55", "Anexo_5.5", "Anexo_5.5_Seguimiento_Modificado.docx"
            )

            # 4. Carta Mentor IE
            render_coordinator_doc_card(
                "✉️ Carta Asignación Mentor IE", "Documento probatorio de asignación institucional con sellos.",
                has_mentor_ie, "🛑 Aún no has asignado a un Mentor Institucional en el sistema.",
                "btn_carta", "dl_carta", "Carta_Mentor_IE", "Carta_Asignacion_Mentor_IE.docx"
            )

            # 5. Acta Materias
            render_coordinator_doc_card(
                "📝 Acta Calificaciones Materias", "Vaciado simulado de actas de calificaciones de periodo.",
                has_all_reqs, "🛑 Requiere tener modelo activo para vaciar acta.",
                "btn_acta", "dl_acta", "Acta_Calificaciones", "Acta_Calificaciones_Materia.docx"
            )

        with tab_admin:
            st.error("Zona de Peligro")
            st.warning("Eliminar a este alumno borrará permanentemente toda su información, historial de proyecto y calificaciones asociadas.")
            with st.form(key="delete_student_form"):
                confirm = st.checkbox("Estoy seguro que deseo dar de baja a este alumno y toda su información.")
                submitted = st.form_submit_button("Dar de Baja Definitiva")
                if submitted:
                    if confirm:
                        try:
                            supabase.table("alumnos").delete().eq("id", student_id).execute()
                            st.success("Alumno dado de baja exitosamente.")
                            st.session_state["view_student_id"] = None
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al eliminar: {e}")
                    else:
                        st.error("Debe confirmar la casilla para proceder.")

    else:
        # LIST VIEW
        tab1, tab2 = st.tabs(["Listado de Alumnos", "Registrar Nuevo Alumno"])
        
        with tab1:
            st.markdown("#### Alumnos Inscritos")
            supabase = get_supabase_client()
            
            res = supabase.table("alumnos").select("*").order("ap_paterno").execute()
            students = res.data
            
            if students:
                # Add Select All functionality
                col_sa1, col_sa2 = st.columns([1, 4])
                with col_sa1:
                    select_all = st.checkbox("☑️ Seleccionar Todos", key="sel_all_alumnos")
                
                if st.session_state.get("prev_sel_all_alumnos") != select_all:
                    st.session_state["prev_sel_all_alumnos"] = select_all
                    for s in students:
                        st.session_state[f"sel_{s['id']}"] = select_all

                # Add headers for columns
                hc0, hc1, hc2, hc3, hc4 = st.columns([0.5, 1, 2, 2, 2])
                hc0.write("**Sel.**")
                hc1.write("**Matrícula**")
                hc2.write("**Nombre del Alumno**")
                hc3.write("**Correo Institucional**")
                st.divider()

                selected_students = []
                for s in students:
                    c0, c1, c2, c3, c4 = st.columns([0.5, 1, 2, 2, 2])
                    
                    with c0:
                        is_checked = st.checkbox(" ", key=f"sel_{s['id']}")
                        if is_checked:
                            selected_students.append(s['id'])
                            
                    c1.write(f"**{s['matricula']}**")
                    c2.write(f"{s['ap_paterno']} {s['ap_materno']} {s['nombre']}")
                    c3.write(s.get('email_institucional', ''))
                    
                    with c4:
                        if st.button("Ver Expediente", key=f"view_st_{s['id']}"):
                            st.session_state["view_student_id"] = s["id"]
                            st.rerun()
                    st.divider()

                # Batch Action Area
                if selected_students:
                    st.warning(f"⚠️ {len(selected_students)} alumno(s) seleccionado(s) para dar de baja.")
                    with st.form("batch_delete_form"):
                        confirm_batch = st.checkbox("Confirmar baja definitiva de los alumnos seleccionados.")
                        if st.form_submit_button("Dar de Baja Seleccionados"):
                            if confirm_batch:
                                try:
                                    supabase.table("alumnos").delete().in_("id", selected_students).execute()
                                    st.success(f"{len(selected_students)} alumno(s) eliminados correctamente.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error en baja masiva: {e}")
                            else:
                                st.error("Por favor, marque la casilla de confirmación para proceder.")
            else:
                st.info("No hay alumnos registrados aún.")

        with tab2:
            render_registro_coordinador()
