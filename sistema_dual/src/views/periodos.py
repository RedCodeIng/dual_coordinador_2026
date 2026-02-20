import streamlit as st
from datetime import datetime
from src.db_connection import get_supabase_client
from src.utils.email_sender import send_period_invites

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

            st.markdown("###### Sub-Periodos para Envío de Documentos")
            st.caption("Configura las fechas dentro del periodo actual en las que se podrán generar y enviar estos Anexos/Documentos.")
            
            # Anexo 1
            col_d1_start, col_d1_end = st.columns(2)
            d1_inicio = col_d1_start.date_input("Inicio Anexo 1 (Plan de Formación)", value=datetime.today())
            d1_fin = col_d1_end.date_input("Fin Anexo 1", value=datetime.today())
            
            # Anexo 2
            col_d2_start, col_d2_end = st.columns(2)
            d2_inicio = col_d2_start.date_input("Inicio Anexo 2 (Carta de Asignación)", value=datetime.today())
            d2_fin = col_d2_end.date_input("Fin Anexo 2", value=datetime.today())
            
            # Anexo 3
            col_d3_start, col_d3_end = st.columns(2)
            d3_inicio = col_d3_start.date_input("Inicio Anexo 3 (Reporte Bimestral)", value=datetime.today())
            d3_fin = col_d3_end.date_input("Fin Anexo 3", value=datetime.today())
            
            # Documento 4
            col_d4_start, col_d4_end = st.columns(2)
            d4_inicio = col_d4_start.date_input("Inicio Doc 4 (Pendiente)", value=datetime.today())
            d4_fin = col_d4_end.date_input("Fin Doc 4", value=datetime.today())
            
            # Documento 5
            col_d5_start, col_d5_end = st.columns(2)
            d5_inicio = col_d5_start.date_input("Inicio Doc 5 (Pendiente)", value=datetime.today())
            d5_fin = col_d5_end.date_input("Fin Doc 5", value=datetime.today())
            st.divider()
            notificar_correo = st.text_input("Enviar calendario (.ics) a este correo (opcional):", help="Si proporcionas un correo, enviaremos archivos de calendario para que los guardes y recuerdes las fechas límite de los documentos.")
            is_active = st.checkbox("Establecer como Activo", value=False)
            
            submitted = st.form_submit_button("Crear Periodo")
            if submitted:
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
            
            if p['activo']:
                c2.success("ACTIVO")
            else:
                c2.caption("Inactivo")
                
            if not p['activo']:
                col_actions = st.columns([1, 1, 1])
                
                # Activate Button
                if col_actions[0].button("activar", key=f"btn_act_{p['id']}", help="Establecer como periodo activo actual"):
                     # Deactivate all (Scoped)
                    q_d = supabase.table("periodos").update({"activo": False})
                    if coordinator_career_id:
                        q_d = q_d.eq("carrera_id", coordinator_career_id)
                    q_d.execute()
                    
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
                        
                        st.markdown("###### Sub-Periodos (Ej. Anexos)")
                        
                        # Anexo 1 Edit
                        ce_d1_1, ce_d1_2 = st.columns(2)
                        n_d1_inicio = ce_d1_1.date_input("Inicio A1", value=parse_date(p.get("inicio_anexo_1", n_inicio)))
                        n_d1_fin = ce_d1_2.date_input("Fin A1", value=parse_date(p.get("fin_anexo_1", n_fin)))
                        
                        # Anexo 2 Edit
                        ce_d2_1, ce_d2_2 = st.columns(2)
                        n_d2_inicio = ce_d2_1.date_input("Inicio A2", value=parse_date(p.get("inicio_anexo_2", n_inicio)))
                        n_d2_fin = ce_d2_2.date_input("Fin A2", value=parse_date(p.get("fin_anexo_2", n_fin)))
                        
                        # Anexo 3 Edit
                        ce_d3_1, ce_d3_2 = st.columns(2)
                        n_d3_inicio = ce_d3_1.date_input("Inicio A3", value=parse_date(p.get("inicio_anexo_3", n_inicio)))
                        n_d3_fin = ce_d3_2.date_input("Fin A3", value=parse_date(p.get("fin_anexo_3", n_fin)))

                        # Doc 4 Edit
                        ce_d4_1, ce_d4_2 = st.columns(2)
                        n_d4_inicio = ce_d4_1.date_input("Inicio Doc 4", value=parse_date(p.get("inicio_doc_4", n_inicio)))
                        n_d4_fin = ce_d4_2.date_input("Fin Doc 4", value=parse_date(p.get("fin_doc_4", n_fin)))

                        # Doc 5 Edit
                        ce_d5_1, ce_d5_2 = st.columns(2)
                        n_d5_inicio = ce_d5_1.date_input("Inicio Doc 5", value=parse_date(p.get("inicio_doc_5", n_inicio)))
                        n_d5_fin = ce_d5_2.date_input("Fin Doc 5", value=parse_date(p.get("fin_doc_5", n_fin)))
                        
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

            else:
                 c3.button("ACTIVO (Cerrar)", key=f"btn_close_{p['id']}", help="Click para cerrar (desactivar) este periodo", on_click=lambda: supabase.table("periodos").update({"activo": False}).eq("id", p['id']).execute() or st.rerun())
                 
            st.divider()
    else:
        st.info("No hay periodos registrados.")
