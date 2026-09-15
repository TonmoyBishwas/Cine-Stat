# CineStat — Project Overview

**DS 1116 · Object Oriented Programming for Data Science Laboratory · Section BA · Spring 2026**

> This file is the working document: what was decided, why, what is left to build, and the
> rules any new code must follow. `README.md` explains what the project *is*; this explains
> how to *work on it*. Read this first when picking the project back up.

---

## 1. The problem

A studio is about to spend $50 million. **32.1% of films never earn that money back** — roughly
one in three. The decision is made before a single frame is shot, from a budget, a genre, an age
rating and a release date.

**CineStat answers one question:** *standing before production, what will this film earn, and is
that enough?*

The honest answer is "partly". Budget explains most of it and nothing else explains much —
which is itself the finding, and the project says so rather than dressing it up.

## 2. The data

**Movie Industry** (IMDb, 1980–2020) — 7,668 films, 15 flat columns, 1.3 MB, committed to
`data/movies.csv` so the project runs offline.

Chosen over two alternatives for concrete reasons:

- **TMDB-5000** stores genres and cast as JSON strings *inside* CSV cells. Parsing nested JSON
  would have dominated the notebook instead of the OOP.
- **IMDb Top 1000** has no budget column, so no regression is possible at all.

After cleaning, **5,418 films** remain (29.3% dropped). The losses are mostly the 2,171 films
with no budget recorded — a film with no budget cannot say anything about spending versus
earning, so keeping it would be worse than dropping it.

**Three honest caveats:**

1. `released` is free text (`"June 13, 1980 (United States)"`). The first word is *usually* the
   month — but a few rows hold a **year** there instead. `DataLoader.clean()` keeps only real
   month names. Trusting the first word blindly would have silently poisoned the seasonality
   analysis.
2. Genres with fewer than 100 films are grouped as `"Other"`, or the charts and the model
   become unreadable. `genre` keeps the true value; `genre_group` is the grouped one.
3. The dataset is box-office gross, not profit. Marketing spend is not in it, so "profit" here
   is `gross − budget` and overstates real profitability.

## 3. Current features

Two halves sharing one core. The notebook and the GUI import the **same classes** — the
analysis is written once and used twice.

| Part | What it is | Run it with |
|---|---|---|
| **Part 1** | 12-section Jupyter notebook, executed with outputs saved | `jupyter notebook notebooks/01_movie_analysis.ipynb` |
| **Part 2** | Four-tab Tkinter app | `python3 main.py` |

| Tab | What it does |
|---|---|
| **Browse** | Every film in a sortable table; search by title, filter by genre / age rating / year range |
| **Charts** | Eight matplotlib figures embedded in the window, with a zoom-and-save toolbar |
| **Compare** | Two films side by side; the winner is decided by `Movie.__gt__`, not by hand |
| **Predict** | Budget and category in → predicted gross, profit, and a Hit / Break-even / Flop verdict |

**The results** — trained on 80% of the films, scored on the unseen 20%:

| Model | Test R² |
|---|---|
| All pre-release features | **0.588** |
| **Budget alone** | **0.579** |
| Pre-release features → log₁₀(gross) | 0.436 |

Genre, age rating and release month together add **under 0.01**. That is reported, not hidden.

**Headline findings:**

| Question | Answer |
|---|---|
| Does budget buy box office? | **Yes** — correlation 0.740, about **$3.33** back per $1 |
| Does budget buy a *good* film? | **No** — correlation **0.072**, indistinguishable from zero |
| Best return on investment | **Horror**, typically ~3× its budget |
| Safest genre | **Animation**, lowest share of money-losers |
| How risky is film making? | **32.1%** never earn back their budget |

## 4. Key decisions, and why

These are the ones worth defending in a viva. Do not quietly reverse them.

**The model excludes `score` and `votes`.** Both correlate strongly with box office — and both
only exist *after* a film is released. Feeding them to a model that claims to predict an unmade
film is **data leakage**. The model sees only budget, runtime, year, genre, age rating and
release month.

**We predict gross, then derive the verdict.** Predicting ROI directly was considered and
rejected: linear regression scores R² ≈ 0.05 on ROI because it is dominated by noise, and the
demo would look broken. Predicting gross (R² 0.588) and computing `profit = gross − budget`
gives the same "success predictor" feel with a model that actually works.

**Budget-alone is reported alongside the full model.** Hiding the 0.579 would make the project
look better and be dishonest. An examiner who spots it costs more than the honesty does.

**Full syllabus coverage over minimalism.** Every lecture topic has a home in the code, each
kept to 5–15 commented lines, so each one can be pointed at during judging.

## 5. How it is built

```
CSV → CSVLoader → MovieCollection → analyzers / predictor → notebook or GUI
```

**The layer rule:** `cinestat/gui/` may import the core. **No core module may import `gui/`.**
Currently true — but *not yet enforced by a test*. See the backlog.

