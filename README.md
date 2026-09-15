# CineStat — Movie Analysis

**DS 1116 — Object Oriented Programming for Data Science Laboratory**
United International University · B.Sc. in Data Science

Analysing 40 years of film data to answer two questions: **what makes a movie make money**,
and **what should I watch next?**

> Working on this project? Read **[PROJECT.md](PROJECT.md)** first — it records the
> decisions and why they were made, the rules new code must follow, and the feature backlog.

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
pip install -r requirements.txt   # pandas, numpy, matplotlib, seaborn, scikit-learn, requests
python main.py                    # launches the app
python -m unittest discover tests # runs all 220 tests
```

The dataset is already in `data/movies.csv`, so nothing needs downloading, and no
internet connection is needed for anything.

**Optional:** the Recommend tab can have its explanations rewritten by an AI. That is the
only part that uses the internet, it is switched off until you add a key, and the tab works
fully without it. See [Explaining with AI](#explaining-with-ai).

---

## The dataset

**Movie Industry** — 7,668 films released between 1980 and 2020, scraped from IMDb.
Source: <https://www.kaggle.com/datasets/danielgrijalvas/movies>

15 columns: `name, rating, genre, year, released, score, votes, director, writer, star,
country, budget, gross, company, runtime`.

After cleaning (dropping films with no budget or box-office figure) **5,418 films** remain.

### Using the bigger dataset (optional)

The app also opens the large **TMDB** export from Kaggle — roughly a million titles, and a
few hundred megabytes:
<https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies>

```bash
python main.py data/tmdb.csv
```

Nothing else changes. `DataLoader.for_file()` reads the first line of the file, sees TMDB's
column names, and hands back a `TMDBLoader` instead of a `CSVLoader`. Every class downstream —
`Movie`, `MovieCollection`, the analyzers, the predictor, all five tabs — carries on unchanged.

Two things `TMDBLoader` has to deal with, and worth saying out loud:

- **The file is too big to open in one go.** It is read in **chunks** of 200,000 rows, each
  chunk filtered down and the leftovers thrown away, so memory use stays flat however big the
  file gets.
- **Most of those rows are unusable for this project.** Only a small share record *both* a
  budget and a box office; the rest are shorts, unreleased titles and blank entries. We keep
  the ones with real money figures. That is still several times more films than `movies.csv`
  has — but "a million films" would be a dishonest thing to claim, so we do not claim it.

`movies.csv` stays the default because it has the age rating (G / PG / PG-13 / R), the director
and the leading actor, which the TMDB export does not.

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
┌─ CineStat ─────────────────────────────────────────── File  Help ─┐
│  [Browse]  [Charts]  [Compare]  [Predict]  [Recommend]            │
└───────────────────────────────────────────────────────────────────┘
```

- **Browse** — search by title, filter by genre / age rating / year range, click any
  column heading to sort.
- **Charts** — eight charts from the notebook, with a zoom-and-save toolbar.
- **Compare** — two films side by side, with the better number highlighted in each row.
- **Predict** — enter a budget, genre, rating, runtime, year and month; get a predicted
  box office, profit, and a **Hit / Break-even / Flop** verdict, with the model's R²
  shown so the estimate is never mistaken for a promise.
- **Recommend** — tick films you liked; get suggestions with a plain-English reason for
  each one. See below.
- **File menu** — export whatever the tab you are looking at is showing, to CSV or JSON.

---

## Recommendations

> "Pick some films you like, and the system suggests more."

### How it works, in four steps

1. **You tick films you enjoyed.** They go into a list on the left.
2. **`UserPreference.from_movies()` works out what they have in common** — the genres that
   keep coming up, the average IMDb score, the usual runtime, the usual era. That is the
   *taste profile*, and it is printed on screen so you can see exactly what was inferred.
3. **A recommender scores every other film out of 100** against that profile, and records
   *why* it gave each mark.
4. **The reasons appear instantly.** Pressing **Explain with AI** sends those same reasons
   to a language model, which rewrites them as a short paragraph.

### The 100 points, and where they come from

