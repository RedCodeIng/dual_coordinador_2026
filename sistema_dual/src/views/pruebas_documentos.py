import streamlit as st
import os
import random
from datetime import datetime
from src.db_connection import get_supabase_client
from src.utils.anexo_data import get_anexo_5_1_data
from src.utils.pdf_generator_docx import generate_docx_document
from src.utils.pdf_generator_images import create_percentage_donut
import base64

def auto_download_file(file_path, file_name):
    """Generates an invisible <a> tag and a JS script to auto-click it, triggering browser download immediately."""
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    b64 = base64.b64encode(bytes_data).decode()
    
    # MIME type estimation
    mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    href = f'<a id="auto_download_{file_name}" href="data:{mime};base64,{b64}" download="{file_name}" style="display:none;"></a>'
    js = f'<script>setTimeout(function() {{ document.getElementById("auto_download_{file_name}").click(); }}, 500);</script>'
    st.components.v1.html(href + js, height=0)

def get_dummy_context():
    """Devuelve un objeto de contexto de prueba completo para garantizar la generación perfecta de PDFs."""
    return {
        "nombre_proyecto": "PROYECTO DUAL SIMULADO DE ALTO IMPACTO",
        "unidad_economica": "INNOVACIONES TECNOLÓGICAS MOCK S.A. DE C.V.",
        "empresa": "INNOVACIONES TECNOLÓGICAS MOCK S.A. DE C.V.",
        "empresa_nombre": "INNOVACIONES TECNOLÓGICAS MOCK S.A. DE C.V.",
        "programa_educativo": "INGENIERÍA EN SISTEMAS COMPUTACIONALES",
        "carrera": "Ingeniería en Sistemas Computacionales",
        "num_estudiantes": "1", 
        "num_mentores_ue": "1",
        "num_mentores_academicos": "1",
        "periodos_vigencia": "Enero - Junio 2026",
        "fechas_periodo": "Enero - Junio 2026",
        "descripcion_proyecto": "Este es un proyecto simulado para validar el correcto funcionamiento y alineación estructural de la generación automática de archivos PDF desde plantillas DOCX en el Sistema de Gestión DUAL del TESE.",
        "horas_semanales": "40",
        "mentor_ue": "Lic. Mentor Industrial Prueba",
        "mentor_ue_nombre": "Lic. Mentor Industrial Prueba",
        "mentor_ie": "Mtro. Mentor Académico Prueba",
        "mentor_ie_nombre": "Mtro. Mentor Académico Prueba",
        "fecha_generacion": datetime.now().strftime('%d/%m/%Y'),
        "fecha_actual": datetime.now().strftime('%d/%m/%Y'),
        "numero_reporte": 1,
        "institucion_educativa": "Tecnológico de Estudios Superiores de Ecatepec (TESE)",
        "nombre_alumno": "ALUMNO DE PRUEBA DUAL",
        "alumno_nombre": "ALUMNO DE PRUEBA DUAL",
        "alumno_matricula": "2026MOCK99",
        "telefono_alumno": "555-MOCK-1234",
        "telefono_mentorue": "555-EMP-9876",
        "telefono_mentorie": "555-TESE-5555",
        "materia_nombre": "Arquitectura de Software y Sistemas Distribuidos",
        "calificacion": "9.5",
        "proyecto_nombre": "PROYECTO DUAL SIMULADO DE ALTO IMPACTO",
        "competencias_list": [
            {"competencia": "Diseñar arquitecturas de software eficientes.", "asignatura": "Arquitectura de Software"},
            {"competencia": "Implementar medidas de seguridad web.", "asignatura": "Seguridad en Redes"},
            {"competencia": "Gestionar bases de datos en la nube.", "asignatura": "Bases de Datos Avanzadas"}
        ],
        "actividades_list": [
            {"actividad": "Levantamiento de requerimientos con el cliente", "horas": "20", "evidencia": "Documento SRS", "lugar": "Empresa", "ponderacion": "20%"},
            {"actividad": "Diseño de la base de datos", "horas": "30", "evidencia": "Diagrama Entidad-Relación", "lugar": "Empresa", "ponderacion": "30%"},
            {"actividad": "Desarrollo del Backend", "horas": "50", "evidencia": "Repositorio Git", "lugar": "Empresa / Remoto", "ponderacion": "50%"}
        ],
        "lista_competencias": [
            {
                "numero_consecutivo": 1,
                "competencia_desarrollada": "Diseñar arquitecturas de software eficientes.",
                "asignaturas_cubre": "Arquitectura de Software",
                "conocimientos_teoricos": "Patrones de diseño, microservicios, seguridad en aplicaciones de red.",
                "descripcion_actividades": "Análisis de la infraestructura actual de la empresa, propuesta de mejora utilizando contenedores Docker y orquestación con Kubernetes."
            },
            {
                "numero_consecutivo": 2,
                "competencia_desarrollada": "Implementación de CI/CD.",
                "asignaturas_cubre": "Ingeniería de Software II",
                "conocimientos_teoricos": "Integración y Despliegue continuo, pipelines de automatización.",
                "descripcion_actividades": "Configuración de GitHub Actions para el despliegue automático hacia servidores en la nube."
            }
        ],
        "evaluaciones": [
            {
                "competencia_alcanzada": "Diseñar arquitecturas de software eficientes.",
                "actividades": [
                    {
                        "descripcion_actividad": "Análisis de la infraestructura actual",
                        "evidencia": "Reporte Técnico",
                        "horas": "15",
                        "p0": "", "p70": "", "p80": "", "p90": "", "p100": "X"
                    },
                    {
                        "descripcion_actividad": "Propuesta de mejora",
                        "evidencia": "Diagrama de Arquitectura",
                        "horas": "20",
                        "p0": "", "p70": "", "p80": "", "p90": "X", "p100": ""
                    }
                ],
                "firma_y_fecha": "Firmado Digitalmente\n" + datetime.now().strftime('%d/%m/%Y')
            }
        ]
    }

