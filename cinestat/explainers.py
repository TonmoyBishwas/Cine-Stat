"""Turning a recommendation into a sentence the user can read.

There are two ways to do it, and they are used through exactly the same
method call, `explain(recommendation, preference)`:

  * RuleExplainer - stitches together the reasons the recommender already
    worked out. Needs no internet, no account and no money.
  * AIExplainer   - sends those same reasons to a language model through
    OpenRouter and gets back a friendlier paragraph.

Swapping one for the other changes nothing else in the program. That is
POLYMORPHISM doing real work: the GUI holds a variable called `explainer`,
calls `explainer.explain(...)`, and genuinely does not know or care which
class it is holding.

WORTH SAYING OUT LOUD IN THE DEMO: the AI does not choose the films. Our own
code in `recommenders.py` chooses them and works out why. The AI is only a
writer, handed those reasons and asked to phrase them nicely. If it is
unavailable we fall back to the rule explainer and the feature still works.

Syllabus topics demonstrated here:
  Class 4  - abstract base class, inheritance, method overriding
  Class 5  - polymorphism
  Class 9  - custom exceptions, file I/O and pathlib (reading the .env file)
"""

import os
from abc import ABC, abstractmethod
from pathlib import Path

from .exceptions import AIServiceError


# ---------------------------------------------------------------------------
# Finding the API key without ever writing it into the source code
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
KEY_NAME = "OPENROUTER_API_KEY"
MODEL_NAME = "OPENROUTER_MODEL"


def read_env_file(path=None):
    """Read a simple KEY=value file into a dictionary.

    A `.env` file is the normal way to keep a secret out of the code. Ours is
    listed in .gitignore, so the key never reaches GitHub.

    Class 9: File I/O with pathlib, and an error we choose to ignore - if the
    file is not there, that is not a problem, the user may use the
    environment variable instead.
    """
    values = {}
    # Looked up when the function RUNS, not when it was written, so a test
    # can point ENV_FILE somewhere harmless.
    path = Path(path) if path else ENV_FILE
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_setting(name, default=""):
    """Look for a setting in the real environment first, then in .env."""
    return os.environ.get(name) or read_env_file().get(name, default)


# ---------------------------------------------------------------------------
# The class hierarchy
# ---------------------------------------------------------------------------
class BaseExplainer(ABC):
    """ABSTRACT base class. Every explainer must be able to explain().

    It also provides `header()`, which both subclasses reuse unchanged - the
    shared part lives in the parent, exactly like DataLoader.clean().
    """

    name = "Explainer"
    needs_internet = False

    @property
    def is_available(self):
        """Can this explainer actually be used right now?

        The rule-based one always can. The AI one needs a key, so it
        OVERRIDES this property.
        """
        return True

    def header(self, recommendation):
        """The first line, identical whichever explainer is used."""
        movie = recommendation.movie
        return (f"{movie.name} ({movie.year}) - {recommendation.match} match, "
                f"{movie.genre}, rated {movie.rating}, "
                f"IMDb {movie.score:.1f}")

    @abstractmethod
    def explain(self, recommendation, preference):
        """Return a short paragraph saying why this film was suggested."""

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}()"


class RuleExplainer(BaseExplainer):
    """Writes the explanation from the reasons our own code produced.

    No internet, no API key, no cost. This is the default, and it is also
    what the AI explainer falls back to when something goes wrong.
    """

    name = "Built-in reasons (works offline)"

    def explain(self, recommendation, preference):
        """Override: join the reasons up into readable sentences."""
        lines = [self.header(recommendation), ""]

        reasons = recommendation.reasons
        if reasons:
            lines.append("Why you might like it:")
            for reason in reasons:
                # Capitalise the first letter so each bullet reads as a line.
                lines.append(f"  - {reason[0].upper()}{reason[1:]}")
        else:
            lines.append("No specific reasons were recorded for this film.")

        if preference is not None and len(preference) > 0:
            liked = ", ".join(preference.liked_titles[:4])
            more = " and others" if len(preference) > 4 else ""
            lines.append("")
            lines.append(f"Based on the films you ticked: {liked}{more}.")

        return "\n".join(lines)


