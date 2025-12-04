#!/usr/bin/env python3
"""
Evidence-Aware Legal Document Drafter

Zero-hallucination document generation with mandatory evidence citation.
Every factual claim must be backed by specific evidence references.
"""

import re
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EvidenceSource:
    """Evidence source with metadata"""
    source_id: str
    description: str
    file_path: Optional[Path] = None
    page_numbers: Optional[List[int]] = None
    exhibit_number: Optional[str] = None
    
@dataclass
class Citation:
    """Citation reference in document"""
    text: str
    evidence_ids: List[str]
    location: int  # Character position in document
    
class EvidenceRegistry:
    """Central registry of all evidence available for citation"""
    
    def __init__(self):
        self.evidence: Dict[str, EvidenceSource] = {}
        
    def register(self, evidence: EvidenceSource) -> None:
        """Register new evidence source"""
        self.evidence[evidence.source_id] = evidence
        
    def get(self, source_id: str) -> Optional[EvidenceSource]:
        """Retrieve evidence by ID"""
        return self.evidence.get(source_id)
        
    def validate_citations(self, citation_ids: List[str]) -> tuple[bool, List[str]]:
        """Validate that all cited evidence exists
        
        Returns:
            (is_valid, missing_ids)
        """
        missing = [cid for cid in citation_ids if cid not in self.evidence]
        return len(missing) == 0, missing

class EvidenceAwareDrafter:
    """Document drafter that enforces evidence-based assertions"""
    
    def __init__(self, evidence_registry: EvidenceRegistry):
        self.registry = evidence_registry
        self.citations: List[Citation] = []
        
    def draft_paragraph(self, 
                       content: str, 
                       evidence_ids: List[str],
                       require_citation: bool = True) -> str:
        """Draft paragraph with mandatory evidence citations
        
        Args:
            content: Paragraph text
            evidence_ids: Evidence sources supporting this paragraph
            require_citation: Whether evidence is required
            
        Returns:
            Formatted paragraph with citations
            
        Raises:
            ValueError: If evidence is required but not provided or invalid
        """
        if require_citation:
            if not evidence_ids:
                raise ValueError(
                    f"Evidence required but not provided for: {content[:50]}..."
                )
            
            is_valid, missing = self.registry.validate_citations(evidence_ids)
            if not is_valid:
                raise ValueError(
                    f"Invalid evidence IDs: {missing}. "
                    f"Content: {content[:50]}..."
                )
        
        # Format citations
        citation_text = self._format_citations(evidence_ids)
        
        # Record citation
        self.citations.append(Citation(
            text=content,
            evidence_ids=evidence_ids,
            location=len(content)
        ))
        
        return f"{content} {citation_text}"
    
    def _format_citations(self, evidence_ids: List[str]) -> str:
        """Format evidence citations for document
        
        Returns LaTeX citation format: (Ex. A, pp. 1-3; Ex. B, p. 5)
        """
        if not evidence_ids:
            return ""
        
        citations = []
        for eid in evidence_ids:
            evidence = self.registry.get(eid)
            if evidence:
                cite_parts = []
                if evidence.exhibit_number:
                    cite_parts.append(f"Ex. {evidence.exhibit_number}")
                if evidence.page_numbers:
                    if len(evidence.page_numbers) == 1:
                        cite_parts.append(f"p. {evidence.page_numbers[0]}")
                    else:
                        cite_parts.append(
                            f"pp. {evidence.page_numbers[0]}-{evidence.page_numbers[-1]}"
                        )
                citations.append(", ".join(cite_parts))
        
        return f"({'; '.join(citations)})"
    
    def validate_document(self, document: str) -> tuple[bool, List[str]]:
        """Validate that document has no uncited factual claims
        
        Returns:
            (is_valid, list of potential uncited claims)
        """
        # Patterns that typically indicate factual claims requiring evidence
        claim_patterns = [
            r'Respondent \w+ (?:did|failed to|refused to)',
            r'On \w+\s+\d+,\s+\d{4}',  # Dates
            r'\$[\d,]+',  # Money amounts
            r'\d+ (?:times|instances|occasions)',  # Quantified events
        ]
        
        uncited_claims = []
        for pattern in claim_patterns:
            matches = re.finditer(pattern, document)
            for match in matches:
                # Check if this match is near a citation
                pos = match.start()
                has_nearby_citation = any(
                    abs(c.location - pos) < 200  # Within 200 chars
                    for c in self.citations
                )
                if not has_nearby_citation:
                    uncited_claims.append(match.group())
        
        return len(uncited_claims) == 0, uncited_claims
    
    def generate_exhibit_list(self) -> str:
        """Generate formatted exhibit list for document"""
        exhibits = {}
        for citation in self.citations:
            for eid in citation.evidence_ids:
                evidence = self.registry.get(eid)
                if evidence and evidence.exhibit_number:
                    exhibits[evidence.exhibit_number] = evidence
        
        result = ["\\section*{Exhibits}\n\\begin{enumerate}"]
        for ex_num in sorted(exhibits.keys()):
            evidence = exhibits[ex_num]
            result.append(f"  \\item Exhibit {ex_num}: {evidence.description}")
        result.append("\\end{enumerate}")
        
        return "\n".join(result)

# Example usage
if __name__ == "__main__":
    # Initialize evidence registry
    registry = EvidenceRegistry()
    
    # Register evidence
    registry.register(EvidenceSource(
        source_id="email_20231015",
        description="Email from Respondent dated October 15, 2023",
        file_path=Path("evidence/emails/2023-10-15.pdf"),
        page_numbers=[1, 2],
        exhibit_number="A"
    ))
    
    registry.register(EvidenceSource(
        source_id="text_20231020",
        description="Text message thread from October 20, 2023",
        file_path=Path("evidence/texts/2023-10-20.pdf"),
        page_numbers=[1],
        exhibit_number="B"
    ))
    
    # Create drafter
    drafter = EvidenceAwareDrafter(registry)
    
    # Draft paragraph with evidence
    para = drafter.draft_paragraph(
        "On October 15, 2023, Respondent sent an email threatening to "
        "withhold custody unless additional payments were made.",
        evidence_ids=["email_20231015"]
    )
    
    print("Drafted paragraph:")
    print(para)
    print("\n" + "="*60 + "\n")
    
    # This would raise an error - no evidence provided
    try:
        drafter.draft_paragraph(
            "Respondent has a history of similar behavior.",
            evidence_ids=[]
        )
    except ValueError as e:
        print(f"Caught expected error: {e}")
        print("\n" + "="*60 + "\n")
    
    # Generate exhibit list
    print(drafter.generate_exhibit_list())
