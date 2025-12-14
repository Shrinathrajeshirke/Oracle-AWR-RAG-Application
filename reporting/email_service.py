"""
Email service for sending reports
Handles SMTP configuration and email delivery
"""

import os
import smtplib
from email.message import EmailMessage
from config.settings import SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
from utils.logger import logging


class EmailService:
    """Handles email sending with SMTP"""
    
    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_username = SMTP_USERNAME
        self.smtp_password = SMTP_PASSWORD
        
        logging.info("EmailService initialized")
        self._validate_config()
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            logging.warning("SMTP configuration incomplete - email sending will fail")
            logging.warning(f"Server: {bool(self.smtp_server)}, Username: {bool(self.smtp_username)}, Password: {bool(self.smtp_password)}")
    
    def send_report(self, to_email: str, subject: str, body: str,
                   attachment_path: str = None, attachment_content: str = None,
                   attachment_filename: str = None) -> bool:
        """
        Send email with optional attachment
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body text
            attachment_path: Path to file attachment (for PDF)
            attachment_content: String content to attach (for HTML/Text)
            attachment_filename: Name for the attachment file
        
        Returns:
            bool: True if email sent successfully
        """
        logging.info(f"Sending email to: {to_email}")
        logging.info(f"Subject: {subject}")
        
        if not all([self.smtp_server, self.smtp_username, self.smtp_password]):
            logging.error("SMTP configuration missing - cannot send email")
            return False
        
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Set main email body
            if attachment_content:
                msg.set_content("Please see the attached report file.")
            else:
                msg.set_content(body)
            
            # Handle file attachment (PDF)
            if attachment_path and os.path.exists(attachment_path):
                logging.info(f"Attaching file: {attachment_path}")
                with open(attachment_path, 'rb') as fp:
                    file_data = fp.read()
                    msg.add_attachment(
                        file_data,
                        maintype='application',
                        subtype='pdf',
                        filename=os.path.basename(attachment_path)
                    )
            
            # Handle string content attachment (HTML or Text)
            if attachment_content and attachment_filename:
                logging.info(f"Attaching content as: {attachment_filename}")
                if attachment_filename.endswith('.html'):
                    msg.add_attachment(
                        attachment_content.encode('utf-8'),
                        maintype='text',
                        subtype='html',
                        filename=attachment_filename
                    )
                else:  # .txt
                    msg.add_attachment(
                        attachment_content.encode('utf-8'),
                        maintype='text',
                        subtype='plain',
                        filename=attachment_filename
                    )
            
            # Send email
            logging.info(f"Connecting to SMTP server: {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logging.info(f"Email sent successfully to: {to_email}")
            return True
        
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def send_text_report(self, to_email: str, subject: str, content: str) -> bool:
        """Send text report via email"""
        logging.info("Sending text report email...")
        return self.send_report(
            to_email=to_email,
            subject=subject,
            body="Text report attached",
            attachment_content=content,
            attachment_filename="awr_report.txt"
        )
    
    def send_html_report(self, to_email: str, subject: str, content: str) -> bool:
        """Send HTML report via email"""
        logging.info("Sending HTML report email...")
        return self.send_report(
            to_email=to_email,
            subject=subject,
            body="HTML report attached",
            attachment_content=content,
            attachment_filename="awr_report.html"
        )
    
    def send_pdf_report(self, to_email: str, subject: str, pdf_path: str) -> bool:
        """Send PDF report via email"""
        logging.info("Sending PDF report email...")
        return self.send_report(
            to_email=to_email,
            subject=subject,
            body="PDF report attached",
            attachment_path=pdf_path
        )