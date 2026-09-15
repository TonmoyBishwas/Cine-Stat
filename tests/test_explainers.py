"""Tests for the two explainers.

The AI tests never touch the internet. A fake stand-in for the `requests`
library is slipped into sys.modules, so we can check exactly what CineStat
sends and how it copes with every kind of reply - including failure.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cinestat import (UserPreference, Recommendation, RuleExplainer,
                      AIExplainer, BaseExplainer, AIServiceError,
                      MovieDataError, build_explainer)
from cinestat import explainers

from tests.helpers import make_movie


def a_recommendation():
    movie = make_movie(name="The Thing", year=1982, genre="Horror",
                       rating="R", score=8.2, runtime=109)
    return Recommendation(movie, 87.0,
                          ["Horror is one of your favourite genres",
                           "well reviewed - IMDb 8.2 out of 10"],
                          source="Matches my taste")


def a_preference():
    preference = UserPreference(genres=["Horror"])
    preference.add_liked(make_movie(name="The Shining"))
    return preference


# ---------------------------------------------------------------------------
# A fake replacement for the `requests` library
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


class FakeRequests:
    """Stands in for `requests` and records what it was asked to send."""

    def __init__(self, response=None, raises=None):
        self.response = response
        self.raises = raises
        self.calls = []

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append({"url": url, "headers": headers, "json": json,
                           "timeout": timeout})
        if self.raises:
            raise self.raises
        return self.response


def good_reply(text="You will probably enjoy this one."):
    return FakeResponse(200, {"choices": [{"message": {"content": text}}]})


class FakeRequestsInstalled:
    """A context manager that puts the fake library in place and takes it away.

    Class 9 again: __enter__ / __exit__, the same idea as ExportSession.
    """

    def __init__(self, fake):
        self.fake = fake
        self.original = None

    def __enter__(self):
        self.original = sys.modules.get("requests")
        sys.modules["requests"] = self.fake
        return self.fake

    def __exit__(self, *exc):
        if self.original is None:
            sys.modules.pop("requests", None)
        else:
            sys.modules["requests"] = self.original
        return False


# ---------------------------------------------------------------------------
class TestRuleExplainer(unittest.TestCase):
    """The offline explainer. This one must always work."""

    def setUp(self):
        self.explainer = RuleExplainer()
        self.recommendation = a_recommendation()
        self.preference = a_preference()

    def test_it_is_always_available(self):
        self.assertTrue(self.explainer.is_available)
        self.assertFalse(self.explainer.needs_internet)

    def test_the_film_is_named_at_the_top(self):
        text = self.explainer.explain(self.recommendation, self.preference)
        self.assertIn("The Thing", text)
        self.assertIn("87%", text)

    def test_every_reason_appears(self):
        text = self.explainer.explain(self.recommendation, self.preference)
        for reason in self.recommendation.reasons:
            self.assertIn(reason[1:], text)

    def test_the_ticked_films_are_mentioned(self):
        text = self.explainer.explain(self.recommendation, self.preference)
        self.assertIn("The Shining", text)

    def test_it_copes_with_no_reasons_and_no_preference(self):
        bare = Recommendation(make_movie(), 50, [])
        text = self.explainer.explain(bare, None)
        self.assertIn("No specific reasons", text)


class TestAIExplainerWithoutAKey(unittest.TestCase):
    """With no key configured, nothing should blow up in the user's face."""

    def setUp(self):
        # Hide any real key this machine happens to have, and point the .env
        # lookup at a folder that certainly has no .env in it.
        self.env_patch = mock.patch.dict(os.environ, {}, clear=True)
        self.env_patch.start()
        self.original_env_file = explainers.ENV_FILE
        explainers.ENV_FILE = Path(tempfile.gettempdir()) / "no-such-.env"

    def tearDown(self):
        self.env_patch.stop()
        explainers.ENV_FILE = self.original_env_file

    def test_it_reports_itself_as_unavailable(self):
        self.assertFalse(AIExplainer().is_available)

    def test_explain_raises_our_own_exception(self):
        with self.assertRaises(AIServiceError) as caught:
            AIExplainer().explain(a_recommendation(), a_preference())
        self.assertIn("OPENROUTER_API_KEY", str(caught.exception))

    def test_that_exception_is_catchable_as_moviedataerror(self):
        with self.assertRaises(MovieDataError):
            AIExplainer().explain(a_recommendation(), a_preference())

    def test_explain_or_fallback_still_produces_an_explanation(self):
        """The whole point: the demo must never break because of the wifi."""
        explainer = AIExplainer()
        text = explainer.explain_or_fallback(a_recommendation(), a_preference())
        self.assertIn("The Thing", text)
        self.assertIsNotNone(explainer.last_error)

    def test_the_factory_falls_back_to_the_offline_explainer(self):
        self.assertIsInstance(build_explainer(), RuleExplainer)


