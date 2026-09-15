"""MovieCollection - an object that holds many Movie objects.

Syllabus topics demonstrated here:
  Class 3  - composition ("a collection HAS-A list of movies")
  Class 5  - operator overloading (__add__, __contains__)
  Class 11 - iterators (__iter__) and generators (filter_by, search)
"""

import pandas as pd

from .movie import Movie
from .exceptions import MovieNotFoundError


class MovieCollection:
    """A container for Movie objects that behaves a lot like a list.

    This is COMPOSITION: a MovieCollection does not *inherit* from Movie,
    it simply *contains* Movie objects.
    """

    def __init__(self, movies=None):
        # One leading underscore = "please treat me as internal".
        self._movies = list(movies) if movies is not None else []

    # ---- making the object behave like a list -----------------------------

    def __len__(self):
        """Lets us write len(collection)."""
        return len(self._movies)

    def __iter__(self):
        """Lets us write  for movie in collection:  -- this is the ITERATOR."""
        return iter(self._movies)

    def __getitem__(self, index):
        """Lets us write collection[0] and collection[:5]."""
        result = self._movies[index]
        # A slice gives back a list, so wrap it up as a collection again.
        if isinstance(index, slice):
            return MovieCollection(result)
        return result

    def __contains__(self, movie):
        """Lets us write  if movie in collection:"""
        return movie in self._movies

    def __add__(self, other):
        """Operator overloading: collection_a + collection_b."""
        if not isinstance(other, MovieCollection):
            return NotImplemented
        return MovieCollection(self._movies + other._movies)

    def __str__(self):
        return f"MovieCollection with {len(self)} movies"

    def __repr__(self):
        return f"MovieCollection({len(self)} movies)"

    # ---- adding and finding -----------------------------------------------

    def add(self, movie):
        """Add one Movie to the collection."""
        if not isinstance(movie, Movie):
            raise TypeError("Only Movie objects can be added")
        self._movies.append(movie)

    def find(self, name):
        """Return the first movie whose name matches exactly (ignoring case).

        Raises MovieNotFoundError if there is no match - see Class 9.
        """
        for movie in self._movies:
            if movie.name.lower() == name.lower():
                return movie
        raise MovieNotFoundError(f"No movie named {name!r} in this collection")

    def names(self):
        """A sorted list of every movie title - used to fill GUI dropdowns."""
        return sorted(movie.name for movie in self._movies)

    # ---- generators: produce results one at a time ------------------------

    def filter_by(self, **criteria):
        """A GENERATOR that yields movies matching every given attribute.

        Example:  collection.filter_by(genre="Horror", rating="R")

        Because this uses `yield` instead of building a list, it does not
        store all the results in memory at once.
        """
        for movie in self._movies:
            if all(getattr(movie, key, None) == value
                   for key, value in criteria.items()):
                yield movie

    def search(self, text):
        """A GENERATOR yielding movies whose title contains `text`."""
        text = text.lower()
        for movie in self._movies:
            if text in movie.name.lower():
                yield movie

    def in_year_range(self, start, end):
        """A GENERATOR yielding movies released between start and end."""
        for movie in self._movies:
            if start <= movie.year <= end:
                yield movie

    # ---- summaries --------------------------------------------------------

    def top_by(self, attribute, n=10):
        """The n movies with the highest value of `attribute`.

        Example: collection.top_by("gross", 5)
        """
        ordered = sorted(self._movies,
                         key=lambda m: getattr(m, attribute),
                         reverse=True)
        return MovieCollection(ordered[:n])

    def genres(self):
        """Every distinct genre present, sorted alphabetically."""
        return sorted({movie.genre for movie in self._movies})

    def ratings(self):
        """Every distinct age rating present, sorted alphabetically."""
        return sorted({movie.rating for movie in self._movies})

    def year_bounds(self):
        """The earliest and latest release year as a (min, max) tuple."""
        if not self._movies:
            return (0, 0)
        years = [movie.year for movie in self._movies]
        return (min(years), max(years))

    def to_dataframe(self):
        """Convert back to a pandas DataFrame for charts and statistics."""
        return pd.DataFrame([movie.to_dict() for movie in self._movies])
