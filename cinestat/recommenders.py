"""The recommendation engine.

"Tick a few films you liked, and we will suggest more."

The design deliberately mirrors `analyzers.py`: one abstract base class that
does the shared work, and small subclasses that each fill in one method. That
one method is `score_movie()` - it decides how well a single film matches, and
says WHY in plain English.

The "why" is written by our own code, not by an AI. The AI in `explainers.py`
only turns these reasons into a friendlier paragraph. That matters: if the
internet is down, the recommendations and their reasons still work.

Syllabus topics demonstrated here:
  Class 4  - abstract base class, inheritance, method overriding
  Class 5  - polymorphism (three recommenders, one interface), dunder methods
  Class 11 - generators (candidates()), decorators (@timed on recommend())
"""

from abc import ABC, abstractmethod

from .preferences import UserPreference
from .utils import timed


class Recommendation:
    """One suggested film, its match score, and the reasons behind it.

    This is a small "value object": it carries a result around instead of us
    passing three loose variables everywhere.
    """

    def __init__(self, movie, score, reasons, source="Recommender"):
        self.movie = movie
        # Clamp to 0-100 so the GUI can always show it as a percentage.
        self.score = max(0.0, min(100.0, float(score)))
        self.reasons = list(reasons)
        self.source = source            # which recommender produced it

    @property
    def match(self):
        """The score written the way the user sees it: '82%'."""
        return f"{self.score:.0f}%"

    # ---- dunder methods: operator overloading -----------------------------

    def __lt__(self, other):
        """Lets sorted() order recommendations by score, best last."""
        if not isinstance(other, Recommendation):
            return NotImplemented
        return self.score < other.score

    def __eq__(self, other):
        if not isinstance(other, Recommendation):
            return NotImplemented
        return self.movie == other.movie

    def __hash__(self):
        return hash(self.movie)

    def __str__(self):
        return f"{self.movie.name} ({self.movie.year}) - {self.match} match"

    def __repr__(self):
        return f"Recommendation({self.movie.name!r}, {self.score:.1f})"

    def to_dict(self):
        """Plain dictionary version - used by the CSV / JSON export."""
        data = self.movie.to_dict()
        data["match_score"] = round(self.score, 1)
        data["reasons"] = " ; ".join(self.reasons)
        data["recommender"] = self.source
        return data


class BaseRecommender(ABC):
    """ABSTRACT base class for every way of recommending films.

    It writes down the steps that never change - filter, score, sort, cut to
    the top n - and leaves the one step that DOES change, `score_movie()`, to
    each subclass. That arrangement has a name: the TEMPLATE METHOD pattern.

    Because all three subclasses are used identically:

        for engine in [ContentRecommender(movies, pref),
                       PopularityRecommender(movies, pref)]:
            engine.recommend(5)

    ...this is POLYMORPHISM, exactly like the analyzers.
    """

    title = "Recommender"
    explanation = "Suggests films."

    def __init__(self, collection, preference=None):
        self.collection = collection
        # Deliberately "is None" and not "preference or UserPreference()".
        # UserPreference defines __len__, so a real profile with no films
        # ticked yet counts as FALSE - and `or` would silently throw away
        # the genres and year range the user had set. A test caught this.
        self.preference = UserPreference() if preference is None else preference

    # ---- the one method every subclass must write -------------------------

    @abstractmethod
    def score_movie(self, movie):
        """Score one film out of 100 and list the reasons for that score.

        Must return a tuple: (score, list_of_reason_strings).
        """

    # ---- the shared machinery ---------------------------------------------

    def candidates(self):
        """A GENERATOR yielding films that are eligible to be suggested.

        `yield` means the films come out one at a time, so we never build a
        second copy of the whole collection in memory.
        """
        for movie in self.collection:
            if movie in self.preference:        # uses __contains__
                continue                        # never suggest what they ticked
            if not self.preference.allows(movie):
                continue
            yield movie

    @timed                       # <- Class 11: the decorator, timing the work
    def recommend(self, n=10, min_score=1.0):
        """The TEMPLATE METHOD: the same four steps for every recommender."""
        results = []
        for movie in self.candidates():
            score, reasons = self.score_movie(movie)
            if score < min_score:
                continue
            results.append(Recommendation(movie, score, reasons, self.title))

        # sorted() works because Recommendation defines __lt__.
        results.sort(reverse=True)
        return results[:n]

    def __str__(self):
        return f"{self.title}: {self.explanation}"

    def __repr__(self):
        return f"{self.__class__.__name__}({len(self.collection)} films)"


