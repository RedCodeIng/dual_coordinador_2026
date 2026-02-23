import docxtpl
import traceback
from test_anexo_54_gen import test_generation

try:
    test_generation()
except Exception as e:
    doc = docxtpl.DocxTemplate(r'src\templates\docs\Anexo_5.4_Reporte_de_Actividades.docx')
    doc.init_docx()
    # It must have crashed inside generate_pdf_from_docx.
    # The traceback will show us where.
    traceback.print_exc()

