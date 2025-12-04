#!/usr/bin/env python3
"""
Jurisdiction Registry and Court Compliance Validator

Validates legal documents against court-specific rules and formatting requirements.
Supports multiple jurisdictions with plug-in architecture.
"""

import yaml
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

class CourtLevel(Enum):
    """Court hierarchy levels"""
    STATE_FAMILY = "state_family"
    STATE_DISTRICT = "state_district"
    STATE_SUPREME = "state_supreme"
    FEDERAL_DISTRICT = "federal_district"
    FEDERAL_CIRCUIT = "federal_circuit"
    FEDERAL_SUPREME = "federal_supreme"

@dataclass
class FormattingRules:
    """Court-specific formatting requirements"""
    font_family: str = "Times New Roman"
    font_size: int = 12
    line_spacing: float = 2.0
    margin_top: float = 1.0  # inches
    margin_bottom: float = 1.0
    margin_left: float = 1.0
    margin_right: float = 1.0
    page_number_location: str = "bottom center"
    
@dataclass
class CitationRules:
    """Citation format requirements"""
    case_citation_format: str = "Bluebook"
    statute_citation_format: str = "Bluebook"
    pin_cite_required: bool = True
    short_form_rules: Dict[str, str] = field(default_factory=dict)

@dataclass
class FilingRules:
    """Filing-specific requirements"""
    max_pages: Optional[int] = None
    certificate_of_service_required: bool = True
    verification_required: bool = False
    exhibits_must_be_labeled: bool = True
    table_of_contents_required_pages: Optional[int] = 25
    table_of_authorities_required: bool = False

@dataclass
class CourtProfile:
    """Complete court jurisdiction profile"""
    court_id: str
    court_name: str
    court_level: CourtLevel
    jurisdiction: str
    formatting: FormattingRules
    citations: CitationRules
    filing: FilingRules
    special_rules: Dict[str, any] = field(default_factory=dict)
    
class JurisdictionRegistry:
    """Registry of court profiles and compliance validators"""
    
    def __init__(self):
        self.profiles: Dict[str, CourtProfile] = {}
        self._load_default_profiles()
        
    def _load_default_profiles(self):
        """Load default court profiles"""
        # Hawaii Family Court
        self.register_profile(CourtProfile(
            court_id="hi_family",
            court_name="Hawaii Family Court",
            court_level=CourtLevel.STATE_FAMILY,
            jurisdiction="Hawaii",
            formatting=FormattingRules(
                font_family="Times New Roman",
                font_size=12,
                line_spacing=2.0,
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0
            ),
            citations=CitationRules(
                case_citation_format="Bluebook",
                statute_citation_format="Hawaii Revised Statutes",
                pin_cite_required=True
            ),
            filing=FilingRules(
                certificate_of_service_required=True,
                verification_required=True,
                exhibits_must_be_labeled=True
            ),
            special_rules={
                "caption_format": "hawaii_standard",
                "signature_block_required": True,
                "pro_se_notice_required": True
            }
        ))
        
        # Northern District of California (CAND)
        self.register_profile(CourtProfile(
            court_id="cand",
            court_name="United States District Court for the Northern District of California",
            court_level=CourtLevel.FEDERAL_DISTRICT,
            jurisdiction="California (Northern District)",
            formatting=FormattingRules(
                font_family="Times New Roman",
                font_size=12,
                line_spacing=2.0,
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0
            ),
            citations=CitationRules(
                case_citation_format="Bluebook",
                statute_citation_format="U.S.C.",
                pin_cite_required=True
            ),
            filing=FilingRules(
                max_pages=25,  # Without leave of court
                certificate_of_service_required=True,
                verification_required=False,
                exhibits_must_be_labeled=True,
                table_of_contents_required_pages=25,
                table_of_authorities_required=True
            ),
            special_rules={
                "ecf_filing_required": True,
                "local_rules_apply": "CAND Local Rules",
                "civil_lr_compliance": True
            }
        ))
        
        # Ninth Circuit Court of Appeals
        self.register_profile(CourtProfile(
            court_id="ca9",
            court_name="United States Court of Appeals for the Ninth Circuit",
            court_level=CourtLevel.FEDERAL_CIRCUIT,
            jurisdiction="Ninth Circuit",
            formatting=FormattingRules(
                font_family="Century Schoolbook",
                font_size=14,
                line_spacing=2.0,
                margin_top=1.0,
                margin_bottom=1.0,
                margin_left=1.0,
                margin_right=1.0
            ),
            citations=CitationRules(
                case_citation_format="Bluebook",
                statute_citation_format="U.S.C.",
                pin_cite_required=True
            ),
            filing=FilingRules(
                max_pages=14000,  # Word count, not pages
                certificate_of_service_required=True,
                verification_required=False,
                exhibits_must_be_labeled=True,
                table_of_contents_required_pages=1,  # Always required
                table_of_authorities_required=True
            ),
            special_rules={
                "word_count_limit": 14000,
                "certificate_of_compliance_required": True,
                "separate_volume_for_excerpts": True
            }
        ))
        
    def register_profile(self, profile: CourtProfile) -> None:
        """Register a court profile"""
        self.profiles[profile.court_id] = profile
        
    def get_profile(self, court_id: str) -> Optional[CourtProfile]:
        """Retrieve court profile by ID"""
        return self.profiles.get(court_id)
    
    def list_courts(self) -> List[str]:
        """List all registered court IDs"""
        return list(self.profiles.keys())

