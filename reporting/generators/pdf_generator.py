"""
PDF report generation
Generates professional PDF reports using ReportLab
"""

import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.colors import HexColor
from utils.logger import logging


class PDFReportGenerator:
    """Generates PDF reports with professional formatting"""
    
    @staticmethod
    def generate(user_query: str, answer_markdown: str, context: list[str], output_path: str) -> str:
        """
        Generate a PDF report with styling
        
        Args:
            user_query: User's question/request
            answer_markdown: AI-generated answer (markdown format)
            context: List of retrieved context chunks
            output_path: Path where PDF will be saved
        
        Returns:
            str: Path to generated PDF file
        """
        logging.info(f"Generating PDF report to: {output_path}")
        
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=50,
                leftMargin=50,
                topMargin=50,
                bottomMargin=30
            )
            
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=HexColor('#2c3e50'),
                spaceAfter=20,
                alignment=1
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=HexColor('#2980b9'),
                spaceAfter=10,
                spaceBefore=15,
            )
            
            subheading_style = ParagraphStyle(
                'SubHeading',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=10,
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontSize=10,
                leading=14,
                spaceAfter=10,
            )
            
            bullet_style = ParagraphStyle(
                'BulletStyle',
                parent=styles['BodyText'],
                fontSize=10,
                leftIndent=20,
                bulletIndent=10,
                spaceAfter=6,
            )
            
            critical_style = ParagraphStyle(
                'CriticalStyle',
                parent=styles['BodyText'],
                fontSize=10,
                textColor=HexColor('#e74c3c'),
                leftIndent=20,
                spaceAfter=6,
            )
            
            warning_style = ParagraphStyle(
                'WarningStyle',
                parent=styles['BodyText'],
                fontSize=10,
                textColor=HexColor('#f39c12'),
                leftIndent=20,
                spaceAfter=6,
            )
            
            # Title
            elements.append(Paragraph("Oracle AWR Analysis Report", title_style))
            elements.append(Spacer(1, 10))
            
            # Metadata
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata = f"<font size=8 color='#7f8c8d'>Generated: {timestamp}</font>"
            elements.append(Paragraph(metadata, styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Query Section
            elements.append(Paragraph("Query", heading_style))
            query_safe = user_query.replace('<', '&lt;').replace('>', '&gt;')
            elements.append(Paragraph(query_safe, body_style))
            elements.append(Spacer(1, 15))
            
            # Answer Section
            elements.append(Paragraph("Analysis Results", heading_style))
            elements.append(Spacer(1, 10))
            
            # Parse and format the answer
            answer_lines = answer_markdown.split('\n')
            
            for line in answer_lines:
                line = line.strip()
                if not line:
                    elements.append(Spacer(1, 6))
                    continue
                
                # Escape HTML characters
                line = line.replace('<', '&lt;').replace('>', '&gt;')
                
                # Handle headers (###, ##, #)
                if line.startswith('### '):
                    text = line.replace('### ', '')
                    elements.append(Paragraph(text, subheading_style))
                elif line.startswith('## '):
                    text = line.replace('## ', '')
                    elements.append(Paragraph(text, heading_style))
                elif line.startswith('# '):
                    text = line.replace('# ', '')
                    elements.append(Paragraph(text, heading_style))
                
                # Handle bold (**text**)
                elif '**' in line:
                    line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                    elements.append(Paragraph(line, body_style))
                
                # Handle bullet points (-, *, •)
                elif line.startswith(('- ', '* ', '• ', '→ ')):
                    text = line.lstrip('-*•→ ')
                    elements.append(Paragraph(f"• {text}", bullet_style))
                
                # Handle numbered lists
                elif line and line[0].isdigit() and '. ' in line[:4]:
                    elements.append(Paragraph(line, bullet_style))
                
                # Handle emoji indicators with appropriate styling
                elif 'CRITICAL' in line.upper() or '🔴' in line:
                    line = line.replace('🔴', '[CRITICAL]')
                    elements.append(Paragraph(f"<b>{line}</b>", critical_style))
                elif 'WARNING' in line.upper() or '🟡' in line:
                    line = line.replace('🟡', '[WARNING]')
                    elements.append(Paragraph(f"<b>{line}</b>", warning_style))
                elif 'INFO' in line or 'ℹ️' in line:
                    line = line.replace('ℹ️', '[INFO]')
                    elements.append(Paragraph(f"<b>{line}</b>", body_style))
                
                # Regular text
                else:
                    elements.append(Paragraph(line, body_style))
            
            elements.append(Spacer(1, 20))
            
            # Retrieved Contexts Section
            elements.append(Paragraph("Retrieved Context Sources", heading_style))
            elements.append(Spacer(1, 10))
            
            if context:
                for i, ctx in enumerate(context[:5], 1):
                    ctx_safe = str(ctx)[:400].replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(f"<b>Source {i}:</b>", subheading_style))
                    elements.append(Paragraph(f"{ctx_safe}...", body_style))
                    elements.append(Spacer(1, 8))
            else:
                elements.append(Paragraph("No context sources retrieved", body_style))
            
            # Footer
            elements.append(Spacer(1, 20))
            footer_text = "<font size=8 color='#95a5a6'>Oracle AWR RAG Application | Powered by AI</font>"
            elements.append(Paragraph(footer_text, styles['Normal']))
            
            # Build PDF
            doc.build(elements)
            logging.info(f"PDF report generated successfully: {output_path}")
            return output_path
        
        except Exception as e:
            logging.error(f"Error generating PDF: {e}")
            raise