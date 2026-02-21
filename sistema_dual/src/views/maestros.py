
import streamlit as st
import pandas as pd
import json
from src.db_connection import get_supabase_client

def render_maestros():
    st.header("Gestión de Maestros y Mentores IE")
    supabase = get_supabase_client()
    
    # Context
    selected_career_name = st.session_state.get("selected_career_name", "")
    selected_career_id = st.session_state.get("selected_career_id", None)
    
    if selected_career_name:
        st.caption(f"Gestionando para: **{selected_career_name}**")

    # Tabs for List and Create
    tab_list, tab_create = st.tabs(["Listado de Maestros", "Registrar Nuevo Maestro"])

    with tab_list:
        # Fetch Teachers Filtered by Career ID
        query = supabase.table("maestros").select("*")
        if selected_career_id:
            query = query.eq("carrera_id", selected_career_id)
            
        res = query.execute()
        
        if res.data:
            # Add Select All functionality
            col_sa1, col_sa2 = st.columns([1, 4])
            with col_sa1:
                select_all = st.checkbox("☑️ Seleccionar Todos", key="sel_all_maestros")
                
            if st.session_state.get("prev_sel_all_maestros") != select_all:
                st.session_state["prev_sel_all_maestros"] = select_all
                for m in res.data:
                    st.session_state[f"sel_m_{m['id']}"] = select_all
                    
            hc0, hc1, hc2, hc3, hc4 = st.columns([0.5, 1, 3, 2, 2])
            hc0.write("**Sel.**")
            hc1.write("**Clave**")
            hc2.write("**Nombre Completo**")
            hc3.write("**Email Institucional**")
            st.divider()
            
            selected_teachers = []
            
            # Use detailed view instead of just a dataframe
            for m in res.data:
                cont = st.container()
                c0, c1, c2, c3, c4 = cont.columns([0.5, 1, 3, 2, 2])
                
                with c0:
                    is_checked = st.checkbox(" ", key=f"sel_m_{m['id']}")
                    if is_checked:
                        selected_teachers.append(m['id'])
                        
                c1.write(f"**{m['clave_maestro']}**")
                c2.write(f"{m['nombre_completo']}")
                c3.write(f"{m['email_institucional']}")
                
                with c4.popover("Acciones"):
                    # Edit Form
                    st.markdown("##### Editar Maestro")
                    with st.form(f"edit_teacher_{m['id']}"):
                        e_clave = st.text_input("Clave", value=m['clave_maestro'])
                        e_nombre = st.text_input("Nombre", value=m['nombre_completo'])
                        e_email = st.text_input("Email", value=m['email_institucional'])
                        e_tel = st.text_input("Teléfono", value=m.get('telefono', ''))
                        e_mentor = st.checkbox("Es Mentor IE", value=m['es_mentor_ie'])
                        
                        if st.form_submit_button("Guardar Cambios"):
                            e_clave = e_clave.strip()
                            e_nombre = e_nombre.strip()
                            e_email = e_email.strip()
                            e_tel = e_tel.strip()
                            
                            supabase.table("maestros").update({
                                "clave_maestro": e_clave,
                                "nombre_completo": e_nombre,
                                "email_institucional": e_email,
                                "telefono": e_tel,
                                "es_mentor_ie": e_mentor
                            }).eq("id", m['id']).execute()
                            st.success("Maestro actualizado.")
                            st.rerun()
                    
                    st.divider()
                    
                    if st.button("Ver Información Completa", key=f"btn_view_{m['id']}"):
                        st.session_state["view_teacher_detail_id"] = m['id']
                        st.session_state["view_teacher_detail_name"] = m['nombre_completo']
                        st.rerun()

                    st.divider()

                    if m.get('es_mentor_ie'):
                        if st.button("🔑 Generar Contraseña (Mentor IE)", key=f"gen_pass_ie_{m['id']}", help="Genera una nueva contraseña temporal y la envía por correo."):
                            import random, string, hashlib
                            raw_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                            hash_pw = hashlib.sha256(raw_pw.encode('utf-8')).hexdigest()
                            supabase.table("maestros").update({"password_hash": hash_pw}).eq("id", m['id']).execute()
                            
                            ctx = {
                                "mentor_nombre": m['nombre_completo'],
                                "mentor_email": m.get('email_institucional', ''),
                                "mentor_password": raw_pw
                            }
                            from src.utils.notifications import send_email
                            send_email(m.get('email_institucional', ''), "Credenciales de Acceso Mentor IE - Sistema DUAL", "recuperacion_mentor.html", ctx)
                            st.success(f"Contraseña de Mentor IE regenerada y enviada a {m['nombre_completo']}.")
                            st.info(f"Contraseña temporal nueva: **{raw_pw}**")
                        st.divider()

                    # Delete Button
                    st.error("Zona de Peligro")
                    if st.button("Eliminar Maestro", key=f"del_m_{m['id']}"):
                        supabase.table("maestros").delete().eq("id", m['id']).execute()
                        st.success("Maestro eliminado.")
                        st.rerun()
                
                st.divider()

            # Batch Action Area
            if selected_teachers:
                st.warning(f"⚠️ {len(selected_teachers)} maestro(s) seleccionado(s) para dar de baja.")
                with st.form("batch_delete_maestros_form"):
                    confirm_batch = st.checkbox("Confirmar eliminación definitiva de los maestros seleccionados.")
                    if st.form_submit_button("Eliminar Seleccionados"):
                        if confirm_batch:
                            try:
                                supabase.table("maestros").delete().in_("id", selected_teachers).execute()
                                st.success(f"{len(selected_teachers)} maestro(s) eliminados correctamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error en baja masiva: {e}")
                        else:
                            st.error("Por favor, marque la casilla de confirmación para proceder.")
                            
                st.info(f"ℹ️ {len(selected_teachers)} maestro(s) seleccionado(s) para enviar credenciales.")
                with st.form("batch_send_credentials_maestros_form"):
                    if st.form_submit_button("📧 Enviar Credenciales a Mentores IE Seleccionados"):
                        import random, string, hashlib
                        from src.utils.notifications import send_email
                        
                        sent_count = 0
                        for t_id in selected_teachers:
                            # Only send to those who are actually Mentores IE
                            t_info = next((t for t in res.data if t['id'] == t_id), None)
                            if t_info and t_info.get('es_mentor_ie') and t_info.get('email_institucional'):
                                raw_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                                hash_pw = hashlib.sha256(raw_pw.encode('utf-8')).hexdigest()
                                supabase.table("maestros").update({"password_hash": hash_pw}).eq("id", t_id).execute()
                                
                                ctx = {
                                    "mentor_nombre": t_info['nombre_completo'],
                                    "mentor_email": t_info['email_institucional'],
                                    "mentor_password": raw_pw
                                }
                                send_email(t_info['email_institucional'], "Credenciales de Acceso Mentor IE - Sistema DUAL", "recuperacion_mentor.html", ctx)
                                sent_count += 1
                                
                        st.success(f"Se generaron y enviaron credenciales a {sent_count} Mentores IE.")
                        # We don't always rerun immediately to let them read the success message.

        else:
            st.info(f"No hay maestros registrados para {selected_career_name}.")
            
    # Handle Detail View if active
    if "view_teacher_detail_id" in st.session_state and st.session_state["view_teacher_detail_id"]:
        t_id = st.session_state["view_teacher_detail_id"]
        t_name = st.session_state["view_teacher_detail_name"]
        
        st.markdown("---")
        st.subheader(f"Detalles de: {t_name}")
        if st.button("Cerrar Detalles", key="close_det_t"):
            del st.session_state["view_teacher_detail_id"]
            st.rerun()
            
        t_tab1, t_tab2 = st.tabs(["Asignaturas Impartidas", "Alumnos Inscritos"])
        
        with t_tab1:
            # Get Subjects
            res_s = supabase.table("rel_maestros_asignaturas").select("asignatura_id, asignaturas(nombre, clave_asignatura, semestre)").eq("maestro_id", t_id).execute()
            # Note: 'grupo' is likely not in 'asignaturas' table but in the relation or students table? 
            # In 'rel_maestros_asignaturas' there is NO group. Group is defined when STUDENT registers. 
            # Wait, 'asignaturas' table has static data. 
            # Actually, the user's previous 'registro.py' code asks for 'Grupo' when registering subject. 
            # So 'Grupo' is in 'rel_alumnos_asignaturas' (or similar).
            
            # Here we just list the subjects the teacher IS AUTHORIZED to teach (linked).
            if res_s.data:
                 # Flatten data
                 subjs_list = []
                 for item in res_s.data:
                     if item.get('asignaturas'):
                         subjs_list.append(item['asignaturas'])
                 st.dataframe(pd.DataFrame(subjs_list), use_container_width=True)
            else:
                st.info("No tiene asignaturas asignadas.")

        with t_tab2:
            # Get Students enrolled with this teacher
            # We need to query 'rel_alumnos_asignaturas' (or the transaction table)
            # Schema check needed? Assuming 'rel_alumnos_asignaturas' has 'maestro_id', 'alumno_id', 'asignatura_id'.
            # Let's check schema/code usage from 'registro.py' -> 'create_student_transaction'
            
            # Based on standard logic:
            try:
                # Query rel_alumnos_asignaturas to get students
                # Note: 'grupo' column is in 'inscripciones_asignaturas' or 'rel_alumnos_asignaturas' (if it exists)
                # Checking schema: 'inscripciones_asignaturas' has 'grupo'. 
                # 'rel_maestros_asignaturas' does NOT.
                # 'proyectos_dual' does NOT.
                # 'rel_alumnos_asignaturas' - Wait, what is this table? 
                # Schema.sql says: 'inscripciones_asignaturas'.
                # The code used 'rel_alumnos_asignaturas' which might be a typo or an old table name?
                # Let's check schema.sql again. Line 152: CREATE TABLE inscripciones_asignaturas ( ... )
                # Line 7: DROP TABLE IF EXISTS inscripciones_asignaturas.
                # I suspect 'rel_alumnos_asignaturas' Does NOT exist in the new schema. 
                # It should be 'inscripciones_asignaturas'.
                
                res_students = supabase.table("inscripciones_asignaturas").select(
                    "alumno_id, alumnos(matricula, nombre, ap_paterno, ap_materno), asignatura_id, asignaturas(nombre), grupo"
                ).eq("maestro_id", t_id).execute()
                
                if res_students.data:
                    # Flatten
                    stud_list = []
                    for r in res_students.data:
                        stud = r.get('alumnos', {})
                        subj = r.get('asignaturas', {})
                        stud_list.append({
                            "Matrícula": stud.get('matricula'),
                            "Alumno": f"{stud.get('nombre')} {stud.get('ap_paterno')} {stud.get('ap_materno')}",
                            "Asignatura": subj.get('nombre'),
                            "Grupo": r.get('grupo')
                        })
                    st.dataframe(pd.DataFrame(stud_list), use_container_width=True)
                else:
                    st.info("No hay alumnos inscritos con este maestro.")
            except Exception as ex:
                st.warning(f"No se pudo cargar alumnos: {ex}")

    with tab_create:
        st.subheader("Alta de Docente / Mentor IE")
        
        with st.form("frm_maestro"):
            c1, c2 = st.columns(2)
            with c1:
                clave = st.text_input("Clave de Maestro (ID Empleado)")
                nombre = st.text_input("Nombre Completo")
                email = st.text_input("Correo Institucional")
                telefono = st.text_input("Teléfono")
            
            with c2:
                # Auto-lock division/carrera to the selected context
                if selected_career_name:
                    st.text_input("Carrera / División", value=selected_career_name, disabled=True)
                
                # Removed manual selectbox as we are enforcing context
                
                # edificio = st.text_input("Edificio") # Removed from schema for simplification or keep? Schema has it removed.
                # cubiculo = st.text_input("Cubículo") # Removed from schema
                es_mentor = st.checkbox("¿Es Mentor IE? (Disponible para proyectos DUAL)", value=False)

            st.markdown("---")
            # ... (Horarios logic removed from schema if I recall correctly? Let's check schema.sql again)
            # Schema: maestros checks: id, clave, nombre, email, telefono, carrera_id, es_mentor_ie. 
            # It removed horarios_json, ubicacion, etc in my recent schema update proposal?
            # YES, I removed them in Step 491 to simplify.
            
            # ... So I should remove them from form too.

            st.markdown("##### Asignaturas que imparte")
            
            # Filter Subjects by Career ID too!
            subj_query = supabase.table("asignaturas").select("id, nombre, clave_asignatura")
            if selected_career_id:
                subj_query = subj_query.eq("carrera_id", selected_career_id)
            res_subj = subj_query.execute()
            
            subjects = res_subj.data if res_subj.data else []
            subject_options = {f"{s['clave_asignatura']} - {s['nombre']}": s["id"] for s in subjects}
            
            selected_subject_names = st.multiselect("Seleccione las asignaturas", list(subject_options.keys()))

            submitted = st.form_submit_button("Guardar Maestro")
            
            if submitted:
                clave = clave.strip()
                nombre = nombre.strip()
                email = email.strip()
                telefono = telefono.strip()
                
                if not clave or not nombre or not email:
                    st.error("Clave, Nombre y Correo son obligatorios.")
                elif not selected_career_id:
                     st.error("Error de contexto: No se identificó la carrera.")
                else:
                    # 1. Insert Teacher
                    maestro_data = {
                        "clave_maestro": clave,
                        "nombre_completo": nombre,
                        "email_institucional": email,
                        "telefono": telefono,
                        "carrera_id": selected_career_id, # Use FK
                        "es_mentor_ie": es_mentor
                    }
                    
                    try:
                        res_ins = supabase.table("maestros").insert(maestro_data).execute()
                        if res_ins.data:
                            new_id = res_ins.data[0]["id"]
                            
                            # 2. Insert Subject Relations
                            if selected_subject_names:
                                rel_data = []
                                for name in selected_subject_names:
                                    s_id = subject_options[name]
                                    rel_data.append({"maestro_id": new_id, "asignatura_id": s_id})
                                
                                supabase.table("rel_maestros_asignaturas").insert(rel_data).execute()
                            
                            st.success(f"Maestro {nombre} registrado correctamente.")
                            st.rerun() # Refresh to show in list
                            
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
