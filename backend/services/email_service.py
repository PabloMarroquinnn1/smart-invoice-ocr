import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


def enviar_reporte_email(destinatario: str, filepath: str, asunto: str = None) -> dict:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASS", "")

    if not smtp_user or not smtp_pass:
        return {
            "status": "error",
            "mensaje": "SMTP no configurado. Configure las variables SMTP_USER y SMTP_PASS."
        }

    if not asunto:
        asunto = f"SmartInvoice - Reporte {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = destinatario
        msg['Subject'] = asunto

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #302b63;">SmartInvoice - Reporte Automático</h2>
            <p>Se adjunta el reporte generado automáticamente por el sistema SmartInvoice.</p>
            <p><strong>Fecha de generación:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
            <p><strong>Archivo:</strong> {os.path.basename(filepath)}</p>
            <hr>
            <p style="color: #888; font-size: 12px;">
                Este correo fue enviado automáticamente por SmartInvoice.
            </p>
        </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(filepath)}'
                )
                msg.attach(part)

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()

        return {
            "status": "ok",
            "mensaje": f"Reporte enviado exitosamente a {destinatario}"
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "mensaje": "Error de autenticación SMTP. Verifique usuario y contraseña."
        }
    except Exception as e:
        return {
            "status": "error",
            "mensaje": f"Error enviando correo: {str(e)}"
        }
