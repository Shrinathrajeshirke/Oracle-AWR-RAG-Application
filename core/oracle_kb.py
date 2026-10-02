"""
Oracle Knowledge Base & MOS Note Resolver
Generates clickable links for Oracle documentation and MOS note IDs.
"""

from typing import Dict, List, Optional


class OracleDocResolver:
    """Provides clickable documentation links for common wait events and ORA errors."""

    MOS_BASE_URL = "https://support.oracle.com/epmos/faces/DocContentDisplay?id="
    ORACLE_DOCS_URL = "https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/"

    # Canonical Wait Event & Error Mapping
    DOC_MAPPINGS = {
        "buffer busy waits": {
            "doc_id": "Doc ID 34405.1",
            "url": "https://support.oracle.com/epmos/faces/DocContentDisplay?id=34405.1",
            "title": "Resolving 'buffer busy waits' in Oracle",
            "free_doc": "https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/resolving-contention-waits.html#GUID-E13CD64E-5712-429C-A2E8-E3A248A96205"
        },
        "enq: tx - row lock contention": {
            "doc_id": "Doc ID 62354.1",
            "url": "https://support.oracle.com/epmos/faces/DocContentDisplay?id=62354.1",
            "title": "TX Transaction Locks - Explanation and Troubleshooting",
            "free_doc": "https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/resolving-contention-waits.html"
        },
        "enq: tx - index contention": {
            "doc_id": "Doc ID 1360208.1",
            "url": "https://support.oracle.com/epmos/faces/DocContentDisplay?id=1360208.1",
            "title": "Troubleshooting enq: TX - index contention Wait Events",
            "free_doc": "https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/resolving-contention-waits.html"
        },
        "latch: cache buffers chains": {
            "doc_id": "Doc ID 163424.1",
            "url": "https://support.oracle.com/epmos/faces/DocContentDisplay?id=163424.1",
            "title": "Troubleshooting 'latch: cache buffers chains' Contention",
            "free_doc": "https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/latch-cache-buffers-chains.html"
        },
        "log file sync": {
            "doc_id": "Doc ID 1376914.1",
            "url": "https://support.oracle.com/epmos/faces/DocContentDisplay?id=1376914.1",
            "title": "Troubleshooting 'log file sync' Waits",
            "free_doc": "https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/resolving-contention-waits.html"
        }
    }

    @classmethod
    def get_references_for_text(cls, text: str) -> List[Dict[str, str]]:
        """Scans response text and returns relevant clickable documentation links."""
        refs = []
        lower_text = text.lower()

        for event, details in cls.DOC_MAPPINGS.items():
            if event in lower_text:
                refs.append(details)

        return refs