class AIExplainer(BaseExplainer):
    """Asks a language model on OpenRouter to write the explanation.

    OpenRouter is one website that forwards requests to many different AI
    models, so a single account and a single URL can reach all of them. The
    request itself is an ordinary HTTPS POST carrying JSON.

    The key is NEVER written in this file. It is read from the environment
    variable OPENROUTER_API_KEY, or from a `.env` file that git ignores.
    """

    name = "AI explanation (OpenRouter)"
    needs_internet = True

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    # A small, cheap, fast model is plenty for writing three sentences.
    # Override it by putting OPENROUTER_MODEL=... in your .env file.
    #
    # MODEL SLUGS GO STALE. OpenRouter retires them, and a retired one does
    # not fail politely - it answers HTTP 404 "No endpoints found", which
    # looks exactly like a broken API key from the outside. This default was
    # "anthropic/claude-3.5-haiku" and had gone that way, so the AI button
    # quietly fell back to the offline reasons on every machine. If that
    # happens again, pick a live slug from https://openrouter.ai/models and
    # change it here. README.md names this same model, and
    # test_the_default_model_is_the_one_the_readme_promises keeps the two
    # from drifting apart again.
    DEFAULT_MODEL = "google/gemini-2.5-flash-lite"
    TIMEOUT_SECONDS = 60
    # Generous on purpose. Several models on OpenRouter are "reasoning"
    # models: they think to themselves first, and that thinking is charged
    # against the SAME budget as the answer. At 220 tokens our model spent
    # 219 of them thinking and returned an empty answer. 800 leaves room for
    # both. A call still costs a fraction of a cent.
    MAX_TOKENS = 800

    SYSTEM_PROMPT = (
        "You are a friendly film recommender inside a student data-science "
        "project. You are given a film, the reasons a scoring algorithm "
        "picked it, and the films the user already said they liked. "
        "Write 2-4 short sentences, in plain English, explaining why this "
        "user in particular might enjoy this film. Use the reasons you are "
        "given - do not invent facts, plot details, awards or cast members "
        "that are not in the information provided. Do not mention scores or "
        "percentages.\n\n"
        "Speak directly to the user, as a friend recommending a film would. "
        "Never mention the algorithm, the scoring, the data or the reasons "
        "list itself - the user should not be able to tell a program was "
        "involved.\n\n"
        "Write PLAIN TEXT only. No bullet points, no headings, and no "
        "Markdown of any kind - no *asterisks*, no _underscores_, no "
        "**bold**. The answer is shown in a plain text box that cannot "
        "render formatting, so any symbols you add appear literally."
    )

    def __init__(self, api_key=None, model=None):
        # An argument wins if given; otherwise look in the environment/.env.
        self.api_key = api_key or load_setting(KEY_NAME)
        self.model = model or load_setting(MODEL_NAME) or self.DEFAULT_MODEL
        # COMPOSITION: the AI explainer HAS-A rule explainer to fall back on.
        self.fallback = RuleExplainer()
        self.last_error = None

    # ---- override the parent's availability check -------------------------

    @property
    def is_available(self):
        """Override: without a key there is nothing we can do."""
        return bool(self.api_key)

    # ---- building the question --------------------------------------------

    def build_prompt(self, recommendation, preference):
        """Turn the recommendation into the text we send to the model.

        Kept as its own method so it can be tested without any internet.
        """
        movie = recommendation.movie
        reasons = "; ".join(recommendation.reasons) or "none recorded"

        liked = "nothing yet"
        if preference is not None and len(preference) > 0:
            liked = ", ".join(preference.liked_titles[:6])

        return (
            f"Film being recommended: {movie.name} ({movie.year})\n"
            f"Genre: {movie.genre}\n"
            f"Age rating: {movie.rating}\n"
            f"Runtime: {movie.runtime:.0f} minutes\n"
            f"IMDb score: {movie.score:.1f} out of 10\n"
            f"Box office: ${movie.gross:,.0f} on a ${movie.budget:,.0f} budget "
            f"({movie.verdict})\n"
            f"Reasons the algorithm chose it: {reasons}\n"
            f"Films this user said they liked: {liked}\n\n"
            f"Write the explanation now."
        )

    # ---- talking to OpenRouter --------------------------------------------

    def explain(self, recommendation, preference):
        """Override: ask the model, and fall back to the rules if it fails."""
        if not self.is_available:
            raise AIServiceError(
                f"No OpenRouter API key found. Put {KEY_NAME}=your-key in a "
                f"file called .env in the project folder, or set it as an "
                f"environment variable.")

        try:
            import requests
        except ImportError:
            raise AIServiceError(
                "The 'requests' library is not installed. "
                "Run: pip install -r requirements.txt")

        payload = {
            "model": self.model,
            "max_tokens": self.MAX_TOKENS,
            # We do NOT try to switch the thinking off here. Some models on
            # OpenRouter refuse outright - z-ai/glm-5.3-flash answers
            # "Reasoning is mandatory for this endpoint and cannot be
            # disabled" with an HTTP 400. Giving the model room to think and
            # then answer is the setting that works everywhere.
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user",
                 "content": self.build_prompt(recommendation, preference)},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            # OpenRouter asks for these two so it can label the traffic.
            "HTTP-Referer": "https://github.com/cinestat",
            "X-Title": "CineStat",
        }

        try:
            response = requests.post(self.API_URL, headers=headers,
                                     json=payload,
                                     timeout=self.TIMEOUT_SECONDS)
        except Exception as error:
            # Covers no internet, DNS failure, timeout - anything at all.
            raise AIServiceError(f"Could not reach OpenRouter: {error}")

        if response.status_code != 200:
            raise AIServiceError(
                f"OpenRouter refused the request (HTTP {response.status_code}): "
                f"{self._error_message(response)}{self._hint(response)}")

        return self._read_reply(response)

    def explain_or_fallback(self, recommendation, preference):
        """Try the AI; if anything goes wrong, use the rules instead.

        The GUI calls this one, so a flat battery of a wifi connection can
        never break the demo. The reason it fell back is kept in
        `self.last_error` so the window can say so honestly.
        """
        self.last_error = None
        try:
            return self.explain(recommendation, preference)
        except AIServiceError as error:
            self.last_error = str(error)
            return self.fallback.explain(recommendation, preference)

    # ---- small helpers for reading the reply ------------------------------

    def _hint(self, response):
        """Turn OpenRouter's HTTP code into something worth acting on.

        Written because of a real afternoon lost to this: a retired model
        slug answers 404 "No endpoints found", which from the outside looks
        identical to a broken key - the AI button simply never worked, and
        the message on screen did not say which of the two it was.
        """
        hints = {
            401: ("The key was not accepted. Check OPENROUTER_API_KEY in "
                  "your .env, and that the key is still live at "
                  "https://openrouter.ai/keys"),
            402: ("The account is out of credit. OpenRouter needs a balance "
                  "even for the very cheap models."),
            404: (f"There is no such model as '{self.model}' any more - "
                  f"slugs get retired. Pick a live one from "
                  f"https://openrouter.ai/models and put it in your .env as "
                  f"OPENROUTER_MODEL, or change AIExplainer.DEFAULT_MODEL. "
                  f"Note this is NOT a problem with your key."),
            429: ("Too many requests too quickly - wait a moment and press "
                  "the button again."),
        }
        hint = hints.get(response.status_code)
        return f"\n\n{hint}" if hint else ""

    @staticmethod
    def _error_message(response):
        """Pull the human-readable message out of an error response."""
        try:
            body = response.json()
        except Exception:
            return response.text[:200]
        error = body.get("error")
        if isinstance(error, dict):
            return error.get("message", str(error))
        return str(error or body)[:200]

    @classmethod
    def _read_reply(cls, response):
        """Dig the text out of OpenRouter's JSON answer."""
        try:
            body = response.json()
            choice = body["choices"][0]
            text = choice["message"]["content"]
        except Exception as error:
            raise AIServiceError(
                f"OpenRouter sent back something unexpected: {error}")

        text = (text or "").strip()
        if text:
            return text

        # An empty answer almost always means one specific thing: the model
        # ran out of room. Say so, instead of leaving the user guessing.
        if choice.get("finish_reason") == "length":
            raise AIServiceError(
                f"The model used up all {cls.MAX_TOKENS} tokens before "
                f"writing anything - this happens with 'reasoning' models "
                f"that think to themselves first. Raise "
                f"AIExplainer.MAX_TOKENS, or put a different model in .env "
                f"as OPENROUTER_MODEL.")
        raise AIServiceError("OpenRouter sent back an empty explanation.")


def build_explainer():
    """Pick the best explainer available on this machine.

    Returns the AI one if a key is configured, otherwise the offline one.
    A plain function like this is sometimes called a FACTORY: its job is to
    decide which class to build so the caller does not have to.
    """
    ai = AIExplainer()
    return ai if ai.is_available else RuleExplainer()