class TestTheQuestionWeSend(unittest.TestCase):
    """build_prompt() can be checked without any internet at all."""

    def setUp(self):
        self.explainer = AIExplainer(api_key="test-key")
        self.prompt = self.explainer.build_prompt(a_recommendation(),
                                                  a_preference())

    def test_the_film_is_described(self):
        for expected in ("The Thing", "1982", "Horror", "8.2", "109"):
            with self.subTest(expected=expected):
                self.assertIn(expected, self.prompt)

    def test_our_own_reasons_are_handed_over(self):
        self.assertIn("Horror is one of your favourite genres", self.prompt)

    def test_the_films_the_user_ticked_are_handed_over(self):
        self.assertIn("The Shining", self.prompt)

    def test_the_model_is_told_not_to_invent_facts(self):
        self.assertIn("do not invent facts", AIExplainer.SYSTEM_PROMPT)

    def test_the_model_is_told_to_write_plain_text(self):
        """Regression: Gemini replied with *asterisks* around film titles,
        and the Tkinter text box has no way to render them - they appeared
        on screen as literal asterisks."""
        prompt = AIExplainer.SYSTEM_PROMPT.lower()
        self.assertIn("plain text", prompt)
        self.assertIn("markdown", prompt)

    def test_the_model_is_told_not_to_mention_the_algorithm(self):
        self.assertIn("algorithm", AIExplainer.SYSTEM_PROMPT.lower())


class TestTalkingToOpenRouter(unittest.TestCase):
    """Every reply OpenRouter could send, faked."""

    def setUp(self):
        self.explainer = AIExplainer(api_key="test-key",
                                     model="test/model")
        self.recommendation = a_recommendation()
        self.preference = a_preference()

    def explain_with(self, fake):
        with FakeRequestsInstalled(fake):
            return self.explainer.explain(self.recommendation, self.preference)

    def test_a_good_reply_comes_back_as_text(self):
        fake = FakeRequests(good_reply("A fine film for you."))
        self.assertEqual(self.explain_with(fake), "A fine film for you.")

    def test_the_key_is_sent_as_a_bearer_token(self):
        fake = FakeRequests(good_reply())
        self.explain_with(fake)
        headers = fake.calls[0]["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test-key")

    def test_the_chosen_model_is_sent(self):
        fake = FakeRequests(good_reply())
        self.explain_with(fake)
        self.assertEqual(fake.calls[0]["json"]["model"], "test/model")

    def test_a_timeout_is_always_set(self):
        """Without one, a dead server would hang the background thread."""
        fake = FakeRequests(good_reply())
        self.explain_with(fake)
        self.assertEqual(fake.calls[0]["timeout"],
                         AIExplainer.TIMEOUT_SECONDS)

    def test_a_rejected_request_becomes_our_exception(self):
        fake = FakeRequests(FakeResponse(
            401, {"error": {"message": "No auth credentials found"}}))
        with self.assertRaises(AIServiceError) as caught:
            self.explain_with(fake)
        self.assertIn("401", str(caught.exception))
        self.assertIn("No auth credentials", str(caught.exception))

    def test_a_network_failure_becomes_our_exception(self):
        fake = FakeRequests(raises=OSError("Name or service not known"))
        with self.assertRaises(AIServiceError) as caught:
            self.explain_with(fake)
        self.assertIn("Could not reach OpenRouter", str(caught.exception))

    def test_a_nonsense_reply_becomes_our_exception(self):
        fake = FakeRequests(FakeResponse(200, {"unexpected": True}))
        with self.assertRaises(AIServiceError):
            self.explain_with(fake)

    def test_an_empty_answer_becomes_our_exception(self):
        fake = FakeRequests(good_reply("   "))
        with self.assertRaises(AIServiceError):
            self.explain_with(fake)

    def test_a_reasoning_model_that_ran_out_of_room_says_so(self):
        """Regression: z-ai/glm-5.3-flash thinks to itself before answering,
        and that thinking is charged against the same token budget. At 220
        tokens it spent 219 thinking and returned content=None, and the user
        just saw 'empty explanation' with no idea what to change."""
        fake = FakeRequests(FakeResponse(200, {
            "choices": [{"finish_reason": "length",
                         "message": {"content": None,
                                     "reasoning": "thinking out loud..."}}],
            "usage": {"completion_tokens_details": {"reasoning_tokens": 219}},
        }))
        with self.assertRaises(AIServiceError) as caught:
            self.explain_with(fake)
        message = str(caught.exception)
        self.assertIn("reasoning", message)
        self.assertIn("OPENROUTER_MODEL", message)

    def test_the_token_budget_leaves_room_for_thinking_and_answering(self):
        self.assertGreaterEqual(AIExplainer.MAX_TOKENS, 500)

    def test_we_never_try_to_switch_reasoning_off(self):
        """Regression: sending reasoning={'enabled': False} makes
        z-ai/glm-5.3-flash reject the whole request with an HTTP 400,
        'Reasoning is mandatory for this endpoint and cannot be disabled'."""
        fake = FakeRequests(good_reply())
        self.explain_with(fake)
        self.assertNotIn("reasoning", fake.calls[0]["json"])

    def test_fallback_returns_the_offline_text_and_records_why(self):
        fake = FakeRequests(raises=OSError("no internet"))
        with FakeRequestsInstalled(fake):
            text = self.explainer.explain_or_fallback(self.recommendation,
                                                      self.preference)
        self.assertIn("Why you might like it", text)
        self.assertIn("no internet", self.explainer.last_error)

    def test_a_successful_call_records_no_error(self):
        fake = FakeRequests(good_reply())
        with FakeRequestsInstalled(fake):
            self.explainer.explain_or_fallback(self.recommendation,
                                               self.preference)
        self.assertIsNone(self.explainer.last_error)


