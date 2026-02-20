import streamlit as st
import pandas as pd
from src.db_connection import get_supabase_client
from src.utils.assignment import assign_mentors_round_robin

def render_reportes():
    st.title("📊 Panel de Inteligencia y Reportes")
    st.markdown("---")
    
    supabase = get_supabase_client()
    
    # -----------------------------------------
    # GLOBAL AUTOMATIONS ROW
    # -----------------------------------------
    col_auto1, col_auto2 = st.columns(2)
    with col_auto1:
        st.info("**Asignación Global de Mentores IE**\n\nEste botón buscará a todos los alumnos con proyectos activos que NO tengan Mentor IE asignado, y se los asignará equitativamente (Round-Robin) basándose en los maestros registrados.")
        if st.button("🎲 Ejecutar Asignación Global", use_container_width=True):
            with st.spinner("Asignando..."):
                success, msg = assign_mentors_round_robin()
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    
    with col_auto2:
         st.warning("**Envío Masivo de Documentos**\n\nEste botón generará y enviará los documentos según las fechas del Periodo Activo a los alumnos que corresponda.")
         if st.button("📧 Ejecutar Envío Masivo DUAL", use_container_width=True):
              st.info("Función en construcción. Se enlazará con la generación de Anexo 5.1.")

    st.markdown("---")
    
    # -----------------------------------------
    # DETAILED DATA EXPLORER
    # -----------------------------------------
    st.subheader("Explorador de Datos Detallado")
    
    # Selection of what to view
    view_type = st.selectbox("Seleccione la vista de datos:", 
                             ["Alumnos Registrados", "Maestros Inscritos", "Unidades Económicas", "Proyectos DUAL"])

    if view_type == "Alumnos Registrados":
        res_alumnos = supabase.table("alumnos").select("*, carreras(nombre)").execute()
        if res_alumnos.data:
            df = pd.DataFrame(res_alumnos.data)
            df['Carrera'] = df['carreras'].apply(lambda x: x.get('nombre') if x else 'N/A')
            
            # Filters
            c_f1, c_f2 = st.columns(2)
            carrera_filter = c_f1.multiselect("Filtrar por Carrera", options=df['Carrera'].unique())
            estatus_filter = c_f2.multiselect("Filtrar por Estatus", options=df['estatus'].unique())
            
            if carrera_filter:
                df = df[df['Carrera'].isin(carrera_filter)]
            if estatus_filter:
                df = df[df['estatus'].isin(estatus_filter)]
                
            display_cols = ['matricula', 'nombre', 'ap_paterno', 'ap_materno', 'Carrera', 'estatus', 'email_institucional', 'semestre']
            st.dataframe(df[display_cols], use_container_width=True)
            
            # Simple Chart
            st.markdown("###### Alumnos por Estatus")
            st.bar_chart(df['estatus'].value_counts())
        else:
            st.info("No hay datos de alumnos.")

    elif view_type == "Maestros Inscritos":
        res_maestros = supabase.table("maestros").select("*, carreras(nombre)").execute()
        if res_maestros.data:
            df = pd.DataFrame(res_maestros.data)
            df['Carrera'] = df['carreras'].apply(lambda x: x.get('nombre') if x else 'N/A')
            
            mentor_filter = st.radio("Filtro Mentores:", ["Todos", "Solo Mentores IE", "No Mentores"])
            if mentor_filter == "Solo Mentores IE":
                df = df[df['es_mentor_ie'] == True]
            elif mentor_filter == "No Mentores":
                df = df[df['es_mentor_ie'] == False]
                
            display_cols = ['clave_maestro', 'nombre_completo', 'email_institucional', 'Carrera', 'es_mentor_ie']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("No hay datos de maestros.")
            
    elif view_type == "Unidades Económicas":
        res_ue = supabase.table("unidades_economicas").select("*").execute()
        if res_ue.data:
             df = pd.DataFrame(res_ue.data)
             st.dataframe(df[['nombre_comercial', 'razon_social', 'rfc', 'direccion_fiscal']], use_container_width=True)
        else:
             st.info("No hay datos de Empresas.")

    elif view_type == "Proyectos DUAL":
        # Complex join for projects
        q_proj = supabase.table("proyectos_dual").select(
            "nombre_proyecto, fecha_inicio_convenio, fecha_fin_convenio, "
            "alumnos(nombre, ap_paterno, matricula), "
            "unidades_economicas(nombre_comercial), "
            "mentores_ue(nombre_completo), "
            "maestros(nombre_completo)"
        ).execute()
        
        if q_proj.data:
             flat_data = []
             for p in q_proj.data:
                 flat_data.append({
                     "Proyecto": p.get("nombre_proyecto"),
                     "Alumno": f"{p['alumnos'].get('nombre', '')} {p['alumnos'].get('ap_paterno', '')}" if p.get('alumnos') else "N/A",
                     "Matrícula": p['alumnos'].get('matricula') if p.get('alumnos') else "N/A",
                     "Empresa (UE)": p['unidades_economicas'].get('nombre_comercial') if p.get('unidades_economicas') else "N/A",
                     "Mentor IE": p['maestros'].get('nombre_completo') if p.get('maestros') else "** SIN ASIGNAR **",
                     "Mentor UE": p['mentores_ue'].get('nombre_completo') if p.get('mentores_ue') else "N/A",
                     "Inicio": p.get("fecha_inicio_convenio"),
                     "Fin": p.get("fecha_fin_convenio")
                 })
             
             df_p = pd.DataFrame(flat_data)
             
             cf1, cf2 = st.columns(2)
             empresas_sel = cf1.multiselect("Filtrar por Empresa", options=df_p['Empresa (UE)'].unique())
             if empresas_sel:
                 df_p = df_p[df_p['Empresa (UE)'].isin(empresas_sel)]
                 
             solo_sin_mentor = cf2.checkbox("Mostrar solo proyectos sin Mentor IE")
             if solo_sin_mentor:
                 df_p = df_p[df_p['Mentor IE'] == "** SIN ASIGNAR **"]
                 
             st.dataframe(df_p, use_container_width=True)
             
             # Chart: Proyectos por Empresa
             st.markdown("###### Distribución de Alumnos por Empresa")
             st.bar_chart(df_p['Empresa (UE)'].value_counts())
        else:
             st.info("No hay proyectos DUAL registrados.")

