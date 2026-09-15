# CineStat — Movie Analysis

**DS 1116 — Object Oriented Programming for Data Science Laboratory**
United International University · B.Sc. in Data Science

Analysing 40 years of film data to answer one question: **what makes a movie make money?**

The project comes in two halves that share the same code:

| Part | What it is | How to run it |
|------|-----------|---------------|
| **Part 1** | A Jupyter notebook exploring the dataset | `jupyter notebook notebooks/01_movie_analysis.ipynb` |
| **Part 2** | A Tkinter desktop app doing the same thing by clicking | `python main.py` |

The notebook and the app both `import` the classes in `cinestat/`. The analysis is
written **once** and used **twice** — nothing is copied and pasted between them.

---

## Getting started

```bash
pip install -r requirements.txt   # pandas, numpy, matplotlib, seaborn, scikit-learn
python main.py                    # launches the app
python -m unittest discover tests # runs all 87 tests
```

The dataset is already in `data/movies.csv`, so nothing needs downloading.

---

## The dataset

**Movie Industry** — 7,668 films released between 1980 and 2020, scraped from IMDb.
Source: <https://www.kaggle.com/datasets/danielgrijalvas/movies>

15 columns: `name, rating, genre, year, released, score, votes, director, writer, star,
country, budget, gross, company, runtime`.

After cleaning (dropping films with no budget or box-office figure) **5,418 films** remain.

---

## What we found

| # | Question | Answer |
|---|----------|--------|
| 1 | Which genre gives the best return? | **Horror** — typically about **3x** its budget |
| 2 | Which genre is safest? | **Animation** — the lowest share of money-losing films |
| 3 | Does a bigger budget mean a *better* film? | **No.** Correlation with IMDb score is only **0.07** |
| 4 | Does a bigger budget mean *more money*? | **Yes.** Correlation **0.74**; about **$3.33** back per $1 |
| 5 | Does the age rating matter? | **Yes.** G and PG films out-earn R-rated ones |
| 6 | Best time to release? | **Summer and December.** January is the worst |
| 7 | How risky is film making? | **32%** of films never earn back their budget |
| 8 | Can we predict box office in advance? | **Partly** — R² **0.588** |

### Two findings worth pointing out

**Money does not buy a good film.** Budget and IMDb score have a correlation of 0.072 —
statistically indistinguishable from zero. Spending more buys you an *audience*,
not a better film.

**Budget does almost all the predictive work.** The full model scores R² = 0.588.
A model using **budget and nothing else** scores 0.579. Genre, age rating and release
month together add less than **0.01**. We report this rather than hide it, because it is
a real result about the industry.

### Why the model ignores reviews

`score` and `votes` correlate strongly with box office — but a film only has them
*after* it is released. Using them to predict an unmade film would be **data leakage**.
The model is trained only on what is knowable in advance: budget, runtime, year, genre,
age rating and release month.

---

## The application

```
┌─ CineStat ───────────────────────────────── File  Help ─┐
│  [Browse]  [Charts]  [Compare]  [Predict]               │
└─────────────────────────────────────────────────────────┘
```

- **Browse** — search by title, filter by genre / age rating / year range, click any
  column heading to sort.
- **Charts** — eight charts from the notebook, with a zoom-and-save toolbar.
- **Compare** — two films side by side, with the better number highlighted in each row.
- **Predict** — enter a budget, genre, rating, runtime, year and month; get a predicted
  box office, profit, and a **Hit / Break-even / Flop** verdict, with the model's R²
  shown so the estimate is never mistaken for a promise.
- **File menu** — export whatever the Browse tab is currently showing to CSV or JSON.

---

## Where each syllabus topic lives in the code

