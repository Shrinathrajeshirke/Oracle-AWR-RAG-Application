"""
Fact Verification
Validates claims in LLM answers against retrieved context
Reduces hallucinations
"""

import re
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from utils.logger import logging


class FactVerifier:
    """
    Verifies facts in LLM responses against retrieved context
    Identifies unsupported or hallucinated claims
    """
    
    def __init__(self):
        """Initialize fact verifier"""
        self.numerical_pattern = re.compile(r'[\d,]+\.?[\d]*')
        self.claim_pattern = re.compile(r'(?:is|are|was|were|has|have|had|be)\s+(.+?)(?:\.|,|;|$)')
        logging.info("FactVerifier initialized")
    
    def extract_claims(self, text: str) -> List[str]:
        """
        Extract key claims from text
        
        Args:
            text: Text to extract claims from
        
        Returns:
            List of extracted claims
        """
        claims = []
        
        # Extract sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Only meaningful sentences
                claims.append(sentence)
        
        return claims
    
    def verify_claim(self, claim: str, context: List[str]) -> Dict:
        """
        Verify a single claim against context
        
        Args:
            claim: Claim to verify
            context: List of context documents
        
        Returns:
            Verification result
        """
        context_text = " ".join(context).lower()
        claim_lower = claim.lower()
        
        # Numerical claims - check if numbers exist
        numbers = self.numerical_pattern.findall(claim)
        numerical_support = False
        
        for number in numbers:
            if number in context_text:
                numerical_support = True
                break
        
        # Keyword matching
        keywords = [w for w in claim_lower.split() if len(w) > 4]
        keyword_matches = sum(1 for kw in keywords if kw in context_text)
        
        # Calculate confidence
        if numerical_support:
            confidence = 0.9
        elif keyword_matches >= len(keywords) * 0.7:  # 70% keyword match
            confidence = 0.7
        elif keyword_matches >= len(keywords) * 0.4:  # 40% keyword match
            confidence = 0.4
        else:
            confidence = 0.1
        
        return {
            "claim": claim,
            "supported": confidence > 0.6,
            "confidence": confidence,
            "keywords_matched": keyword_matches,
            "total_keywords": len(keywords),
            "has_numbers": len(numbers) > 0,
            "numbers_verified": numerical_support
        }
    
    def verify_response(self, answer: str, context_docs: List[Document]) -> Dict:
        """
        Verify all claims in an answer against context
        
        Args:
            answer: LLM-generated answer
            context_docs: Retrieved context documents
        
        Returns:
            Verification report
        """
        logging.info(f"Verifying answer with {len(context_docs)} context documents")
        
        # Extract context text
        context_text = [doc.page_content for doc in context_docs]
        
        # Extract claims
        claims = self.extract_claims(answer)
        
        # Verify each claim
        verifications = []
        for claim in claims:
            if len(claim) > 10:  # Only verify meaningful claims
                verification = self.verify_claim(claim, context_text)
                verifications.append(verification)
        
        # Calculate statistics
        if verifications:
            supported_count = sum(1 for v in verifications if v["supported"])
            avg_confidence = sum(v["confidence"] for v in verifications) / len(verifications)
        else:
            supported_count = 0
            avg_confidence = 0
        
        report = {
            "total_claims": len(verifications),
            "supported_claims": supported_count,
            "unsupported_claims": len(verifications) - supported_count,
            "support_ratio": supported_count / len(verifications) if verifications else 0,
            "average_confidence": avg_confidence,
            "details": verifications
        }
        
        logging.info(
            f"Verification complete: {supported_count}/{len(verifications)} claims supported "
            f"(confidence: {avg_confidence:.2%})"
        )
        
        return report
    
    def flag_unsupported_claims(self, answer: str, context_docs: List[Document]) -> List[str]:
        """
        Identify unsupported claims in answer
        
        Args:
            answer: LLM answer
            context_docs: Context documents
        
        Returns:
            List of unsupported claims
        """
        report = self.verify_response(answer, context_docs)
        
        unsupported = [
            v["claim"] for v in report["details"]
            if not v["supported"]
        ]
        
        logging.warning(f"Found {len(unsupported)} unsupported claims")
        
        return unsupported
    
    def get_verification_badge(self, report: Dict) -> str:
        """
        Get quality badge based on verification
        
        Args:
            report: Verification report
        
        Returns:
            Badge string with emoji and percentage
        """
        ratio = report["support_ratio"]
        
        if ratio >= 0.9:
            return "90%+ Verified"
        elif ratio >= 0.75:
            return "75%+ Verified"
        elif ratio >= 0.6:
            return "60%+ Verified"
        else:
            return "<60% Verified"
    
    def create_verification_summary(self, report: Dict) -> str:
        """
        Create human-readable verification summary
        
        Args:
            report: Verification report
        
        Returns:
            Formatted summary string
        """
        summary = f"""
FACT VERIFICATION REPORT
========================
Total Claims: {report['total_claims']}
Supported: {report['supported_claims']}
Unsupported: {report['unsupported_claims']}
Support Ratio: {report['support_ratio']:.1%}
Average Confidence: {report['average_confidence']:.1%}

Status: {self.get_verification_badge(report)}
"""
        return summary