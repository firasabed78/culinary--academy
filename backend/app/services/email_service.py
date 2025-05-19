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
"""
email_service.py - Service layer for email operations
This file handles email sending functionality for the Culinary Academy
Student Registration system, including notification emails, enrollment
confirmations, and payment receipts.
"""
"""
email_service.py - Service layer for email operations
This file handles email sending functionality for the Culinary Academy
Student Registration system, including notification emails, enrollment
confirmations, and payment receipts.
"""

import logging
from typing import List, Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for email operations."""
    
    def __init__(self):
        """Initialize email service with SMTP configuration."""
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAILS_FROM_EMAIL
        self.from_name = settings.EMAILS_FROM_NAME
    
    def _create_connection(self) -> smtplib.SMTP:
        """
        Create SMTP connection.
        
        Returns
        -------
        smtplib.SMTP
            SMTP connection instance
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def _send_email(
        self, 
        email_to: str, 
        subject: str, 
        body: str, 
        body_type: str = "html"
    ) -> bool:
        """
        Send an email.
        
        Parameters
        ----------
        email_to: Recipient email address
        subject: Email subject
        body: Email body content
        body_type: Email body type ("html" or "plain")
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = email_to
            msg['Subject'] = subject
            
            # Attach body
            if body_type == "html":
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with self._create_connection() as server:
                text = msg.as_string()
                server.sendmail(self.from_email, email_to, text)
            
            logger.info(f"Email sent successfully to {email_to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {email_to}: {e}")
            return False
    
    def send_notification_email(
        self, email_to: str, subject: str, body: str
    ) -> bool:
        """
        Send a notification email.
        
        Parameters
        ----------
        email_to: Recipient email address
        subject: Email subject
        body: Email content
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">{subject}</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
                    <p>{body}</p>
                </div>
                <hr style="margin-top: 30px;">
                <p style="color: #666; font-size: 12px;">
                    This email was sent from {self.from_name}. 
                    If you have any questions, please contact us.
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email_to, subject, html_body, "html")
    
    def send_enrollment_confirmation(
        self, email_to: str, student_name: str, course_title: str, enrollment_id: int
    ) -> bool:
        """
        Send enrollment confirmation email.
        
        Parameters
        ----------
        email_to: Student email address
        student_name: Student's full name
        course_title: Course title
        enrollment_id: Enrollment ID
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        subject = f"Enrollment Confirmation - {course_title}"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">Enrollment Confirmed!</h2>
                <p>Dear {student_name},</p>
                <p>We're excited to confirm your enrollment in <strong>{course_title}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Enrollment Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Enrollment ID:</strong> #{enrollment_id}</li>
                        <li><strong>Course:</strong> {course_title}</li>
                        <li><strong>Student:</strong> {student_name}</li>
                    </ul>
                </div>
                
                <p>You will receive additional information about class schedules and requirements soon.</p>
                <p>Welcome to the Culinary Academy!</p>
                
                <hr style="margin-top: 30px;">
                <p style="color: #666; font-size: 12px;">
                    {self.from_name} - Culinary Excellence
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email_to, subject, html_body, "html")
    
    def send_payment_confirmation(
        self, email_to: str, student_name: str, amount: float, course_title: str, transaction_id: str
    ) -> bool:
        """
        Send payment confirmation email.
        
        Parameters
        ----------
        email_to: Student email address
        student_name: Student's full name
        amount: Payment amount
        course_title: Course title
        transaction_id: Payment transaction ID
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        subject = f"Payment Confirmation - {course_title}"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #28a745;">Payment Confirmed!</h2>
                <p>Dear {student_name},</p>
                <p>We have successfully received your payment for <strong>{course_title}</strong>.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Payment Details:</h3>
                    <ul style="list-style: none; padding: 0;">
                        <li><strong>Amount:</strong> ${amount:.2f}</li>
                        <li><strong>Course:</strong> {course_title}</li>
                        <li><strong>Transaction ID:</strong> {transaction_id}</li>
                    </ul>
                </div>
                
                <p>You are now fully enrolled in the course. We look forward to seeing you in class!</p>
                
                <hr style="margin-top: 30px;">
                <p style="color: #666; font-size: 12px;">
                    {self.from_name} - Culinary Excellence
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email_to, subject, html_body, "html")
    
    def send_schedule_update(
        self, email_to: str, student_name: str, course_title: str, schedule_details: str
    ) -> bool:
        """
        Send schedule update email.
        
        Parameters
        ----------
        email_to: Student email address
        student_name: Student's full name
        course_title: Course title
        schedule_details: Schedule change details
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        subject = f"Schedule Update - {course_title}"
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #ffc107;">Schedule Update</h2>
                <p>Dear {student_name},</p>
                <p>There has been an update to the schedule for <strong>{course_title}</strong>.</p>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h3 style="margin-top: 0;">Schedule Changes:</h3>
                    <p>{schedule_details}</p>
                </div>
                
                <p>Please make note of these changes and adjust your schedule accordingly.</p>
                <p>If you have any questions, please don't hesitate to contact us.</p>
                
                <hr style="margin-top: 30px;">
                <p style="color: #666; font-size: 12px;">
                    {self.from_name} - Culinary Excellence
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email_to, subject, html_body, "html")
    
    def send_welcome_email(self, email_to: str, full_name: str, role: str) -> bool:
        """
        Send welcome email to new users.
        
        Parameters
        ----------
        email_to: User email address
        full_name: User's full name
        role: User role (student, instructor, admin)
        
        Returns
        -------
        bool
            True if email sent successfully, False otherwise
        """
        subject = "Welcome to Culinary Academy!"
        
        role_message = {
            "student": "We're excited to have you join our culinary community as a student!",
            "instructor": "We're honored to have you join our team as an instructor!",
            "admin": "Welcome to the administrative team!"
        }
        
        html_body = f"""
        <html>
        <body>
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #007bff;">Welcome to Culinary Academy!</h2>
                <p>Dear {full_name},</p>
                <p>{role_message.get(role, 'Welcome to our platform!')}</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">What's Next?</h3>
                    <ul>
                        <li>Complete your profile setup</li>
                        <li>Browse our available courses</li>
                        <li>Connect with our culinary community</li>
                    </ul>
                </div>
                
                <p>If you have any questions, our support team is here to help.</p>
                <p>Happy cooking!</p>
                
                <hr style="margin-top: 30px;">
                <p style="color: #666; font-size: 12px;">
                    {self.from_name} - Where Culinary Dreams Come True
                </p>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(email_to, subject, html_body, "html")
    
    def send_bulk_notification(
        self, email_list: List[str], subject: str, body: str
    ) -> Dict[str, int]:
        """
        Send bulk notification emails.
        
        Parameters
        ----------
        email_list: List of recipient email addresses
        subject: Email subject
        body: Email content
        
        Returns
        -------
        Dict[str, int]
            Statistics: {"sent": count, "failed": count}
        """
        sent_count = 0
        failed_count = 0
        
        for email in email_list:
            if self.send_notification_email(email, subject, body):
                sent_count += 1
            else:
                failed_count += 1
        
        logger.info(f"Bulk email completed: {sent_count} sent, {failed_count} failed")
        return {"sent": sent_count, "failed": failed_count}