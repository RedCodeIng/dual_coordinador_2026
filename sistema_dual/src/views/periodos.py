import streamlit as st
from datetime import datetime
from src.db_connection import get_supabase_client

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
                            "activo": is_active,
                            "carrera_id": coordinator_career_id # Associate logic
                        }
                        
                        supabase.table("periodos").insert(new_period).execute()
                        st.success(f"Periodo '{nombre_periodo}' creado.")
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
                        
                        if st.form_submit_button("Guardar Cambios"):
                            supabase.table("periodos").update({
                                "nombre": new_name,
                                "fecha_inicio": str(n_inicio),
                                "fecha_fin": str(n_fin),
                                "fecha_limite_registro": str(n_lim)
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
