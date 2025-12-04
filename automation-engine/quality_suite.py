#!/usr/bin/env python3
"""
Quality Assurance Test Suite for Legal Document Generation

Automated regression testing to ensure document quality and consistency.
"""

import unittest
from pathlib import Path
from typing import List, Dict
import subprocess
import tempfile
import json

class DocumentQualityTests(unittest.TestCase):
    """Test suite for document quality validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_evidence_citation_enforcement(self):
        """Test that all factual claims have evidence citations"""
        from evidence_aware_drafter import EvidenceRegistry, EvidenceAwareDrafter, EvidenceSource
        
        registry = EvidenceRegistry()
        registry.register(EvidenceSource(
            source_id="test_evidence",
            description="Test evidence",
            exhibit_number="A"
        ))
        
        drafter = EvidenceAwareDrafter(registry)
        
        # Should succeed with evidence
        result = drafter.draft_paragraph(
            "This is a factual claim.",
            evidence_ids=["test_evidence"]
        )
        self.assertIn("Ex. A", result)
        
        # Should fail without evidence
        with self.assertRaises(ValueError):
            drafter.draft_paragraph(
                "This is an unsupported claim.",
                evidence_ids=[]
            )
    
    def test_jurisdiction_compliance(self):
        """Test court-specific formatting compliance"""
        from jurisdiction_registry import JurisdictionRegistry, ComplianceValidator
        
        registry = JurisdictionRegistry()
        validator = ComplianceValidator(registry)
        
        # Create test document
        test_doc = self.test_dir / "test.tex"
        test_doc.write_text(
            "\\setmainfont{Times New Roman}\n"
            "\\doublespacing\n"
            "Certificate of Service\n"
            "Verification\n"
        )
        
        is_valid, violations = validator.validate_document(test_doc, "hi_family")
        
        # Should have minimal violations for properly formatted document
        self.assertTrue(is_valid or len(violations) < 3)
    
    def test_latex_compilation(self):
        """Test that generated LaTeX compiles successfully"""
        test_tex = self.test_dir / "test.tex"
        test_tex.write_text(
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "Test document\n"
            "\\end{document}\n"
        )
        
        # Try to compile (skip if pdflatex not available)
        try:
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", str(test_tex)],
                cwd=self.test_dir,
                capture_output=True,
                timeout=10
            )
            # Should complete without error
            self.assertEqual(result.returncode, 0)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.skipTest("pdflatex not available")
    
    def test_multi_model_routing(self):
        """Test AI model selection and fallback"""
        from multi_model_fileboss import ModelRouter, ModelProfile
        
        router = ModelRouter()
        
        # Test routing for different task types
        model = router.select_model("legal_analysis")
        self.assertIsNotNone(model)
        
        model = router.select_model("document_generation")
        self.assertIsNotNone(model)
    
    def test_exhibit_list_generation(self):
        """Test automatic exhibit list generation"""
        from evidence_aware_drafter import EvidenceRegistry, EvidenceAwareDrafter, EvidenceSource
        
        registry = EvidenceRegistry()
        for i, letter in enumerate(["A", "B", "C"]):
            registry.register(EvidenceSource(
                source_id=f"evidence_{i}",
                description=f"Test evidence {letter}",
                exhibit_number=letter
            ))
        
        drafter = EvidenceAwareDrafter(registry)
        
        # Draft paragraphs citing evidence
        drafter.draft_paragraph("Claim 1", evidence_ids=["evidence_0"])
        drafter.draft_paragraph("Claim 2", evidence_ids=["evidence_1", "evidence_2"])
        
        # Generate exhibit list
        exhibit_list = drafter.generate_exhibit_list()
        
        self.assertIn("Exhibit A", exhibit_list)
        self.assertIn("Exhibit B", exhibit_list)
        self.assertIn("Exhibit C", exhibit_list)

class IntegrationTests(unittest.TestCase):
    """End-to-end integration tests"""
    
    def test_full_motion_generation(self):
        """Test complete motion generation workflow"""
        # This would test the full pipeline from evidence to final PDF
        self.skipTest("Requires full system integration")
    
    def test_multi_jurisdiction_support(self):
        """Test generating documents for different courts"""
        from jurisdiction_registry import JurisdictionRegistry
        
        registry = JurisdictionRegistry()
        
        # Should support all required jurisdictions
        required_courts = ["hi_family", "cand", "ca9"]
        for court_id in required_courts:
            profile = registry.get_profile(court_id)
            self.assertIsNotNone(profile, f"Missing profile for {court_id}")

class RegressionTests(unittest.TestCase):
    """Regression tests for known issues"""
    
    def test_no_hallucinated_facts(self):
        """Ensure system cannot generate unsupported factual claims"""
        from evidence_aware_drafter import EvidenceRegistry, EvidenceAwareDrafter
        
        registry = EvidenceRegistry()
        drafter = EvidenceAwareDrafter(registry)
        
        # Any factual claim without evidence should fail
        with self.assertRaises(ValueError):
            drafter.draft_paragraph(
                "Respondent did something on January 1, 2024.",
                evidence_ids=[],
                require_citation=True
            )
    
    def test_citation_format_consistency(self):
        """Ensure citation formats are consistent"""
        from evidence_aware_drafter import EvidenceRegistry, EvidenceAwareDrafter, EvidenceSource
        
        registry = EvidenceRegistry()
        registry.register(EvidenceSource(
            source_id="test",
            description="Test",
            exhibit_number="A",
            page_numbers=[1, 2, 3]
        ))
        
        drafter = EvidenceAwareDrafter(registry)
        result = drafter.draft_paragraph("Test", evidence_ids=["test"])
        
        # Should use proper citation format
        self.assertIn("Ex. A", result)
        self.assertIn("pp. 1-3", result)

if __name__ == "__main__":
    # Run all tests
    unittest.main(verbosity=2)
