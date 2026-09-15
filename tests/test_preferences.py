"""Tests for UserPreference - the taste profile.

Covers the encapsulation rules (Class 3), the custom exception (Class 9),
the dunder methods (Class 5) and the alternative constructor.
"""

import unittest

from cinestat import UserPreference, InvalidPreferenceError, MovieDataError

from tests.helpers import make_movie, make_collection


class TestPreferenceBasics(unittest.TestCase):

    def test_a_new_preference_is_empty(self):
        preference = UserPreference()
        self.assertTrue(preference.is_empty)
        self.assertEqual(len(preference), 0)
        self.assertEqual(str(preference), "No preferences set yet")

    def test_genres_are_stored_as_a_set_of_clean_names(self):
        preference = UserPreference(genres=[" Horror ", "Action", "Horror"])
        self.assertEqual(preference.genres, {"Horror", "Action"})

    def test_last_liked_is_none_until_something_is_added(self):
        self.assertIsNone(UserPreference().last_liked)


class TestPreferenceValidation(unittest.TestCase):
    """Class 9: bad values raise our own exception, not a random one."""

    def test_a_bare_string_is_rejected_for_genres(self):
        # "Horror" would silently become {'H','o','r'...} without this guard.
        with self.assertRaises(InvalidPreferenceError):
            UserPreference(genres="Horror")

    def test_a_bare_string_is_rejected_for_ratings(self):
        with self.assertRaises(InvalidPreferenceError):
            UserPreference(ratings="R")

    def test_min_score_must_be_on_the_imdb_scale(self):
        for bad_value in (-1, 10.5, 99):
            with self.subTest(value=bad_value):
                with self.assertRaises(InvalidPreferenceError):
                    UserPreference(min_score=bad_value)

    def test_min_score_must_be_a_number(self):
        with self.assertRaises(InvalidPreferenceError):
            UserPreference(min_score="very good")

    def test_years_that_are_not_numbers_are_rejected(self):
        with self.assertRaises(InvalidPreferenceError):
            UserPreference(year_from="the eighties")

    def test_a_backwards_year_range_is_rejected(self):
        with self.assertRaises(InvalidPreferenceError):
            UserPreference(year_from=2010, year_to=1990)

    def test_our_exception_is_catchable_as_moviedataerror(self):
        """Every CineStat error shares one base class - see exceptions.py."""
        with self.assertRaises(MovieDataError):
            UserPreference(min_score=50)

    def test_the_private_attribute_is_name_mangled(self):
        """Class 3: __genres really is renamed behind the scenes."""
        preference = UserPreference(genres=["Horror"])
        self.assertFalse(hasattr(preference, "__genres"))
        self.assertEqual(preference._UserPreference__genres, {"Horror"})


class TestLikedFilms(unittest.TestCase):

    def setUp(self):
        self.preference = UserPreference()
        self.movie = make_movie(name="Alien", year=1979)

    def test_adding_a_film_records_its_title(self):
        self.preference.add_liked(self.movie)
        self.assertEqual(self.preference.liked_titles, ["Alien"])
        self.assertEqual(self.preference.last_liked, "Alien")

    def test_the_same_film_is_never_added_twice(self):
        self.preference.add_liked(self.movie)
        self.preference.add_liked(self.movie)
        self.assertEqual(len(self.preference), 1)

    def test_in_keyword_works_on_a_preference(self):
        """Class 5: __contains__ lets us write  if movie in preference."""
        self.assertNotIn(self.movie, self.preference)
        self.preference.add_liked(self.movie)
        self.assertIn(self.movie, self.preference)
        self.assertIn("Alien", self.preference)

    def test_removing_a_film_that_was_never_there_is_harmless(self):
        self.preference.remove_liked("Nothing")
        self.assertEqual(len(self.preference), 0)


class TestHardFilters(unittest.TestCase):
    """allows() decides which films are eligible at all."""

    def test_year_range_is_enforced(self):
        preference = UserPreference(year_from=1990, year_to=2000)
        self.assertTrue(preference.allows(make_movie(year=1995)))
        self.assertFalse(preference.allows(make_movie(year=1985)))
        self.assertFalse(preference.allows(make_movie(year=2005)))

    def test_minimum_score_is_enforced(self):
        preference = UserPreference(min_score=7.0)
        self.assertTrue(preference.allows(make_movie(score=8.0)))
        self.assertFalse(preference.allows(make_movie(score=6.9)))

    def test_ratings_are_enforced_only_when_given(self):
        self.assertTrue(UserPreference().allows(make_movie(rating="R")))
        picky = UserPreference(ratings=["PG"])
        self.assertFalse(picky.allows(make_movie(rating="R")))

    def test_no_genre_preference_means_every_genre_passes(self):
        self.assertTrue(UserPreference().likes_genre("Anything"))


class TestFromMovies(unittest.TestCase):
    """The @classmethod that builds a profile out of the films ticked."""

    def setUp(self):
        self.collection = make_collection(30)

    def test_an_empty_list_gives_an_empty_preference(self):
        self.assertTrue(UserPreference.from_movies([]).is_empty)

    def test_the_most_common_genres_are_kept(self):
        horror = [m for m in self.collection if m.genre == "Horror"][:4]
        preference = UserPreference.from_movies(horror)
        self.assertIn("Horror", preference.genres)

    def test_only_the_top_few_genres_are_kept(self):
        preference = UserPreference.from_movies(self.collection)
        self.assertLessEqual(len(preference.genres),
                             UserPreference.TOP_GENRES)

    def test_the_score_floor_sits_just_below_the_average(self):
        movies = [make_movie(name="A", score=8.0),
                  make_movie(name="B", score=8.0)]
        preference = UserPreference.from_movies(movies)
        self.assertAlmostEqual(preference.min_score, 7.0)

    def test_the_floor_never_goes_below_zero(self):
        preference = UserPreference.from_movies([make_movie(score=0.5)])
        self.assertGreaterEqual(preference.min_score, 0.0)

    def test_runtime_and_era_are_averaged(self):
        movies = [make_movie(name="A", year=1990, runtime=100),
                  make_movie(name="B", year=2000, runtime=140)]
        preference = UserPreference.from_movies(movies)
        self.assertAlmostEqual(preference.preferred_runtime, 120.0)
        self.assertEqual(preference.preferred_year, 1995)

    def test_the_ticked_titles_are_remembered(self):
        movies = list(self.collection)[:3]
        preference = UserPreference.from_movies(movies)
        self.assertEqual(preference.liked_titles, [m.name for m in movies])

    def test_age_rating_is_not_copied_across_by_default(self):
        """Liking three R films does not mean you refuse PG-13."""
        movies = [make_movie(name="A", rating="R"),
                  make_movie(name="B", rating="R")]
        self.assertEqual(UserPreference.from_movies(movies).ratings, set())
        self.assertEqual(
            UserPreference.from_movies(movies, use_ratings=True).ratings, {"R"})

    def test_str_lists_what_was_learned(self):
        text = str(UserPreference.from_movies(list(self.collection)[:3]))
        self.assertIn("genres:", text)
        self.assertIn("3 films ticked", text)


if __name__ == "__main__":
    unittest.main()