def render_pruebas_documentos():
    st.header("Pruebas de Generación de Documentos")
    st.info("Esta sección utilza datos de alumnos reales al azar (que cuentan con proyecto y unidad económica) para probar el formato visual y estructural de los PDFs generados.")
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Anexo 5.1", 
        "📄 Anexo 5.4", 
        "📄 Anexo 5.5", 
        "✉️ Carta Mentor IE", 
        "📝 Acta Materias",
        "🛠️ Entorno MOCK"
    ])
    
    with tab1:
        st.subheader("Anexo 5.1 - Plan de Formación")
        if st.button("Generar Prueba Anexo 5.1", use_container_width=True):
            with st.spinner("Compilando documento con datos del Universo MOCK..."):
                data = get_dummy_context()
                import tempfile
                out_dir = tempfile.gettempdir()
                
                docx_path = os.path.join(out_dir, f"Prueba_Anexo_5.1_MOCK.docx")
                template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", "Anexo_5.1_Plan_de_Formacion.docx")
                
                success, result_msg = generate_docx_document("Anexo_5.1_Plan_de_Formacion.docx", data, docx_path, template_path)
                
                if success:
                    auto_download_file(docx_path, os.path.basename(docx_path))
                    st.success("¡Documento generado! La descarga comenzará automáticamente.")
                    st.session_state["test_5_1_path"] = docx_path
                else:
                    st.error(f"Error: {result_msg}")
                    
        if st.session_state.get("test_5_1_path") and os.path.exists(st.session_state["test_5_1_path"]):
            active_path = st.session_state["test_5_1_path"]
            with open(active_path, "rb") as f:
                st.download_button("⬇️ Descargar Anexo 5.1 Manualmente", f.read(), os.path.basename(active_path), key="dl_5_1")

    with tab2:
        st.subheader("Anexo 5.4 - Reporte de Actividades")
        if st.button("Generar Prueba Anexo 5.4", use_container_width=True):
            with st.spinner("Compilando documento e insertando gráficas simuladas..."):
                chart_path = os.path.join(os.path.dirname(__file__), "test_chart_temp.png")
                create_percentage_donut(85, chart_path) # Dummy 85%
                
                context = get_dummy_context()
                context["grafica_promedio"] = f"IMAGE_PATH:{chart_path}"
                
                import tempfile
                out_dir = tempfile.gettempdir()
                docx_path = os.path.join(out_dir, f"Prueba_Anexo_5.4_MOCK.docx")
                template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", "Anexo_5.4_Reporte_de_Actividades.docx")
                
                success, result_msg = generate_docx_document("Anexo_5.4_Reporte_de_Actividades.docx", context, docx_path, template_path)
                if os.path.exists(chart_path): os.remove(chart_path)
                if success:
                    auto_download_file(docx_path, os.path.basename(docx_path))
                    st.success("¡Documento generado! La descarga comenzará automáticamente.")
                    st.session_state["test_5_4_path"] = docx_path
                else: st.error(result_msg)
                
        if st.session_state.get("test_5_4_path") and os.path.exists(st.session_state["test_5_4_path"]):
            active_path = st.session_state["test_5_4_path"]
            with open(active_path, "rb") as f:
                st.download_button("⬇️ Descargar Anexo 5.4 Manualmente", f.read(), os.path.basename(active_path), key="dl_5_4")

    # Reusable function for the new generic mock documents
    def generate_generic_mock(tab_obj, template_file, out_prefix, gen_btn_key, dl_btn_key):
        with tab_obj:
            st.subheader(out_prefix.replace('_', ' '))
            if st.button(f"Generar {out_prefix.replace('_', ' ')}", use_container_width=True, key=gen_btn_key):
                with st.spinner("Generando documento con Universo MOCK..."):
                    context = get_dummy_context()
                    
                    import tempfile
                    out_dir = tempfile.gettempdir()
                    docx_path = os.path.join(out_dir, f"Prueba_{out_prefix}_MOCK.docx")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "docs", template_file)
                    
                    success, result_msg = generate_docx_document(template_file, context, docx_path, template_path)
                    
                    if success:
                        auto_download_file(docx_path, os.path.basename(docx_path))
                        st.success("¡Documento generado! La descarga comenzará automáticamente.")
                        st.session_state[f"test_{gen_btn_key}_path"] = docx_path
                    else:
                        st.error(f"Error: {result_msg}")
                        
            if st.session_state.get(f"test_{gen_btn_key}_path") and os.path.exists(st.session_state[f"test_{gen_btn_key}_path"]):
                active_path = st.session_state[f"test_{gen_btn_key}_path"]
                with open(active_path, "rb") as f:
                    st.download_button(f"⬇️ Descargar {out_prefix} Manualmente", f.read(), os.path.basename(active_path), key=dl_btn_key)

    generate_generic_mock(tab3, "Anexo_5.5_Seguimiento_Modificado.docx", "Anexo_5.5", "btn_gen_55", "dl_btn_55")
    generate_generic_mock(tab4, "Carta_Asignacion_Mentor_IE.docx", "Carta_Mentor_IE", "btn_gen_carta", "dl_btn_carta")
    generate_generic_mock(tab5, "Acta_Calificaciones_Materia.docx", "Acta_Calificaciones", "btn_gen_acta", "dl_btn_acta")

    with tab6:
        st.subheader("Entorno de Pruebas (Ciclo Completo DUAL)")
        st.info("Utiliza esta herramienta para inyectar un alumno falso con un proyecto e inscripciones falsas utilizando las Unidades Económicas y Maestros ya existentes en el sistema. Esto te permite recorrer todo el sistema como Estudiante o como Mentor sin arruinar datos reales.")
        
        st.markdown("""
        ### Pasos para probar el sistema
        1. Presiona **Instalar Universo MOCK** abajo.
        2. Ve al **Control de Fases** -> **Fase 2** y Asígnale un *Mentor Institucional (MOCK Maestro)* a los alumnos MOCK. (Te llegará un correo con sus contraseñas).
        3. Cierra sesión y **Entra como uno de los alumnos** (Matrícula: `MOCK-ALU-1` : `MOCK-ALU-1`). Llena sus datos y ve a sus documentos.
        4. Inicia sesión como el **Mentor UE** o **Mentor IE** (con la contraseña que te llegó) y evalúa al alumno para recibir los PDF finales.
        """)
        
        def purge_mock_universe(supa):
            # Because of CASCADE, deleting masters/UE deletes projects/enrolls.
            supa.table("alumnos").delete().like("matricula", "MOCK-%").execute()
            supa.table("mentores_ue").delete().like("nombre_completo", "MOCK %").execute()
            supa.table("unidades_economicas").delete().like("rfc", "MOCK-%").execute()
            supa.table("maestros").delete().like("clave_maestro", "MOCK-%").execute()
            
            # Limpiar competencias MOCK manual (si las asigs se borran, por llave foránea también se borran, pero mejor prevenir)
            res_asig_mock = supa.table("asignaturas").select("id").like("clave_asignatura", "MOCK-%").execute()
            if res_asig_mock.data:
                asig_ids_mock = [a['id'] for a in res_asig_mock.data]
                supa.table("asignatura_competencias").delete().in_("asignatura_id", asig_ids_mock).execute()

            # Subjects are deleted explicitly last.
            supa.table("asignaturas").delete().like("clave_asignatura", "MOCK-%").execute()

        col_mock1, col_mock2 = st.columns(2)
        
        with col_mock1:
            if st.button("🚀 Instalar Universo MOCK", use_container_width=True):
                with st.spinner("Inyectando 16 entidades... (Tardará unos segundos)"):
                    try:
                        supabase = get_supabase_client()
                        
                        # Verify prerequisites
                        res_p = supabase.table("periodos").select("id").eq("activo", True).execute()
                        if not res_p.data:
                            st.error("No hay ningún periodo activo. No se puede construir el universo.")
                        else:
                            periodo_id = res_p.data[0]['id']
                            
                            res_c = supabase.table("carreras").select("id").limit(1).execute()
                            if not res_c.data:
                                st.error("No hay carreras registradas. No se puede construir el universo.")
                            else:
                                carrera_id = res_c.data[0]['id']
                                
                                # Clean potential previous mocks
                                purge_mock_universe(supabase)
                                
                                tgt_email = "jairyanez44@gmail.com"
                                
                                # 1. Generate 3 Asignaturas
                                asig_data = [
                                    {"clave_asignatura": "MOCK-ASIG-1", "nombre": "MOCK Arquitectura Software", "semestre": 6, "carrera_id": carrera_id},
                                    {"clave_asignatura": "MOCK-ASIG-2", "nombre": "MOCK Desarrollo Distribuido", "semestre": 7, "carrera_id": carrera_id},
                                    {"clave_asignatura": "MOCK-ASIG-3", "nombre": "MOCK Gestión de Equipos", "semestre": 8, "carrera_id": carrera_id}
                                ]
                                res_asig = supabase.table("asignaturas").insert(asig_data).execute()
                                asig_ids = [a['id'] for a in res_asig.data]
                                
                                # 2. Generate 5 Maestros
                                mae_data = [
                                    {"clave_maestro": f"MOCK-MAE-{i}", "nombre_completo": f"MOCK Maestro {i}", "email_institucional": tgt_email, "es_mentor_ie": True, "carrera_id": carrera_id}
                                    for i in range(1, 6)
                                ]
                                res_mae = supabase.table("maestros").insert(mae_data).execute()
                                mae_ids = [m['id'] for m in res_mae.data]
                                
                                # 3. Generate 2 UEs
                                ue_data = [
                                    {"nombre_comercial": "MOCK Tech Corporation", "rfc": "MOCK-RFC-1"},
                                    {"nombre_comercial": "MOCK Innova Labs", "rfc": "MOCK-RFC-2"}
                                ]
                                res_ue = supabase.table("unidades_economicas").insert(ue_data).execute()
                                ue_ids = [u['id'] for u in res_ue.data]
                                
                                # 4. Generate 3 Mentores UE (1 for UE1, 2 for UE2)
                                mue_data = [
                                    {"ue_id": ue_ids[0], "nombre_completo": "MOCK Mentor Ejecutivo 1", "email": tgt_email},
                                    {"ue_id": ue_ids[1], "nombre_completo": "MOCK Mentor Ejecutivo 2", "email": tgt_email},
                                    {"ue_id": ue_ids[1], "nombre_completo": "MOCK Mentor Asociado 3", "email": tgt_email}
                                ]
                                res_mue = supabase.table("mentores_ue").insert(mue_data).execute()
                                mue_ids = [m['id'] for m in res_mue.data]
                                
                                # 5. Generate 3 Alumnos
                                alu_data = [
                                    {
                                        "carrera_id": carrera_id,
                                        "matricula": f"MOCK-ALU-{i}",
                                        "curp": f"MOCK1234567890123{i}",
                                        "nombre": f"MOCK Estudiante {i}",
                                        "ap_paterno": "Prueba",
                                        "ap_materno": "Mock",
                                        "email_institucional": tgt_email,
                                        "email_personal": tgt_email,
                                        "semestre": str(6 + (i % 3)),
                                        "tipo_ingreso": "Nuevo Ingreso",
                                        "estatus": "Activo"
                                    } for i in range(1, 4)
                                ]
                                res_alu = supabase.table("alumnos").insert(alu_data).execute()
                                alu_ids = [a['id'] for a in res_alu.data]
                                
                                # 6. Generate 2 Competencias for each Mock Asignatura
                                competencias_data = []
                                for asig_doc_id in asig_ids:
                                    competencias_data.extend([
                                        {
                                            "asignatura_id": asig_doc_id,
                                            "numero_competencia": 1,
                                            "competencia_desarrollada": "Competencia Simulada MOCK 1",
                                            "conocimientos_teoricos": "Conocimiento Teórico Estándar para pruebas automáticas de reportes y formatos PDF. Se validará la inyección.",
                                            "descripcion_actividades": "Actividad simulada para esta materia MOCK con el formato establecido en la base de datos."
                                        },
                                        {
                                            "asignatura_id": asig_doc_id,
                                            "numero_competencia": 2,
                                            "competencia_desarrollada": "Competencia Simulada MOCK 2",
                                            "conocimientos_teoricos": "El segundo conocimiento teórico que debe inyectarse dinámicamente en el Anexo 5.4.",
                                            "descripcion_actividades": "Segunda actividad que requiere validación por parte del maestro y del mentor de la unidad económica."
                                        }
                                    ])
                                supabase.table("asignatura_competencias").insert(competencias_data).execute()
                                
                                st.success("¡Universo MOCK Inyectado! (3 Asignaturas, 6 Competencias, 5 Maestros, 2 UEs, 3 Mentores UE, 3 Alumnos). Todos usarán el correo proporcionado para pruebas de Fases.")
                    except Exception as e:
                        st.error(f"Error insertando: {e}")
        
        with col_mock2:
            if st.button("🗑️ Purgar Universo MOCK", use_container_width=True):
                with st.spinner("Borrando todo rastro de los Mocks..."):
                    try:
                        supabase = get_supabase_client()
                        purge_mock_universe(supabase)
                        st.success("Toda la información falsa (Alumnos, UEs, Maestros, Materias) ha sido desintegrada.")
                    except Exception as e:
                        st.error(f"Error borrando: {e}")

        st.divider()
        st.subheader("Descarga de Manuales del Sistema")
        st.info("Obtén las versiones en PDF de los manuales del sistema. Puedes modificar los archivos .docx originales en la carpeta `templates/docs` y el sistema generará el PDF actualizado al vuelo.")
        
        col_man1, col_man2 = st.columns(2)
        
        with col_man1:
            if st.button("📄 Generar Word: Manual de Usuario", use_container_width=True):
                with st.spinner("Compilando Manual..."):
                    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "output")
                    os.makedirs(out_dir, exist_ok=True)
                    docx_path = os.path.join(out_dir, "Manual_Usuario_Sistema_DUAL.docx")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "docs", "Manual_Usuario_Sistema_DUAL.docx")
                    
                    success, msg = generate_docx_document("Manual_Usuario_Sistema_DUAL.docx", {}, docx_path, template_path)
                    if success:
                        st.session_state["path_manual_usr"] = docx_path
                        st.success("Manual listo para descargar.")
                    else:
                        st.error(f"Error generando: {msg}")
                        
            if st.session_state.get("path_manual_usr") and os.path.exists(st.session_state["path_manual_usr"]):
                with open(st.session_state["path_manual_usr"], "rb") as f:
                    st.download_button("⬇️ Descargar Manual de Usuario (Word)", f.read(), "Manual_Usuario_Sistema_DUAL.docx", key="dl_usr")
                    
        with col_man2:
            if st.button("⚙️ Generar Word: Manual Técnico", use_container_width=True):
                with st.spinner("Compilando Manual..."):
                    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tests", "output")
                    os.makedirs(out_dir, exist_ok=True)
                    docx_path = os.path.join(out_dir, "Manual_Tecnico_Sistema_DUAL.docx")
                    template_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates", "docs", "Manual_Tecnico_Sistema_DUAL.docx")
                    
                    success, msg = generate_docx_document("Manual_Tecnico_Sistema_DUAL.docx", {}, docx_path, template_path)
                    if success:
                        st.session_state["path_manual_tec"] = docx_path
                        st.success("Manual listo para descargar.")
                    else:
                        st.error(f"Error generando: {msg}")
                        
            if st.session_state.get("path_manual_tec") and os.path.exists(st.session_state["path_manual_tec"]):
                with open(st.session_state["path_manual_tec"], "rb") as f:
                    st.download_button("⬇️ Descargar Manual Técnico (Word)", f.read(), "Manual_Tecnico_Sistema_DUAL.docx", key="dl_tec")
