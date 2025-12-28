"""
Email Service using Resend
Handles sending transactional emails (Welcome, Reset Password, Payments).
"""
import os
import resend
from utils.logging_config import logger

# Initialize Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
else:
    logger.warning("RESEND_API_KEY not set. Emails will be printed to console.")

FROM_EMAIL = "NorteAcoes <onboarding@resend.dev>" # Default dev email, change in prod

def send_email(to_email: str, subject: str, html_content: str):
    """
    Send an email using Resend.
    
    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML body
        
    Returns:
        True if sent, False otherwise
    """
    if not RESEND_API_KEY:
        logger.info(f"📧 [MOCK EMAIL] To: {to_email} | Subject: {subject}")
        return True
        
    try:
        r = resend.Emails.send({
            "from": FROM_EMAIL,
            "to": to_email,
            "subject": subject,
            "html": html_content
        })
        logger.info("email_sent", id=r.get("id"), to=to_email)
        return True
    except Exception as e:
        logger.error("email_failed", error=str(e), to=to_email)
        return False

def send_welcome_email(name: str, email: str):
    """Send welcome email to new user."""
    subject = "Bem-vindo ao NorteAcoes! 🚀"
    html = f"""
    <h1>Olá, {name}!</h1>
    <p>Estamos muito felizes em ter você conosco.</p>
    p>O NorteAcoes vai te ajudar a encontrar as melhores oportunidades da bolsa com Inteligência Artificial.</p>
    <br>
    <p>Se tiver dúvidas, responda este email.</p>
    <p>Att,<br>Equipe NorteAcoes</p>
    """
    return send_email(email, subject, html)

def send_reset_password_email(email: str, reset_link: str):
    """Send password reset link."""
    subject = "Recuperação de Senha - NorteAcoes"
    html = f"""
    <h2>Recuperação de Senha</h2>
    <p>Você solicitou a redefinição de sua senha.</p>
    <p>Clique no botão abaixo para criar uma nova senha:</p>
    <a href="{reset_link}" style="padding: 12px 24px; background-color: #7c3aed; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">Redefinir Senha</a>
    <p>Se não foi você, ignore este email.</p>
    """
    return send_email(email, subject, html)

def send_payment_success_email(email: str, amount: int):
    """Send payment confirmation email."""
    # Amount comes in cents from Stripe usually, verify this
    formatted_amount = f"R$ {amount/100:.2f}".replace('.', ',')
    
    subject = "Pagamento Confirmado! Você é PRO 🚀"
    html = f"""
    <h1>Pagamento Confirmado!</h1>
    <p>Obrigado por assinar o NorteAcoes Premium.</p>
    <p>Detalhes da transação:</p>
    <ul>
        <li><strong>Valor:</strong> {formatted_amount}</li>
        <li><strong>Plano:</strong> Assinatura Mensal</li>
        <li><strong>Status:</strong> Ativo</li>
    </ul>
    <p>Agora você tem acesso ilimitado a todos os rankings e IA.</p>
    <br>
    <a href="https://acoes.vercel.app/" style="padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 6px; display: inline-block;">Acessar Dashboard PRO</a>
    """
    return send_email(email, subject, html)
