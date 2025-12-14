"""
Report generation orchestrator
Coordinates report generation and delivery across multiple formats
"""

import os
import uuid
from reporting.generators.text_generator import TextReportGenerator
from reporting.generators.html_generator import HTMLReportGenerator
from reporting.generators.pdf_generator import PDFReportGenerator
from reporting.email_service import EmailService
from config.settings import TEMP_DIR
from utils.logger import logging


class ReportBuilder:
    """Orchestrates report generation and delivery"""
    
    def __init__(self):
        """Initialize report builder"""
        self.text_generator = TextReportGenerator()
        self.html_generator = HTMLReportGenerator()
        self.pdf_generator = PDFReportGenerator()
        self.email_service = EmailService()
        
        # Ensure temp directory exists
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        logging.info("ReportBuilder initialized")
    
    def generate_text_report(self, user_query: str, answer: str, contexts: list) -> str:
        """
        Generate text format report
        
        Args:
            user_query: User's question
            answer: AI-generated answer
            contexts: Retrieved contexts
        
        Returns:
            str: Text report content
        """
        logging.info("Generating text report...")
        return self.text_generator.generate(user_query, answer, contexts)
    
    def generate_html_report(self, user_query: str, answer: str, contexts: list) -> str:
        """
        Generate HTML format report
        
        Args:
            user_query: User's question
            answer: AI-generated answer
            contexts: Retrieved contexts
        
        Returns:
            str: HTML report content
        """
        logging.info("Generating HTML report...")
        return self.html_generator.generate(user_query, answer, contexts)
    
    def generate_pdf_report(self, user_query: str, answer: str, contexts: list) -> str:
        """
        Generate PDF format report
        
        Args:
            user_query: User's question
            answer: AI-generated answer
            contexts: Retrieved contexts
        
        Returns:
            str: Path to generated PDF file
        """
        logging.info("Generating PDF report...")
        pdf_path = os.path.join(TEMP_DIR, f"awr_report_{uuid.uuid4().hex[:8]}.pdf")
        return self.pdf_generator.generate(user_query, answer, contexts, pdf_path)
    
    def generate_and_send_report(self, user_query: str, answer: str, contexts: list,
                                to_email: str, report_format: str = "pdf") -> bool:
        """
        Generate report and send via email in one operation
        
        Args:
            user_query: User's question
            answer: AI-generated answer
            contexts: Retrieved contexts
            to_email: Recipient email address
            report_format: Format to generate ('pdf', 'html', or 'text')
        
        Returns:
            bool: True if report generated and sent successfully
        """
        logging.info(f"Generating {report_format} report and sending to {to_email}...")
        
        try:
            subject = f"AWR Analysis Report - {user_query[:50]}..."
            
            if report_format == "text":
                content = self.generate_text_report(user_query, answer, contexts)
                success = self.email_service.send_text_report(to_email, subject, content)
                
            elif report_format == "html":
                content = self.generate_html_report(user_query, answer, contexts)
                success = self.email_service.send_html_report(to_email, subject, content)
                
            elif report_format == "pdf":
                pdf_path = self.generate_pdf_report(user_query, answer, contexts)
                success = self.email_service.send_pdf_report(to_email, subject, pdf_path)
                
                # Cleanup temp PDF after sending
                if success and os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                        logging.info(f"Cleaned up temporary PDF: {pdf_path}")
                    except Exception as e:
                        logging.warning(f"Could not delete temp PDF {pdf_path}: {e}")
            else:
                logging.error(f"Unknown report format: {report_format}")
                return False
            
            if success:
                logging.info(f"Report sent successfully to {to_email}")
            else:
                logging.error(f"Failed to send report to {to_email}")
            
            return success
            
        except Exception as e:
            logging.error(f"Error generating/sending report: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False
    
    def generate_all_formats(self, user_query: str, answer: str, contexts: list) -> dict:
        """
        Generate reports in all formats at once
        
        Args:
            user_query: User's question
            answer: AI-generated answer
            contexts: Retrieved contexts
        
        Returns:
            dict: Reports in all formats with keys 'text', 'html', 'pdf'
        """
        logging.info("Generating reports in all formats...")
        
        try:
            text_report = self.generate_text_report(user_query, answer, contexts)
            html_report = self.generate_html_report(user_query, answer, contexts)
            pdf_path = self.generate_pdf_report(user_query, answer, contexts)
            
            return {
                "text": text_report,
                "html": html_report,
                "pdf": pdf_path,
                "success": True
            }
        
        except Exception as e:
            logging.error(f"Error generating reports: {e}")
            return {"success": False, "error": str(e)}