`ContentRecommender` — the default. Every mark is traceable to one line of code:

| Test | Points | What it asks |
|---|---:|---|
| Genre | 40 | Is this one of the genres you keep picking? |
| IMDb score | 25 | Is it well reviewed? (score ÷ 10 × 25) |
| Age rating | 15 | Does it match the ratings you chose? |
| Runtime | 10 | Is it about as long as the films you like? |
| Era | 10 | Did it come out around the same time as them? |

Three recommenders share one abstract base class and are used identically:

| Method | What it does |
|---|---|
| **Matches my taste** | The table above — scores every film against your whole profile |
| **Similar to my last pick** | Compares everything against *one* film instead of a profile |
| **Most popular (baseline)** | **Ignores your taste completely.** Best reviewed, most watched |

The baseline is there on purpose, for the same reason the Predict tab reports the
budget-only model next to the full one: if "the most famous film in the database" satisfies
you just as well, the clever recommender is not earning its keep, and we would rather find
that out than hide it.

### Explaining with AI

**The AI does not choose the films.** `recommenders.py` chooses them and works out why. The
AI is handed those reasons and asked to phrase them nicely — nothing more. That is a
deliberate design choice, and it has three consequences worth stating:

- **Every suggestion is explainable without it.** The reasons are computed by our own code
  and shown on screen before the AI is ever called.
- **Nothing breaks without a key or without internet.** `AIExplainer.explain_or_fallback()`
  catches the failure, returns the offline explanation instead, and says on screen that it
  did so. There is a test for exactly this.
- **The model cannot invent a film.** It only ever rephrases facts it was given, and the
  system prompt tells it not to add plot details, awards or cast members.

To switch it on:

```bash
cp .env.example .env          # then paste your key into .env
```

```ini
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=google/gemini-2.5-flash-lite
```

Any model slug from <https://openrouter.ai/models> works. **Avoid "reasoning" models here** —
they think to themselves before answering, and that thinking is charged against the *same*
token budget as the answer:

| Model | Reply time | Note |
|---|---|---|
| `google/gemini-2.5-flash-lite` | **~1.6 s** | what the project uses |
| `z-ai/glm-5.3-flash` | 30–40 s | a reasoning model; tried and rejected |

With `MAX_TOKENS = 220`, glm spent **219 tokens thinking** and returned an empty answer.
`AIExplainer.MAX_TOKENS` is now 800 so any model has room, but the real fix was picking a
model that answers directly. Switching the thinking off is *not* an option — glm rejects that
outright with *"Reasoning is mandatory for this endpoint and cannot be disabled"*.

The system prompt also insists on **plain text**: Gemini otherwise wraps film titles in
`*asterisks*`, and the Tkinter text box has no way to render Markdown, so they show up
literally on screen.

Get a key from <https://openrouter.ai/keys>. `.env` is in `.gitignore`, so the key never
reaches GitHub, and it appears nowhere in the source code.

The network call runs on a **background thread**, so the window stays usable while you wait —
that is what `threading` is doing in `recommend_tab.py`, and the only reason it is there.

---

## Where each syllabus topic lives in the code

