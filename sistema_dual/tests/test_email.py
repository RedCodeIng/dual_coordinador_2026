import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils.notifications import send_email

def test_send_email():
    # Usar el correo del remitente como destinatario para la prueba
    to_email = os.getenv("SMTP_USER")
    if not to_email:
        print("Error: SMTP_USER no definido en .env")
        return

    print(f"Enviando correo de prueba a {to_email}...")
    
    context = {
        "nombre": "Administrador",
        "mensaje": "Este es un correo de prueba del Sistema de Gestión Dual. Si estás leyendo esto, la configuración SMTP funciona correctamente.",
        "accion_url": "http://localhost:8501",
        "accion_texto": "Ir al Sistema"
    }
    
    success, message = send_email(to_email, "Prueba de Notificación - Sistema Dual", "base_notification.html", context)
    
    if success:
        print("✅ Correo enviado exitosamente.")
    else:
        print(f"❌ Error al enviar correo: {message}")

if __name__ == "__main__":
    test_send_email()
