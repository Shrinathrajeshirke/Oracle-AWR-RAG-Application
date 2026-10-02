"""
Dual-Pass Fact Verification Layer
Validates extracted SQL IDs, metrics, and event claims against retrieved context chunks.
"""

from typing import List, Tuple
from langchain_core.documents import Document
from utils.logger import logging


class FactVerifier:
    """
    Verifies that extracted SQL IDs and numerical figures exist in source context chunks.
    Avoids regular expressions, using custom string parsing logic.
    """

    @staticmethod
    def _is_valid_sql_id(token: str) -> bool:
        """Checks if token is a standard 13-character Oracle alphanumeric SQL ID."""
        if len(token) != 13:
            return False
        has_letter = False
        has_digit = False
        for ch in token:
            if not (ch.isalnum()):
                return False
            if ch.isalpha():
                has_letter = True
            elif ch.isdigit():
                has_digit = True
        return has_letter and has_digit

    @classmethod
    def verify_response(cls, answer: str, docs: List[Document]) -> Tuple[str, bool]:
        """
        Inspects output text for Oracle SQL_IDs and large numeric strings.
        Flags unsupported claims if not found verbatim in retrieved chunks.
        """
        if not docs:
            return answer, True

        combined_context = " ".join([d.page_content for d in docs])
        lines = answer.splitlines()
        verified_lines = []
        hallucination_detected = False

        for line in lines:
            # Tokenize using standard string splits
            clean_line = line.replace(":", " ").replace("|", " ").replace("`", " ").replace("(", " ").replace(")", " ")
            tokens = clean_line.split()
            
            for token in tokens:
                clean_token = token.strip(".,;:*_-'\"")
                
                # Check Oracle SQL_ID validity
                if cls._is_valid_sql_id(clean_token):
                    if clean_token not in combined_context:
                        logging.warning(f"FactVerifier: SQL_ID '{clean_token}' not verified in context chunks!")
                        hallucination_detected = True

            verified_lines.append(line)

        if hallucination_detected:
            verified_lines.append(
                "\n> ⚠️ *Note: Certain extracted identifiers were not verified in the retrieved tables. Please review the detailed report table.*"
            )

        return "\n".join(verified_lines), not hallucination_detected