| File | Responsibility |
|---|---|
| `exceptions.py` | Exception hierarchy. Imports nothing. |
| `movie.py` | One film, with private `__budget` / `__gross` behind validating properties |
| `collection.py` | The container everything downstream reads |
| `loaders.py` | `DataLoader(ABC)` → `CSVLoader`, `JSONLoader`; shared `clean()` |
| `analyzers.py` | `BaseAnalyzer(ABC)`, `ExportMixin`, three analyzers |
| `predictor.py` | `SuccessPredictor` — linear regression |
| `utils.py` | `@timed` decorator, `ExportSession` context manager, `money()` |
| `gui/` | Window, shared base tab, our own `MoviePicker` widget, one file per tab |

**Size:** 956 lines core · 978 lines GUI · 697 lines tests · **87 tests**.

Unlike ClassLens (the other project in `~/Codes/CineMatch`), CineStat **does** use pandas and
scikit-learn. That is a deliberate difference — it matches the syllabus reading list (McKinney,
*Python for Data Analysis*) and CO3, "standard framework-specific libraries". Be ready to say
that if asked why the regression is not hand-written.

## 6. Feature backlog

Ordered by how much they add per line of code. Nothing here is started.

### Gaps against the syllabus — highest value

| # | Feature | Why it matters |
|---|---|---|
| **B1** | **Predictor hierarchy** — `BasePredictor(ABC)` → `AveragePredictor` (baseline), `BudgetOnlyPredictor`, `FullPredictor`, then one loop that trains and scores all three | The biggest structural gap. Right now `SuccessPredictor` is one standalone class: **no ABC, no inheritance, no polymorphism in the model layer.** This turns the budget-alone comparison we already compute into a real demonstration of polymorphism doing work. |
| **B2** | **Background threading** — load the CSV and train off the main thread so the window never freezes | **"Multithreaded Programming" is in the UGC-approved course contents and CineStat covers none of it.** Say plainly it is not for speed (training takes <1s) but so the window cannot freeze. |
| **B3** | **Model serialization** — save and reload the trained model | Class 9 lists *"File I/O (text/CSV/JSON), pathlib, context manager, **serialization**"*. Every item is covered except serialization; JSON export is only half of it. |
| **B4** | **Architecture test** — assert no core module imports `gui/` | The README *claims* MVC-lite separation. A test makes it enforced rather than promised. ~15 lines. |

### Features that would strengthen the demo

| # | Feature | Why it matters |
|---|---|---|
| **B5** | **"Why this prediction?"** — break the predicted gross into contributions (*budget +$142M, July release +$8M, R rating −$21M*) | Turns a bare number into an explanation. The coefficients already exist in `top_coefficients()`. |
| **B6** | **Console mode** — `python3 -m cinestat.console` runs the whole analysis as text | Proves the core is genuinely independent of the GUI, and is a fallback if Tkinter misbehaves on the demo machine. |
| **B7** | **Similar films finder** — "films most like this one" by nearest neighbour | Natural fifth tab; gives Compare something to feed on. |
| **B8** | **Insights tab** — auto-generated plain-English findings | Considered during planning and deliberately cut as the lowest OOP value per line. Revisit only if the demo needs more visible surface. |

**If only one gets built: B1.** It closes the biggest structural gap and reuses work already done.

## 7. Rules for new code

- **New analysis goes in `cinestat/`, never in a tab.** Tabs ask the core for answers; they
  never calculate. A tab doing arithmetic on a DataFrame is a bug.
- **New charts go in `ChartsTab.charts`** — the dict mapping a name to the method that draws
  it. Add an entry, add a method; nothing else changes.
- **Every new class gets tests** in `tests/`. The suite runs in ~1 second; keep it that way.
- **Keep it explainable.** Anything that cannot be explained line-by-line in a viva is worth
  less than a simpler thing that can.

## 8. Two Tkinter traps already hit

Both were caught by the GUI tests, and both are easy to hit again.

**Never give a Tkinter widget class a `__str__` method.** Tkinter calls `str(widget)` internally
to get the widget's *path name*. Overriding it makes `notebook.add(tab)` fail with
`bad window path name` — the app will not even open. Override `__repr__` instead. Guarded by
`test_tabs_do_not_override_str`.

**A widget must not fire its callback while still being built.** `MoviePicker` selected a film
inside `__init__`, calling back into a tab that was only half constructed. It now takes
`notify=False` during setup.

**Bonus, not a bug:** macOS with numpy 2.x prints a false *"divide by zero encountered in
matmul"* during normal matrix multiplication. Verified false — sklearn's output matches a
hand-calculated matmul exactly, difference `0.0`. Suppressed narrowly in
`utils.quiet_blas_warning()`.

## 9. Running it

```bash
python3 main.py                                      # the desktop app
jupyter notebook notebooks/01_movie_analysis.ipynb   # Part 1
python3 -m unittest discover tests                   # 87 tests
```

Python 3.12 with `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn` and `tkinter`
(`pip install -r requirements.txt`). No internet needed — the dataset ships in `data/`.

The GUI tests skip themselves automatically on a machine with no screen.

## 10. Two things to say plainly if asked

**The model is 59% right, and that is the honest ceiling.** The remaining 41% is the script,
the cast, the marketing and the luck — none of which a spreadsheet can measure. The Predict tab
shows R² on screen for exactly this reason, so nobody mistakes an estimate for a promise.

**Budget does almost all of the work.** Genre, rating and month add under 0.01 R². That is not a
failed model; it is a real result about the film industry, and it is more interesting reported
than buried.