| Class | Topic | Where to find it |
|-------|-------|------------------|
| 2 | Classes, objects, constructors, instance variables | `Movie.__init__` — `cinestat/movie.py` |
| 3 | **Encapsulation, name mangling** | `Movie.__budget` / `__gross`, reached through `@property` with validation |
| 3 | Static vs non-static members | `Movie.count`, `Movie.HIT_RATIO` (class) vs `self.name` (instance) |
| 3 | **Composition** | `MovieCollection` *contains* a list of `Movie` objects — `cinestat/collection.py` |
| 3 | **Encapsulation again** | `UserPreference.__genres` / `__ratings` / `__min_score` behind validating properties — `cinestat/preferences.py` |
| 4 | **Abstraction, inheritance, overriding** | `DataLoader(ABC)` → `CSVLoader`, `JSONLoader`, `TMDBLoader` — `cinestat/loaders.py` |
| 4 | **Abstraction again, twice** | `BaseRecommender(ABC)` → three recommenders; `BaseExplainer(ABC)` → two explainers |
| 4 | **Template method** | `BaseRecommender.recommend()` writes the four steps once; subclasses fill in only `score_movie()` |
| 4 | **Factory method** | `DataLoader.for_file()` reads the header row and hands back the right subclass — `cinestat/loaders.py` |
| 5 | **Polymorphism** | `GenreAnalyzer`, `TrendAnalyzer`, `FinancialAnalyzer` all answer `.run()` — `cinestat/analyzers.py` |
| 5 | **Polymorphism doing real work** | `ContentRecommender`, `SimilarityRecommender`, `PopularityRecommender` all answer `.recommend()`; `RuleExplainer` and `AIExplainer` both answer `.explain()` and the GUI cannot tell them apart |
| 5 | **Duck typing** | `MovieApp.active_tab()` exports from any tab that answers `current_rows()` — no shared base class needed |
| 5 | **Operator overloading / dunder** | `__str__`, `__repr__`, `__eq__`, `__hash__`, `__lt__`, `__gt__` on `Movie`; `__len__`, `__iter__`, `__getitem__`, `__contains__`, `__add__` on `MovieCollection`; `__contains__` / `__len__` on `UserPreference`; `__lt__` on `Recommendation` so `sorted()` ranks them |
| 5 | **Multiple inheritance** | `FinancialAnalyzer(BaseAnalyzer, ExportMixin)`; `BaseTab(ttk.Frame, ABC)` |
| 7 | Tkinter widgets, layouts, callbacks | `cinestat/gui/` — `ttk.Notebook`, `Treeview`, `Combobox`, `bind()`, `command=` |
| 8 | **MVC-lite, multi-file GUI** | Logic in `cinestat/`, interface in `cinestat/gui/`. Tabs ask the analysis classes for answers; they never calculate anything themselves |
| 9 | **Custom exceptions** | `MovieDataError` → `InvalidBudgetError`, `InvalidGrossError`, `MovieNotFoundError`, `ModelNotTrainedError`, `DataFileError`, `InvalidPreferenceError`, `AIServiceError` |
| 9 | **Context manager**, File I/O, `pathlib` | `ExportSession` (`__enter__` / `__exit__`) and `quiet_blas_warning` (`@contextmanager`) — `cinestat/utils.py`; `with pd.read_csv(chunksize=...)` in `TMDBLoader.load()`; `read_env_file()` reading the `.env` |
| 10 | **unittest**, modules, packages, imports | `tests/` — 220 tests; `cinestat/` and `cinestat/gui/` are proper packages |
| 11 | **Decorators** | `@timed` on `BaseAnalyzer.run()` — prints how long each analysis took |
| 11 | **Iterators and generators** | `MovieCollection.__iter__`; `filter_by()`, `search()`, `in_year_range()` all `yield` |
| 11 | Functions as objects | `ChartsTab.charts` maps a chart name to the *method* that draws it; `RecommendTab.ENGINES` maps a menu label to the *class* that provides it |
| 12 | **Multithreading** | The OpenRouter call runs on a `threading.Thread` so the window never freezes; the reply is handed back to the main thread with `self.after(0, ...)` — `cinestat/gui/recommend_tab.py` |

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
│   ├── loaders.py                     # DataLoader(ABC) → CSVLoader, JSONLoader, TMDBLoader
│   ├── analyzers.py                   # BaseAnalyzer(ABC) → Genre/Trend/Financial
│   ├── predictor.py                   # SuccessPredictor (linear regression)
│   ├── preferences.py                 # UserPreference — the taste profile
│   ├── recommenders.py                # BaseRecommender(ABC) → Content/Similarity/Popularity
│   ├── explainers.py                  # BaseExplainer(ABC) → RuleExplainer, AIExplainer
│   ├── utils.py                       # @timed, ExportSession, money()
│   └── gui/                           # Part 2
│       ├── app.py                     # MovieApp(tk.Tk) — window, menu, tabs
│       ├── base_tab.py                # BaseTab(ttk.Frame, ABC)
│       ├── widgets.py                 # MoviePicker — our own widget
│       ├── browse_tab.py
│       ├── charts_tab.py
│       ├── compare_tab.py
│       ├── predict_tab.py
│       └── recommend_tab.py
├── tests/                             # 220 unittest tests
├── .env.example                       # copy to .env and add an OpenRouter key
├── main.py                            # python main.py [optional data file]
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

