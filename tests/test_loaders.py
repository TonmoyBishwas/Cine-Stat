"""Tests for the loaders, and especially TMDBLoader.

TMDBLoader exists so the project can use the very large Kaggle dataset
(millions of rows) instead of the 7,668-row movies.csv. These tests build a
small TMDB-shaped file in a temporary folder, so they need no download and
finish in milliseconds.
"""

import csv
import tempfile
import unittest
from pathlib import Path

from cinestat import (DataLoader, CSVLoader, JSONLoader, TMDBLoader,
                      MovieCollection, DataFileError)


TMDB_COLUMNS = ["id", "title", "vote_average", "vote_count", "status",
                "release_date", "revenue", "runtime", "adult", "budget",
                "imdb_id", "original_language", "overview", "popularity",
                "genres", "production_companies"]


def a_tmdb_row(index, **overrides):
    """One row shaped exactly like the Kaggle TMDB export."""
    row = {
        "id": index,
        "title": f"Sample Film {index}",
        "vote_average": 7.5,
        "vote_count": 5000,
        "status": "Released",
        "release_date": "1999-07-16",
        "revenue": 200_000_000,
        "runtime": 120,
        "adult": False,
        "budget": 50_000_000,
        "imdb_id": f"tt{index}",
        "original_language": "en",
        "overview": "Some description.",
        "popularity": 12.5,
        "genres": "Drama, Crime",
        "production_companies": "Warner Bros., Legendary",
    }
    row.update(overrides)
    return row


def write_tmdb_file(folder, rows):
    path = Path(folder) / "tmdb.csv"
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TMDB_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return path


class TestLoaderHierarchy(unittest.TestCase):
    """Class 4 and 5: three subclasses, one abstract parent."""

    def test_the_abstract_loader_cannot_be_created(self):
        with self.assertRaises(TypeError):
            DataLoader("data/movies.csv")

    def test_every_loader_is_a_dataloader(self):
        for loader_class in (CSVLoader, JSONLoader, TMDBLoader):
            with self.subTest(loader=loader_class.__name__):
                self.assertTrue(issubclass(loader_class, DataLoader))

    def test_a_missing_file_raises_our_own_exception(self):
        for loader_class in (CSVLoader, JSONLoader, TMDBLoader):
            with self.subTest(loader=loader_class.__name__):
                with self.assertRaises(DataFileError):
                    loader_class("no/such/file.csv")


