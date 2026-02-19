
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