| Class | Topic | Where to find it |
|-------|-------|------------------|
| 2 | Classes, objects, constructors, instance variables | `Movie.__init__` — `cinestat/movie.py` |
| 3 | **Encapsulation, name mangling** | `Movie.__budget` / `__gross`, reached through `@property` with validation |
| 3 | Static vs non-static members | `Movie.count`, `Movie.HIT_RATIO` (class) vs `self.name` (instance) |
| 3 | **Composition** | `MovieCollection` *contains* a list of `Movie` objects — `cinestat/collection.py` |
| 4 | **Abstraction, inheritance, overriding** | `DataLoader(ABC)` → `CSVLoader`, `JSONLoader` — `cinestat/loaders.py` |
| 5 | **Polymorphism** | `GenreAnalyzer`, `TrendAnalyzer`, `FinancialAnalyzer` all answer `.run()` — `cinestat/analyzers.py` |
| 5 | **Operator overloading / dunder** | `__str__`, `__repr__`, `__eq__`, `__hash__`, `__lt__`, `__gt__` on `Movie`; `__len__`, `__iter__`, `__getitem__`, `__contains__`, `__add__` on `MovieCollection` |
| 5 | **Multiple inheritance** | `FinancialAnalyzer(BaseAnalyzer, ExportMixin)`; `BaseTab(ttk.Frame, ABC)` |
| 7 | Tkinter widgets, layouts, callbacks | `cinestat/gui/` — `ttk.Notebook`, `Treeview`, `Combobox`, `bind()`, `command=` |
| 8 | **MVC-lite, multi-file GUI** | Logic in `cinestat/`, interface in `cinestat/gui/`. Tabs ask the analysis classes for answers; they never calculate anything themselves |
| 9 | **Custom exceptions** | `MovieDataError` → `InvalidBudgetError`, `InvalidGrossError`, `MovieNotFoundError`, `ModelNotTrainedError`, `DataFileError` |
| 9 | **Context manager**, File I/O, `pathlib` | `ExportSession` (`__enter__` / `__exit__`) and `quiet_blas_warning` (`@contextmanager`) — `cinestat/utils.py` |
| 10 | **unittest**, modules, packages, imports | `tests/` — 87 tests; `cinestat/` and `cinestat/gui/` are proper packages |
| 11 | **Decorators** | `@timed` on `BaseAnalyzer.run()` — prints how long each analysis took |
| 11 | **Iterators and generators** | `MovieCollection.__iter__`; `filter_by()`, `search()`, `in_year_range()` all `yield` |
| 11 | Functions as objects | `ChartsTab.charts` is a dictionary mapping a chart name to the *method* that draws it |

---

## Project layout

```
CineStat/
├── data/movies.csv                    # the dataset (1.3 MB)
├── notebooks/01_movie_analysis.ipynb  # Part 1
├── cinestat/                          # the shared core
│   ├── exceptions.py                  # custom exception hierarchy
│   ├── movie.py                       # Movie
│   ├── collection.py                  # MovieCollection
│   ├── loaders.py                     # DataLoader(ABC) → CSVLoader, JSONLoader
│   ├── analyzers.py                   # BaseAnalyzer(ABC) → Genre/Trend/Financial
│   ├── predictor.py                   # SuccessPredictor (linear regression)
│   ├── utils.py                       # @timed, ExportSession, money()
│   └── gui/                           # Part 2
│       ├── app.py                     # MovieApp(tk.Tk) — window, menu, tabs
│       ├── base_tab.py                # BaseTab(ttk.Frame, ABC)
│       ├── widgets.py                 # MoviePicker — our own widget
│       ├── browse_tab.py
│       ├── charts_tab.py
│       ├── compare_tab.py
│       └── predict_tab.py
├── tests/                             # 87 unittest tests
├── main.py                            # python main.py
└── requirements.txt
```

---

## Using the classes yourself

```python
from cinestat import CSVLoader, SuccessPredictor, GenreAnalyzer

# Abstraction: CSVLoader knows how to read a CSV; the cleaning is inherited.
movies = CSVLoader("data/movies.csv").to_collection()

print(len(movies))                         # __len__
print(movies[0])                           # __getitem__ and __str__

# A generator — films are produced one at a time, not all at once.
horror = list(movies.filter_by(genre="Horror"))

# Operator overloading.
print(movies.find("Avatar") > movies.find("Titanic"))   # True

# Polymorphism: every analyzer is used the same way.
GenreAnalyzer(movies).report()

# The model.
predictor = SuccessPredictor(movies)
print(f"R-squared: {predictor.train():.3f}")
print(predictor.predict(50_000_000, "Action", "PG-13", 120, 2020, "July"))
```

---

## Two bugs worth knowing about

Both were found by the automated GUI tests, and both are easy to hit again:

**Never give a Tkinter widget class a `__str__` method.** Tkinter calls `str(widget)`
internally to get the widget's *path name*. Overriding it makes `notebook.add(tab)` fail
with `bad window path name`. Override `__repr__` instead —
see the comment in `cinestat/gui/base_tab.py`, guarded by a test.

**A widget should not fire its callback while it is still being built.** `MoviePicker`
selected a film inside `__init__`, which called back into a tab that was only half
constructed. It now takes a `notify=False` flag during setup —
see `cinestat/gui/widgets.py`.

---

## Testing

```bash
python -m unittest discover tests -v
```

87 tests covering the `Movie` validation rules, every dunder method, the generators,
the abstract base classes, the context manager, the model, and all four GUI tabs
(including that a bad budget produces a dialog rather than a crash).
The GUI tests skip themselves automatically on a machine with no screen.