class ContentRecommender(BaseRecommender):
    """The main recommender: match each film against the user's taste profile.

    "Content-based" means we compare the FILM'S OWN PROPERTIES (genre, rating,
    IMDb score, runtime, era) with what the user said they liked. We are not
    using other people's viewing history - our dataset does not have any.

    The 100 points are split up like this, and every point is explainable:
    """

    title = "Matches my taste"
    explanation = ("Scores every film against the genres, ratings, length and "
                   "era of the films you ticked.")

    # Static members: the marks available for each test. Changing the weights
    # here changes the whole recommender, and nothing else has to be touched.
    GENRE_POINTS = 40
    RATING_POINTS = 15
    QUALITY_POINTS = 25
    RUNTIME_POINTS = 10
    ERA_POINTS = 10

    RUNTIME_TOLERANCE = 45.0     # minutes away before runtime scores nothing
    ERA_TOLERANCE = 30.0         # years away before era scores nothing

    def score_movie(self, movie):
        """Override: add up the five tests and explain each one."""
        score = 0.0
        reasons = []

        # 1. Genre - the biggest single factor.
        if self.preference.genres:
            if movie.genre_group in self.preference.genres:
                score += self.GENRE_POINTS
                reasons.append(
                    f"{movie.genre_group} is one of your favourite genres")
        else:
            # No genre preference given, so nobody should be punished for it.
            score += self.GENRE_POINTS / 2

        # 2. Age rating.
        if self.preference.ratings and movie.rating in self.preference.ratings:
            score += self.RATING_POINTS
            reasons.append(f"rated {movie.rating}, same as the films you picked")

        # 3. Quality, straight from the IMDb score.
        if movie.score > 0:
            quality = (movie.score / 10.0) * self.QUALITY_POINTS
            score += quality
            if movie.score >= 7.5:
                reasons.append(f"well reviewed - IMDb {movie.score:.1f} out of 10")

        # 4. Runtime: closer to the user's usual length is better.
        wanted_runtime = self.preference.preferred_runtime
        if wanted_runtime and movie.runtime > 0:
            gap = abs(movie.runtime - wanted_runtime)
            closeness = max(0.0, 1.0 - gap / self.RUNTIME_TOLERANCE)
            score += closeness * self.RUNTIME_POINTS
            if gap <= 15:
                reasons.append(
                    f"{movie.runtime:.0f} minutes long, about the length you like")

        # 5. Era: closer to the years the user's films came from is better.
        wanted_year = self.preference.preferred_year
        if wanted_year:
            gap = abs(movie.year - wanted_year)
            closeness = max(0.0, 1.0 - gap / self.ERA_TOLERANCE)
            score += closeness * self.ERA_POINTS
            if gap <= 5:
                reasons.append(f"from {movie.year}, the era you watch most")

        if not reasons:
            reasons.append("a reasonable all-round match")
        return score, reasons


class SimilarityRecommender(BaseRecommender):
    """"More films like THIS one" - compare against a single chosen film.

    Where ContentRecommender compares against a whole profile, this one
    compares against one seed film. Notice the constructor takes an extra
    argument and then calls super().__init__() to let the parent do its part.
    """

    title = "Similar to my last pick"
    explanation = "Finds the films closest to a single film you choose."

    GENRE_POINTS = 35
    RATING_POINTS = 15
    SCORE_POINTS = 25
    RUNTIME_POINTS = 15
    ERA_POINTS = 10

    SCORE_TOLERANCE = 2.5        # IMDb points away before quality scores 0
    RUNTIME_TOLERANCE = 40.0
    ERA_TOLERANCE = 20.0

    def __init__(self, collection, preference=None, seed=None):
        super().__init__(collection, preference)
        # If no seed film was handed in, use the film the user ticked last.
        if seed is None and self.preference.last_liked:
            seed = self.collection.find(self.preference.last_liked)
        self.seed = seed

    def score_movie(self, movie):
        """Override: how close is this film to the seed film?"""
        if self.seed is None:
            return 0.0, []

        score = 0.0
        reasons = []

        if movie.genre_group == self.seed.genre_group:
            score += self.GENRE_POINTS
            reasons.append(f"another {movie.genre_group} film")

        if movie.rating == self.seed.rating:
            score += self.RATING_POINTS
            reasons.append(f"carries the same {movie.rating} rating")

        if movie.score > 0 and self.seed.score > 0:
            gap = abs(movie.score - self.seed.score)
            closeness = max(0.0, 1.0 - gap / self.SCORE_TOLERANCE)
            score += closeness * self.SCORE_POINTS
            if gap <= 0.5:
                reasons.append(
                    f"reviewed almost the same - IMDb {movie.score:.1f} "
                    f"against {self.seed.score:.1f}")

        if movie.runtime > 0 and self.seed.runtime > 0:
            gap = abs(movie.runtime - self.seed.runtime)
            closeness = max(0.0, 1.0 - gap / self.RUNTIME_TOLERANCE)
            score += closeness * self.RUNTIME_POINTS
            if gap <= 10:
                reasons.append(f"a similar length, {movie.runtime:.0f} minutes")

        gap = abs(movie.year - self.seed.year)
        closeness = max(0.0, 1.0 - gap / self.ERA_TOLERANCE)
        score += closeness * self.ERA_POINTS
        if gap <= 3:
            reasons.append(f"came out around the same time ({movie.year})")

        if not reasons:
            reasons.append(f"loosely comparable to {self.seed.name}")
        return score, reasons


class PopularityRecommender(BaseRecommender):
    """The honest baseline: ignore taste completely, suggest famous good films.

    We keep this for the same reason the Predict tab reports the budget-only
    model next to the full one. If "most popular film in the database" does
    just as well as the clever recommender, the clever one is not earning its
    keep, and we would rather find that out than hide it.
    """

    title = "Most popular (baseline)"
    explanation = ("Ignores your taste completely and suggests the best "
                   "reviewed, most watched films. Here as a fair comparison.")

    SCORE_POINTS = 60
    VOTES_POINTS = 40
    VOTES_FOR_FULL_MARKS = 500_000

    def score_movie(self, movie):
        """Override: quality plus audience size, and nothing else."""
        quality = (movie.score / 10.0) * self.SCORE_POINTS
        share = min(1.0, movie.votes / self.VOTES_FOR_FULL_MARKS)
        popularity = share * self.VOTES_POINTS
        reasons = [f"IMDb {movie.score:.1f} from {movie.votes:,} voters",
                   "picked purely on popularity, not on your taste"]
        return quality + popularity, reasons
