"""Tests for the Movie class (Syllabus Class 10: unittest)."""

import unittest

from cinestat import Movie, InvalidBudgetError
from cinestat.exceptions import InvalidGrossError
from tests.helpers import make_movie


class TestMovieBasics(unittest.TestCase):

    def test_constructor_stores_values(self):
        movie = make_movie(name="Alien", year=1979, genre="Horror")
        self.assertEqual(movie.name, "Alien")
        self.assertEqual(movie.year, 1979)
        self.assertEqual(movie.genre, "Horror")

    def test_genre_group_defaults_to_genre(self):
        self.assertEqual(make_movie(genre="Horror").genre_group, "Horror")

    def test_genre_group_can_be_overridden(self):
        movie = make_movie(genre="Western", genre_group="Other")
        self.assertEqual(movie.genre, "Western")
        self.assertEqual(movie.genre_group, "Other")


class TestMovieValidation(unittest.TestCase):
    """The private __budget is why these checks can be trusted."""

    def test_negative_budget_is_rejected(self):
        with self.assertRaises(InvalidBudgetError):
            make_movie(budget=-5)

    def test_non_numeric_budget_is_rejected(self):
        with self.assertRaises(InvalidBudgetError):
            make_movie(budget="lots of money")

    def test_negative_gross_is_rejected(self):
        with self.assertRaises(InvalidGrossError):
            make_movie(gross=-1)

    def test_budget_cannot_be_set_to_a_negative_later(self):
        movie = make_movie()
        with self.assertRaises(InvalidBudgetError):
            movie.budget = -100

    def test_name_mangling_hides_the_real_attribute(self):
        """__budget is stored as _Movie__budget, not as 'budget'."""
        movie = make_movie(budget=500)
        self.assertIn("_Movie__budget", vars(movie))
        self.assertNotIn("budget", vars(movie))


class TestMovieCalculations(unittest.TestCase):

    def test_profit(self):
        self.assertEqual(make_movie(budget=100, gross=250).profit, 150)

    def test_profit_can_be_negative(self):
        self.assertEqual(make_movie(budget=300, gross=100).profit, -200)

    def test_roi(self):
        self.assertAlmostEqual(make_movie(budget=100, gross=250).roi, 2.5)

    def test_verdict_hit(self):
        self.assertEqual(make_movie(budget=100, gross=300).verdict, "Hit")

    def test_verdict_break_even(self):
        self.assertEqual(make_movie(budget=100, gross=150).verdict, "Break-even")

    def test_verdict_flop(self):
        self.assertEqual(make_movie(budget=100, gross=50).verdict, "Flop")


class TestMovieOperators(unittest.TestCase):
    """Class 5: operator overloading."""

    def test_less_than_compares_gross(self):
        small = make_movie(name="Small", gross=100)
        big = make_movie(name="Big", gross=900)
        self.assertLess(small, big)

    def test_greater_than_compares_gross(self):
        small = make_movie(name="Small", gross=100)
        big = make_movie(name="Big", gross=900)
        self.assertGreater(big, small)

    def test_sorting_uses_gross(self):
        movies = [make_movie(name="B", gross=500),
                  make_movie(name="A", gross=100),
                  make_movie(name="C", gross=900)]
        self.assertEqual([m.name for m in sorted(movies)], ["A", "B", "C"])

    def test_equality_uses_name_and_year(self):
        # Same title and year, very different money -> still the same film.
        a = make_movie(name="Dune", year=2021, gross=100)
        b = make_movie(name="Dune", year=2021, gross=999)
        self.assertEqual(a, b)

    def test_different_year_is_a_different_movie(self):
        self.assertNotEqual(make_movie(name="Dune", year=1984),
                            make_movie(name="Dune", year=2021))

    def test_movies_can_go_in_a_set(self):
        """Works because we defined __hash__ alongside __eq__."""
        movies = {make_movie(name="Dune", year=2021),
                  make_movie(name="Dune", year=2021)}
        self.assertEqual(len(movies), 1)

    def test_str_is_readable(self):
        text = str(make_movie(name="Alien", year=1979))
        self.assertIn("Alien", text)
        self.assertIn("1979", text)


class TestMovieHelpers(unittest.TestCase):

    def test_to_dict_contains_calculated_fields(self):
        data = make_movie(budget=100, gross=300).to_dict()
        self.assertEqual(data["profit"], 200)
        self.assertEqual(data["verdict"], "Hit")

    def test_count_increases_when_movies_are_created(self):
        """Class 3: a static (class) member shared by every object."""
        before = Movie.count
        make_movie()
        make_movie()
        self.assertEqual(Movie.count, before + 2)


if __name__ == "__main__":
    unittest.main()
