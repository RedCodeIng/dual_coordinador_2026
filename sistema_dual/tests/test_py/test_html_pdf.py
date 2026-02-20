import os
import sys

# Add project root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.anexo_data import get_anexo_5_1_data
from src.utils.pdf_generator_docx import generate_pdf_from_docx
from src.db_connection import get_supabase_client

def test_html_pdf():
    print("Iniciando prueba de generación HTML -> PDF...")
    
    # 1. Get Data from DB
    supabase = get_supabase_client()
    res = supabase.table("proyectos_dual").select("alumno_id").limit(1).execute()
    
    if not res.data:
        print("❌ No se encontraron datos de prueba.")
        return

    student_id = res.data[0]["alumno_id"]
    print(f"Usando alumno ID: {student_id}")
    
    context, msg = get_anexo_5_1_data(student_id)
    if not context:
        print(f"❌ Error al obtener datos: {msg}")
        return

    # 2. Generate PDF
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "ANEXO_5.1_HTML_GENERATED.pdf")
    
    # Use user's converted HTML
    template_path = os.path.join(os.path.dirname(__file__), '../src/templates/docs/Anexo_5.1_Plan_de_Formacion.docx')
    if not os.path.exists(template_path):
        print(f"⚠️ Plantilla no encontrada: {template_path}")
        return

    success, msg = generate_pdf_from_docx("ignored", context, output_path, template_path=template_path)
    
    if success:
        print(f"✅ PDF generado exitosamente: {msg}")
    else:
        print(f"❌ Error al generar PDF: {msg}")

if __name__ == "__main__":
    test_html_pdf()
