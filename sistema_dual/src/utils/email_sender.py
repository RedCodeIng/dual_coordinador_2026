import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import streamlit as st

def send_confirmation_email(to_email, student_name):
    """
    Sends a confirmation email to the student.
    
    Args:
        to_email (str): Recipient email.
        student_name (str): Name of the student.
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_EMAIL", "test@example.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "password")

    subject = "Confirmación de Registro DUAL (Por Coordinación)"
    
    body = f"""
    Hola {student_name},
    
    Tu registro en el Sistema de Gestión DUAL ha sido completado por la coordinación académica.
    
    Puedes ingresar al portal de alumnos con tu Matrícula y CURP.
    
    Atentamente,
    Coordinación DUAL
    """

    # If no real credentials, just log it (Mock mode)
    if sender_email == "test@example.com" or not sender_password:
        print(f"--- MOCK EMAIL TO {to_email} ---")
        print(f"Subject: {subject}")
        print(body)
        print("-------------------------------")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e

def generate_ics_content(title, start_date, end_date):
    """Generates the raw string content for an .ics calendar file."""
    # Convert dates to YYYYMMDD format
    # ICS all-day events usually require DTEND to be the day AFTER the user's end date
    if isinstance(end_date, str): end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    if isinstance(start_date, str): start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    
    dtstart = start_date.strftime("%Y%m%d")
    dtend = (end_date + timedelta(days=1)).strftime("%Y%m%d") 
    
    return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//SISTEMA DUAL//MX
BEGIN:VEVENT
DTSTART;VALUE=DATE:{dtstart}
DTEND;VALUE=DATE:{dtend}
SUMMARY:ENTREGA DUAL: {title}
DESCRIPTION:Periodo de entrega para {title} en el Sistema de Gestión DUAL.
END:VEVENT
END:VCALENDAR"""

def send_period_invites(to_email, period_name, dates_dict):
    """
    Sends an email with .ics attachments for each document period.
    dates_dict format: {'Anexo 1': (start_date, end_date)}
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_USER", "test@example.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "password")

    if not to_email:
        return False

    subject = f"Calendario de Entregas DUAL - Periodo {period_name}"
    body = f"Hola,\n\nSe ha configurado el Periodo {period_name} en el Sistema DUAL.\nAdjunto encontrarás las invitaciones de calendario (.ics) para las fechas de entrega de los documentos.\n\nPor favor, abre los archivos adjuntos para guardarlos en tu respectivo calendario.\n\nAtentamente,\nSistema DUAL"
    
    if sender_email == "test@example.com" or not sender_password:
        print(f"--- MOCK CALENDAR EMAIL TO {to_email} ---")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach .ics files
        for doc_name, (start, end) in dates_dict.items():
            if start and end:
                ics_data = generate_ics_content(doc_name, start, end)
                part = MIMEBase('text', 'calendar', method='REQUEST')
                part.set_payload(ics_data.encode('utf-8'))
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="Entrega_{doc_name.replace(" ", "_").replace("(", "").replace(")", "")}.ics"')
                msg.attach(part)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send calendar invites: {e}")
        return False

def send_document_email(to_email, student_name, document_name, file_path):
    """
    Sends an email with a document attached manually.
    """
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    sender_email = os.environ.get("SMTP_USER", "test@example.com")
    sender_password = os.environ.get("SMTP_PASSWORD", "password")

    if not to_email:
        return False

    subject = f"Documento DUAL: {document_name}"
    body = f"Hola {student_name},\n\nAdjunto encontrarás el documento '{document_name}' correspondiente a tu proceso en el Sistema DUAL.\n\nAtentamente,\nCoordinación DUAL"
    
    if sender_email == "test@example.com" or not sender_password:
        print(f"--- MOCK DOCUMENT EMAIL TO {to_email} ---")
        return True

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            file_name = os.path.basename(file_path)
            part.add_header('Content-Disposition', f'attachment; filename="{file_name}"')
            msg.attach(part)
        else:
            return False

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send document email: {e}")
        return False
