"""Tests for MovieCollection, the analyzers, and the export context manager."""

import json
import tempfile
import unittest
from pathlib import Path

from cinestat import (MovieCollection, MovieNotFoundError,
                      GenreAnalyzer, TrendAnalyzer, FinancialAnalyzer,
                      BaseAnalyzer)
from cinestat.utils import ExportSession, money
from tests.helpers import make_collection, make_movie, GENRES


class TestCollectionBehavesLikeAList(unittest.TestCase):

    def setUp(self):
        self.collection = make_collection(60)

    def test_len(self):
        self.assertEqual(len(self.collection), 60)

    def test_iteration_visits_every_movie(self):
        self.assertEqual(sum(1 for _ in self.collection), 60)

    def test_indexing(self):
        self.assertEqual(self.collection[0].name, "Film 0")

    def test_slicing_returns_a_collection(self):
        chunk = self.collection[:5]
        self.assertIsInstance(chunk, MovieCollection)
        self.assertEqual(len(chunk), 5)

    def test_contains(self):
        self.assertIn(self.collection[3], self.collection)

    def test_adding_two_collections(self):
        """Operator overloading: collection_a + collection_b."""
        combined = make_collection(10) + make_collection(5)
        self.assertEqual(len(combined), 15)

    def test_add_rejects_non_movies(self):
        with self.assertRaises(TypeError):
            MovieCollection().add("not a movie")


class TestCollectionSearching(unittest.TestCase):

    def setUp(self):
        self.collection = make_collection(60)

    def test_find_is_case_insensitive(self):
        self.assertEqual(self.collection.find("film 7").name, "Film 7")

    def test_find_raises_when_missing(self):
        with self.assertRaises(MovieNotFoundError):
            self.collection.find("Nonexistent Movie")

    def test_filter_by_returns_only_matching_genre(self):
        """filter_by is a generator - Class 11."""
        results = list(self.collection.filter_by(genre="Horror"))
        self.assertTrue(results, "expected at least one horror film")
        self.assertTrue(all(m.genre == "Horror" for m in results))

    def test_filter_by_accepts_two_criteria(self):
        results = list(self.collection.filter_by(genre="Action", rating="R"))
        self.assertTrue(all(m.genre == "Action" and m.rating == "R"
                            for m in results))

    def test_filter_by_is_a_generator(self):
        import types
        self.assertIsInstance(self.collection.filter_by(genre="Action"),
                              types.GeneratorType)

    def test_search_matches_part_of_a_title(self):
        self.assertTrue(list(self.collection.search("Film 1")))

    def test_year_range(self):
        results = list(self.collection.in_year_range(1995, 2000))
        self.assertTrue(all(1995 <= m.year <= 2000 for m in results))

    def test_top_by_gross_is_sorted_highest_first(self):
        top = self.collection.top_by("gross", 3)
        grosses = [m.gross for m in top]
        self.assertEqual(len(top), 3)
        self.assertEqual(grosses, sorted(grosses, reverse=True))

    def test_genres_lists_each_genre_once(self):
        self.assertEqual(self.collection.genres(), sorted(GENRES))

    def test_year_bounds(self):
        low, high = self.collection.year_bounds()
        self.assertLessEqual(low, high)

    def test_empty_collection_year_bounds(self):
        self.assertEqual(MovieCollection().year_bounds(), (0, 0))

    def test_to_dataframe_has_one_row_per_movie(self):
        self.assertEqual(len(self.collection.to_dataframe()), 60)


class TestAnalyzers(unittest.TestCase):
    """Class 4 and 5: abstraction and polymorphism."""

    def setUp(self):
        self.collection = make_collection(60)

    def test_base_analyzer_cannot_be_created(self):
        """It is abstract, so Python refuses to build one."""
        with self.assertRaises(TypeError):
            BaseAnalyzer(self.collection)

    def test_every_analyzer_works_the_same_way(self):
        """POLYMORPHISM: one loop, three different calculations."""
        for analyzer_class in (GenreAnalyzer, TrendAnalyzer, FinancialAnalyzer):
            analyzer = analyzer_class(self.collection)
            results = analyzer.run()
            self.assertFalse(results.empty,
                             f"{analyzer_class.__name__} returned nothing")
            self.assertTrue(analyzer.summary())

    def test_genre_analyzer_has_a_row_per_genre(self):
        results = GenreAnalyzer(self.collection).run()
        self.assertEqual(sorted(results.index), sorted(GENRES))

    def test_financial_analyzer_inherits_from_both_parents(self):
        """MULTIPLE INHERITANCE: it is an analyzer AND it can export."""
        from cinestat.analyzers import ExportMixin
        self.assertTrue(issubclass(FinancialAnalyzer, BaseAnalyzer))
        self.assertTrue(issubclass(FinancialAnalyzer, ExportMixin))

    def test_financial_analyzer_can_export(self):
        analyzer = FinancialAnalyzer(self.collection)
        analyzer.run()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "financial.csv"
            analyzer.export(path)
            self.assertTrue(path.exists())
            self.assertIn("rating", path.read_text())


class TestExportSession(unittest.TestCase):
    """Class 9: the context manager."""

    def setUp(self):
        self.rows = [m.to_dict() for m in make_collection(5)]

    def test_writes_csv(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "out.csv"
            with ExportSession(path) as export:
                written = export.write(self.rows)
            self.assertEqual(written, 5)
            self.assertEqual(len(path.read_text().strip().splitlines()), 6)

    def test_writes_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "out.json"
            with ExportSession(path) as export:
                export.write(self.rows)
            self.assertEqual(len(json.loads(path.read_text())), 5)

    def test_creates_missing_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "deep" / "nested" / "out.csv"
            with ExportSession(path) as export:
                export.write(self.rows)
            self.assertTrue(path.exists())

    def test_file_is_closed_even_if_an_error_happens(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "out.csv"
            session = ExportSession(path)
            with self.assertRaises(ValueError):
                with session as export:
                    export.write(self.rows)
                    raise ValueError("something went wrong")
            self.assertTrue(session._file.closed)


class TestMoneyFormatting(unittest.TestCase):

    def test_billions(self):
        self.assertEqual(money(2_800_000_000), "$2.80B")

    def test_millions(self):
        self.assertEqual(money(138_400_000), "$138.4M")

    def test_negative(self):
        self.assertEqual(money(-5_000_000), "-$5.0M")


if __name__ == "__main__":
    unittest.main()
