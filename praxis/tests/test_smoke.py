# ---------- Smoke Test Suite: SMB / Regional / Edge-Case Queries ----------
"""
Automated validation that the full NLP pipeline (interpreter → engine →
intelligence) returns sensible results for real-world queries.

Run:
    python -m praxis.tests.test_smoke          # from repo root
    python -m pytest praxis/tests/test_smoke.py -v

Coverage targets:
  • SMB budget-conscious queries
  • Regional / industry-specific queries
  • Negation filtering  ("not X", "no Y")
  • Multi-intent queries
  • Nonsense / typo queries  → should still return something or fail gracefully
  • Zero-budget / free-tier queries
"""

import sys
import os
import unittest

# Ensure praxis package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from praxis.engine import find_tools
from praxis.interpreter import interpret

# ==============================================================
# Helpers
# ==============================================================

def _search(query: str, top_n: int = 5, profile=None):
    """Full pipeline: interpret → find_tools."""
    parsed = interpret(query)
    return find_tools(parsed, top_n=top_n, profile=profile)


def _names(results):
    return [t.name.lower() for t in results]


# ==============================================================
# SMB / Budget Queries
# ==============================================================
class TestSMBQueries(unittest.TestCase):
    """Small-business & budget-first personas."""

    def test_free_writing_tool(self):
        results = _search("free AI writing tool for small business")
        self.assertTrue(len(results) >= 1, "Should return at least 1 result")
        names = _names(results)
        # At least one typical writing tool should appear
        writing_tools = {"chatgpt", "jasper", "copy.ai", "grammarly", "writesonic", "rytr"}
        self.assertTrue(any(n in writing_tools for n in names),
                        f"Expected a writing tool; got {names}")

    def test_no_budget_marketing(self):
        results = _search("marketing tool for small biz no budget")
        self.assertTrue(len(results) >= 1)

    def test_affordable_design(self):
        results = _search("cheap design tool for social media posts")
        self.assertTrue(len(results) >= 1)
        names = _names(results)
        design_tools = {"canva", "adobe firefly", "midjourney", "dall-e",
                        "figma ai", "looka", "designify"}
        self.assertTrue(any(n in design_tools for n in names),
                        f"Expected a design tool; got {names}")


# ==============================================================
# Regional / Industry-Specific
# ==============================================================
class TestRegionalIndustry(unittest.TestCase):

    def test_farm_compliance(self):
        results = _search("best AI for Kansas farm ops compliance")
        self.assertTrue(len(results) >= 1, "Farm compliance query should return results")

    def test_healthcare_hipaa(self):
        results = _search("HIPAA compliant AI for patient scheduling")
        self.assertTrue(len(results) >= 1)

    def test_legal_research(self):
        results = _search("AI for legal document review and research")
        self.assertTrue(len(results) >= 1)

    def test_restaurant_operations(self):
        # No restaurant-specific tools in catalog — should return empty
        # rather than filler tools (absolute score threshold)
        results = _search("AI tool for restaurant inventory and ordering")
        self.assertTrue(len(results) == 0, f"Expected empty (no restaurant tools); got {_names(results)}")


# ==============================================================
# Negation Filtering
# ==============================================================
class TestNegation(unittest.TestCase):

    def test_no_chatgpt(self):
        results = _search("AI writing tool not ChatGPT")
        names = _names(results)
        self.assertNotIn("chatgpt", names,
                         "ChatGPT should be excluded by negation")

    def test_without_expensive(self):
        # "without" should be parsed as negation context
        results = _search("coding assistant without GitHub Copilot")
        names = _names(results)
        self.assertNotIn("github copilot", names)


# ==============================================================
# Multi-Intent / Complex Queries
# ==============================================================
class TestMultiIntent(unittest.TestCase):

    def test_writing_and_design(self):
        results = _search("I need something for writing blog posts and also creating images")
        self.assertTrue(len(results) >= 2,
                        "Multi-intent should return multiple tools")

    def test_code_and_deploy(self):
        results = _search("AI for writing code and deploying to cloud")
        self.assertTrue(len(results) >= 1)


# ==============================================================
# Typo Resilience
# ==============================================================
class TestTypoResilience(unittest.TestCase):

    def test_misspelled_writing(self):
        results = _search("writting asistant for bloging")
        self.assertTrue(len(results) >= 1,
                        "Typo query should still return results")

    def test_misspelled_design(self):
        results = _search("desgin tool for logos")
        self.assertTrue(len(results) >= 1)


# ==============================================================
# Edge Cases / Nonsense
# ==============================================================
class TestEdgeCases(unittest.TestCase):

    def test_empty_query(self):
        results = _search("")
        # Empty should not crash; may return empty or fallback
        self.assertIsInstance(results, list)

    def test_single_word(self):
        results = _search("automation")
        self.assertTrue(len(results) >= 1)

    def test_very_long_query(self):
        long_q = "I need an AI tool " * 50
        results = _search(long_q)
        self.assertIsInstance(results, list)

    def test_special_characters(self):
        results = _search("AI tool for $$$$ <scripts> & 'quotes'")
        self.assertIsInstance(results, list)


# ==============================================================
# Category-Specific Sanity Checks
# ==============================================================
class TestCategorySanity(unittest.TestCase):

    def test_coding_returns_code_tools(self):
        results = _search("best AI coding assistant")
        names = _names(results)
        code_tools = {"github copilot", "cursor", "tabnine", "codeium",
                      "replit ai", "replit", "amazon codewhisperer",
                      "chatgpt", "claude", "langchain", "replit agent"}
        self.assertTrue(any(n in code_tools for n in names),
                        f"Expected a coding tool; got {names}")

    def test_analytics_returns_data_tools(self):
        results = _search("AI for business analytics and data visualization")
        self.assertTrue(len(results) >= 1)

    def test_customer_support_tools(self):
        results = _search("AI chatbot for customer support")
        self.assertTrue(len(results) >= 1)
        names = _names(results)
        support_tools = {"intercom ai", "drift", "zendesk ai", "tidio",
                         "chatgpt", "freshdesk ai"}
        self.assertTrue(any(n in support_tools for n in names),
                        f"Expected a support tool; got {names}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
