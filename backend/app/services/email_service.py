"""
Objective: Implement an email service for sending various types of notifications.
This file provides a dedicated service for email communication, supporting
different message templates for user interactions throughout the application.


The EmailService is a specialized service for handling all email communications in your application, providing templated notification emails for various user interactions.
Key Features:

Email Delivery Functionality:

SMTP Integration: Connects to SMTP servers for email delivery
HTML Support: Sends rich HTML-formatted emails
Recipient Management: Supports CC and BCC recipients
Error Handling: Robust error detection and logging


Notification Templates:

Welcome Emails: For new user registrations
Enrollment Updates: For course enrollment status changes
Payment Receipts: For successful payments
Password Reset: For account recovery
Generic Notifications: For custom system messages


Personalization Features:

User Name: Including user's name in greetings
Course Details: Referencing specific course titles
Transaction Information: Including payment amounts and IDs
Status Updates: Human-friendly status messages


Technical Implementations:

MIME Support: Proper email formatting with MIME types
TLS Security: Optional TLS encryption for SMTP connections
Authentication: SMTP authentication support
Logging: Comprehensive logging of email operations



Business Value:
This service provides critical communication capabilities to your application:

User Engagement: Welcoming new users and keeping them informed
Transaction Transparency: Confirming enrollments and payments
Status Updates: Keeping users informed of application events
Security Support: Enabling password reset and account recovery
Professional Presentation: HTML-formatted, branded emails

Design Considerations:

Configuration-Driven: Settings loaded from application configuration
Failure Tolerance: Graceful handling of configuration or delivery issues
Template Patterns: Consistent email formatting and branding
Flexible API: Both specific template methods and general-purpose sending

The implementation follows email best practices, including proper MIME handling, error catching, and logging. It centralizes all email formatting and sending logic in one place, making it easy to maintain consistent communications throughout the application.
This service integrates with various business processes in your application, such as user registration, enrollment management, and payment processing, providing the notification component of these workflows.

"""

import logging
import smtplib
from email.mime.text import MIMEText  # For email content
from email.mime.multipart import MIMEMultipart  # For mixed content emails
from typing import List, Optional
from datetime import datetime

from app.core.config import settings  # Application settings

# Set up logging
logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails.
    
    Provides a centralized service for sending various types of email notifications
    to users, including welcome emails, enrollment updates, and payment receipts.
    """
    
    def __init__(self):
        """
        Initialize the email service.
        
        Loads email configuration from application settings,
        including SMTP server details and sender information.
        """
        # SMTP server configuration
        self.smtp_host = settings.SMTP_HOST  # SMTP server address
        self.smtp_port = settings.SMTP_PORT  # SMTP server port
        self.smtp_user = settings.SMTP_USER  # SMTP username
        self.smtp_password = settings.SMTP_PASSWORD  # SMTP password
        self.smtp_tls = settings.SMTP_TLS  # Whether to use TLS
        
        # Sender information
        self.from_email = settings.EMAILS_FROM_EMAIL  # Sender email address
        self.from_name = settings.EMAILS_FROM_NAME  # Sender display name
    
    def send_email(
        self, 
        email_to: str,  # Recipient email
        subject: str,   # Email subject
        body: str,      # Email body content
        html: bool = True,  # Whether body is HTML or plain text
        cc: Optional[List[str]] = None,  # Carbon copy recipients
        bcc: Optional[List[str]] = None  # Blind carbon copy recipients
    ) -> bool:
        """
        Send an email.
        
        Core method for sending emails with proper MIME formatting,
        error handling, and logging.
        
        Args:
            email_to: Recipient email address
            subject: Email subject line
            body: Email body content
            html: Whether body is HTML (True) or plain text (False)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Skip if SMTP is not configured
        if not self.smtp_host or not self.smtp_port:
            logger.warning("SMTP settings not configured, email not sent")
            return False
        
        # Create MIME multipart message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{self.from_name} <{self.from_email}>"
        message["To"] = email_to
        
        # Add CC and BCC if provided
        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)
        
        # Add body content with appropriate MIME type
        if html:
            message.attach(MIMEText(body, "html"))
        else:
            message.attach(MIMEText(body, "plain"))
        
        try:
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                # Use TLS if configured
                if self.smtp_tls:
                    server.starttls()
                
                # Authenticate if credentials provided
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                
                # Compile all recipients
                recipients = [email_to]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                # Send the email
                server.sendmail(
                    self.from_email,
                    recipients,
                    message.as_string()
                )
            
            logger.info(f"Email sent to {email_to}")
            return True
        
        except Exception as e:
            # Log any errors that occur
            logger.error(f"Error sending email to {email_to}: {e}")
            return False
    
    def send_welcome_email(self, email_to: str, full_name: str) -> bool:
        """
        Send a welcome email to a new user.
        
        Sends a formatted welcome message to newly registered users.
        
        Args:
            email_to: User's email address
            full_name: User's full name for personalization
            
        Returns:
            True if email sent successfully, False otherwise
        """
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
        """
        Send an enrollment confirmation email.
        
        Notifies users when their enrollment request has been received.
        
        Args:
            email_to: User's email address
            full_name: User's full name for personalization
            course_title: Title of the course enrolled in
            
        Returns:
            True if email sent successfully, False otherwise
        """
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
        """
        Send an email about enrollment status change.
        
        Notifies users when their enrollment status has been updated
        (e.g., approved, rejected, completed).
        
        Args:
            email_to: User's email address
            full_name: User's full name for personalization
            course_title: Title of the course
            status: New enrollment status (approved, rejected, completed)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        # Map status to friendly text
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
        """
        Send a payment receipt email.
        
        Provides users with a confirmation and receipt of their payment.
        
        Args:
            email_to: User's email address
            full_name: User's full name for personalization
            course_title: Title of the course
            amount: Payment amount
            transaction_id: Payment transaction identifier
            
        Returns:
            True if email sent successfully, False otherwise
        """
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
        """
        Send a notification email.
        
        Generic method for sending custom notification emails.
        
        Args:
            email_to: User's email address
            subject: Email subject
            body: Email content
            
        Returns:
            True if email sent successfully, False otherwise
        """
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
        """
        Send a password reset email.
        
        Sends a password reset link with a secure token to users
        who have requested to reset their password.
        
        Args:
            email_to: User's email address
            full_name: User's full name for personalization
            reset_token: Secure token for password reset
            
        Returns:
            True if email sent successfully, False otherwise
        """
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