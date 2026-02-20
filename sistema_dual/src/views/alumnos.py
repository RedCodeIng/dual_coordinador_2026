# Force Reload
import streamlit as st
import pandas as pd
import os
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
                    new_nombre = sanitize_input(new_nombre)
                    new_ap_paterno = sanitize_input(new_ap_paterno)
                    new_ap_materno = sanitize_input(new_ap_materno)
                    new_nss = sanitize_input(new_nss)
                    new_email_inst = sanitize_input(new_email_inst)
                    new_email_pers = sanitize_input(new_email_pers)
                    new_tel = sanitize_input(new_tel)
                    
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
                    
                    
                    st.markdown(f"**Empresa (Solo lectura):** {ue_name}")
                    st.markdown("**Mentor Industrial (UE) (Solo lectura):**")
                    if mentor_ue:
                         st.caption(f"{mentor_ue.get('nombre_completo')} - {mentor_ue.get('email')}")
                    else:
                         st.caption("Sin Mentor UE asignado")


                    if st.form_submit_button("Actualizar Datos del Proyecto"):
                        # Sanitize
                        new_proj_name = sanitize_input(new_proj_name)
                        new_desc = sanitize_input(new_desc)
                        
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
                    res_teachers = supabase.table("maestros").select("id, nombre_completo").eq("es_mentor_ie", True).execute()
                    if res_teachers.data:
                        teacher_opts = {t['nombre_completo']: t['id'] for t in res_teachers.data}
                        selected_new_mentor = st.selectbox("Seleccionar Manualmente", list(teacher_opts.keys()), index=None, placeholder="Seleccione un docente...")
                        
                        if st.button("Guardar Asignación Manual"):
                            if selected_new_mentor:
                                new_mentor_id = teacher_opts[selected_new_mentor]
                                supabase.table("proyectos_dual").update({"mentor_ie_id": new_mentor_id}).eq("id", proj['id']).execute()
                                st.success("Mentor Académico actualizado.")
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

        with tab_academic:
            st.markdown("##### Carga Académica")
            
            # Need to fetch enrolled subjects: inscripciones_asignaturas joined with asignaturas and maestros
            try:
                res_insc = supabase.table("inscripciones_asignaturas").select(
                    "*, asignaturas(clave_asignatura, nombre, semestre), maestros(nombre_completo)"
                ).eq("alumno_id", student_id).execute()
                
                if res_insc.data:
                    data_rows = []
                    for item in res_insc.data:
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
                else:
                    st.info("No hay asignaturas inscritas.")
            except Exception as e:
                st.error(f"Error al cargar carga académica: {e}")

        with tab_docs:
            st.markdown("##### Generación de Documentos DUAL")
            st.info("Aquí puedes generar manualmente los documentos oficiales para este alumno o enviarlos por correo.")
            
            c_doc1, c_doc2 = st.columns([3, 1])
            c_doc1.markdown("**Anexo 5.1 - Plan de Formación DUAL**")
            
            out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "output")
            os.makedirs(out_dir, exist_ok=True)
            pdf_path = os.path.join(out_dir, f"Anexo_5.1_{student['matricula']}.pdf")
            docx_path = pdf_path.replace('.pdf', '.docx')
            
            file_exists = os.path.exists(pdf_path) or os.path.exists(docx_path)
            btn_label = "Regenerar Anexo 5.1" if file_exists else "Generar Anexo 5.1"
            
            if c_doc2.button(btn_label, key="btn_gen_5_1"):
                with st.spinner("Recopilando datos y generando documento..."):
                    try:
                        data = get_anexo_5_1_data(student_id)
                        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", "Anexo_5.1_Plan_de_Formacion.docx")
                        
                        success, result_msg = generate_pdf_from_docx(
                            template_name="Anexo_5.1_Plan_de_Formacion.docx", 
                            context=data, 
                            output_path=pdf_path,
                            template_path=template_path
                        )
                        
                        if success:
                            st.success("Documento generado y guardado exitosamente.")
                            st.rerun()
                        else:
                            st.error(f"Error en la generación: {result_msg}")
                            
                    except Exception as e:
                        st.error(f"Error general al generar: {e}")

            if file_exists:
                active_path = pdf_path if os.path.exists(pdf_path) else docx_path
                is_pdf = active_path.endswith('.pdf')
                
                st.success(f"✅ Documento listo: {os.path.basename(active_path)}")
                
                col_dl, col_mail = st.columns([1, 1])
                
                # Download Button
                with open(active_path, "rb") as f:
                    file_bytes = f.read()
                
                col_dl.download_button(
                    label="⬇️ Descargar Documento",
                    data=file_bytes,
                    file_name=os.path.basename(active_path),
                    mime="application/pdf" if is_pdf else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
                
                # Email Button
                if col_mail.button("📧 Enviar por Correo al Alumno"):
                    target_email = student.get('email_institucional') or student.get('email_personal')
                    if not target_email:
                        st.error("El alumno no tiene un correo registrado.")
                    else:
                        with st.spinner("Enviando correo..."):
                            full_name = f"{student.get('nombre')} {student.get('ap_paterno')}"
                            sent = send_document_email(target_email, full_name, "Anexo 5.1 - Plan de Formación", active_path)
                            if sent:
                                st.success(f"¡Documento enviado exitosamente a {target_email}!")
                            else:
                                st.error("Ocurrió un error enviando el correo. Verifica las credenciales SMTP.")

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
                # Add headers for columns
                hc0, hc1, hc2, hc3, hc4 = st.columns([0.5, 1, 2, 2, 2])
                hc0.write("**Seleccionar**")
                hc1.write("**Matrícula**")
                hc2.write("**Nombre del Alumno**")
                hc3.write("**Correo Institucional**")
                st.divider()

                selected_students = []
                for s in students:
                    c0, c1, c2, c3, c4 = st.columns([0.5, 1, 2, 2, 2])
                    
                    with c0:
                        if st.checkbox(" ", key=f"sel_{s['id']}"): # Space label for accessibility without widening
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
