"""Tests for the recommendation engine.

Covers the abstract base class (Class 4), polymorphism across the three
recommenders (Class 5), the generator (Class 11) and the dunder methods.
"""

import inspect
import unittest

from cinestat import (Movie, UserPreference, Recommendation, BaseRecommender,
                      ContentRecommender, SimilarityRecommender,
                      PopularityRecommender)

from tests.helpers import make_movie, make_collection

ALL_RECOMMENDERS = [ContentRecommender, SimilarityRecommender,
                    PopularityRecommender]


class TestRecommendation(unittest.TestCase):
    """The small value object that carries one suggestion around."""

    def setUp(self):
        self.movie = make_movie(name="Alien", year=1979)
        self.recommendation = Recommendation(self.movie, 82.4, ["a reason"])

    def test_the_score_is_shown_as_a_percentage(self):
        self.assertEqual(self.recommendation.match, "82%")

    def test_the_score_is_clamped_to_0_and_100(self):
        self.assertEqual(Recommendation(self.movie, 250, []).score, 100.0)
        self.assertEqual(Recommendation(self.movie, -30, []).score, 0.0)

    def test_less_than_lets_sorted_order_them(self):
        """Class 5: __lt__ is what makes sorted() work."""
        low = Recommendation(self.movie, 10, [])
        high = Recommendation(make_movie(name="Other"), 90, [])
        self.assertLess(low, high)
        self.assertEqual(sorted([high, low])[0], low)

    def test_two_recommendations_for_the_same_film_are_equal(self):
        other = Recommendation(self.movie, 5, ["different reason"])
        self.assertEqual(self.recommendation, other)
        self.assertEqual(len({self.recommendation, other}), 1)

    def test_comparing_with_something_else_is_not_an_error(self):
        self.assertEqual(self.recommendation.__lt__(42), NotImplemented)
        self.assertEqual(self.recommendation.__eq__("Alien"), NotImplemented)

    def test_str_is_readable(self):
        self.assertIn("Alien", str(self.recommendation))
        self.assertIn("82%", str(self.recommendation))

    def test_to_dict_carries_the_film_plus_the_reasons(self):
        row = self.recommendation.to_dict()
        self.assertEqual(row["name"], "Alien")
        self.assertEqual(row["match_score"], 82.4)
        self.assertIn("a reason", row["reasons"])


class TestAbstractBaseClass(unittest.TestCase):
    """Class 4: BaseRecommender is a contract, not something you can build."""

    def test_the_base_class_cannot_be_created(self):
        with self.assertRaises(TypeError):
            BaseRecommender(make_collection(5))

    def test_a_subclass_that_forgets_score_movie_cannot_be_created(self):
        class Forgetful(BaseRecommender):
            pass
        with self.assertRaises(TypeError):
            Forgetful(make_collection(5))

    def test_every_recommender_really_is_a_baserecommender(self):
        for engine_class in ALL_RECOMMENDERS:
            with self.subTest(engine=engine_class.__name__):
                self.assertTrue(issubclass(engine_class, BaseRecommender))

    def test_candidates_is_a_generator(self):
        """Class 11: it yields films one at a time instead of building a list."""
        engine = ContentRecommender(make_collection(10), UserPreference())
        self.assertTrue(inspect.isgenerator(engine.candidates()))


class TestSharedBehaviour(unittest.TestCase):
    """Rules that must hold for all three recommenders - POLYMORPHISM."""

    def setUp(self):
        self.collection = make_collection(60)
        self.liked = list(self.collection)[:3]
        self.preference = UserPreference.from_movies(self.liked)

    def each_engine(self):
        """Build all three the same way. That is the whole point of the ABC."""
        for engine_class in ALL_RECOMMENDERS:
            yield engine_class(self.collection, self.preference)

    def test_every_engine_answers_recommend(self):
        for engine in self.each_engine():
            with self.subTest(engine=engine.title):
                results = engine.recommend(5)
                self.assertLessEqual(len(results), 5)
                self.assertTrue(
                    all(isinstance(r, Recommendation) for r in results))

    def test_results_come_back_best_first(self):
        for engine in self.each_engine():
            with self.subTest(engine=engine.title):
                scores = [r.score for r in engine.recommend(10)]
                self.assertEqual(scores, sorted(scores, reverse=True))

    def test_a_film_the_user_ticked_is_never_suggested(self):
        for engine in self.each_engine():
            with self.subTest(engine=engine.title):
                names = [r.movie.name for r in engine.recommend(50)]
                for movie in self.liked:
                    self.assertNotIn(movie.name, names)

    def test_every_suggestion_comes_with_at_least_one_reason(self):
        for engine in self.each_engine():
            with self.subTest(engine=engine.title):
                for recommendation in engine.recommend(5):
                    self.assertTrue(recommendation.reasons)

    def test_the_hard_filters_are_obeyed(self):
        preference = UserPreference(min_score=7.0, year_from=1995,
                                    year_to=2005)
        # SimilarityRecommender needs a film to compare against; the other
        # two do not. Everything after that is identical for all three.
        for engine_class in ALL_RECOMMENDERS:
            if engine_class is SimilarityRecommender:
                engine = engine_class(self.collection, preference,
                                      seed=self.collection[0])
            else:
                engine = engine_class(self.collection, preference)
            with self.subTest(engine=engine.title):
                for recommendation in engine.recommend(20):
                    movie = recommendation.movie
                    self.assertGreaterEqual(movie.score, 7.0)
                    self.assertTrue(1995 <= movie.year <= 2005)

    def test_an_empty_profile_is_not_thrown_away(self):
        """Regression: UserPreference has __len__, so an untouched profile
        is falsy. `preference or UserPreference()` used to discard it and
        with it the genre and year settings the user had typed in."""
        preference = UserPreference(genres=["Horror"], year_from=1995)
        self.assertEqual(len(preference), 0)          # falsy, but real
        for engine_class in ALL_RECOMMENDERS:
            with self.subTest(engine=engine_class.__name__):
                engine = engine_class(self.collection, preference)
                self.assertIs(engine.preference, preference)

    def test_an_engine_describes_itself(self):
        for engine in self.each_engine():
            with self.subTest(engine=engine.title):
                self.assertIn(engine.title, str(engine))


