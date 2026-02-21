import streamlit as st
import pandas as pd
import random
import string
import hashlib
from src.db_connection import get_supabase_client
from src.utils.notifications import send_email

def render_empresas():
    st.header("Gestión de Unidades Económicas (UE) y Mentores")
    supabase = get_supabase_client()

    if "view_ue_mode" not in st.session_state:
        st.session_state["view_ue_mode"] = "list"

    if st.session_state["view_ue_mode"] == "list":
        tab_list, tab_create = st.tabs(["Listado de Empresas", "Registrar Nueva UE"])

        with tab_list:
            res = supabase.table("unidades_economicas").select("*").execute()
            if res.data:
                # Add Select All functionality
                col_sa1, col_sa2 = st.columns([1, 4])
                with col_sa1:
                    select_all = st.checkbox("☑️ Seleccionar Todos", key="sel_all_empresas")
                    
                if st.session_state.get("prev_sel_all_empresas") != select_all:
                    st.session_state["prev_sel_all_empresas"] = select_all
                    for ue in res.data:
                        st.session_state[f"sel_ue_{ue['id']}"] = select_all
                        
                hc0, hc1, hc2, hc3 = st.columns([0.5, 3, 2, 2])
                hc0.write("**Sel.**")
                hc1.write("**Nombre Comercial**")
                hc2.write("**Razón Social**")
                hc3.write("**Acciones**")
                st.divider()

                selected_companies = []
                
                for ue in res.data:
                    c0, c1, c2, c3 = st.columns([0.5, 3, 2, 2])
                    
                    with c0:
                        is_checked = st.checkbox(" ", key=f"sel_ue_{ue['id']}")
                        if is_checked:
                            selected_companies.append(ue['id'])
                            
                    c1.write(f"**{ue['nombre_comercial']}**")
                    c2.write(f"{ue['razon_social']}")
                    
                    with c3.popover("Acciones"):
                        # View Details Button
                        if st.button("Ver Detalles", key=f"view_{ue['id']}"):
                            st.session_state["selected_ue_id"] = ue["id"]
                            st.session_state["selected_ue_name"] = ue["nombre_comercial"]
                            st.session_state["view_ue_mode"] = "detail"
                            st.rerun()

                        st.divider()

                        # Edit Button
                        st.markdown("##### Editar Empresa")
                        with st.form(f"edit_ue_{ue['id']}"):
                            e_nombre = st.text_input("Nombre Comercial", value=ue['nombre_comercial'])
                            e_razon = st.text_input("Razón Social", value=ue['razon_social'])
                            e_rfc = st.text_input("RFC", value=ue.get('rfc', ''))
                            e_dir = st.text_area("Dirección", value=ue.get('direccion_fiscal', ''))
                            
                            if st.form_submit_button("Guardar Cambios"):
                                supabase.table("unidades_economicas").update({
                                    "nombre_comercial": e_nombre,
                                    "razon_social": e_razon,
                                    "rfc": e_rfc,
                                    "direccion_fiscal": e_dir
                                }).eq("id", ue['id']).execute()
                                st.success("Actualizado")
                                st.rerun()
                        
                        st.divider()
                        
                        # Delete Button
                        st.error("Zona de Peligro")
                        if st.button("Eliminar Empresa", key=f"del_ue_{ue['id']}"):
                            try:
                                supabase.table("unidades_economicas").delete().eq("id", ue['id']).execute()
                                st.success("Eliminada")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al eliminar: {e}")
                    
                    st.divider()
                    
                # Batch Action Area
                if selected_companies:
                    st.warning(f"⚠️ {len(selected_companies)} empresa(s) seleccionada(s) para eliminar.")
                    with st.form("batch_delete_empresas_form"):
                        confirm_batch = st.checkbox("Confirmar eliminación definitiva de las empresas seleccionadas.")
                        if st.form_submit_button("Eliminar Seleccionados"):
                            if confirm_batch:
                                try:
                                    supabase.table("unidades_economicas").delete().in_("id", selected_companies).execute()
                                    st.success(f"{len(selected_companies)} empresa(s) eliminada(s) correctamente.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error en baja masiva: {e}")
                            else:
                                st.error("Por favor, marque la casilla de confirmación para proceder.")
                                
                    st.info(f"ℹ️ {len(selected_companies)} empresa(s) seleccionada(s) para enviar credenciales a sus Mentores.")
                    with st.form("batch_send_credentials_ue_form"):
                        if st.form_submit_button("📧 Enviar Credenciales a Mentores UE Seleccionados"):
                            import random, string, hashlib
                            from src.utils.notifications import send_email
                            
                            try:
                                # Get Mentores UE for the selected companies
                                res_mentors = supabase.table("mentores_ue").select("*").in_("ue_id", selected_companies).execute()
                                mentors = res_mentors.data if res_mentors.data else []
                                
                                sent_count = 0
                                for m in mentors:
                                    if m.get('email'):
                                        raw_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                                        hash_pw = hashlib.sha256(raw_pw.encode('utf-8')).hexdigest()
                                        supabase.table("mentores_ue").update({"password_hash": hash_pw}).eq("id", m['id']).execute()
                                        
                                        ctx = {
                                            "mentor_nombre": m['nombre_completo'],
                                            "mentor_email": m['email'],
                                            "mentor_password": raw_pw
                                        }
                                        send_email(m['email'], "Credenciales de Acceso Mentor UE - Sistema DUAL", "recuperacion_mentor.html", ctx)
                                        sent_count += 1
                                        
                                st.success(f"Se generaron y enviaron credenciales a {sent_count} Mentores UE.")
                            except Exception as e:
                                st.error(f"Error al enviar credenciales masivas: {e}")
            else:
                st.info("No hay unidades económicas registradas.")

        with tab_create:
            st.subheader("Alta de Unidad Económica")
            with st.form("frm_ue"):
                c1, c2 = st.columns(2)
                with c1:
                    nombre = st.text_input("Nombre Comercial")
                    razon = st.text_input("Razón Social")
                    rfc = st.text_input("RFC")
                with c2:
                    direccion = st.text_area("Dirección Fiscal")
                
                resumen = st.text_area("Resumen de la Empresa")
                mision = st.text_area("Misión")
                vision = st.text_area("Visión")
                
                c3, c4 = st.columns(2)
                with c3:
                    herramientas = st.text_area("Herramientas (Hardware/Software)")
                with c4:
                    certificaciones = st.text_area("Certificaciones Destacadas")

                st.markdown("---")
                st.markdown("##### Datos del Mentor UE")
                st.caption("Registre aquí al mentor industrial responsable.")
                
                cm1, cm2 = st.columns(2)
                with cm1:
                    m_nombre = st.text_input("Nombre del Mentor (con Grado)", key="ue_reg_m_nombre")
                    m_cargo = st.text_input("Cargo del Mentor", key="ue_reg_m_cargo")
                with cm2:
                    m_email = st.text_input("Correo del Mentor", key="ue_reg_m_email")
                    m_tel = st.text_input("Teléfono del Mentor", key="ue_reg_m_tel")

                submitted = st.form_submit_button("Guardar Empresa")
                
                if submitted:
                    nombre = nombre.strip()
                    razon = razon.strip()
                    rfc = rfc.strip()
                    direccion = direccion.strip()
                    m_nombre = m_nombre.strip()
                    m_cargo = m_cargo.strip()
                    m_email = m_email.strip()
                    m_tel = m_tel.strip()
                    
                    if not nombre:
                         st.error("El Nombre Comercial es obligatorio.")
                    elif not m_nombre or not m_cargo or not m_email or not m_tel:
                         st.error("Todos los datos del Mentor son obligatorios.")
                    else:
                        new_ue = {
                            "nombre_comercial": nombre,
                            "razon_social": razon,
                            "rfc": rfc,
                            "direccion_fiscal": direccion,
                            "resumen": resumen,
                            "mision": mision,
                            "vision": vision,
                            "herramientas_hw_sw": herramientas,
                            "certificaciones": certificaciones
                        }
                        try:
                            # 1. Insert Company
                            res_ue = supabase.table("unidades_economicas").insert(new_ue).execute()
                            if res_ue.data:
                                new_ue_id = res_ue.data[0]['id']
                                
                                # Generate a random 8-char alphanumeric password
                                raw_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                                hashed_pwd = hashlib.sha256(raw_password.encode('utf-8')).hexdigest()
                                
                                # 2. Insert Mentor (Mandatory)
                                new_mentor = {
                                    "ue_id": new_ue_id,
                                    "nombre_completo": m_nombre,
                                    "cargo": m_cargo,
                                    "email": m_email,
                                    "telefono": m_tel,
                                    "password_hash": hashed_pwd
                                }
                                supabase.table("mentores_ue").insert(new_mentor).execute()
                                
                                # 3. Send Email with Credentials
                                context_email = {
                                    "mentor_nombre": m_nombre,
                                    "empresa_nombre": nombre,
                                    "mentor_email": m_email,
                                    "mentor_password": raw_password
                                }
                                
                                # Email the Mentor directly
                                send_email(m_email, "Credenciales de Acceso - Sistema DUAL", "nuevo_mentor.html", context_email)
                                
                                st.info(f"Contraseña temporal generada: **{raw_password}** (Guarda esta contraseña, ya fue enviada por correo pero puedes proporcionarla directamente al mentor).")
                                
                                # Coordinador Copy (BCC Simulator)
                                send_email("jairyanez44@gmail.com", f"Copia CCO (Sistema DUAL) - Credenciales {nombre}", "base_notification.html", context)
                                
                                st.success(f"Empresa '{nombre}' y Mentor '{m_nombre}' registrados exitosamente. Se ha enviado un correo con la contraseña.")
                                
                                st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")

    elif st.session_state["view_ue_mode"] == "detail":
        ue_id = st.session_state["selected_ue_id"]
        ue_name = st.session_state["selected_ue_name"]
        
        c_back, c_title = st.columns([1, 5])
        c_back.button("< Volver", on_click=lambda: st.session_state.update({"view_ue_mode": "list"}), key="btn_back_list")
        c_title.markdown(f"### {ue_name}")
        
        # Details Tab
        tab_det, tab_mentors, tab_students = st.tabs(["📝 Información General", "👥 Mentores UE", "🎓 Alumnos Asignados"])
        
        # -- TAB 1: GENERAL INFO (EDITABLE) --
        with tab_det:
             res_det = supabase.table("unidades_economicas").select("*").eq("id", ue_id).single().execute()
             if res_det.data:
                 ue = res_det.data
                 
                 with st.form("edit_full_ue"):
                     st.markdown("#### Editar Información de la Empresa")
                     
                     col_e1, col_e2 = st.columns(2)
                     with col_e1:
                         ed_nombre = st.text_input("Nombre Comercial", value=ue.get('nombre_comercial', ''))
                         ed_razon = st.text_input("Razón Social", value=ue.get('razon_social', ''))
                         ed_rfc = st.text_input("RFC", value=ue.get('rfc', ''))
                         ed_dir = st.text_area("Dirección Fiscal", value=ue.get('direccion_fiscal', '') or ue.get('direccion', '')) # Fallback
                         
                     with col_e2:
                         ed_mision = st.text_area("Misión", value=ue.get('mision', ''))
                         ed_vision = st.text_area("Visión", value=ue.get('vision', ''))
                         ed_hw = st.text_area("Herramientas (HW/SW)", value=ue.get('herramientas_hw_sw', ''))
                         ed_cert = st.text_area("Certificaciones", value=ue.get('certificaciones', ''))
                         ed_resumen = st.text_area("Resumen", value=ue.get('resumen', ''))
                         
                     if st.form_submit_button("💾 Guardar Cambios Generales"):
                         ed_nombre = ed_nombre.strip()
                         ed_razon = ed_razon.strip()
                         ed_rfc = ed_rfc.strip()
                         ed_dir = ed_dir.strip()
                         
                         updates = {
                             "nombre_comercial": ed_nombre,
                             "razon_social": ed_razon,
                             "rfc": ed_rfc,
                             "direccion_fiscal": ed_dir,
                             "mision": ed_mision,
                             "vision": ed_vision,
                             "herramientas_hw_sw": ed_hw,
                             "certificaciones": ed_cert,
                             "resumen": ed_resumen
                         }
                         try:
                             supabase.table("unidades_economicas").update(updates).eq("id", ue_id).execute()
                             st.success("Información actualizada correctamente.")
                             st.session_state["selected_ue_name"] = ed_nombre # Update title
                             st.rerun()
                         except Exception as e:
                             st.error(f"Error al actualizar: {e}")
             else:
                 st.error("No se encontró la información de la empresa.")

        # -- TAB 2: MENTORS --
        with tab_mentors:
            st.markdown("##### Mentores Registrados")
            
            # List Mentors
            res_mentors = supabase.table("mentores_ue").select("*").eq("ue_id", ue_id).execute()
            mentors = res_mentors.data if res_mentors.data else []
            
            if mentors:
                for mm in mentors:
                    with st.container():
                        mc1, mc2, mc3 = st.columns([2, 2, 1])
                        mc1.markdown(f"**{mm['nombre_completo']}**")
                        mc1.caption(f"Cargo: {mm.get('cargo', 'N/A')}")
                        
                        mc2.markdown(f"📧 {mm.get('email', 'N/A')}")
                        mc2.markdown(f"📞 {mm.get('telefono', 'N/A')}")
                        
                        with mc3.popover("Editar Mentor"):
                            with st.form(f"edit_m_{mm['id']}"):
                                em_nom = st.text_input("Nombre", value=mm['nombre_completo'])
                                em_car = st.text_input("Cargo", value=mm.get('cargo', ''))
                                em_ema = st.text_input("Email", value=mm.get('email', ''))
                                em_tel = st.text_input("Tel", value=mm.get('telefono', ''))
                                
                                if st.form_submit_button("Actualizar"):
                                    em_nom = em_nom.strip()
                                    em_car = em_car.strip()
                                    em_ema = em_ema.strip()
                                    em_tel = em_tel.strip()
                                    
                                    supabase.table("mentores_ue").update({
                                        "nombre_completo": em_nom,
                                        "cargo": em_car,
                                        "email": em_ema,
                                        "telefono": em_tel
                                    }).eq("id", mm['id']).execute()
                                    st.success("Guardado")
                                    st.rerun()
                                    
                            st.divider()
                            
                            # Generar nuevo acceso
                            if st.button("🔑 Generar Nueva Contraseña", key=f"gen_pass_{mm['id']}", help="Genera una nueva contraseña temporal y la envía por correo."):
                                import random, string, hashlib
                                raw_pw = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                                hash_pw = hashlib.sha256(raw_pw.encode('utf-8')).hexdigest()
                                supabase.table("mentores_ue").update({"password_hash": hash_pw}).eq("id", mm['id']).execute()
                                
                                ctx = {
                                    "mentor_nombre": mm['nombre_completo'],
                                    "mentor_email": mm.get('email', ''),
                                    "mentor_password": raw_pw
                                }
                                from src.utils.notifications import send_email
                                send_email(mm.get('email', ''), "Recuperación de Acceso - Sistema DUAL", "recuperacion_mentor.html", ctx)
                                st.success(f"Contraseña regenerada y enviada a {mm['nombre_completo']}.")
                                st.info(f"Contraseña temporal nueva: **{raw_pw}** (Cópiala y envíala directamente si es necesario o verifícala aquí).")
                            
                            st.divider()
                            
                            if st.button("Eliminar", key=f"del_mue_{mm['id']}"):
                                supabase.table("mentores_ue").delete().eq("id", mm['id']).execute()
                                st.success("Eliminado")
                                st.rerun()
                        st.divider()
            else:
                st.info("No hay mentores registrados.")

            # Add Mentor
            with st.expander("➕ Registrar Nuevo Mentor"):
                with st.form("add_mentor_new"):
                    cm1, cm2 = st.columns(2)
                    with cm1:
                        m_nombre = st.text_input("Nombre Completo")
                        m_cargo = st.text_input("Cargo")
                    with cm2:
                        m_email = st.text_input("Correo Electrónico")
                        m_tel = st.text_input("Teléfono")
                    
                    if st.form_submit_button("Guardar Mentor"):
                        m_nombre = m_nombre.strip()
                        m_cargo = m_cargo.strip()
                        m_email = m_email.strip()
                        m_tel = m_tel.strip()
                        
                        if not m_nombre:
                            st.error("Nombre requerido.")
                        else:
                            try:
                                supabase.table("mentores_ue").insert({
                                    "ue_id": ue_id,
                                    "nombre_completo": m_nombre,
                                    "cargo": m_cargo,
                                    "email": m_email,
                                    "telefono": m_tel
                                }).execute()
                                st.success("Mentor agregado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")

        # -- TAB 3: STUDENTS (NEW) --
        with tab_students:
            st.markdown("##### Alumnos Asignados (Proyectos Activos)")
            
            # Query projects linked to this UE
            # We want student info, so we join with 'alumnos' and then 'carreras' to get the name
            res_projs = supabase.table("proyectos_dual").select(
                "*, alumnos(matricula, nombre, ap_paterno, ap_materno, carreras(nombre)), mentores_ue(nombre_completo)"
            ).eq("ue_id", ue_id).execute()
            
            projs = res_projs.data if res_projs.data else []
            
            if projs:
                st.metric("Total Alumnos", len(projs))
                
                data_studs = []
                for p in projs:
                    stud = p.get("alumnos", {})
                    mentor = p.get("mentores_ue", {})
                    # Extract career name from nested dict
                    carrera_obj = stud.get("carreras", {}) if stud else {}
                    carrera_name = carrera_obj.get("nombre", "Sin Carrera") if carrera_obj else "Sin Carrera"

                    data_studs.append({
                        "Matrícula": stud.get("matricula"),
                        "Alumno": f"{stud.get('nombre')} {stud.get('ap_paterno')} {stud.get('ap_materno')}",
                        "Carrera": carrera_name,
                        "Proyecto": p.get("nombre_proyecto"),
                        "Mentor Asignado": mentor.get("nombre_completo") if mentor else "Sin Mentor"
                    })
                
                st.dataframe(pd.DataFrame(data_studs), use_container_width=True)
            else:
                st.info("No hay alumnos asignados a esta empresa actualmente.")
