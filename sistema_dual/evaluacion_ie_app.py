import streamlit as st
from src.db_connection import get_supabase_client
import sys
import os

def render_evaluacion_ie_publica():
    st.set_page_config(page_title="Evaluación DUAL - Mentor IE", page_icon="📝", layout="centered")
    
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 20px;">
            <img src="https://i.imgur.com/NsK8IXi.png" alt="TESE Logo" width="150">
            <h2 style="color: #8d2840;">Portal de Evaluación DUAL (Mentor Institucional)</h2>
            <p>Registre la evaluación del reporte y desempeño académico de sus estudiantes asignados.</p>
        </div>
        <hr>
        """, 
        unsafe_allow_html=True
    )

    query_params = st.query_params
    token = query_params.get("token", None)
    
    if not token:
        st.error("Enlace inválido o expirado. Por favor, utilice el enlace proporcionado en su correo electrónico oficial.")
        return
        
    supabase = get_supabase_client()
    
    # In a real app, token would be a secure hash verified against a DB table `tokens_acceso`.
    # For now, we simulate by assuming the token is the mentor_ie_id (Base64 encoded ideally, but plain for demo).
    # In production: decoding(token) -> mentor_id
    mentor_id = token
    
    try:
        # 1. Verify Mentor exists
        res_mentor = supabase.table("maestros").select("nombre_completo, email_institucional").eq("id", mentor_id).single().execute()
        if not res_mentor.data:
            st.error("No se reconoció la identidad del evaluador.")
            return
            
        mentor = res_mentor.data
        st.info(f"Bienvenido/a, **{mentor['nombre_completo']}**")
        
        # 2. Get students assigned to this mentor
        # Needs to join proyectos_dual with alumnos
        res_projs = supabase.table("proyectos_dual").select(
            "id, alumno_id, calificacion_ie, ue_id, unidades_economicas(nombre_comercial), alumnos(matricula, nombre, ap_paterno, ap_materno)"
        ).eq("mentor_ie_id", mentor_id).execute()
        
        proyectos = res_projs.data if res_projs.data else []
        
        if not proyectos:
            st.warning("Actualmente no tiene alumnos asignados o el periodo de evaluación ha concluido.")
            return
            
        st.markdown("### Alumnos Asignados")
        
        for p in proyectos:
            alumno = p.get('alumnos', {})
            ue = p.get('unidades_economicas', {})
            
            student_name = f"{alumno.get('nombre', '')} {alumno.get('ap_paterno', '')} {alumno.get('ap_materno', '')}".strip()
            matricula = alumno.get('matricula', 'S/N')
            empresa = ue.get('nombre_comercial', 'N/A')
            
            current_grade = p.get('calificacion_ie')
            
            with st.expander(f"🎓 {student_name} ({matricula}) - {empresa}", expanded=(current_grade is None)):
                st.write("**Instrucciones:** Evalúe el desempeño del estudiante basándose en los reportes parciales y el reporte final entregados.")
                
                with st.form(f"eval_form_{p['id']}"):
                    # Calificación suele ser base 10 o 100. Asumiendo base 10.
                    val = current_grade if current_grade is not None else 0.0
                    
                    calificacion = st.number_input(
                        "Calificación Final IE (0 a 10)", 
                        min_value=0.0, max_value=10.0, value=float(val), step=0.1,
                        help="Representa el 30% de la calificación dual total."
                    )
                    
                    observaciones = st.text_area("Observaciones o Retroalimentación (Opcional)")
                    
                    if st.form_submit_button("Guardar Evaluación"):
                        supabase.table("proyectos_dual").update({
                            "calificacion_ie": calificacion
                        }).eq("id", p['id']).execute()
                        st.success(f"Calificación de {calificacion} guardada para {student_name}.")
                        st.rerun()

    except Exception as e:
        st.error(f"Error de sistema: {e}")

if __name__ == "__main__":
    render_evaluacion_ie_publica()