class TestContentRecommender(unittest.TestCase):

    def setUp(self):
        self.collection = make_collection(60)

    def test_a_favourite_genre_scores_higher_than_a_stranger(self):
        preference = UserPreference(genres=["Horror"])
        engine = ContentRecommender(self.collection, preference)
        horror = make_movie(name="Scary", genre="Horror", score=7.0,
                            runtime=100, year=2000)
        comedy = make_movie(name="Funny", genre="Comedy", score=7.0,
                            runtime=100, year=2000)
        self.assertGreater(engine.score_movie(horror)[0],
                           engine.score_movie(comedy)[0])

    def test_the_genre_is_named_in_the_reasons(self):
        engine = ContentRecommender(self.collection,
                                    UserPreference(genres=["Horror"]))
        _, reasons = engine.score_movie(make_movie(genre="Horror"))
        self.assertTrue(any("Horror" in reason for reason in reasons))

    def test_a_better_reviewed_film_scores_higher(self):
        engine = ContentRecommender(self.collection, UserPreference())
        good = make_movie(name="Good", score=9.0)
        poor = make_movie(name="Poor", score=3.0)
        self.assertGreater(engine.score_movie(good)[0],
                           engine.score_movie(poor)[0])

    def test_no_genre_preference_does_not_punish_anybody(self):
        engine = ContentRecommender(self.collection, UserPreference())
        self.assertGreater(engine.score_movie(make_movie())[0], 0)

    def test_suggestions_lean_towards_the_liked_genre(self):
        horror = [m for m in self.collection if m.genre == "Horror"][:3]
        preference = UserPreference.from_movies(horror)
        results = ContentRecommender(self.collection, preference).recommend(5)
        self.assertTrue(
            all(r.movie.genre in preference.genres for r in results))


class TestSimilarityRecommender(unittest.TestCase):

    def setUp(self):
        self.collection = make_collection(60)
        self.seed = self.collection[0]

    def test_the_seed_defaults_to_the_last_film_ticked(self):
        preference = UserPreference()
        preference.add_liked(self.seed)
        engine = SimilarityRecommender(self.collection, preference)
        self.assertEqual(engine.seed, self.seed)

    def test_with_no_seed_at_all_nothing_is_suggested(self):
        engine = SimilarityRecommender(self.collection, UserPreference())
        self.assertIsNone(engine.seed)
        self.assertEqual(engine.recommend(5), [])

    def test_a_film_in_the_same_genre_scores_higher(self):
        engine = SimilarityRecommender(self.collection, UserPreference(),
                                       seed=self.seed)
        same = make_movie(name="Same", genre=self.seed.genre,
                          rating=self.seed.rating, score=self.seed.score,
                          runtime=self.seed.runtime, year=self.seed.year)
        different = make_movie(name="Different", genre="Comedy",
                               rating="G", score=2.0, runtime=200, year=1950)
        self.assertGreater(engine.score_movie(same)[0],
                           engine.score_movie(different)[0])

    def test_an_explicit_seed_beats_the_last_ticked_film(self):
        preference = UserPreference()
        preference.add_liked(self.collection[1])
        engine = SimilarityRecommender(self.collection, preference,
                                       seed=self.seed)
        self.assertEqual(engine.seed, self.seed)


class TestPopularityRecommender(unittest.TestCase):
    """The honest baseline, kept for the same reason as budget_only_r2()."""

    def setUp(self):
        self.collection = make_collection(60)

    def test_it_ignores_the_genre_preference_completely(self):
        movie = make_movie(genre="Comedy", score=8.0, votes=100_000)
        picky = PopularityRecommender(self.collection,
                                      UserPreference(genres=["Horror"]))
        open_minded = PopularityRecommender(self.collection, UserPreference())
        self.assertEqual(picky.score_movie(movie)[0],
                         open_minded.score_movie(movie)[0])

    def test_more_voters_means_a_higher_score(self):
        engine = PopularityRecommender(self.collection, UserPreference())
        famous = make_movie(name="Famous", score=8.0, votes=1_000_000)
        obscure = make_movie(name="Obscure", score=8.0, votes=10)
        self.assertGreater(engine.score_movie(famous)[0],
                           engine.score_movie(obscure)[0])

    def test_it_says_out_loud_that_it_ignored_your_taste(self):
        engine = PopularityRecommender(self.collection, UserPreference())
        _, reasons = engine.score_movie(make_movie())
        self.assertTrue(any("not on your taste" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
