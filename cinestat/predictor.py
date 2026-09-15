"""SuccessPredictor - the linear regression model.

It answers: "if I spend this much on this kind of film, what will it earn?"

IMPORTANT DESIGN NOTE (worth mentioning in the demo):
We train ONLY on information that exists BEFORE a film is released -
budget, runtime, year, genre, age rating and release month.

We deliberately leave out `score` and `votes`. Those only exist after people
have watched the film, so using them to predict a film that has not been made
yet would be cheating. That mistake has a name: DATA LEAKAGE.
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

from .movie import Movie
from .utils import quiet_blas_warning
from .exceptions import InvalidBudgetError, ModelNotTrainedError


class SuccessPredictor:
    """Predicts box-office gross, then works out whether that is a Hit."""

    # Features available before a film comes out.
    NUMERIC = ["budget", "runtime", "year"]
    CATEGORICAL = ["genre_group", "rating", "month"]

    def __init__(self, collection):
        self.collection = collection
        self.df = collection.to_dataframe()

        self.model = LinearRegression()
        self.is_trained = False

        # Filled in by train()
        self.r2 = None               # how much of the variation we explain
        self.mae = None              # average error in dollars
        self.columns = None          # the exact feature columns used
        self.coefficients = None

    # ---- preparing the data -----------------------------------------------

    def _build_features(self, df):
        """Turn text columns (genre, rating, month) into 0/1 number columns.

        A linear regression can only do arithmetic, so "Action" has to become
        something like genre_group_Action = 1. That is called one-hot encoding.
        """
        features = pd.get_dummies(
            df[self.NUMERIC + self.CATEGORICAL],
            columns=self.CATEGORICAL,
            drop_first=True,
        )
        return features.astype(float)

    # ---- training ---------------------------------------------------------

    def train(self, test_size=0.2, random_state=42):
        """Fit the model and measure how good it is on unseen movies."""
        X = self._build_features(self.df)
        y = self.df["gross"]
        self.columns = list(X.columns)

        # Hold back 20% of the films so we can test on data the model
        # has never seen. Testing on the training data would flatter it.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state)

        self.model.fit(X_train, y_train)
        with quiet_blas_warning():
            predictions = self.model.predict(X_test)
            self.r2 = self.model.score(X_test, y_test)
        self.mae = mean_absolute_error(y_test, predictions)
        self.coefficients = pd.Series(self.model.coef_, index=self.columns)
        self.is_trained = True
        return self.r2

    def budget_only_r2(self, test_size=0.2, random_state=42):
        """Train a second model on budget alone, for honest comparison.

        Spoiler: it scores almost as well. Budget is doing nearly all the work.
        """
        X = self.df[["budget"]]
        y = self.df["gross"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state)
        simple_model = LinearRegression().fit(X_train, y_train)
        with quiet_blas_warning():
            return simple_model.score(X_test, y_test)

    # ---- predicting -------------------------------------------------------

    def predict(self, budget, genre, rating, runtime, year, month):
        """Predict the gross for one imaginary film.

        Returns a dictionary with the predicted gross, the profit, and a
        Hit / Break-even / Flop verdict.
        """
        if not self.is_trained:
            raise ModelNotTrainedError(
                "Call train() before predict().")

        # Validate the budget the same way the Movie class does.
        try:
            budget = float(budget)
        except (TypeError, ValueError):
            raise InvalidBudgetError(f"Budget must be a number, got {budget!r}")
        if budget <= 0:
            raise InvalidBudgetError("Budget must be greater than zero.")

        row = pd.DataFrame([{
            "budget": budget,
            "runtime": float(runtime),
            "year": int(year),
            "genre_group": genre,
            "rating": rating,
            "month": month,
        }])

        features = self._build_features(row)
        # The single row will be missing most one-hot columns, so line it up
        # with the columns used in training and fill the gaps with 0.
        features = features.reindex(columns=self.columns, fill_value=0.0)

        with quiet_blas_warning():
            gross = float(self.model.predict(features)[0])
        gross = max(gross, 0.0)      # a film cannot earn negative money
        profit = gross - budget
        roi = gross / budget

        if roi >= Movie.HIT_RATIO:
            verdict = "Hit"
        elif roi >= 1.0:
            verdict = "Break-even"
        else:
            verdict = "Flop"

        return {
            "gross": gross,
            "profit": profit,
            "roi": roi,
            "verdict": verdict,
            "r2": self.r2,
            "mae": self.mae,
        }

    # ---- explaining the model ---------------------------------------------

    def top_coefficients(self, n=10):
        """The features that move the prediction the most."""
        if not self.is_trained:
            raise ModelNotTrainedError("Call train() before inspecting coefficients.")
        return self.coefficients.reindex(
            self.coefficients.abs().sort_values(ascending=False).index).head(n)

    def options(self):
        """The choices to offer in the GUI dropdowns."""
        return {
            "genres": sorted(self.df["genre_group"].unique()),
            "ratings": sorted(self.df["rating"].unique()),
            "months": ["January", "February", "March", "April", "May", "June",
                       "July", "August", "September", "October", "November",
                       "December"],
        }

    def __str__(self):
        if not self.is_trained:
            return "SuccessPredictor (not trained yet)"
        return f"SuccessPredictor (R2={self.r2:.3f}, trained on {len(self.df)} movies)"
