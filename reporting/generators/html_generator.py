"""
HTML report generation
Generates styled HTML reports from RAG responses
"""

import markdown
from utils.logger import logging


class HTMLReportGenerator:
    """Generates HTML reports with styling"""
    
    @staticmethod
    def generate(user_query: str, answer_markdown: str, context: list[str]) -> str:
        """
        Generate an HTML report with styling
        
        Args:
            user_query: User's question/request
            answer_markdown: AI-generated answer (markdown format)
            context: List of retrieved context chunks
        
        Returns:
            str: HTML report content
        """
        logging.info("Generating HTML report...")
        
        context_html_list = ''.join([f'<li>{c}</li>' for c in context]) if context else '<li>No sources retrieved</li>'
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oracle AWR Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 40px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 4px solid #3498db;
            padding-bottom: 15px;
            margin-bottom: 30px;
            text-align: center;
            font-size: 2.5em;
        }}
        h2 {{
            color: #2980b9;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-top: 35px;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}
        h3 {{
            color: #34495e;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        .query {{
            background-color: #ecf0f1;
            padding: 20px;
            border-left: 5px solid #3498db;
            margin: 20px 0;
            border-radius: 4px;
            font-size: 1.05em;
        }}
        .answer {{
            background-color: #f9f9f9;
            padding: 25px;
            border-left: 5px solid #27ae60;
            margin: 20px 0;
            line-height: 1.8;
            border-radius: 4px;
        }}
        .context {{
            font-size: 0.95em;
            color: #555;
            margin-top: 30px;
            background-color: #fef9e7;
            padding: 20px;
            border-radius: 5px;
            border-left: 5px solid #f39c12;
        }}
        .context ul {{
            list-style-type: disc;
            padding-left: 25px;
            margin: 10px 0;
        }}
        .context li {{
            margin-bottom: 12px;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            font-size: 0.85em;
            color: #7f8c8d;
            border-top: 1px solid #ecf0f1;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 3px 8px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        .metric {{
            background-color: #e8f4f8;
            padding: 10px;
            margin: 8px 0;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
        strong {{
            color: #2c3e50;
            font-weight: 600;
        }}
        em {{
            color: #555;
            font-style: italic;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            border: 1px solid #2980b9;
        }}
        td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Oracle AWR Analysis Report</h1>
        
        <h2>Query</h2>
        <div class="query">
            <strong>{user_query}</strong>
        </div>
        
        <h2>Analysis Results</h2>
        <div class="answer">
            {markdown.markdown(answer_markdown)}
        </div>
        
        <h2>Retrieved Context Sources</h2>
        <div class="context">
            <ul>
                {context_html_list}
            </ul>
        </div>
        
        <div class="footer">
            <p><strong>Oracle AWR RAG Application</strong></p>
            <p>Powered by Advanced AI & Vector Search</p>
            <p>© 2025 - All Rights Reserved</p>
        </div>
    </div>
</body>
</html>"""
        
        logging.info(f"HTML report generated ({len(html_content)} characters)")
        return html_content