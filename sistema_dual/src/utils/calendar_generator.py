import os
from datetime import datetime, timedelta

def create_event_ics(title, description, start_date, end_date=None, location="Sistema de Gestión DUAL", file_name="evento_dual.ics"):
    """
    Genera un archivo .ics básico para adjuntar en correos electrónicos.
    
    Args:
        title (str): Título del evento (ej. 'Entrega de Anexo 5.1').
        description (str): Descripción detallada del evento.
        start_date (datetime o str): Fecha de inicio. Si es str, debe estar en formato ISO (YYYY-MM-DD).
        end_date (datetime o str, opcional): Fecha de fin. Si se omite, durará 1 día (evento de todo el día).
        location (str): Ubicación del evento.
        file_name (str): Nombre del archivo a generar.
        
    Returns:
        str: Ruta absoluta al archivo .ics generado, o None si hay error.
    """
    try:
        # 1. Parse dates
        if isinstance(start_date, str):
            # Try to grab just the date part if it comes as full ISO with time
            start_str = start_date.split('T')[0] if 'T' in start_date else start_date
            dt_start = datetime.strptime(start_str, "%Y-%m-%d")
        else:
            dt_start = start_date
            
        if end_date:
            if isinstance(end_date, str):
                end_str = end_date.split('T')[0] if 'T' in end_date else end_date
                dt_end = datetime.strptime(end_str, "%Y-%m-%d")
            else:
                dt_end = end_date
        else:
            dt_end = dt_start + timedelta(days=1)
            
        # Format for iCal (YYYYMMDDTHHMMSSZ, but for all-day we can use just YYYYMMDD)
        # Using all-day events format for simplicity and broader compatibility for deadlines
        dtstamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dtstart_str = dt_start.strftime("%Y%m%d")
        # For all-day events in iCal, DTEND is exclusive, so add 1 day
        dtend_val = dt_end + timedelta(days=1) if dt_start == dt_end else dt_end
        dtend_str = dtend_val.strftime("%Y%m%d")
        
        # 2. Build ICS Content
        # Escape newlines for iCal format
        desc_escaped = description.replace('\n', '\\n').replace('\r', '')
        
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Tecnológico de Estudios Superiores de Ecatepec//Sistema DUAL//ES
CALSCALE:GREGORIAN
BEGIN:VEVENT
DTSTAMP:{dtstamp}
UID:{dtstamp}-{hash(title)}@sistemadual.tese.edu.mx
DTSTART;VALUE=DATE:{dtstart_str}
DTEND;VALUE=DATE:{dtend_str}
SUMMARY:{title}
DESCRIPTION:{desc_escaped}
LOCATION:{location}
END:VEVENT
END:VCALENDAR"""

        # 3. Save to output directory
        out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests", "output", "calendar")
        os.makedirs(out_dir, exist_ok=True)
        
        filepath = os.path.join(out_dir, file_name)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ics_content)
            
        return filepath
        
    except Exception as e:
        print(f"Error generando ICS: {e}")
        return None
