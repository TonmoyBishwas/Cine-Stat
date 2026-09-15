"""Shared test data so each test file does not repeat itself."""

from cinestat import Movie, MovieCollection

GENRES = ["Action", "Comedy", "Horror"]
RATINGS = ["R", "PG-13"]
MONTHS = ["July", "December"]


def make_movie(name="Test Film", year=2000, genre="Action", rating="R",
               budget=1_000_000, gross=3_000_000, **extra):
    """Build one Movie with sensible defaults, overriding only what we need."""
    return Movie(name=name, year=year, genre=genre, rating=rating,
                 budget=budget, gross=gross, **extra)


def make_collection(size=60):
    """Build a small, predictable collection for tests.

    Gross is always 3x the budget, so every film is a 'Hit'.
    """
    collection = MovieCollection()
    for i in range(size):
        budget = 1_000_000 * (i + 1)
        collection.add(Movie(
            name=f"Film {i}",
            year=1990 + (i % 20),
            genre=GENRES[i % len(GENRES)],
            rating=RATINGS[i % len(RATINGS)],
            budget=budget,
            gross=budget * 3,
            runtime=90 + (i % 40),
            score=5 + (i % 5),
            votes=1000 * i,
            month=MONTHS[i % len(MONTHS)],
        ))
    return collection
