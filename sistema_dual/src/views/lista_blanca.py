import streamlit as st
import pandas as pd
from src.db_connection import get_supabase_client
import io

def render_lista_blanca():
    st.title("Lista Blanca de Alumnos")
    st.markdown("Gestione los alumnos autorizados para inscribirse en el sistema.")
    
    supabase = get_supabase_client()
    
    tab1, tab2 = st.tabs(["Cargar CSV", "Ver Lista Actual"])
    
    # Get User Context (Coordinator career)
    user = st.session_state.get("user", {})
    coordinator_career_id = user.get("carrera_id")

    with tab1:
        st.subheader("Cargar Alumnos desde CSV")
        st.info("El archivo CSV debe tener las columnas headers: MATRICULA, CURP, NOMBRE COMPLETO")
        
        uploaded_file = st.file_uploader("Seleccionar archivo CSV", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                
                # Normalize headers
                df.columns = [c.upper().strip() for c in df.columns]
                
                required_cols = ["MATRICULA", "NOMBRE COMPLETO"]
                if not all(col in df.columns for col in required_cols):
                    st.error(f"El archivo debe contener al menos las columnas: {', '.join(required_cols)}")
                else:
                    st.dataframe(df.head(), use_container_width=True)
                    st.caption(f"Total de registros a procesar: {len(df)}")
                    
                    if st.button("Procesar y Cargar Lista"):
                        progress_bar = st.progress(0)
                        success_count = 0
                        skip_count = 0
                        error_count = 0
                        
                        total = len(df)
                        
                        for i, row in df.iterrows():
                            matricula = str(row["MATRICULA"]).strip()
                            nombre = str(row["NOMBRE COMPLETO"]).strip()
                            curp = str(row.get("CURP", "")).strip() if "CURP" in df.columns else None
                            
                            try:
                                # Check duplicate (Ideally per career, but usually global unique matricula)
                                res = supabase.table("lista_blanca").select("matricula").eq("matricula", matricula).execute()
                                if res.data:
                                    skip_count += 1
                                else:
                                    # Insert
                                    new_record = {
                                        "matricula": matricula,
                                        "nombre_completo": nombre,
                                        "curp": curp,
                                        "registrado": False,
                                        "carrera_id": coordinator_career_id # Associate with Coordinator's Career
                                    }
                                    supabase.table("lista_blanca").insert(new_record).execute()
                                    success_count += 1
                            except Exception as e:
                                error_count += 1
                            
                            progress_bar.progress((i + 1) / total)
                            
                        st.success(f"Proceso finalizado: {success_count} nuevos, {skip_count} omitidos, {error_count} errores.")
                        
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

    with tab2:
        st.subheader("Alumnos Autorizados")
        
        # --- MANUAL ADD ---
        with st.expander("➕ Agregar Alumno Manualmente", expanded=False):
            with st.form("add_wb_manual"):
                c1, c2, c3 = st.columns(3)
                new_matricula = c1.text_input("Matrícula")
                new_curp = c2.text_input("CURP")
                new_nombre = c3.text_input("Nombre Completo")
                
                submitted_manual = st.form_submit_button("Agregar a Lista Blanca")
                
                if submitted_manual:
                    if new_matricula and new_nombre:
                        try:
                            # Check existence
                            res_exist = supabase.table("lista_blanca").select("*").eq("matricula", new_matricula).execute()
                            
                            if res_exist.data:
                                existing = res_exist.data[0]
                                existing_career = existing.get("carrera_id")
                                
                                if existing_career == coordinator_career_id:
                                    st.error("Esta matrícula ya existe en su lista.")
                                elif existing_career is None:
                                    # Claim orphan record
                                    supabase.table("lista_blanca").update({
                                        "carrera_id": coordinator_career_id,
                                        "nombre_completo": new_nombre.strip(),
                                        "curp": new_curp.strip() if new_curp else None
                                    }).eq("matricula", new_matricula).execute()
                                    st.success(f"Alumno '{new_nombre}' recuperado y asignado a su carrera.")
                                    st.rerun()
                                else:
                                    st.error("Esta matrícula ya está registrada en otra carrera.")
                            else:
                                supabase.table("lista_blanca").insert({
                                    "matricula": new_matricula.strip(),
                                    "curp": new_curp.strip() if new_curp else None,
                                    "nombre_completo": new_nombre.strip(),
                                    "registrado": False,
                                    "carrera_id": coordinator_career_id # Associate with Coordinator's Career
                                }).execute()
                                st.success(f"Alumno {new_nombre} agregado correctamente.")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error al agregar: {e}")
                    else:
                        st.warning("Matrícula y Nombre son obligatorios.")

        # --- LIST & ACTIONS ---
        st.divider()
        
        # Search / Filter
        c_search, c_refresh = st.columns([4, 1])
        search = c_search.text_input("Buscar matrícula o nombre", "")
        if c_refresh.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
        
        try:
             # Fetch Data (Filtered by Career if generic coordinator)
             query = supabase.table("lista_blanca").select("*").order("created_at", desc=True)
             
             if coordinator_career_id:
                 query = query.eq("carrera_id", coordinator_career_id)
                 
             res = query.execute()
             
             if res.data:
                 df = pd.DataFrame(res.data)
                 
                 # Join with Career Name if needed (Assuming generic list view)
                 # Or just show career_id/name if fetched.
                 
                 # Filter search
                 if search:
                     mask = (
                         df["matricula"].astype(str).str.contains(search, case=False) |
                         df["nombre_completo"].astype(str).str.contains(search, case=False)
                     )
                     df = df[mask]
                 
                 # Display Table
                 st.dataframe(
                     df, 
                     column_config={
                         "registrado": st.column_config.CheckboxColumn("¿Registrado?", disabled=True),
                         "created_at": st.column_config.DatetimeColumn("Fecha Carga", format="D MMM YYYY, h:mm a")
                     },
                     use_container_width=True,
                     hide_index=True
                 )
                 
                 st.divider()
                 st.subheader("🛠️ Editar / Eliminar")
                 
                 col_sel, col_act = st.columns([3, 1])
                 
                 # Select Record to Edit/Delete
                 student_options = df.apply(lambda x: f"{x['matricula']} - {x['nombre_completo']}", axis=1).tolist()
                 selected_student_str = col_sel.selectbox("Seleccione un alumno para modificar:", [""] + student_options)
                 
                 if selected_student_str:
                     sel_matricula = selected_student_str.split(" - ")[0]
                     selected_record = df[df["matricula"] == sel_matricula].iloc[0]
                     
                     with st.form("edit_wb_form"):
                         st.write(f"Editando: **{selected_record['nombre_completo']}**")
                         
                         ce1, ce2, ce3 = st.columns(3)
                         # Matricula is usually PK or unique identifier, better not editable or strict validation
                         edit_matricula = ce1.text_input("Matrícula", value=selected_record["matricula"], disabled=True) 
                         edit_curp = ce2.text_input("CURP", value=selected_record["curp"] if selected_record["curp"] else "")
                         edit_nombre = ce3.text_input("Nombre Completo", value=selected_record["nombre_completo"])
                         
                         c_edit, c_del = st.columns(2)
                         
                         submitted_edit = c_edit.form_submit_button("💾 Guardar Cambios", use_container_width=True)
                         # Delete button inside form is tricky, usually separate button outside or workaround
                         # Streamlit forms don't support multiple submit buttons with different actions easily if they are both submits
                         # But we can use logic. 
                         
                         if submitted_edit:
                             try:
                                 supabase.table("lista_blanca").update({
                                     "curp": edit_curp.strip(),
                                     "nombre_completo": edit_nombre.strip()
                                 }).eq("matricula", sel_matricula).execute()
                                 st.success("Información actualizada.")
                                 st.rerun()
                             except Exception as e:
                                 st.error(f"Error al actualizar: {e}")

                     # Delete Button (Outside Form to avoid accidental submits or confusion)
                     if st.button(f"🗑️ Eliminar a {selected_record['nombre_completo']}", type="primary"):
                         try:
                             supabase.table("lista_blanca").delete().eq("matricula", sel_matricula).execute()
                             st.success("Registro eliminado.")
                             st.rerun()
                         except Exception as e:
                             st.error(f"Error al eliminar: {e}")

             else:
                 st.info("La lista blanca está vacía.")
                 
        except Exception as e:
             st.error(f"Error al cargar la lista: {e}")
