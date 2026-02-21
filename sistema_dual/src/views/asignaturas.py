
import streamlit as st
import pandas as pd
from src.db_connection import get_supabase_client

def render_asignaturas():
    st.header("Gestión de Asignaturas y Competencias")
    supabase = get_supabase_client()

    # Context
    selected_career_name = st.session_state.get("selected_career_name", "")
    selected_career_id = st.session_state.get("selected_career_id", None)

    if selected_career_name:
        st.caption(f"Gestionando para: **{selected_career_name}**")

    if "view_subject_mode" not in st.session_state:
        st.session_state["view_subject_mode"] = "list"
    
    if st.session_state["view_subject_mode"] == "list":
        # Tabs
        tab_list, tab_create = st.tabs(["Listado de Asignaturas", "Registrar Nueva Asignatura"])
        
        with tab_list:
            # Semester Filter
            col_filt_1, col_filt_2 = st.columns([1, 4])
            with col_filt_1:
                 # Fetch distinct semesters to populate filter
                 res_sems = supabase.table("asignaturas").select("semestre").execute()
                 available_sems = sorted(list(set([s['semestre'] for s in res_sems.data if s['semestre']])))
                 sel_sem = st.selectbox("Filtrar por Semestre", ["Todos"] + available_sems)
                 
            st.divider()
            
            # Filter Query
            query = supabase.table("asignaturas").select("*")
            if selected_career_id:
                query = query.eq("carrera_id", selected_career_id)
            if sel_sem != "Todos":
                query = query.eq("semestre", sel_sem)
                
            res = query.execute()
            
            if res.data:
                # Add Select All functionality
                col_sa1, col_sa2 = st.columns([1, 4])
                with col_sa1:
                    select_all = st.checkbox("☑️ Seleccionar Todos", key="sel_all_asignaturas")

                if st.session_state.get("prev_sel_all_asignaturas") != select_all:
                    st.session_state["prev_sel_all_asignaturas"] = select_all
                    for s in res.data:
                        st.session_state[f"sel_s_{s['id']}"] = select_all

                # Header row
                hc0, hc1, hc2, hc3, hc4 = st.columns([0.5, 1.5, 4, 1, 2])
                hc0.write("**Sel.**")
                hc1.caption("CLAVE")
                hc2.caption("NOMBRE DE ASIGNATURA")
                hc3.caption("SEMESTRE")
                hc4.caption("ACCIONES")
                st.markdown("---")
                
                selected_subjects = []
                
                for s in sorted(res.data, key=lambda x: (x.get('semestre', 0), x['nombre'])):
                    cont = st.container()
                    c0, c1, c2, c3, c4 = cont.columns([0.5, 1.5, 4, 1, 2])
                    
                    with c0:
                        is_checked = st.checkbox(" ", key=f"sel_s_{s['id']}")
                        if is_checked:
                            selected_subjects.append(s['id'])
                            
                    c1.write(f"**{s['clave_asignatura']}**")
                    c2.write(f"{s['nombre']}")
                    c3.write(f"Semestre {s.get('semestre', '-')}")
                    
                    with c4.popover("Acciones"):
                        # Short edit
                        st.markdown("##### Editar Básicos")
                        with st.form(f"edit_subj_{s['id']}"):
                            e_clave = st.text_input("Clave", value=s['clave_asignatura'])
                            e_nombre = st.text_input("Nombre", value=s['nombre'])
                            e_semestre = st.number_input("Semestre", min_value=1, max_value=12, value=s.get('semestre') or 1)
                            
                            if st.form_submit_button("Guardar"):
                                supabase.table("asignaturas").update({
                                    "clave_asignatura": e_clave,
                                    "nombre": e_nombre,
                                    "semestre": e_semestre
                                }).eq("id", s['id']).execute()
                                st.success("Asignatura actualizada.")
                                st.rerun()
                                
                        st.divider()
                        
                        if st.button("Ver Detalles / Competencias", key=f"btn_view_{s['id']}"):
                            st.session_state["selected_subject_id"] = s['id']
                            st.session_state["selected_subject_name"] = f"{s['clave_asignatura']} - {s['nombre']}"
                            st.session_state["view_subject_mode"] = "detail"
                            st.rerun()

                        st.divider()

                        st.error("Zona de Peligro")
                        if st.button("Eliminar Asignatura", key=f"del_s_{s['id']}"):
                            supabase.table("asignaturas").delete().eq("id", s['id']).execute()
                            st.success("Asignatura eliminada.")
                            st.rerun()
                    
                    st.divider()

                # Batch Action Area
                if selected_subjects:
                    st.warning(f"⚠️ {len(selected_subjects)} asignatura(s) seleccionada(s) para eliminar.")
                    with st.form("batch_delete_asignaturas_form"):
                        confirm_batch = st.checkbox("Confirmar eliminación definitiva de las asignaturas seleccionadas.")
                        if st.form_submit_button("Eliminar Seleccionados"):
                            if confirm_batch:
                                try:
                                    supabase.table("asignaturas").delete().in_("id", selected_subjects).execute()
                                    st.success(f"{len(selected_subjects)} asignatura(s) eliminadas correctamente.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error en baja masiva: {e}")
                            else:
                                st.error("Por favor, marque la casilla de confirmación para proceder.")
            else:
                st.info(f"No hay asignaturas registradas que coincidan con los filtros.")

        with tab_create:
            st.subheader("Alta de Asignatura")
            with st.form("frm_asignatura"):
                c1, c2 = st.columns(2)
                with c1:
                    clave = st.text_input("Clave Asignatura")
                    nombre = st.text_input("Nombre Asignatura")
                    
                    if selected_career_name:
                        st.text_input("Carrera", value=selected_career_name, disabled=True)
                    
                with c2:
                    semestre = st.number_input("Semestre (Ej. 7, 8)", min_value=1, max_value=12, value=7)
                
                submitted = st.form_submit_button("Guardar Asignatura")
                if submitted:
                    clave = clave.strip()
                    nombre = nombre.strip()
                    
                    if not clave or not nombre:
                        st.error("Clave y Nombre son obligatorios.")
                    elif not selected_career_id:
                        st.error("Error de contexto: No se identificó la carrera.")
                    else:
                        new_subj = {
                            "clave_asignatura": clave,
                            "nombre": nombre,
                            "carrera_id": selected_career_id,
                            "semestre": semestre
                        }
                        try:
                            res = supabase.table("asignaturas").insert(new_subj).execute()
                            
                            if res.data:
                                new_id = res.data[0]['id']
                                st.success(f"Asignatura {nombre} registrada.")
                                
                                # Auto-redirect to details
                                st.session_state["selected_subject_id"] = new_id
                                st.session_state["selected_subject_name"] = f"{clave} - {nombre}"
                                st.session_state["view_subject_mode"] = "detail"
                                st.rerun()
                            else:
                                st.error("No se pudo registrar la asignatura (No ID returned).")

                        except Exception as e:
                            st.error(f"Error: {e}")

    elif st.session_state["view_subject_mode"] == "detail":
        subj_id = st.session_state["selected_subject_id"]
        subj_name = st.session_state["selected_subject_name"]
        
        st.button("< Volver al Listado", on_click=lambda: st.session_state.update({"view_subject_mode": "list"}))
        st.markdown(f"### Detalles de {subj_name}")
        
        # Fetch Details
        res_det = supabase.table("asignaturas").select("*").eq("id", subj_id).single().execute()
        subj = res_det.data
        
        # --- Edit Subject Form ---
        with st.expander("Editar Datos de la Asignatura"):
            with st.form("edit_subj_form"):
                new_clave = st.text_input("Clave", value=subj.get("clave_asignatura", ""))
                new_nombre = st.text_input("Nombre", value=subj.get("nombre", ""))
                new_semestre = st.number_input("Semestre", min_value=1, max_value=12, value=subj.get("semestre", 1))
                
                if st.form_submit_button("Actualizar Asignatura"):
                    new_clave = new_clave.strip()
                    new_nombre = new_nombre.strip()
                    
                    try:
                        supabase.table("asignaturas").update({
                            "clave_asignatura": new_clave,
                            "nombre": new_nombre,
                            "semestre": new_semestre
                        }).eq("id", subj_id).execute()
                        st.success("Asignatura actualizada.")
                        st.session_state["selected_subject_name"] = f"{new_clave} - {new_nombre}"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")

 
        
        tab_comp, tab_maestros, tab_alumnos = st.tabs(["Competencias", "Maestros Asignados", "Alumnos Inscritos"])
        
        with tab_comp:
            st.markdown("#### Competencias y Actividades")
            
            # --- Logic to Recalculate Weights ---
            def recalculate_weights(subject_id):
                # 1. Get all competencies for this subject
                res_c = supabase.table("asignatura_competencias").select("id").eq("asignatura_id", subject_id).execute()
                comp_ids = [c['id'] for c in res_c.data] if res_c.data else []
                
                if not comp_ids:
                    return
                
                # 2. Count total activities
                res_a = supabase.table("actividades_aprendizaje").select("id", count="exact").in_("competencia_id", comp_ids).execute()
                total_acts = res_a.count
                
                if total_acts > 0:
                    new_weight = 100.0 / total_acts
                    # 3. Update all activities
                    supabase.table("actividades_aprendizaje").update({"ponderacion": new_weight})\
                        .in_("competencia_id", comp_ids).execute()

            # --- Add Competency Form ---
            with st.expander("Agregar Nueva Competencia"):
                with st.form("add_comp_form", clear_on_submit=True):
                    c_num = st.number_input("Número de Competencia", min_value=1, value=1)
                    c_desc = st.text_area("Descripción de la Competencia")
                    if st.form_submit_button("Guardar Competencia"):
                        try:
                            supabase.table("asignatura_competencias").insert({
                                "asignatura_id": subj_id,
                                "numero_competencia": c_num,
                                "descripcion_competencia": c_desc
                            }).execute()
                            st.success("Competencia agregada.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

            # --- List Competencies ---
            res_comps = supabase.table("asignatura_competencias").select("*").eq("asignatura_id", subj_id).order("numero_competencia").execute()
            
            if res_comps.data:
                for comp in res_comps.data:
                    with st.container():
                        # Header with Delete Button
                        c_head_1, c_head_2 = st.columns([0.85, 0.15])
                        with c_head_1:
                            st.markdown(f"#### Competencia {comp['numero_competencia']}")
                            st.markdown(f"**Descripción:** {comp['descripcion_competencia']}")
                        with c_head_2:
                            if st.button("Eliminar", key=f"del_comp_{comp['id']}", type="primary"):
                                try:
                                    supabase.table("asignatura_competencias").delete().eq("id", comp['id']).execute()
                                    # Recalculate weights for the subject just in case activities were deleted cascade
                                    recalculate_weights(subj_id)
                                    st.success("Competencia eliminada")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        # Fetch Activities for this Competency
                        res_acts = supabase.table("actividades_aprendizaje").select("*").eq("competencia_id", comp['id']).order("created_at").execute()
                        acts = res_acts.data if res_acts.data else []
                        
                        if acts:
                            st.markdown("**Actividades de Aprendizaje:**")
                            # Display as clean rows with delete buttons
                            for act in acts:
                                ca1, ca2, ca3, ca4, ca5, ca6 = st.columns([0.3, 0.1, 0.2, 0.1, 0.1, 0.1])
                                with ca1: st.caption(act["descripcion_actividad"])
                                with ca2: st.caption(f"{act['horas_dedicacion']} hr")
                                with ca3: st.caption(act["evidencia"])
                                with ca4: st.caption(act["lugar"])
                                with ca5: st.caption(f"**{act['ponderacion']}%**")
                                with ca6:
                                    if st.button("🗑️", key=f"del_act_{act['id']}", help="Eliminar actividad"):
                                        try:
                                            supabase.table("actividades_aprendizaje").delete().eq("id", act['id']).execute()
                                            recalculate_weights(subj_id)
                                            st.toast("Actividad eliminada y ponderaciones recalculadas.")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                        else:
                            st.caption("No hay actividades registradas en esta competencia.")

                        # Add Activity Form (Nested in Expander per Competency)
                        with st.expander(f"➕ Agregar Actividad a C{comp['numero_competencia']}"):
                            with st.form(f"add_act_{comp['id']}", clear_on_submit=True):
                                a_desc = st.text_input("Actividad")
                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    a_horas = st.number_input("Horas Dedicación", min_value=1, value=5)
                                with c2:
                                    a_evidencia = st.selectbox("Evidencia", ["Documento digital y escrito", "Diagrama digital y escrito", "Video documental"])
                                with c3:
                                    a_lugar = st.selectbox("Lugar", ["UE", "IE"])
                                
                                if st.form_submit_button("Guardar Actividad"):
                                    try:
                                        # Insert
                                        supabase.table("actividades_aprendizaje").insert({
                                            "competencia_id": comp['id'],
                                            "descripcion_actividad": a_desc,
                                            "horas_dedicacion": a_horas,
                                            "evidencia": a_evidencia,
                                            "lugar": a_lugar,
                                            "ponderacion": 0 # Will be updated
                                        }).execute()
                                        
                                        # Recalculate ALL weights for this subject
                                        recalculate_weights(subj_id)
                                        
                                        st.success("Actividad agregada y ponderaciones recalculadas.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        st.divider()
            else:
                st.info("No hay competencias registradas. Agrega una para comenzar.")

        with tab_maestros:
            st.markdown("#### Maestros que imparten esta asignatura")
            
            # Feature Request: Link Teacher Here
            with st.expander("Vincular Maestro a esta Asignatura"):
                # Fetch all teachers FILTERED BY CAREER (via Division)
                t_query = supabase.table("maestros").select("id, nombre_completo, clave_maestro")
                if selected_career_id:
                    t_query = t_query.eq("carrera_id", selected_career_id)
                all_teachers_res = t_query.execute()
                all_teachers = all_teachers_res.data if all_teachers_res.data else []
                
                res_rel = supabase.table("rel_maestros_asignaturas").select("maestro_id").eq("asignatura_id", subj_id).execute()
                linked_ids = [r['maestro_id'] for r in res_rel.data] if res_rel.data else []
                
                available_teachers = [t for t in all_teachers if t['id'] not in linked_ids]
                
                if available_teachers:
                    t_options = {f"{t['clave_maestro']} - {t['nombre_completo']}": t['id'] for t in available_teachers}
                    
                    with st.form("link_teacher_form"):
                        sel_teacher = st.selectbox("Seleccione Maestro", list(t_options.keys()))
                        
                        if st.form_submit_button("Vincular"):
                            t_id = t_options[sel_teacher]
                            try:
                                supabase.table("rel_maestros_asignaturas").insert({"maestro_id": t_id, "asignatura_id": subj_id}).execute()
                                st.success("Maestro vinculado exitosamente.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al vincular: {e}")
                else:
                    st.info("Todos los maestros disponibles ya están vinculados.")

            # List Linked Teachers
            if linked_ids:
                res_teachers = supabase.table("maestros").select("*").in_("id", linked_ids).execute()
                if res_teachers.data:
                     st.dataframe(pd.DataFrame(res_teachers.data)[["clave_maestro", "nombre_completo", "email_institucional"]], use_container_width=True)
            else:
                st.info("No hay maestros asignados a esta materia.")

        with tab_alumnos:
             # Query Enrollments
             res_subjs = supabase.table("inscripciones_asignaturas").select("alumno_id, grupo").eq("asignatura_id", subj_id).execute()
             a_ids = [r['alumno_id'] for r in res_subjs.data] if res_subjs.data else []
             
             if a_ids:
                 res_students = supabase.table("alumnos").select("*").in_("id", a_ids).execute()
                 if res_students.data:
                      df_students = pd.DataFrame(res_students.data)
                      # Safe access to columns
                      columns_to_show = ["matricula", "nombre", "ap_paterno"]
                      if "carrera" in df_students.columns:
                          columns_to_show.append("carrera")
                      
                      st.dataframe(df_students[columns_to_show], use_container_width=True)
                 else:
                      st.info("No se encontraron datos de los alumnos inscritos.")
             else:
                  st.info("No hay alumnos inscritos en esta materia.")