class TestReadingTheEnvFile(unittest.TestCase):
    """Class 9: File I/O with pathlib, used to keep the key out of the code."""

    def test_a_missing_file_is_not_an_error(self):
        missing = Path(tempfile.gettempdir()) / "definitely-not-here.env"
        self.assertEqual(explainers.read_env_file(missing), {})

    def test_keys_values_comments_and_quotes(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text(
                "# a comment\n"
                "OPENROUTER_API_KEY=sk-or-abc123\n"
                'OPENROUTER_MODEL="vendor/model"\n'
                "\n"
                "not a setting line\n", encoding="utf-8")
            values = explainers.read_env_file(path)
        self.assertEqual(values["OPENROUTER_API_KEY"], "sk-or-abc123")
        self.assertEqual(values["OPENROUTER_MODEL"], "vendor/model")
        self.assertEqual(len(values), 2)

    def test_a_key_given_in_code_beats_the_environment(self):
        with mock.patch.dict(os.environ,
                             {"OPENROUTER_API_KEY": "from-environment"}):
            self.assertEqual(AIExplainer(api_key="given").api_key, "given")
            self.assertEqual(AIExplainer().api_key, "from-environment")

    def test_the_factory_picks_the_ai_when_a_key_exists(self):
        with mock.patch.dict(os.environ,
                             {"OPENROUTER_API_KEY": "sk-or-test"}):
            self.assertIsInstance(build_explainer(), AIExplainer)


class TestPolymorphism(unittest.TestCase):
    """Class 5: both explainers are used through the same call."""

    def test_both_are_baseexplainers(self):
        for explainer in (RuleExplainer(), AIExplainer(api_key="x")):
            with self.subTest(explainer=explainer.name):
                self.assertIsInstance(explainer, BaseExplainer)

    def test_the_base_class_cannot_be_created(self):
        with self.assertRaises(TypeError):
            BaseExplainer()

    def test_they_share_the_header_written_once_in_the_parent(self):
        recommendation = a_recommendation()
        header = RuleExplainer().header(recommendation)
        self.assertEqual(AIExplainer(api_key="x").header(recommendation),
                         header)

    def test_the_ai_explainer_has_a_rule_explainer_inside_it(self):
        """COMPOSITION: the AI one HAS-A offline one to fall back on."""
        self.assertIsInstance(AIExplainer(api_key="x").fallback, RuleExplainer)


if __name__ == "__main__":
    unittest.main()
