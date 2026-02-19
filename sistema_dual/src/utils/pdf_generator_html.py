import os
import io
import re
from xhtml2pdf import pisa
from jinja2 import Environment, FileSystemLoader, Template

def generate_pdf_from_html(template_name, context, output_path, template_path=None):
    """
    Generates a PDF from an HTML template using xhtml2pdf.
    Handles HTML cleaning (fixing split tags) and background image injection.
    
    Args:
        template_name (str): Name of the HTML template (if in templates dir)
        context (dict): Data to enrich the template
        output_path (str): Full path where the PDF will be saved
        template_path (str): Optional absolute path to a specific HTML file
        
    Returns:
        bool, str: Success status and message
    """
    try:
        # 1. Load HTML Content
        if template_path and os.path.exists(template_path):
            base_dir = os.path.dirname(template_path)
            with open(template_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()
        else:
            # Fallback to standard templates dir
            base_dir = os.path.join(os.path.dirname(__file__), '../templates/docs')
            t_path = os.path.join(base_dir, template_name)
            if not os.path.exists(t_path):
                 return False, f"Plantilla no encontrada: {t_path}"
            with open(t_path, "r", encoding="utf-8", errors="ignore") as f:
                html_content = f.read()

        # 2. Preprocess: Clean Logic Tags & Remove Word CSS
        # Word's CSS breaks xhtml2pdf. We remove <style> blocks.
        html_content = re.sub(r'<style>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        
        def clean_tag(match):
            inner = match.group(1) 
            clean_var = re.sub(r'<[^>]+>', '', inner)
            clean_var = clean_var.strip()
            return f"{{{{ {clean_var} }}}}"
        
        html_content = re.sub(r'\{\{(.*?)\}\}', clean_tag, html_content, flags=re.DOTALL)
        
        # 2.5 Inject Loop Logic (Wrap rows)
        # We need to find the <tr ...> that contains {{ competencia }} and wrap it.
        # Regex to find a tr that contains a specific string.
        # We use a pattern that matches <tr [optional attrs]> ... content ... </tr>
        # The content must contain the target variable.
        
        def inject_loop(html, target_var, list_name, iter_name, var_map):
            # Regex explanation:
            # <tr[^>]*> : Match start tag of tr with any attributes
            # (?:(?!</tr>).)*? : Match content lazily, ensuring we don't cross </tr>
            # {{ target_var }} : Match the target variable (cleaned)
            # (?:(?!</tr>).)*? : Match more content
            # </tr> : Match end tag
            
            pattern = re.compile(r'(<tr[^>]*>(?:(?!</tr>).)*?\{\{\s*' + re.escape(target_var) + r'\s*\}\}(?:(?!</tr>).)*?</tr>)', re.DOTALL | re.IGNORECASE)
            
            def replace_row(match):
                row_content = match.group(1)
                # Replace variables inside the row with iterator prefix
                # e.g. {{ competencia }} -> {{ c.competencia }}
                for old_var, new_attr in var_map.items():
                    # Handle spaces in {{ var }}
                    row_content = re.sub(r'\{\{\s*' + re.escape(old_var) + r'\s*\}\}', f"{{{{ {iter_name}.{new_attr} }}}}", row_content)
                
                # Wrap with loop
                return f"{{% for {iter_name} in {list_name} %}}{row_content}{{% endfor %}}"
                
            return pattern.sub(replace_row, html)

        # Apply for Competencias
        html_content = inject_loop(html_content, "competencia", "competencias_list", "c", {
            "competencia": "competencia",
            "asignatura": "asignatura"
        })
        
        # Apply for Actividades
        html_content = inject_loop(html_content, "actividad", "actividades_list", "a", {
            "actividad": "actividad",
            "horas": "horas",
            "evidencia": "evidencia",
            "lugar": "lugar", 
            "ponderacion": "ponderacion"
        })

        # 3. Inject Background Image CSS
        # Check if background image exists in the same dir
        bg_image_name = "fondo_anexos_carta.jpg"
        bg_path = os.path.join(base_dir, bg_image_name)
        
        if os.path.exists(bg_path):
            # Convert to URI
            bg_uri = pathlib_to_uri(bg_path)
            
            # CSS to inject
            # We need to ensure we don't break existing styles.
            # Best place: inside <head> after existing <style> or append to it?
            # Or just prepend a new <style> block before </head>.
            
            bg_css = f"""
            <style>
                @page {{
                    size: letter;
                    margin: 2cm; /* Default margin for content */
                    background-image: url('{bg_uri}');
                    background-position: center;
                    background-repeat: no-repeat;
                    background-size: contain; 
                    
                    @frame header_frame {{
                        -pdf-frame-content: header_content;
                        top: 1cm;
                        margin-left: 1cm;
                        margin-right: 1cm;
                        height: 3cm;
                    }}
                }}
            </style>
            """
            # Inject before </head>
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", f"{bg_css}</head>")
            else:
                 # No head? Prepend to body
                 html_content = bg_css + html_content
                 
        # 4. Render with Jinja2 (using Template directly since we modified source)
        # We need to pass the environment so filters work if needed
        template = Template(html_content)
        rendered_html = template.render(context)
        
        # 5. Generate PDF
        with open(output_path, "wb") as result_file:
            pisa_status = pisa.CreatePDF(
                io.StringIO(rendered_html),
                dest=result_file,
                encoding='utf-8',
                base_url=base_dir # Important for relative image paths (if any others exist)
            )
            
        if pisa_status.err:
            return False, f"Error generando PDF: {pisa_status.err}"
            
        return True, f"PDF generado exitosamente en: {output_path}"
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, str(e)

def pathlib_to_uri(path):
    """Helper to convert path to file URI"""
    return os.path.abspath(path).replace('\\', '/')

