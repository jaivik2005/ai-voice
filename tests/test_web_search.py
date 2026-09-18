"""Unit tests for the web boundary; all provider calls are mocked."""
import importlib.util
import os
import unittest
from unittest.mock import patch

HAS_WEB_DEPS = all(importlib.util.find_spec(name) for name in ("pydantic", "httpx", "bs4"))

@unittest.skipUnless(HAS_WEB_DEPS, "web dependencies are not installed; run pip install -r requirements.txt")
class WebSearchTests(unittest.TestCase):
    def test_project_root_configuration_is_loaded(self):
        import config
        self.assertTrue(config.PROJECT_ROOT.is_dir())
        self.assertEqual(config.WEB_SEARCH_PROVIDER, os.getenv("WEB_SEARCH_PROVIDER", "").lower())

    def test_missing_configuration(self):
        from web.search_engine import SearchEngine, SearchUnavailable
        with patch.dict(os.environ, {"SEARCH_API_KEY": "", "WEB_SEARCH_PROVIDER": ""}, clear=False):
            with self.assertRaisesRegex(SearchUnavailable, "provider is missing"):
                SearchEngine(api_key="", provider="").search("test")
        with patch.dict(os.environ, {"SEARCH_API_KEY": "", "WEB_SEARCH_PROVIDER": "tavily"}, clear=False):
            with self.assertRaisesRegex(SearchUnavailable, "API key is missing"):
                SearchEngine(api_key="", provider="tavily").search("test")

    def test_tavily_provider_selection_and_success(self):
        from web.search_engine import SearchEngine

        class Response:
            def raise_for_status(self): pass
            def json(self):
                return {"results": [{"title": "OpenAI", "url": "https://openai.com", "content": "Official site"}]}

        class Client:
            def post(self, url, **kwargs):
                self.url, self.kwargs = url, kwargs
                return Response()

        client = Client()
        with patch.dict(os.environ, {"SEARCH_API_KEY": "masked-test-key", "WEB_SEARCH_PROVIDER": "tavily"}, clear=False), patch("web.search_engine.cache_get", return_value=None), patch("web.search_engine.cache_put"):
            response = SearchEngine(client=client).search("OpenAI test provider selection")
        self.assertEqual(client.url, "https://api.tavily.com/search")
        self.assertEqual(response.results[0].url, "https://openai.com")

    def test_api_failure_is_graceful(self):
        import httpx
        from web.search_engine import SearchEngine, SearchUnavailable

        class Client:
            def post(self, *args, **kwargs):
                raise httpx.ConnectError("connection failed")

        with self.assertRaisesRegex(SearchUnavailable, "couldn't reach"):
            SearchEngine(api_key="masked-test-key", provider="tavily", client=Client()).search("test")

    def test_invalid_provider(self):
        from web.search_engine import SearchEngine, SearchUnavailable
        with self.assertRaisesRegex(SearchUnavailable, "Unsupported web search provider"):
            SearchEngine(api_key="masked-test-key", provider="unknown").search("test")

    def test_intent_detection(self):
        from core.intent import Action
        from core.nlu import RuleBasedNLU
        nlu = RuleBasedNLU()
        self.assertEqual(nlu.parse("search Python documentation")[0].action, Action.DOCUMENTATION_SEARCH)
        self.assertEqual(nlu.parse("find the official website of OpenAI")[0].action, Action.WEBSITE_SEARCH)
        self.assertEqual(nlu.parse("find the official webste of OpenAi")[0].action, Action.WEBSITE_SEARCH)
        self.assertEqual(nlu.parse("find the offical webste of OpenAi")[0].action, Action.WEBSITE_SEARCH)
        self.assertEqual(nlu.parse("serach the web for Python tutorials")[0].action, Action.WEB_SEARCH)
        self.assertEqual(nlu.parse("find MongoDB doucmentation")[0].action, Action.DOCUMENTATION_SEARCH)
        self.assertEqual(nlu.parse("what is the latestt Node.js version")[0].action, Action.NEWS_SEARCH)
        self.assertEqual(nlu.parse("find my resume")[0].action, Action.SEARCH_FILES)
        self.assertEqual(nlu.parse("find my project report")[0].action, Action.SEARCH_FILES)
        self.assertEqual(nlu.parse("where is my PDF")[0].action, Action.SEARCH_FILES)
        self.assertEqual(nlu.parse("open my Documents folder")[0].action, Action.OPEN)
        self.assertEqual(nlu.parse("find the official website for my company")[0].action, Action.WEBSITE_SEARCH)
        self.assertEqual(nlu.parse("find my OpenAI project report")[0].action, Action.SEARCH_FILES)
        self.assertEqual(nlu.parse("search my files for Python")[0].action, Action.SEARCH_FILES)
        self.assertEqual(nlu.parse("serach the web for Python tutorials")[0].parameters["query"], "Python tutorials")

    def test_documentation_query_requests_official_docs(self):
        from web.query_planner import plan_query
        self.assertEqual(plan_query("MongoDB", mode="docs").queries, ["MongoDB official documentation"])

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

    def test_documentation_sources_outrank_repository_sources(self):
        from web.models import SearchResult
        from web.source_ranker import rank_and_deduplicate
        ranked = rank_and_deduplicate([
            SearchResult(title="Repository", url="https://github.com/example/project"),
            SearchResult(title="Documentation", url="https://example.com/docs"),
        ], prefer_official=True)
        self.assertEqual(ranked[0].title, "Documentation")

    def test_citations_are_traceable(self):
        from web.models import SearchResult
        from web.summarizer import summarize
        answer = summarize("test", [SearchResult(title="Source", url="https://example.com", source="example.com")])
        self.assertEqual(answer.citations[0].source_id, "S1")
        self.assertIn("[S1]", answer.detail)

    def test_summary_displays_url_description_and_domain(self):
        from web.models import SearchResult
        from web.summarizer import summarize
        result = SearchResult(title="OpenAI - Official site", url="https://openai.com/", snippet="AI research and deployment company.", source="openai.com")
        detail = summarize("Find the official website of OpenAI", [result]).detail
        self.assertIn("[S1] OpenAI - Official site", detail)
        self.assertIn("URL: https://openai.com/", detail)
        self.assertIn("Description: AI research and deployment company.", detail)
        self.assertIn("Domain: openai.com", detail)
        self.assertIn("official result", detail.lower())

    def test_summary_handles_missing_url_and_snippet(self):
        from web.models import SearchResult
        from web.summarizer import summarize
        detail = summarize("test", [SearchResult(title="Result")]).detail
        self.assertIn("URL: Unavailable", detail)
        self.assertIn("Description: No description available.", detail)

    def test_follow_up_context(self):
        from core.context import ConversationContext
        context = ConversationContext(); context.remember_search("topic", [{"title": "One"}])
        self.assertEqual(context.last_search_query, "topic")
        self.assertEqual(context.last_search_results[0]["title"], "One")

if __name__ == "__main__": unittest.main()
