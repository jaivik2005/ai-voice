"""Unit tests for the web boundary; all provider calls are mocked."""
import importlib.util
import unittest

HAS_WEB_DEPS = all(importlib.util.find_spec(name) for name in ("pydantic", "httpx", "bs4"))

@unittest.skipUnless(HAS_WEB_DEPS, "web dependencies are not installed; run pip install -r requirements.txt")
class WebSearchTests(unittest.TestCase):
    def test_intent_detection(self):
        from core.intent import Action
        from core.nlu import RuleBasedNLU
        self.assertEqual(RuleBasedNLU().parse("search Python documentation")[0].action, Action.DOCUMENTATION_SEARCH)
        self.assertEqual(RuleBasedNLU().parse("find the official website of OpenAI")[0].action, Action.WEBSITE_SEARCH)

    def test_url_validation(self):
        from security.validator import SecurityError, validate_web_url
        self.assertEqual(validate_web_url("https://example.com/path"), "https://example.com/path")
        with self.assertRaises(SecurityError): validate_web_url("http://example.com")
        with self.assertRaises(SecurityError): validate_web_url("https://localhost/test")

    def test_result_parser_and_ranking(self):
        from web.result_parser import parse_results
        from web.source_ranker import rank_and_deduplicate
        results = parse_results({"web": {"results": [
            {"title": "Example", "url": "https://example.com/a", "description": "one"},
            {"title": "Duplicate", "url": "https://example.com/a/", "description": "two"},
            {"title": "Agency", "url": "https://agency.gov/info", "description": "primary"},
        ]}}, "brave")
        ranked = rank_and_deduplicate(results)
        self.assertEqual(len(ranked), 2)
        self.assertEqual(ranked[0].title, "Agency")

    def test_citations_are_traceable(self):
        from web.models import SearchResult
        from web.summarizer import summarize
        answer = summarize("test", [SearchResult(title="Source", url="https://example.com", source="example.com")])
        self.assertEqual(answer.citations[0].source_id, "S1")
        self.assertIn("[S1]", answer.detail)

    def test_follow_up_context(self):
        from core.context import ConversationContext
        context = ConversationContext(); context.remember_search("topic", [{"title": "One"}])
        self.assertEqual(context.last_search_query, "topic")
        self.assertEqual(context.last_search_results[0]["title"], "One")

if __name__ == "__main__": unittest.main()
