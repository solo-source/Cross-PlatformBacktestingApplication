# New module: generates HTML via Jinja2 and exports PDF via WeasyPrint

import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

class ReportGenerator:
    def __init__(self, template_dir: str = 'templates'):
        # Set up Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=True
        )

    def generate_html(self, output_path: str, context: dict):
        """
        Renders an HTML report using the 'report.html' Jinja2 template and provided context.
        """
        template = self.env.get_template('report.html')
        html_content = template.render(**context)

        # Write HTML file
        html_file = output_path.replace('.pdf', '.html')
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        return html_file, html_content

    def html_to_pdf(self, html_content: str, pdf_path: str):
        """
        Converts HTML content to PDF using WeasyPrint.
        """
        HTML(string=html_content).write_pdf(pdf_path)
        return pdf_path

    def generate_report(self, context: dict, output_dir: str = 'reports', filename: str = 'backtest_report.pdf'):
        """
        Orchestrates HTML rendering and PDF conversion, returns output file paths.
        -- context should include keys: title, dates, equity_vals, drawdown_vals, metrics (dict), trades_table (list of dicts)
        """
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, filename)
        html_file, html_content = self.generate_html(pdf_path, context)
        self.html_to_pdf(html_content, pdf_path)
        return html_file, pdf_path
