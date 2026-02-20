
import streamlit as st
from src.db_connection import get_supabase_client
from src.views.registro_coordinador import render_registro_coordinador
# Import New Modules
from src.views.maestros import render_maestros
from src.views.asignaturas import render_asignaturas
from src.views.empresas import render_empresas

def render_dashboard():
    # Context
    selected_career_name = st.session_state.get("selected_career_name", "")
    
    # Top Bar: User Info & Logout
    c1, c2 = st.columns([3, 1])
    with c1:
        user = st.session_state.get('user', {}) or {}
        st.markdown(f"<h3 style='color:#1f497d; font-family:sans-serif; margin-bottom:0;'>Usuario: {user.get('nombre_completo', 'Usuario')}</h3>", unsafe_allow_html=True)
        
        carrera_id = user.get('carrera_id')
        carrera_name = "Global (Todas las carreras)"
        
        if carrera_id:
            # If a specific career is selected, use its name
            if selected_career_name:
                carrera_name = selected_career_name
            else:
                # Fallback if selected_career_name is not set but carrera_id is present
                # This might happen if the user has a career_id but hasn't explicitly selected one in the UI
                carrera_name = f"Carrera ID: {carrera_id}" # Or fetch career name from DB if needed
        
        st.markdown(f"<h4 style='color:gray; font-family:sans-serif; margin-top:0;'>Carrera: {carrera_name}</h4>", unsafe_allow_html=True)
            
    with c2:
        if st.button("Cerrar Sesión", key="btn_logout_dashboard", use_container_width=True):
            st.query_params.clear()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    st.markdown("---")

    # Main Navigation via Tabs (Always Visible)
    t_reportes, t_alumnos, t_maestros, t_asignaturas, t_empresas, t_periodos, t_lista = st.tabs([
        "📊 Reportes y Analítica",
        "🎓 Alumnos", 
        "👨‍🏫 Maestros", 
        "📚 Asignaturas", 
        "🏢 Unidades Económicas", 
        "📅 Periodos",
        "📋 Lista Blanca"
    ])

    with t_reportes:
        try:
            from src.views.reportes import render_reportes
            render_reportes()
        except Exception as e:
            st.error(f"Error cargando reportes: {e}")

    with t_alumnos:
        from src.views.alumnos import render_alumnos
        render_alumnos()

    with t_maestros:
        try:
            render_maestros()
        except Exception as e:
            st.error(f"Error cargando maestros: {e}")

    with t_asignaturas:
        try:
            render_asignaturas()
        except Exception as e:
            st.error(f"Error cargando asignaturas: {e}")

    with t_empresas:
        try:
            render_empresas()
        except Exception as e:
            st.error(f"Error cargando empresas: {e}")

    with t_periodos:
        try:
            from src.views.periodos import render_periodos
            render_periodos()
        except ImportError:
            st.warning("Módulo de Periodos en construcción.")
        except Exception as e:
            st.error(f"Error cargando periodos: {e}")
            
    with t_lista:
        try:
            from src.views.lista_blanca import render_lista_blanca
            render_lista_blanca()
        except ImportError:
            st.warning("Módulo de Lista Blanca no encontrado.")
        except Exception as e:
            st.error(f"Error cargando lista blanca: {e}")
