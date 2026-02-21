import sys
import os
import streamlit as st

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.views.auth import render_login
from src.views.dashboard import render_dashboard
from src.views.registro import render_registro
from src.utils.ui import inject_custom_css, render_header

def main():
    # MUST BE THE FIRST STREAMLIT COMMAND
    st.set_page_config(
        page_title="Sistema de Gestión DUAL",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': "Sistema de Gestión DUAL - EdoMex"
        }
    )

    # 1. Inject Global CSS
    inject_custom_css()
    
    # 2. Render Header (Base64 Logos)
    # Only show header if logged in OR we can show it always. 
    # Usually better to show it always for branding.
    if "user" in st.session_state:
        render_header() 

    # 3. Session Persistence Logic (Restore from Query Param)
    # Simple mechanism: ?session_token=USER_ID (In production use secure cookies/JWT)
    query_params = st.query_params
    token = query_params.get("session_token", None)
    
    if "user" not in st.session_state and token:
        # Try to restore session
        from src.db_connection import get_supabase_client
        supabase = get_supabase_client()
        
        # Check Coordinator
        try:
             res = supabase.table("usuarios_coordinadores").select("*").eq("no_empleado", token).execute()
             if res.data:
                 user = res.data[0]
                 st.session_state["user"] = user
                 st.session_state["role"] = "coordinator"
                 # Need to fetch selected career name - tricky if not stored.
                 # For now, default to None or user's assigned career
                 if user.get("carrera_id"):
                     res_car = supabase.table("carreras").select("nombre").eq("id", user["carrera_id"]).single().execute()
                     if res_car.data:
                         st.session_state["selected_career_name"] = res_car.data["nombre"]
                 st.toast("Sesión restaurada exitosamente.", icon="🔄")
        except Exception as e:
            pass # Fail silently
            
    # 3. Routing
    if "user" not in st.session_state:
        # Login view handles its own specific styles if needed, or inherits global
        render_login()
    else:
        role = st.session_state.get("role")
        
        if role == "coordinator":
            render_dashboard()
        elif role == "student":
            st.title("Portal del Alumno DUAL")
            st.info("Bienvenido. Tu estatus actual es: Activo")
            # Logic for student dashboard if already registered
            # Import needed
            try:
                from src.views.student_dashboard import render_student_dashboard
                render_student_dashboard()
            except ImportError:
                pass
        elif role == "student_register":
            render_registro()
        else:
            st.error("Rol desconocido. Contacte al administrador.")

if __name__ == "__main__":
    main()
