"""
Data Sanitization & PII Masking Module
Masks sensitive enterprise parameters before storing in the shared solution cache.
"""

import ipaddress
from typing import Dict, List, Tuple


class AwrSanitizer:
    """Masks DB Identifiers, Hostnames, IP Addresses, and Schemas."""

    @staticmethod
    def _is_ip(token: str) -> bool:
        try:
            ipaddress.ip_address(token.strip())
            return True
        except ValueError:
            return False

    @classmethod
    def sanitize(cls, text: str, db_metadata: Dict[str, str] = None) -> str:
        if not text:
            return ""

        sanitized = text

        # 1. Mask explicitly known metadata if provided (DB Name, Host, Instance)
        if db_metadata:
            for key, val in db_metadata.items():
                if val and len(str(val)) > 2:
                    replacement = f"<{key.upper()}_MASKED>"
                    sanitized = sanitized.replace(str(val), replacement)

        # 2. Token-level sanitization for IPs and host-style qualifiers
        lines = sanitized.splitlines()
        clean_lines = []

        for line in lines:
            tokens = line.split(" ")
            new_tokens = []
            for t in tokens:
                clean_t = t.strip("(),;:'\"")
                if cls._is_ip(clean_t):
                    new_tokens.append(t.replace(clean_t, "<IP_MASKED>"))
                elif ".internal" in clean_t or ".corp" in clean_t or ".local" in clean_t:
                    new_tokens.append("<HOST_MASKED>")
                else:
                    new_tokens.append(t)
            clean_lines.append(" ".join(new_tokens))

        return "\n".join(clean_lines)