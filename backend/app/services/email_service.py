import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_tls = settings.SMTP_TLS
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
    
    def send_email(
        self, 
        email_to: str,
        subject: str,
        body: str,
        html: bool = True,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send an email."""
        # Skip if SMTP is not configured
        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP settings not configured, email not sent")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = email_to
        
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        
        # Add body
        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                recipients = [email_to]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(
                    self.from_email,
                    recipients,
                    message.as_string()
                )
            logger.info(f"Email sent to {email_to}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {email_to}: {e}")
            return False
    
    def send_welcome_email(self, email_to: str, full_name: str) -> bool:
        """Send a welcome email to a new user."""
        subject = f"Welcome to {settings.PROJECT_NAME}"
        body = f"""
        <html>
        <body>
            <h1>Welcome to {settings.PROJECT_NAME}!</h1>
            <p>Hi {full_name},</p>
            <p>Thank you for joining our culinary community. We're excited to have you on board.</p>
            <p>You can now browse courses, enroll, and start your culinary journey.</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=body)
    
    def send_enrollment_confirmation_email(
        self, email_to: str, full_name: str, course_title: str
    ) -> bool:
        """Send an enrollment confirmation email."""
        subject = f"Enrollment Confirmation - {course_title}"
        body = f"""
        <html>
        <body>
            <h1>Enrollment Confirmation</h1>
            <p>Hi {full_name},</p>
            <p>Your enrollment in <strong>{course_title}</strong> has been received and is pending approval.</p>
            <p>We'll notify you once your enrollment is processed.</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=body)
    
    def send_enrollment_status_email(
        self, email_to: str, full_name: str, course_title: str, status: str
    ) -> bool:
        """Send an email about enrollment status change."""
        status_text = {
            "approved": "has been approved",
            "rejected": "has been rejected",
            "completed": "has been marked as completed"
        }.get(status, "has been updated")
        
        subject = f"Enrollment Status Update - {course_title}"
        body = f"""
        <html>
        <body>
            <h1>Enrollment Status Update</h1>
            <p>Hi {full_name},</p>
            <p>Your enrollment in <strong>{course_title}</strong> {status_text}.</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=body)
    
    def send_payment_receipt_email(
        self, email_to: str, full_name: str, course_title: str, 
        amount: float, transaction_id: str
    ) -> bool:
        """Send a payment receipt email."""
        subject = f"Payment Receipt - {course_title}"
        body = f"""
        <html>
        <body>
            <h1>Payment Receipt</h1>
            <p>Hi {full_name},</p>
            <p>Your payment for <strong>{course_title}</strong> has been processed successfully.</p>
            <p><strong>Amount:</strong> ${amount:.2f}</p>
            <p><strong>Transaction ID:</strong> {transaction_id}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Thank you for your payment!</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=body)
    
    def send_notification_email(
        self, email_to: str, subject: str, body: str
    ) -> bool:
        """Send a notification email."""
        html_body = f"""
        <html>
        <body>
            <h1>{subject}</h1>
            <p>{body}</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=html_body)
    
    def send_password_reset_email(
        self, email_to: str, full_name: str, reset_token: str
    ) -> bool:
        """Send a password reset email."""
        subject = "Password Reset Request"
        reset_url = f"{settings.SERVER_HOST}/reset-password?token={reset_token}"
        
        body = f"""
        <html>
        <body>
            <h1>Password Reset Request</h1>
            <p>Hi {full_name},</p>
            <p>We received a request to reset your password. If you didn't make this request, you can ignore this email.</p>
            <p>To reset your password, click the link below:</p>
            <p><a href="{reset_url}">Reset Your Password</a></p>
            <p>This link will expire in 24 hours.</p>
            <p>Best regards,<br>The {settings.PROJECT_NAME} Team</p>
        </body>
        </html>
        """
        
        return self.send_email(email_to=email_to, subject=subject, body=body)