"""
Document Processor with Table-Structure Preservation, Section Header Inheritance, and Header Pinning
"""

import os
import re
from typing import List
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.logger import logging


class DocumentProcessor:
    def __init__(self, chunk_size: int = 2500, chunk_overlap: int = 400):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n### ", "\n\n## ", "\n\n", "\n", " ", ""]
        )
        logging.info("DocumentProcessor initialized with 2500/400 Table-Aware Chunking")

    def _html_table_to_markdown(self, table_soup) -> str:
        """Converts an HTML <table> into Markdown, preserving parent section headings."""
        # Find preceding heading if available
        heading = ""
        prev = table_soup.find_previous(["h2", "h3", "h4", "a"])
        if prev:
            h_text = prev.get_text(strip=True)
            if h_text and len(h_text) > 3 and not h_text.lower().startswith("back to"):
                heading = f"\n### Table Section: {h_text}\n"

        rows = table_soup.find_all("tr")
        if not rows:
            return ""

        grid = []
        for row in rows:
            cells = row.find_all(["th", "td"])
            cell_texts = [
                re.sub(r"\s+", " ", cell.get_text(strip=True)).replace("|", "/")
                for cell in cells
            ]
            if any(cell_texts):
                grid.append(cell_texts)

        if not grid:
            return ""

        max_cols = max(len(r) for r in grid)
        for r in grid:
            while len(r) < max_cols:
                r.append("")

        header = grid[0]
        separator = ["---"] * max_cols
        data_rows = grid[1:] if len(grid) > 1 else []

        md_lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |"
        ]
        for r in data_rows:
            md_lines.append("| " + " | ".join(r) + " |")

        return heading + "\n" + "\n".join(md_lines) + "\n"

    def _extract_header_summary(self, soup: BeautifulSoup) -> str:
        """Extracts the top-level AWR report metadata header."""
        header_lines = []
        for table in soup.find_all("table")[:4]:
            text = table.get_text(" ", strip=True)
            if any(k in text for k in ["DB Name", "Database", "Instance", "Elapsed", "CPUs", "Cores", "Host"]):
                header_lines.append(self._html_table_to_markdown(table))

        if not header_lines:
            header_lines.append(soup.get_text()[:1500])

        summary = (
            "### AWR REPORT SYSTEM & DATABASE HEADER METADATA (PINNED)\n"
            + "\n".join(header_lines)
        )
        return summary

    def load_and_split_document(self, file_path: str, doc_id: str, filename: str) -> List[Document]:
        logging.info(f"Loading and processing document with table structure: {filename}")

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Pinned Header Chunk (Chunk 0)
        header_text = self._extract_header_summary(soup)
        header_doc = Document(
            page_content=header_text,
            metadata={
                "document_id": doc_id,
                "filename": filename,
                "chunk_id": 0,
                "is_header": True,
                "section": "awr_header_metadata"
            }
        )

        # 2. In-place conversion of HTML tables to Markdown with section tagging
        for table in soup.find_all("table"):
            md_table = self._html_table_to_markdown(table)
            table.replace_with(soup.new_string(f"\n\n{md_table}\n\n"))

        clean_text = soup.get_text()
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text)

        # 3. Split remaining content with expanded boundaries
        text_chunks = self.text_splitter.split_text(clean_text)
        documents = [header_doc]

        for idx, chunk in enumerate(text_chunks, start=1):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "document_id": doc_id,
                        "filename": filename,
                        "chunk_id": idx,
                        "is_header": False,
                        "section": "report_body"
                    }
                )
            )

        logging.info(f"Processed {filename}: created 1 pinned header chunk + {len(documents)-1} body chunks")
        return documents