class ComplianceValidator:
    """Validates documents against court requirements"""
    
    def __init__(self, registry: JurisdictionRegistry):
        self.registry = registry
        
    def validate_document(self, 
                         document_path: Path,
                         court_id: str) -> tuple[bool, List[str]]:
        """Validate document against court requirements
        
        Returns:
            (is_compliant, list_of_violations)
        """
        profile = self.registry.get_profile(court_id)
        if not profile:
            return False, [f"Unknown court ID: {court_id}"]
        
        violations = []
        
        # Read document (simplified - would use proper LaTeX/PDF parser)
        content = document_path.read_text() if document_path.exists() else ""
        
        # Check formatting requirements
        violations.extend(self._check_formatting(content, profile.formatting))
        
        # Check filing requirements
        violations.extend(self._check_filing_rules(content, profile.filing))
        
        # Check special rules
        violations.extend(self._check_special_rules(content, profile.special_rules))
        
        return len(violations) == 0, violations
    
    def _check_formatting(self, content: str, rules: FormattingRules) -> List[str]:
        """Check formatting compliance"""
        violations = []
        
        # Check for font specification in LaTeX
        if rules.font_family and f"\\setmainfont{{{rules.font_family}}}" not in content:
            violations.append(
                f"Required font '{rules.font_family}' not specified"
            )
        
        # Check line spacing
        if rules.line_spacing and f"\\{rules.line_spacing}" not in content:
            violations.append(
                f"Required line spacing {rules.line_spacing} not set"
            )
        
        return violations
    
    def _check_filing_rules(self, content: str, rules: FilingRules) -> List[str]:
        """Check filing rule compliance"""
        violations = []
        
        if rules.certificate_of_service_required:
            if "certificate of service" not in content.lower():
                violations.append("Certificate of Service required but not found")
        
        if rules.verification_required:
            if "verification" not in content.lower():
                violations.append("Verification required but not found")
        
        if rules.table_of_authorities_required:
            if "table of authorities" not in content.lower():
                violations.append("Table of Authorities required but not found")
        
        return violations
    
    def _check_special_rules(self, content: str, rules: Dict) -> List[str]:
        """Check special court-specific rules"""
        violations = []
        
        if rules.get("pro_se_notice_required"):
            if "pro se" not in content.lower():
                violations.append(
                    "Pro se notice may be required for self-represented litigants"
                )
        
        if rules.get("certificate_of_compliance_required"):
            if "certificate of compliance" not in content.lower():
                violations.append("Certificate of Compliance required but not found")
        
        return violations

# Example usage
if __name__ == "__main__":
    registry = JurisdictionRegistry()
    
    print("Registered Courts:")
    for court_id in registry.list_courts():
        profile = registry.get_profile(court_id)
        print(f"- {court_id}: {profile.court_name}")
    
    print("\n" + "="*60 + "\n")
    
    # Get specific court profile
    hi_profile = registry.get_profile("hi_family")
    print(f"Hawaii Family Court Profile:")
    print(f"  Font: {hi_profile.formatting.font_family}")
    print(f"  Font Size: {hi_profile.formatting.font_size}pt")
    print(f"  Line Spacing: {hi_profile.formatting.line_spacing}")
    print(f"  Verification Required: {hi_profile.filing.verification_required}")
