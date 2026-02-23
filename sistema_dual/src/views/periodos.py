import streamlit as st
from datetime import datetime
from src.db_connection import get_supabase_client
from src.utils.email_sender import send_period_invites

def wipe_mentor_passwords(supabase):
    """Borra todas las contraseñas de los Mentores UE cuando se cierra un periodo."""
    try:
        supabase.table("mentores_ue").update({"password_hash": None}).neq("nombre_completo", "").execute()
    except Exception as e:
        print(f"Error wiped: {e}")

def render_periodos():
    st.subheader("Gestión de Periodos Escolares")
    
    supabase = get_supabase_client()
    
    # Get User Context (Coordinator career)
    user = st.session_state.get("user", {})
    coordinator_career_id = user.get("carrera_id")

    # --- Action: Create New Period ---
    with st.expander("Crear Nuevo Periodo"):
        with st.form("new_period_form"):
            nombre_periodo = st.text_input("Nombre del Periodo (Ej. 2026-1)")
            
            c_dates1, c_dates2, c_dates3 = st.columns(3)
            with c_dates1:
                fecha_inicio = st.date_input("Fecha Inicio", value=datetime.today())
            with c_dates2:
                fecha_fin = st.date_input("Fecha Fin", value=datetime.today())
            with c_dates3:
                fecha_limite = st.date_input("Fecha Límite Registro", value=datetime.today())

            st.markdown("###### Las 5 Fases DUAL")
            st.caption("Configura las fechas dentro del periodo actual para cada fase del modelo DUAL.")
            st.info("Fase 1: Registro de Alumnos. (Utiliza la Fecha Límite de Registro de arriba)")
            
            # Fase 2
            st.write("**Fase 2: Asignación (Plan de Formación Anexo 5.1)** - Se asigna Mentor IE, se genera Anexo 5.1 y Cartas.")
            col_d1_start, col_d1_end = st.columns(2)
            d1_inicio = col_d1_start.date_input("Inicio Fase 2", value=datetime.today())
            d1_fin = col_d1_end.date_input("Fin Fase 2", value=datetime.today())
            
            # Fase 3
            st.write("**Fase 3: Evaluación UE (70%)** - Mentores de Empresa (UE) envían Anexo 5.4 y evalúan competencia.")
            col_d2_start, col_d2_end = st.columns(2)
            d2_inicio = col_d2_start.date_input("Inicio Fase 3", value=datetime.today())
            d2_fin = col_d2_end.date_input("Fin Fase 3", value=datetime.today())
            
            # Fase 4
            st.write("**Fase 4: Evaluación IE (30%)** - Mentores Académicos evalúan por materia.")
            col_d3_start, col_d3_end = st.columns(2)
            d3_inicio = col_d3_start.date_input("Inicio Fase 4", value=datetime.today())
            d3_fin = col_d3_end.date_input("Fin Fase 4", value=datetime.today())
            
            # Fase 5
            st.write("**Fase 5: Cierre** - Finalización y actas firmadas.")
            col_d4_start, col_d4_end = st.columns(2)
            d4_inicio = col_d4_start.date_input("Inicio Fase 5", value=datetime.today())
            d4_fin = col_d4_end.date_input("Fin Fase 5", value=datetime.today())
            
            # Extensión / Otros
            col_d5_start, col_d5_end = st.columns(2)
            d5_inicio = col_d5_start.date_input("Extensión/Opcional (Inicio)", value=datetime.today())
            d5_fin = col_d5_end.date_input("Extensión/Opcional (Fin)", value=datetime.today())
            st.divider()
            notificar_correo = st.text_input("Enviar calendario (.ics) a este correo (opcional):", help="Si proporcionas un correo, enviaremos archivos de calendario para que los guardes y recuerdes las fechas límite de los documentos.")
            is_active = st.checkbox("Establecer como Activo", value=False)
            
            submitted = st.form_submit_button("Crear Periodo")
            
        if submitted:
            nombre_periodo = nombre_periodo.strip()
            if not nombre_periodo:
                st.error("El nombre es requerido.")
            else:
                try:
                    # Deactivate others if this one is active (Scoped by Career)
                    if is_active:
                        query_deact = supabase.table("periodos").update({"activo": False}).neq("id", "00000000-0000-0000-0000-000000000000")
                        if coordinator_career_id:
                            query_deact = query_deact.eq("carrera_id", coordinator_career_id)
                        query_deact.execute()
                        wipe_mentor_passwords(supabase)
                    
                    new_period = {
                        "nombre": nombre_periodo,
                        "fecha_inicio": str(fecha_inicio),
                        "fecha_fin": str(fecha_fin),
                        "fecha_limite_registro": str(fecha_limite),
                        "inicio_anexo_1": str(d1_inicio),
                        "fin_anexo_1": str(d1_fin),
                        "inicio_anexo_2": str(d2_inicio),
                        "fin_anexo_2": str(d2_fin),
                        "inicio_anexo_3": str(d3_inicio),
                        "fin_anexo_3": str(d3_fin),
                        "inicio_doc_4": str(d4_inicio),
                        "fin_doc_4": str(d4_fin),
                        "inicio_doc_5": str(d5_inicio),
                        "fin_doc_5": str(d5_fin),
                        "activo": is_active,
                        "carrera_id": coordinator_career_id # Associate logic
                    }
                    
                    supabase.table("periodos").insert(new_period).execute()
                    st.success(f"Periodo '{nombre_periodo}' creado exitosamente.")
                    
                    if notificar_correo:
                        dates_dict = {
                            "Anexo 1 (Plan de Formación)": (d1_inicio, d1_fin),
                            "Anexo 2 (Carta de Asignación)": (d2_inicio, d2_fin),
                            "Anexo 3 (Reporte Bimestral)": (d3_inicio, d3_fin),
                            "Documento 4": (d4_inicio, d4_fin),
                            "Documento 5": (d5_inicio, d5_fin)
                        }
                        send_period_invites(notificar_correo, nombre_periodo, dates_dict)
                        st.info(f"Invitaciones de calendario enviadas a: {notificar_correo}")
                        
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al crear: {e}")

    # --- List Periods ---
    st.markdown("#### Listado de Periodos")
    
    query = supabase.table("periodos").select("*").order("created_at", desc=True)
    if coordinator_career_id:
        query = query.eq("carrera_id", coordinator_career_id)
        
    res = query.execute()
    periods = res.data if res.data else []
    
    if periods:
        for p in periods:
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"**{p['nombre']}**")
            c1.caption(f"📅 **Inicio:** {p.get('fecha_inicio', 'N/A')} &nbsp;|&nbsp; **Fin:** {p.get('fecha_fin', 'N/A')}")
            c1.caption(f"📝 **Límite Registro:** {p.get('fecha_limite_registro', 'N/A')}")
            
            with c1.expander("Ver Fechas de Entrega (Anexos)", expanded=False):
                st.markdown(f"""
                - **Fase 1 (Registro):** Hasta {p.get('fecha_limite_registro', 'N/A')}
                - **Fase 2 (Asignación/A5.1):** {p.get('inicio_anexo_1', 'N/A')} al {p.get('fin_anexo_1', 'N/A')}
                - **Fase 3 (Eval. UE 70%):** {p.get('inicio_anexo_2', 'N/A')} al {p.get('fin_anexo_2', 'N/A')}
                - **Fase 4 (Eval. IE 30%):** {p.get('inicio_anexo_3', 'N/A')} al {p.get('fin_anexo_3', 'N/A')}
                - **Fase 5 (Cierre):** {p.get('inicio_doc_4', 'N/A')} al {p.get('fin_doc_4', 'N/A')}
                """)
            
            if p['activo']:
                c2.success("ACTIVO")
            else:
                c2.caption("Inactivo")
                
            col_actions = st.columns([1, 1, 1, 1])
            
            if not p['activo']:
                # Activate Button
                if col_actions[0].button("activar", key=f"btn_act_{p['id']}", help="Establecer como periodo activo actual"):
                     # Deactivate all (Scoped)
                    q_d = supabase.table("periodos").update({"activo": False})
                    if coordinator_career_id:
                        q_d = q_d.eq("carrera_id", coordinator_career_id)
                    q_d.execute()
                    wipe_mentor_passwords(supabase)
                    
                    # Activate this one
                    supabase.table("periodos").update({"activo": True}).eq("id", p['id']).execute()
                    st.rerun()

            # Edit Button (Expander)
            with col_actions[1].popover("Editar"):
                st.markdown(f"Editar **{p['nombre']}**")
                with st.form(f"edit_period_{p['id']}"):
                    new_name = st.text_input("Nombre", value=p['nombre'])
                    # Parse dates if they are strings, or keep if date objects (usually strings from JSON)
                    # Helper to parse YYYY-MM-DD
                    def parse_date(d_str):
                        if isinstance(d_str, str):
                            return datetime.strptime(d_str, '%Y-%m-%d').date()
                        return d_str

                    n_inicio = st.date_input("Inicio", value=parse_date(p.get('fecha_inicio', datetime.today())))
                    n_fin = st.date_input("Fin", value=parse_date(p.get('fecha_fin', datetime.today())))
                    n_lim = st.date_input("Límite Reg.", value=parse_date(p.get('fecha_limite_registro', datetime.today())))
                    
                    st.markdown("###### Fases del Modelo DUAL")
                    
                    # Fase 2
                    ce_d1_1, ce_d1_2 = st.columns(2)
                    n_d1_inicio = ce_d1_1.date_input("Inicio Fase 2", value=parse_date(p.get("inicio_anexo_1", n_inicio)))
                    n_d1_fin = ce_d1_2.date_input("Fin Fase 2", value=parse_date(p.get("fin_anexo_1", n_fin)))
                    
                    # Fase 3
                    ce_d2_1, ce_d2_2 = st.columns(2)
                    n_d2_inicio = ce_d2_1.date_input("Inicio Fase 3", value=parse_date(p.get("inicio_anexo_2", n_inicio)))
                    n_d2_fin = ce_d2_2.date_input("Fin Fase 3", value=parse_date(p.get("fin_anexo_2", n_fin)))
                    
                    # Fase 4
                    ce_d3_1, ce_d3_2 = st.columns(2)
                    n_d3_inicio = ce_d3_1.date_input("Inicio Fase 4", value=parse_date(p.get("inicio_anexo_3", n_inicio)))
                    n_d3_fin = ce_d3_2.date_input("Fin Fase 4", value=parse_date(p.get("fin_anexo_3", n_fin)))

                    # Fase 5
                    ce_d4_1, ce_d4_2 = st.columns(2)
                    n_d4_inicio = ce_d4_1.date_input("Inicio Fase 5", value=parse_date(p.get("inicio_doc_4", n_inicio)))
                    n_d4_fin = ce_d4_2.date_input("Fin Fase 5", value=parse_date(p.get("fin_doc_4", n_fin)))

                    # Doc 5 Edit
                    ce_d5_1, ce_d5_2 = st.columns(2)
                    n_d5_inicio = ce_d5_1.date_input("Inicio Extra", value=parse_date(p.get("inicio_doc_5", n_inicio)))
                    n_d5_fin = ce_d5_2.date_input("Fin Extra", value=parse_date(p.get("fin_doc_5", n_fin)))
                    
                    if st.form_submit_button("Guardar Cambios"):
                        supabase.table("periodos").update({
                            "nombre": new_name,
                            "fecha_inicio": str(n_inicio),
                            "fecha_fin": str(n_fin),
                            "fecha_limite_registro": str(n_lim),
                            "inicio_anexo_1": str(n_d1_inicio),
                            "fin_anexo_1": str(n_d1_fin),
                            "inicio_anexo_2": str(n_d2_inicio),
                            "fin_anexo_2": str(n_d2_fin),
                            "inicio_anexo_3": str(n_d3_inicio),
                            "fin_anexo_3": str(n_d3_fin),
                            "inicio_doc_4": str(n_d4_inicio),
                            "fin_doc_4": str(n_d4_fin),
                            "inicio_doc_5": str(n_d5_inicio),
                            "fin_doc_5": str(n_d5_fin),
                        }).eq("id", p['id']).execute()
                        st.success("Actualizado")
                        st.rerun()
            
            if not p['activo']:
                # Delete Button
                with col_actions[2].popover("Eliminar"):
                    st.error("¿Seguro de eliminar este periodo y todos sus datos relacionados?")
                    if st.button("Sí, Eliminar", key=f"del_p_{p['id']}"):
                        try:
                            supabase.table("periodos").delete().eq("id", p['id']).execute()
                            st.success("Eliminado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

                # Purge Students Button
                with col_actions[3].popover("⚠️ Purgar"):
                    st.error("¿Seguro de ELIMINAR A TODOS LOS ALUMNOS registrados en este periodo? (Esto borrará sus Proyectos, Inscripciones y Anexos permanentemente. Los maestros, empresas y materias quedarán intactos).")
                    if st.button("Sí, Purgar Alumnos", key=f"purge_p_{p['id']}", type="primary"):
                        try:
                            # Find all students associated with this period through proyectos_dual or inscripciones
                            res_proj = supabase.table("proyectos_dual").select("alumno_id").eq("periodo_id", p['id']).execute()
                            res_insc = supabase.table("inscripciones_asignaturas").select("alumno_id").eq("periodo_id", p['id']).execute()
                            
                            student_ids = set()
                            if res_proj.data:
                                student_ids.update([row['alumno_id'] for row in res_proj.data])
                            if res_insc.data:
                                student_ids.update([row['alumno_id'] for row in res_insc.data])
                                
                            student_ids_list = list(student_ids)
                            
                            if student_ids_list:
                                supabase.table("alumnos").delete().in_("id", student_ids_list).execute()
                                st.success(f"{len(student_ids_list)} alumnos y sus datos eliminados con éxito del periodo.")
                            else:
                                st.info("No se encontraron alumnos en este periodo.")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error durante la purga: {e}")

            else:
                 with c3.popover("⚙️ Cerrar Periodo (Opciones)"):
                     st.write("**Periodo Activo.** Al cerrar el periodo, se borrarán las contraseñas temporales de los Mentores IE.")
                     
                     action_close = st.radio("Acción para los alumnos inscritos:", [
                         "1) Archivar a Todos (Finalizar)",
                         "2) Analizar y Retener (Reinscripción Automática)"
                     ], help="La Opción 2 mantendrá activos a los alumnos que aún no terminan su convenio, preparándolos para el siguiente periodo. Borrará únicamente su carga académica pero conservará su proyecto.")
                     
                     if st.button("Ejecutar Cierre de Periodo", type="primary", key=f"btn_close_adv_{p['id']}"):
                         try:
                             # 1. Disable Period & Wipe Passwords
                             supabase.table("periodos").update({"activo": False}).eq("id", p['id']).execute()
                             wipe_mentor_passwords(supabase)
                             
                             # 2. Handle Students
                             if "Archivar a Todos" in action_close:
                                 # This sets statuses to Archivados or leaves them inactive. We'll set estatus to "Terminado"
                                 # Find all students in this period
                                 res_proj = supabase.table("proyectos_dual").select("alumno_id").eq("periodo_id", p['id']).execute()
                                 if res_proj.data:
                                     s_ids = [r['alumno_id'] for r in res_proj.data]
                                     supabase.table("alumnos").update({"estatus": "Terminado"}).in_("id", s_ids).execute()
                                     st.success(f"{len(s_ids)} alumnos marcados como Terminados.")
                             
                             elif "Analizar y Retener" in action_close:
                                 res_proj = supabase.table("proyectos_dual").select("alumno_id, fecha_fin_convenio").eq("periodo_id", p['id']).execute()
                                 if res_proj.data:
                                     to_grad = []
                                     to_keep = []
                                     
                                     # Get current period end date
                                     period_end_date_str = p.get('fecha_fin')
                                     period_end_date = datetime.strptime(period_end_date_str, '%Y-%m-%d').date() if period_end_date_str else datetime.today().date()
                                     
                                     for row in res_proj.data:
                                         al_id = row['alumno_id']
                                         fin_conv_str = row.get('fecha_fin_convenio')
                                         
                                         if fin_conv_str:
                                             try:
                                                fin_conv = datetime.strptime(fin_conv_str, '%Y-%m-%d').date()
                                                if fin_conv <= period_end_date:
                                                    to_grad.append(al_id)
                                                else:
                                                    to_keep.append(al_id)
                                             except ValueError:
                                                to_keep.append(al_id) # Safe fallback
                                         else:
                                             to_keep.append(al_id) # Safe fallback
                                     
                                     if to_grad:
                                         supabase.table("alumnos").update({"estatus": "En Espera de Egreso"}).in_("id", to_grad).execute()
                                     
                                     if to_keep:
                                         supabase.table("alumnos").update({"estatus": "En Espera de Reinscripción"}).in_("id", to_keep).execute()
                                         
                                     st.success(f"{len(to_grad)} alumnos pasados a Espera de Egreso. {len(to_keep)} conservan convenio y esperan su nueva carga académica.")
                             
                             st.rerun()
                         except Exception as e:
                             st.error(f"Error al cerrar periodo: {e}")
                 
                 with c3.popover("⚠️ Purgar"):
                    st.error("¿ELIMINAR A TODOS LOS ALUMNOS de este periodo activo? (Borrando proyectos, inscripciones y anexos).")
                    if st.button("Sí, Purgar Alumnos", key=f"purge_act_{p['id']}", type="primary"):
                        try:
                            res_proj = supabase.table("proyectos_dual").select("alumno_id").eq("periodo_id", p['id']).execute()
                            res_insc = supabase.table("inscripciones_asignaturas").select("alumno_id").eq("periodo_id", p['id']).execute()
                            
                            student_ids = set()
                            if res_proj.data: student_ids.update([row['alumno_id'] for row in res_proj.data])
                            if res_insc.data: student_ids.update([row['alumno_id'] for row in res_insc.data])
                                
                            student_ids_list = list(student_ids)
                            if student_ids_list:
                                supabase.table("alumnos").delete().in_("id", student_ids_list).execute()
                                st.success(f"{len(student_ids_list)} alumnos eliminados.")
                            else:
                                st.info("No hay alumnos.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                 
            st.divider()
    else:
        st.info("No hay periodos registrados.")
