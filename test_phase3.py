from reporting.report_builder import ReportBuilder

builder = ReportBuilder()

# Generate text report
text_content = builder.generate_text_report(
    user_query="What are the top wait events?",
    answer="The top wait events are...",
    contexts=["context_1", "context_2"]
)
print(text_content)

# Generate HTML report
html_content = builder.generate_html_report(
    user_query="...",
    answer="...",
    contexts=[...]
)

# Generate PDF report
pdf_path = builder.generate_pdf_report(
    user_query="...",
    answer="...",
    contexts=[...]
)