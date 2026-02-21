import streamlit as st
import time
from src.db_connection import get_supabase_client
from src.components.login_ui import get_login_css, get_login_header

def render_login():
    """Renders the login view."""
    st.markdown(get_login_css(), unsafe_allow_html=True)
    
    # --- Data Fetching (Outside Form) ---
    carreras_options = {}
    fetch_error = None
    
    try:
        supabase = get_supabase_client()
        res_carreras = supabase.table("carreras").select("id, nombre").execute()
        if res_carreras.data:
            carreras_data = res_carreras.data
            carreras_data.sort(key=lambda x: x["nombre"])
            carreras_options = {c["nombre"]: c["id"] for c in carreras_data}
    except Exception as e:
        fetch_error = f"Error conectando a la base de datos: {e}"

    # --- UI Rendering ---
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        st.markdown(get_login_header(), unsafe_allow_html=True)
        
        if fetch_error:
            st.error(fetch_error)
            if st.button("Reintentar Conexión"):
                st.rerun()

        with st.form("login_form"):
            identifier = st.text_input("Usuario (Matrícula o No. Empleado)")
            password = st.text_input("Contraseña (o CURP)", type="password")
            
            selected_career_id = None
            selected_career_name = None

            if carreras_options:
                career_list = list(carreras_options.keys())
                
                # Establecer Ingeniería en Sistemas Computacionales como opción predeterminada
                default_idx = 0
                for i, c in enumerate(career_list):
                    if "Sistemas Computacionales" in c or "SISTEMAS COMPUTACIONALES" in c.upper():
                        default_idx = i
                        break
                        
                selected_career_name = st.selectbox("Seleccione su Carrera / División", career_list, index=default_idx)
                if selected_career_name: 
                    selected_career_id = carreras_options[selected_career_name]
            elif not fetch_error: # Only show this if no error but also no careers
                 st.warning("No se encontraron carreras registradas.")

            submitted = st.form_submit_button("Ingresar")
            
            if submitted:
                if not identifier or not password:
                    st.error("Por favor, ingrese usuario y contraseña.")
                
                elif not selected_career_id and not (identifier == "admin"): # Allow admin bypass if needed, or stick to strict
                    st.error("Debe seleccionar una carrera para ingresar.")
                
                else:
                    # Proceed with Login Logic
                    # 1. Check Coordinator
                    if identifier.isdigit():
                         try:
                            response = supabase.table("usuarios_coordinadores").select("*").eq("no_empleado", identifier).execute()
                            if response.data:
                                user = response.data[0]
                                st.session_state["user"] = user
                                st.session_state["role"] = "coordinator"
                                st.session_state["selected_career_name"] = selected_career_name
                                st.session_state["selected_career_id"] = selected_career_id
                                st.session_state["selected_career_id"] = selected_career_id
                                st.success(f"Bienvenido Coordinador - {selected_career_name}")
                                
                                # Set Session Token for Persistence
                                st.query_params["session_token"] = identifier
                                
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Usuario no encontrado en Coordinadores.")
                         except Exception as e:
                             st.error(f"Error al buscar coordinador: {e}")

                    # 2. Check Student
                    else:
                        try:
                            response = supabase.table("alumnos").select("*").eq("matricula", identifier).execute()
                            if response.data:
                                student = response.data[0]
                                if student.get("curp") == password:
                                   st.session_state["user"] = student
                                   st.session_state["role"] = "student"
                                   st.session_state["selected_career"] = selected_career_name
                                   st.success(f"Bienvenido Alumno - {selected_career_name}")
                                   time.sleep(1)
                                   st.rerun()
                                else:
                                     st.error("Contraseña incorrecta.")
                            else:
                                # Register Flow
                                st.session_state["user"] = {"matricula": identifier, "curp": password}
                                st.session_state["role"] = "student_register"
                                st.session_state["selected_career"] = selected_career_name
                                st.info("No se encontró registro. Redirigiendo a formulario de inscripción...")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error verificando alumno: {e}")
