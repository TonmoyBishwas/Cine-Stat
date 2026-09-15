"""UserPreference - an object that remembers what one person likes.

This is the input to the recommender: the user ticks a few films they enjoyed,
and this class turns that into a reusable taste profile.

Syllabus topics demonstrated here:
  Class 2  - classes, objects, constructors, instance variables
  Class 3  - encapsulation, private attributes, name mangling, static members
  Class 5  - operator overloading (__contains__, __len__, __str__)
  Class 9  - custom exceptions (InvalidPreferenceError)
"""

from collections import Counter

from .exceptions import InvalidPreferenceError


class UserPreference:
    """What kind of film this user enjoys.

    There are two ways to build one:

      1. By hand, from the GUI filters:
             UserPreference(genres=["Horror"], min_score=7.0)

      2. From films the user says they liked - the interesting one:
             UserPreference.from_movies([the_shining, alien, the_thing])

    The second way is an ALTERNATIVE CONSTRUCTOR (a @classmethod). It looks at
    the films, counts which genres keep coming up, and builds the profile for
    the user instead of asking them to describe their own taste.
    """

    # ---- static (class) members -------------------------------------------
    # Shared by every UserPreference object, not stored per object.
    SCORE_MIN = 0.0
    SCORE_MAX = 10.0
    TOP_GENRES = 3          # how many favourite genres from_movies() keeps
    SCORE_SLACK = 1.0       # allow films 1 point below the user's average

    def __init__(self, genres=None, ratings=None, min_score=0.0,
                 year_from=1900, year_to=2100, preferred_runtime=None,
                 preferred_year=None, liked_titles=None):
        """Build a taste profile. Every argument is optional."""

        # ---- private instance variables -----------------------------------
        # Two leading underscores make Python rename these behind the scenes
        # to _UserPreference__genres and so on. That is NAME MANGLING: code
        # outside the class cannot reach them by accident.
        self.__genres = set()
        self.__ratings = set()
        self.__min_score = 0.0

        # Assigning through the properties below means the values get checked.
        self.genres = genres or []
        self.ratings = ratings or []
        self.min_score = min_score

        # ---- normal (public) instance variables ---------------------------
        try:
            self.year_from = int(year_from)
            self.year_to = int(year_to)
        except (TypeError, ValueError):
            raise InvalidPreferenceError(
                f"Years must be whole numbers, got {year_from!r} "
                f"and {year_to!r}")
        if self.year_from > self.year_to:
            raise InvalidPreferenceError(
                f"Year range runs backwards: {self.year_from} to {self.year_to}")

        # Roughly how long, and how old, the films this user likes are.
        # None means "no opinion", and the recommender then skips that test.
        self.preferred_runtime = (float(preferred_runtime)
                                  if preferred_runtime else None)
        self.preferred_year = int(preferred_year) if preferred_year else None

        # A LIST, not a set, so we remember the order they were added in and
        # can ask for the most recent one. Duplicates are blocked by add_liked.
        self.liked_titles = list(liked_titles) if liked_titles else []

    # ---- properties: controlled access to the private variables -----------

    @property
    def genres(self):
        """The set of genres this user enjoys."""
        return self.__genres

    @genres.setter
    def genres(self, values):
        """Writing preference.genres = [...] runs this, so we can check it."""
        if isinstance(values, str):
            raise InvalidPreferenceError(
                "genres must be a list of names, not a single string")
        cleaned = {str(value).strip() for value in values if str(value).strip()}
        self.__genres = cleaned

    @property
    def ratings(self):
        """The set of age ratings this user is happy with (R, PG-13, ...)."""
        return self.__ratings

    @ratings.setter
    def ratings(self, values):
        if isinstance(values, str):
            raise InvalidPreferenceError(
                "ratings must be a list of names, not a single string")
        self.__ratings = {str(value).strip() for value in values
                          if str(value).strip()}

    @property
    def min_score(self):
        """The lowest IMDb score this user will accept."""
        return self.__min_score

    @min_score.setter
    def min_score(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise InvalidPreferenceError(
                f"Minimum score must be a number, got {value!r}")
        if not self.SCORE_MIN <= value <= self.SCORE_MAX:
            raise InvalidPreferenceError(
                f"Minimum score must be between {self.SCORE_MIN} and "
                f"{self.SCORE_MAX}, got {value}")
        self.__min_score = value

    # ---- calculated properties (read-only) --------------------------------

    @property
    def is_empty(self):
        """True when the user has not told us anything yet."""
        return (not self.genres and not self.ratings and not self.liked_titles
                and self.min_score == 0.0)

    @property
    def last_liked(self):
        """The title the user added most recently, or None."""
        return self.liked_titles[-1] if self.liked_titles else None

    # ---- using the profile ------------------------------------------------

    def add_liked(self, movie):
        """Remember one film the user says they enjoyed.

        Accepts a Movie object or a plain title string.
        """
        title = movie.name if hasattr(movie, "name") else str(movie)
        if title not in self.liked_titles:
            self.liked_titles.append(title)
        return title

    def remove_liked(self, title):
        """Forget one film. Does nothing if it was never there."""
        if title in self.liked_titles:
            self.liked_titles.remove(title)

    def allows(self, movie):
        """The HARD filters: is this film even eligible to be suggested?

        Genre and runtime are soft - they change the score. These three are
        hard, because suggesting a film the user explicitly ruled out is worse
        than suggesting nothing.
        """
        if not self.year_from <= movie.year <= self.year_to:
            return False
        if movie.score < self.min_score:
            return False
        if self.ratings and movie.rating not in self.ratings:
            return False
        return True

    def likes_genre(self, genre):
        """True if the given genre is one of the user's favourites.

        An empty genre list means "no preference", so everything passes.
        """
        return not self.genres or genre in self.genres

    # ---- dunder methods: operator overloading -----------------------------

    def __contains__(self, movie):
        """Lets us write  if movie in preference:  - meaning "I liked this"."""
        title = movie.name if hasattr(movie, "name") else str(movie)
        return title in self.liked_titles

    def __len__(self):
        """Lets us write len(preference) - how many films were ticked."""
        return len(self.liked_titles)

    def __str__(self):
        """A one-line summary for humans, shown in the GUI."""
        if self.is_empty:
            return "No preferences set yet"
        parts = []
        if self.genres:
            parts.append("genres: " + ", ".join(sorted(self.genres)))
        if self.ratings:
            parts.append("ratings: " + ", ".join(sorted(self.ratings)))
        if self.min_score > 0:
            parts.append(f"IMDb {self.min_score:.1f}+")
        if self.year_from > 1900 or self.year_to < 2100:
            parts.append(f"{self.year_from}-{self.year_to}")
        if self.preferred_runtime:
            parts.append(f"around {self.preferred_runtime:.0f} min")
        if self.liked_titles:
            parts.append(f"{len(self.liked_titles)} films ticked")
        return " | ".join(parts)

    def __repr__(self):
        return (f"UserPreference(genres={sorted(self.genres)}, "
                f"liked={len(self.liked_titles)})")

    # ---- the alternative constructor --------------------------------------

    @classmethod
    def from_movies(cls, movies, top_genres=None, use_ratings=False):
        """Work out a taste profile from the films the user ticked.

        A @classmethod is a second way of building an object. `cls` is the
        class itself, so the last line really means UserPreference(...).

        What it does, in plain English:
          * count the genres and keep the most common few
          * take the average IMDb score and allow one point below it
          * take the average runtime and release year as "what this user likes"
        """
        movies = list(movies)
        if not movies:
            return cls()

        top_genres = top_genres or cls.TOP_GENRES

        # Counter is a dictionary that counts things for us.
        counts = Counter(movie.genre_group for movie in movies)
        favourite = [genre for genre, _ in counts.most_common(top_genres)]

        scores = [movie.score for movie in movies if movie.score > 0]
        average_score = sum(scores) / len(scores) if scores else 0.0
        floor = max(cls.SCORE_MIN, average_score - cls.SCORE_SLACK)

        runtimes = [movie.runtime for movie in movies if movie.runtime > 0]
        average_runtime = sum(runtimes) / len(runtimes) if runtimes else None

        years = [movie.year for movie in movies]
        average_year = round(sum(years) / len(years))

        return cls(
            genres=favourite,
            # Age rating is only copied across if the user asks for it. Liking
            # three R-rated films does not mean you refuse to watch PG-13.
            ratings=[movie.rating for movie in movies] if use_ratings else [],
            min_score=round(floor, 1),
            preferred_runtime=average_runtime,
            preferred_year=average_year,
            liked_titles=[movie.name for movie in movies],
        )