And the recommender:

```python
from cinestat import (CSVLoader, UserPreference, ContentRecommender,
                      PopularityRecommender, RuleExplainer, build_explainer)

movies = CSVLoader("data/movies.csv").to_collection()

# An alternative constructor: work the profile out from films, not from a form.
liked = [movies.find(title) for title in ["The Shining", "The Thing", "Aliens"]]
me = UserPreference.from_movies(liked)
print(me)        # genres: Action, Drama, Horror | IMDb 7.3+ | around 131 min | ...

print(movies.find("The Shining") in me)     # True — __contains__

# Polymorphism: both engines are used identically.
for engine in [ContentRecommender(movies, me), PopularityRecommender(movies, me)]:
    print(f"\n{engine}")
    for suggestion in engine.recommend(3):
        print(" ", suggestion)               # __str__ on Recommendation

# And so are both explainers. build_explainer() returns the AI one if a key
# is configured and the offline one if not — the calling code is the same.
top = ContentRecommender(movies, me).recommend(1)[0]
print(build_explainer().explain(top, me))
```

---

## Two bugs worth knowing about

Both were found by the automated GUI tests, and both are easy to hit again:

**Never give a Tkinter widget class a `__str__` method.** Tkinter calls `str(widget)`
internally to get the widget's *path name*. Overriding it makes `notebook.add(tab)` fail
with `bad window path name`. Override `__repr__` instead —
see the comment in `cinestat/gui/base_tab.py`, guarded by a test.

**Never hard-code one half of a colour pair.** The explanation box asked for a near-white
background and left the text colour alone. macOS dark mode makes the default text colour
**white**, so the explanation rendered white on white and was completely invisible — while
every test still passed, because the words were in the widget. Tkinter's own defaults
(`systemTextBackgroundColor` / `systemTextColor`) are correct in both modes, so the fix was to
stop overriding them. `muted_colour()` in `base_tab.py` does the same job for secondary grey
text, working the shade out from the window's actual brightness at runtime.

**A widget should not fire its callback while it is still being built.** `MoviePicker`
selected a film inside `__init__`, which called back into a tab that was only half
constructed. It now takes a `notify=False` flag during setup —
see `cinestat/gui/widgets.py`.

**`x or default` is a trap on any class that defines `__len__`.** `BaseRecommender` used
to write `self.preference = preference or UserPreference()`. Because `UserPreference`
defines `__len__`, a brand-new profile with no films ticked yet counts as **False** — so a
real profile carrying the user's genres and year range was silently thrown away and
replaced with an empty one. It is now `UserPreference() if preference is None else
preference`, guarded by `test_an_empty_profile_is_not_thrown_away`.

**Setting a Treeview selection does not explain the row straight away.**
`tree.selection_set()` only *queues* the `<<TreeviewSelect>>` event for the next trip round
the event loop. `RecommendTab.recommend()` therefore calls `show_reasons()` itself rather
than waiting for the event.

---

## Testing

```bash
python -m unittest discover tests -v
```

220 tests covering the `Movie` validation rules, every dunder method, the generators,
the abstract base classes, the context manager, the model, the taste profile, all three
recommenders, both explainers, `TMDBLoader`'s chunked reading, and all five GUI tabs
(including that a bad budget produces a dialog rather than a crash).

**No test ever touches the internet.** A fake stand-in for the `requests` library is
slipped into `sys.modules`, so the AI code path is tested against a successful reply, an
HTTP 401, a dead connection, a malformed reply and an empty reply — without a key and
without a network. The GUI tests skip themselves automatically on a machine with no screen.
