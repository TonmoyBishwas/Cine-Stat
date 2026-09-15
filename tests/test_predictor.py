"""Tests for SuccessPredictor and the data loaders."""

import unittest
from pathlib import Path

from cinestat import (SuccessPredictor, CSVLoader, JSONLoader, DataLoader,
                      ModelNotTrainedError, InvalidBudgetError, DataFileError)
from tests.helpers import make_collection

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "movies.csv"


class TestPredictorBeforeTraining(unittest.TestCase):

    def setUp(self):
        self.predictor = SuccessPredictor(make_collection(60))

    def test_predict_before_train_raises(self):
        with self.assertRaises(ModelNotTrainedError):
            self.predictor.predict(1_000_000, "Action", "R", 120, 2020, "July")

    def test_coefficients_before_train_raises(self):
        with self.assertRaises(ModelNotTrainedError):
            self.predictor.top_coefficients()

    def test_is_trained_starts_false(self):
        self.assertFalse(self.predictor.is_trained)


class TestPredictorAfterTraining(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.predictor = SuccessPredictor(make_collection(120))
        cls.predictor.train()

    def test_training_sets_the_flag(self):
        self.assertTrue(self.predictor.is_trained)

    def test_r2_is_a_sensible_number(self):
        self.assertGreaterEqual(self.predictor.r2, -1.0)
        self.assertLessEqual(self.predictor.r2, 1.0)

    def test_prediction_has_all_expected_keys(self):
        result = self.predictor.predict(1_000_000, "Action", "R", 120, 2020, "July")
        for key in ("gross", "profit", "roi", "verdict", "r2", "mae"):
            self.assertIn(key, result)

    def test_profit_equals_gross_minus_budget(self):
        result = self.predictor.predict(2_000_000, "Comedy", "R", 100, 2015, "July")
        self.assertAlmostEqual(result["profit"], result["gross"] - 2_000_000, places=2)

    def test_gross_is_never_negative(self):
        result = self.predictor.predict(1, "Horror", "R", 80, 1990, "December")
        self.assertGreaterEqual(result["gross"], 0)

    def test_verdict_is_one_of_three_labels(self):
        result = self.predictor.predict(5_000_000, "Horror", "R", 95, 2010, "December")
        self.assertIn(result["verdict"], ("Hit", "Break-even", "Flop"))

    def test_bigger_budget_predicts_bigger_gross(self):
        """Sanity check: the model should have learned budget matters."""
        small = self.predictor.predict(1_000_000, "Action", "R", 120, 2010, "July")
        large = self.predictor.predict(90_000_000, "Action", "R", 120, 2010, "July")
        self.assertGreater(large["gross"], small["gross"])

    def test_negative_budget_raises(self):
        with self.assertRaises(InvalidBudgetError):
            self.predictor.predict(-100, "Action", "R", 120, 2020, "July")

    def test_zero_budget_raises(self):
        with self.assertRaises(InvalidBudgetError):
            self.predictor.predict(0, "Action", "R", 120, 2020, "July")

    def test_text_budget_raises(self):
        with self.assertRaises(InvalidBudgetError):
            self.predictor.predict("fifty million", "Action", "R", 120, 2020, "July")

    def test_unknown_genre_does_not_crash(self):
        """A genre the model never saw becomes all-zero columns, not an error."""
        result = self.predictor.predict(1_000_000, "Documentary", "R", 120, 2020, "July")
        self.assertGreaterEqual(result["gross"], 0)

    def test_options_lists_twelve_months(self):
        self.assertEqual(len(self.predictor.options()["months"]), 12)


class TestLoaders(unittest.TestCase):
    """Class 4: abstraction and inheritance."""

    def test_dataloader_is_abstract(self):
        with self.assertRaises(TypeError):
            DataLoader("data/movies.csv")

    def test_missing_file_raises(self):
        with self.assertRaises(DataFileError):
            CSVLoader("data/does_not_exist.csv")

    def test_both_loaders_inherit_from_dataloader(self):
        self.assertTrue(issubclass(CSVLoader, DataLoader))
        self.assertTrue(issubclass(JSONLoader, DataLoader))


@unittest.skipUnless(DATA_FILE.exists(), "data/movies.csv not downloaded")
class TestRealDataset(unittest.TestCase):
    """One end-to-end check against the real file."""

    @classmethod
    def setUpClass(cls):
        cls.collection = CSVLoader(DATA_FILE).to_collection()

    def test_cleaning_keeps_a_reasonable_number_of_movies(self):
        self.assertGreater(len(self.collection), 5000)

    def test_no_movie_has_a_zero_budget(self):
        self.assertTrue(all(m.budget > 0 for m in self.collection))

    def test_every_month_is_a_real_month_name(self):
        months = {m.month for m in self.collection}
        self.assertTrue(months.issubset(set(DataLoader.MONTHS)),
                        f"unexpected month values: {months - set(DataLoader.MONTHS)}")

    def test_model_explains_most_of_the_variation(self):
        r2 = SuccessPredictor(self.collection).train()
        self.assertGreater(r2, 0.5, "model is much worse than expected")


if __name__ == "__main__":
    unittest.main()
