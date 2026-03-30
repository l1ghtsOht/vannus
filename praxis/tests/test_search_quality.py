"""
Search quality regression tests.

These tests assert that specific queries return expected tools in the
top results. They protect scoring fixes from silent regression.

Each test encodes a real user query (from Railway production logs or
manual testing) and the tools that MUST appear in the results.
"""
import unittest

try:
    from ..engine import find_tools
    from ..interpreter import interpret
except ImportError:
    from praxis.engine import find_tools
    from praxis.interpreter import interpret


def _search(query, top_n=5):
    """Simulate the API path: interpret → find_tools."""
    struct = interpret(query)
    return find_tools(struct, top_n=top_n)


def _names(results):
    return [t.name.lower() for t in results]


class TestSearchQuality(unittest.TestCase):
    """Core search quality — these should never regress."""

    def test_blog_writing_returns_writing_tools(self):
        results = _search("I need tools to write blog posts, emails, and marketing copy")
        names = _names(results)
        writing_tools = {"jasper", "copy.ai", "writesonic", "grammarly", "chatgpt"}
        self.assertTrue(
            any(n in writing_tools for n in names),
            f"Expected a writing tool; got {names}",
        )

    def test_podcast_returns_audio_tools(self):
        results = _search("I need AI tools for podcast recording, editing, and transcription")
        names = _names(results)
        audio_tools = {"descript", "otter.ai", "elevenlabs", "murf ai"}
        self.assertTrue(
            any(n in audio_tools for n in names),
            f"Expected an audio tool; got {names}",
        )

    def test_helpdesk_returns_support_tools(self):
        results = _search("I need customer support tools for chat, tickets, and helpdesk")
        names = _names(results)
        support_tools = {"zendesk", "intercom", "freshdesk", "tidio", "drift"}
        matches = [n for n in names if n in support_tools]
        self.assertGreaterEqual(
            len(matches), 3,
            f"Expected at least 3 support tools; got {names}",
        )

    def test_coding_returns_dev_tools(self):
        results = _search("I need AI coding assistants for writing and debugging code")
        names = _names(results)
        dev_tools = {"chatgpt", "claude", "cursor", "github copilot", "replit", "replit agent"}
        self.assertTrue(
            any(n in dev_tools for n in names),
            f"Expected a coding tool; got {names}",
        )

    def test_crm_returns_crm_tools(self):
        results = _search("best crm for small business")
        names = _names(results)
        crm_tools = {"salesforce", "hubspot", "apollo.io", "pipedrive"}
        matches = [n for n in names if n in crm_tools]
        self.assertGreaterEqual(
            len(matches), 2,
            f"Expected at least 2 CRM tools; got {names}",
        )

    def test_design_returns_design_tools(self):
        results = _search("free design tool")
        names = _names(results)
        design_tools = {"figma ai", "canva ai", "dall-e", "stability ai", "miro", "midjourney"}
        matches = [n for n in names if n in design_tools]
        self.assertGreaterEqual(
            len(matches), 2,
            f"Expected at least 2 design tools; got {names}",
        )

    def test_lead_gen_returns_sales_tools(self):
        results = _search("lead generation")
        names = _names(results)
        sales_tools = {"apollo.io", "hubspot", "salesforce", "outreach", "drift"}
        self.assertTrue(
            any(n in sales_tools for n in names),
            f"Expected a sales/lead-gen tool; got {names}",
        )

    def test_social_media_returns_social_tools(self):
        results = _search("social media scheduling")
        names = _names(results)
        social_tools = {"buffer", "hootsuite", "sprout social", "later"}
        self.assertTrue(
            any(n in social_tools for n in names),
            f"Expected a social media tool; got {names}",
        )


class TestNoFillerTools(unittest.TestCase):
    """Filler tools should not appear in unrelated searches."""

    def _assert_no_filler(self, query):
        results = _search(query)
        names = _names(results)
        filler = {"hugging face", "langchain", "supabase", "stripe", "vanta"}
        found_filler = [n for n in names if n in filler]
        self.assertEqual(
            found_filler, [],
            f"Filler tools in '{query}': {found_filler} (full results: {names})",
        )

    def test_no_filler_in_helpdesk(self):
        self._assert_no_filler("helpdesk software")

    def test_no_filler_in_podcast(self):
        self._assert_no_filler("I need AI tools for podcast recording")

    def test_no_filler_in_support(self):
        self._assert_no_filler("customer support tools")


class TestBudgetFilter(unittest.TestCase):
    """Budget hard-filter must actually eliminate paid tools."""

    def test_free_budget_returns_only_free_tools(self):
        # Simulate: save profile with free budget, then search
        try:
            from ..profile import UserProfile
        except ImportError:
            from praxis.profile import UserProfile

        try:
            from ..stack import compose_stack
        except ImportError:
            from praxis.stack import compose_stack

        struct = interpret("I need writing tools")
        profile = UserProfile(
            profile_id="test_free_budget",
            budget="free",
            skill_level="beginner",
        )
        result = compose_stack(struct, profile=profile, stack_size=3)
        for entry in result.get("stack", []):
            tool = entry["tool"]
            pricing = tool.pricing or {}
            self.assertTrue(
                pricing.get("free_tier", False),
                f"{tool.name} has no free tier but was returned for free-only budget",
            )

    def test_funnel_data_present(self):
        struct = interpret("I need marketing tools")
        try:
            from ..stack import compose_stack
        except ImportError:
            from praxis.stack import compose_stack
        result = compose_stack(struct, stack_size=3)
        self.assertIn("funnel", result)
        self.assertIn("steps", result["funnel"])
        self.assertIn("total_tools", result["funnel"])


if __name__ == "__main__":
    unittest.main()