class TestTheLoaderFactory(unittest.TestCase):
    """DataLoader.for_file() picks the subclass by reading the header row."""

    DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "movies.csv"

    def test_it_picks_csvloader_for_our_own_dataset(self):
        if not self.DATA_FILE.exists():
            self.skipTest("data/movies.csv not present")
        self.assertIsInstance(DataLoader.for_file(self.DATA_FILE), CSVLoader)

    def test_it_picks_tmdbloader_for_the_kaggle_export(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, [a_tmdb_row(i) for i in range(3)])
            self.assertIsInstance(DataLoader.for_file(path), TMDBLoader)

    def test_it_picks_jsonloader_by_the_file_extension(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "movies.json"
            path.write_text("[]", encoding="utf-8")
            self.assertIsInstance(DataLoader.for_file(path), JSONLoader)

    def test_a_missing_file_still_raises_our_own_exception(self):
        with self.assertRaises(DataFileError):
            DataLoader.for_file("no/such/file.csv")

    def test_extra_arguments_are_passed_through(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, [a_tmdb_row(i) for i in range(30)])
            loader = DataLoader.for_file(path, max_movies=5)
            self.assertEqual(len(loader.to_collection()), 5)


class TestTMDBLoader(unittest.TestCase):

    def test_it_produces_a_normal_moviecollection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, [a_tmdb_row(i) for i in range(20)])
            collection = TMDBLoader(path).to_collection()

        self.assertIsInstance(collection, MovieCollection)
        self.assertEqual(len(collection), 20)
        movie = collection[0]
        self.assertEqual(movie.name, "Sample Film 0")
        self.assertEqual(movie.year, 1999)
        self.assertEqual(movie.month, "July")
        self.assertEqual(movie.budget, 50_000_000)
        self.assertEqual(movie.gross, 200_000_000)
        self.assertEqual(movie.verdict, "Hit")

    def test_only_the_first_genre_is_kept(self):
        """'Drama, Crime, Thriller' becomes 'Drama', like movies.csv."""
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, [a_tmdb_row(i) for i in range(5)])
            collection = TMDBLoader(path).to_collection()
        self.assertEqual(collection[0].genre, "Drama")
        self.assertEqual(collection[0].company, "Warner Bros.")

    def test_rows_without_money_figures_are_dropped(self):
        """The real file is mostly rows with no budget or no box office."""
        rows = [a_tmdb_row(i) for i in range(10)]
        rows += [a_tmdb_row(100 + i, budget=0) for i in range(10)]
        rows += [a_tmdb_row(200 + i, revenue=0) for i in range(10)]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)
            collection = TMDBLoader(path).to_collection()
        self.assertEqual(len(collection), 10)

    def test_unreleased_and_barely_rated_films_are_dropped(self):
        rows = [a_tmdb_row(i) for i in range(5)]
        rows += [a_tmdb_row(100 + i, status="Post Production") for i in range(5)]
        rows += [a_tmdb_row(200 + i, vote_count=1) for i in range(5)]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)
            collection = TMDBLoader(path).to_collection()
        self.assertEqual(len(collection), 5)

    def test_a_broken_release_date_is_dropped_not_guessed(self):
        rows = [a_tmdb_row(i) for i in range(5)]
        rows += [a_tmdb_row(100, release_date=""),
                 a_tmdb_row(101, release_date="not a date")]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)
            collection = TMDBLoader(path).to_collection()
        self.assertEqual(len(collection), 5)

    def test_reading_in_chunks_gives_the_same_answer_as_reading_at_once(self):
        """The whole point of TMDBLoader: memory stays flat on a huge file."""
        rows = [a_tmdb_row(i) for i in range(500)]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)

            one_go = TMDBLoader(path)
            in_pieces = TMDBLoader(path)
            in_pieces.CHUNK_SIZE = 25          # forces 20 separate chunks

            self.assertEqual(len(one_go.to_collection()),
                             len(in_pieces.to_collection()))

    def test_max_movies_caps_the_result(self):
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, [a_tmdb_row(i) for i in range(300)])
            loader = TMDBLoader(path, max_movies=50)
            loader.CHUNK_SIZE = 20
            self.assertEqual(len(loader.to_collection()), 50)

    def test_a_file_with_no_usable_rows_says_so_clearly(self):
        rows = [a_tmdb_row(i, budget=0, revenue=0) for i in range(10)]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)
            with self.assertRaises(DataFileError) as caught:
                TMDBLoader(path).to_collection()
        self.assertIn("COLUMN_MAP", str(caught.exception))

    def test_the_wrong_kind_of_csv_names_the_columns_it_found(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "wrong.csv"
            path.write_text("apples,pears\n1,2\n", encoding="utf-8")
            with self.assertRaises(DataFileError) as caught:
                TMDBLoader(path).to_collection()
        self.assertIn("apples", str(caught.exception))

    def test_a_file_without_the_optional_columns_still_loads(self):
        """Not every TMDB export carries genres or production companies."""
        columns = [c for c in TMDB_COLUMNS
                   if c not in ("genres", "production_companies")]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "slim.csv"
            with open(path, "w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                for index in range(5):
                    row = a_tmdb_row(index)
                    writer.writerow({c: row[c] for c in columns})
            collection = TMDBLoader(path).to_collection()

        self.assertEqual(len(collection), 5)
        self.assertEqual(collection[0].genre, "Unknown")
        self.assertEqual(collection[0].company, "")

    def test_the_result_works_with_the_rest_of_cinestat(self):
        """Nothing downstream needs changing - that is what COLUMN_MAP buys."""
        from cinestat import GenreAnalyzer, UserPreference, ContentRecommender

        rows = [a_tmdb_row(i, genres="Horror" if i % 2 else "Drama",
                           vote_average=5 + (i % 5),
                           release_date=f"{1990 + i % 20}-06-01")
                for i in range(60)]
        with tempfile.TemporaryDirectory() as folder:
            path = write_tmdb_file(folder, rows)
            collection = TMDBLoader(path).to_collection()

        self.assertTrue(GenreAnalyzer(collection).run() is not None)

        preference = UserPreference.from_movies(list(collection)[:3])
        results = ContentRecommender(collection, preference).recommend(5)
        self.assertTrue(results)
        self.assertTrue(all(r.reasons for r in results))


if __name__ == "__main__":
    unittest.main()
