"""The Movie class - one row of the dataset becomes one Movie object.

Syllabus topics demonstrated here:
  Class 2 - classes, objects, constructors, instance variables
  Class 3 - encapsulation, private attributes, name mangling, static members
  Class 5 - operator overloading with dunder methods
"""

from .exceptions import InvalidBudgetError, InvalidGrossError


class Movie:
    """A single movie from the dataset."""

    # ---- static (class) members -------------------------------------------
    # These belong to the CLASS, not to any one object. Every Movie shares them.
    count = 0                       # how many Movie objects have been created
    HIT_RATIO = 2.0                 # gross >= 2x budget is counted as a Hit

    def __init__(self, name, year, genre, rating, budget, gross,
                 score=0.0, votes=0, runtime=0.0,
                 director="", star="", company="", month="", genre_group=""):
        """The constructor. Runs automatically when you write Movie(...)."""

        # ---- normal (public) instance variables ---------------------------
        self.name = str(name)
        self.year = int(year)
        self.genre = str(genre)
        # The genre used for charts and the model. Rare genres are grouped
        # together as "Other" by the loader; if not given we just reuse genre.
        self.genre_group = str(genre_group) if genre_group else str(genre)
        self.rating = str(rating)
        self.score = float(score)
        self.votes = int(votes)
        self.runtime = float(runtime)
        self.director = str(director)
        self.star = str(star)
        self.company = str(company)
        self.month = str(month)

        # ---- private instance variables -----------------------------------
        # Two leading underscores make Python secretly rename these to
        # _Movie__budget and _Movie__gross. That is called NAME MANGLING.
        # It stops code outside the class from changing them by accident.
        self.__budget = 0.0
        self.__gross = 0.0

        # We assign through the properties below, so the values get checked.
        self.budget = budget
        self.gross = gross

        Movie.count += 1            # update the shared class variable

    # ---- properties: controlled access to the private variables -----------

    @property
    def budget(self):
        """Reading movie.budget actually runs this method."""
        return self.__budget

    @budget.setter
    def budget(self, value):
        """Writing movie.budget = x runs this method, so we can validate x."""
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise InvalidBudgetError(f"Budget must be a number, got {value!r}")
        if value < 0:
            raise InvalidBudgetError(f"Budget cannot be negative, got {value}")
        self.__budget = value

    @property
    def gross(self):
        return self.__gross

    @gross.setter
    def gross(self, value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            raise InvalidGrossError(f"Gross must be a number, got {value!r}")
        if value < 0:
            raise InvalidGrossError(f"Gross cannot be negative, got {value}")
        self.__gross = value

    # ---- calculated properties (read-only) --------------------------------

    @property
    def profit(self):
        """Money made after paying back the budget."""
        return self.gross - self.budget

    @property
    def roi(self):
        """Return On Investment: how many dollars came back per dollar spent."""
        if self.budget == 0:
            return 0.0
        return self.gross / self.budget

    @property
    def verdict(self):
        """A simple label describing how the movie performed."""
        if self.roi >= Movie.HIT_RATIO:
            return "Hit"
        if self.roi >= 1.0:
            return "Break-even"
        return "Flop"

    # ---- dunder methods: operator overloading -----------------------------

    def __str__(self):
        """Used by print(movie) - meant for humans."""
        return f"{self.name} ({self.year}) - {self.genre}, ${self.gross:,.0f} gross"

    def __repr__(self):
        """Used in lists and the shell - meant for programmers."""
        return f"Movie({self.name!r}, {self.year})"

    def __eq__(self, other):
        """Lets us write  movie_a == movie_b."""
        if not isinstance(other, Movie):
            return NotImplemented
        return self.name == other.name and self.year == other.year

    def __hash__(self):
        """Needed because we defined __eq__; lets Movies go in a set or dict."""
        return hash((self.name, self.year))

    def __lt__(self, other):
        """Lets us write movie_a < movie_b, and makes sorted(movies) work."""
        if not isinstance(other, Movie):
            return NotImplemented
        return self.gross < other.gross

    def __gt__(self, other):
        """Lets us write movie_a > movie_b (used by the Compare tab)."""
        if not isinstance(other, Movie):
            return NotImplemented
        return self.gross > other.gross

    # ---- helpers ----------------------------------------------------------

    def to_dict(self):
        """Plain dictionary version - handy for saving to CSV or JSON."""
        return {
            "name": self.name, "year": self.year, "genre": self.genre,
            "genre_group": self.genre_group,
            "rating": self.rating, "month": self.month,
            "runtime": self.runtime, "score": self.score, "votes": self.votes,
            "director": self.director, "star": self.star, "company": self.company,
            "budget": self.budget, "gross": self.gross,
            "profit": self.profit, "roi": round(self.roi, 2),
            "verdict": self.verdict,
        }

    @classmethod
    def from_row(cls, row):
        """Build a Movie from one row of a cleaned pandas DataFrame.

        A classmethod is an alternative constructor: Movie.from_row(row).
        """
        return cls(
            name=row["name"], year=row["year"], genre=row["genre"],
            rating=row["rating"], budget=row["budget"], gross=row["gross"],
            score=row.get("score", 0.0), votes=row.get("votes", 0),
            runtime=row.get("runtime", 0.0), director=row.get("director", ""),
            star=row.get("star", ""), company=row.get("company", ""),
            month=row.get("month", ""), genre_group=row.get("genre_group", ""),
        )
