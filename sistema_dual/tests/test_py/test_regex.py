import docxtpl
from docxtpl.template import *

doc = docxtpl.DocxTemplate(r"src\templates\docs\Anexo_5.4_Reporte_de_Actividades.docx")
doc.init_docx()
xml = doc.get_xml()

print("Initial xml length:", len(xml))

patched = doc.patch_xml(xml)

print("Patched xml length:", len(patched))

import re
pat = r'<w:tr[ >](?:(?!<w:tr[ >]).)*({%|{{)tr ([^}%]*(?:%}|}})).*?</w:tr>'
matches = re.findall(pat, xml, flags=re.DOTALL)
print("Matches BEFORE patch:", matches)

matches = re.findall(pat, patched, flags=re.DOTALL)
print("Matches AFTER patch:", matches)

for m in re.finditer(r'{%tr.*?%}', xml):
    print("Found raw str in xml:", m.group(0))

