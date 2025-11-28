import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid
from typing import Optional
from app.config import SMTP_SERVER, SMTP_PORT, EMAIL_USER, EMAIL_PASSWORD, BASE_URL

def generate_verification_token() -> str:
    return str(uuid.uuid4())

def send_verification_email(email: str, token: str, base_url: str = BASE_URL) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = "Confirme seu cadastro - Sistema de Finanças"
        
        verification_link = f"{base_url}/verify-email?token={token}"
        
        body = f"""
        <html>
        <body>
            <h2>Bem-vindo ao Sistema de Finanças!</h2>
            <p>Para ativar sua conta, clique no link abaixo:</p>
            <p><a href="{verification_link}">Confirmar Email</a></p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p>{verification_link}</p>
            <p>Este link expira em 24 horas.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

def send_password_reset_email(email: str, token: str, base_url: str = BASE_URL) -> bool:
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = email
        msg['Subject'] = "Redefinir senha - Sistema de Finanças"
        
        reset_link = f"{base_url}/reset-password?token={token}"
        
        body = f"""
        <html>
        <body>
            <h2>Redefinir sua senha</h2>
            <p>Você solicitou a redefinição de sua senha. Clique no link abaixo para criar uma nova senha:</p>
            <p><a href="{reset_link}">Redefinir Senha</a></p>
            <p>Ou copie e cole este link no seu navegador:</p>
            <p>{reset_link}</p>
            <p>Este link expira em 1 hora.</p>
            <p>Se você não solicitou esta redefinição, ignore este email.</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email de reset: {e}")
        return False