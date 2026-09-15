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

**CineStat answers two questions.** *Standing before production, what will this film earn, and
is that enough?* And, from the other side of the screen: *given what I already like, what should
I watch next, and why that?*

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

**The big Kaggle dataset is supported but is not the default.** `TMDBLoader` opens the ~1M-row
TMDB export, streaming it in 200,000-row chunks so memory stays flat. `DataLoader.for_file()`
picks the loader from the header row, so `python3 main.py data/tmdb.csv` is the only change.

It stays optional for two honest reasons, and both are worth saying out loud rather than
letting an examiner find them:

- **The row count is not the film count.** Only a small share of those million rows record
  *both* a budget and a box office; the rest are shorts, unreleased titles and blank entries.
  After the same cleaning `movies.csv` gets, what survives is several times larger than 5,418 —
  a real improvement, but nowhere near a million. Claiming "we used a million films" would be
  false.
- **It has no age certification.** TMDB's export carries no G / PG / PG-13 / R column, no
  director and no lead actor. Three existing features depend on those. `movies.csv` is the
  richer file per row; the TMDB file is the bigger one. We support both and default to the
  richer.

## 3. Current features

Two halves sharing one core. The notebook and the GUI import the **same classes** — the
analysis is written once and used twice.

| Part | What it is | Run it with |
|---|---|---|
| **Part 1** | 12-section Jupyter notebook, executed with outputs saved | `jupyter notebook notebooks/01_movie_analysis.ipynb` |
| **Part 2** | Five-tab Tkinter app | `python3 main.py` |

| Tab | What it does |
|---|---|
| **Browse** | Every film in a sortable table; search by title, filter by genre / age rating / year range |
| **Charts** | Eight matplotlib figures embedded in the window, with a zoom-and-save toolbar |
| **Compare** | Two films side by side; the winner is decided by `Movie.__gt__`, not by hand |
| **Predict** | Budget and category in → predicted gross, profit, and a Hit / Break-even / Flop verdict |
| **Recommend** | Tick films you liked → suggestions scored out of 100, each with the reasons it was picked, optionally rewritten by an AI |

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

### The recommender, added after the first submission

**The AI does not choose the films — it only writes them up.** `recommenders.py` picks the
films and records, in plain English, why it gave each mark. `AIExplainer` is handed those
reasons and asked to phrase them nicely. This was a deliberate choice over "send the dataset
to a model and ask it what to watch", and it buys three things:

- every suggestion is explainable line by line, which a black box would not be;
- the feature works with no key, no account and no internet;
- the model cannot invent a film, because it never chooses one.

If asked *"so what is the AI actually doing?"* — the honest answer is "rewriting our reasons
as a paragraph, and nothing else", and that is by design.

**The explanation falls back instead of failing.** `explain_or_fallback()` catches every
`AIServiceError`, returns the offline explanation, and tells the user on screen that it did.
A dead wifi connection in the demo room cannot break the tab. Two tests cover this path.

**The key is never in the source code.** It is read at runtime from `OPENROUTER_API_KEY` in
the environment or in `.env`, which `.gitignore` excludes. `.env.example` is committed instead.

**A popularity baseline sits next to the real recommender.** Same reasoning as reporting the
budget-only R² next to the full model: if "the most famous film in the database" satisfies the
user just as well, the content-based one is not earning its keep. Better to show that than to
hide it.

**The scoring is arithmetic, not a second machine-learning model.** 40 points for genre, 25 for
IMDb score, 15 for rating, 10 for runtime, 10 for era. A nearest-neighbour model over one-hot
features would score marginally better and would be impossible to explain at the whiteboard.
The weights are class attributes at the top of `ContentRecommender`, so the whole behaviour of
the recommender can be pointed at in five lines.

**The taste profile is inferred, not typed in.** `UserPreference.from_movies()` counts the
genres, averages the score, runtime and year, and builds the profile from the films the user
ticked. The result is printed on screen, so the user can see exactly what was inferred about
them rather than having to trust it.

## 5. How it is built

```
CSV → DataLoader.for_file() → MovieCollection → analyzers / predictor  → notebook or GUI
                                             └→ recommenders → explainers → GUI
```

**The layer rule:** `cinestat/gui/` may import the core. **No core module may import `gui/`.**
Currently true — but *not yet enforced by a test*. See the backlog.

| File | Responsibility |
|---|---|
| `exceptions.py` | Exception hierarchy. Imports nothing. |
| `movie.py` | One film, with private `__budget` / `__gross` behind validating properties |
| `collection.py` | The container everything downstream reads |
| `loaders.py` | `DataLoader(ABC)` → `CSVLoader`, `JSONLoader`, `TMDBLoader`; shared `clean()`; `for_file()` factory |
| `analyzers.py` | `BaseAnalyzer(ABC)`, `ExportMixin`, three analyzers |
| `predictor.py` | `SuccessPredictor` — linear regression |
| `preferences.py` | `UserPreference` — the taste profile, with private validated attributes |
| `recommenders.py` | `Recommendation`, `BaseRecommender(ABC)` → three recommenders |
| `explainers.py` | `BaseExplainer(ABC)` → `RuleExplainer`, `AIExplainer`; reads the `.env` |
| `utils.py` | `@timed` decorator, `ExportSession` context manager, `money()` |
| `gui/` | Window, shared base tab, our own `MoviePicker` widget, one file per tab |

**Size:** 2,120 lines core · 1,574 lines GUI · 2,097 lines tests · **220 tests**, still ~1.3 s.

`requests` is the one new dependency, used by `AIExplainer` and nothing else. It is imported
*inside* the method rather than at the top of the file, so the rest of CineStat still runs if
it is missing.

Unlike ClassLens (the other project in `~/Codes/CineMatch`), CineStat **does** use pandas and
scikit-learn. That is a deliberate difference — it matches the syllabus reading list (McKinney,
*Python for Data Analysis*) and CO3, "standard framework-specific libraries". Be ready to say
that if asked why the regression is not hand-written.

## 6. Feature backlog

Ordered by how much they add per line of code.

### Done since the first submission

| # | Feature | Where it landed |
|---|---|---|
| **B2** | **Background threading** — *partly done.* The OpenRouter call runs on a `threading.Thread`, with the reply handed back via `self.after(0, ...)`. The original idea — loading the CSV and training off the main thread — is still open and is now the smaller half of the item. | `gui/recommend_tab.py` |
| **B7** | **Similar films finder** | `SimilarityRecommender`, reachable from the Recommend tab's method dropdown |

### Gaps against the syllabus — highest value

| # | Feature | Why it matters |
|---|---|---|
| **B1** | **Predictor hierarchy** — `BasePredictor(ABC)` → `AveragePredictor` (baseline), `BudgetOnlyPredictor`, `FullPredictor`, then one loop that trains and scores all three | The biggest structural gap. Right now `SuccessPredictor` is one standalone class: **no ABC, no inheritance, no polymorphism in the model layer.** This turns the budget-alone comparison we already compute into a real demonstration of polymorphism doing work. |
| **B2b** | **Threaded start-up** — load the CSV and train off the main thread too, with a progress bar | The AI call already covers threading, so this is now about polish rather than coverage. Matters most if the big TMDB dataset becomes the default, because that one takes seconds to load. |
| **B3** | **Model serialization** — save and reload the trained model | Class 9 lists *"File I/O (text/CSV/JSON), pathlib, context manager, **serialization**"*. Every item is covered except serialization; JSON export is only half of it. |
| **B4** | **Architecture test** — assert no core module imports `gui/` | The README *claims* MVC-lite separation. A test makes it enforced rather than promised. ~15 lines. |

### Features that would strengthen the demo

| # | Feature | Why it matters |
|---|---|---|
| **B5** | **"Why this prediction?"** — break the predicted gross into contributions (*budget +$142M, July release +$8M, R rating −$21M*) | Turns a bare number into an explanation. The coefficients already exist in `top_coefficients()`. |
| **B6** | **Console mode** — `python3 -m cinestat.console` runs the whole analysis as text | Proves the core is genuinely independent of the GUI, and is a fallback if Tkinter misbehaves on the demo machine. |
| **B9** | **"Because you liked X"** — name the specific ticked film that drove each suggestion, not just the genre | The reasons currently say *"Horror is one of your favourite genres"*. Saying *"because you liked The Shining"* is more convincing and the data to do it is already in `UserPreference.liked_titles`. |
| **B8** | **Insights tab** — auto-generated plain-English findings | Considered during planning and deliberately cut as the lowest OOP value per line. Revisit only if the demo needs more visible surface. |

**If only one gets built: B1.** It closes the biggest structural gap and reuses work already
done — and `BaseRecommender` is now a worked example of exactly the shape `BasePredictor`
should take, so the second one is cheaper than the first was.

## 7. Rules for new code

- **New analysis goes in `cinestat/`, never in a tab.** Tabs ask the core for answers; they
  never calculate. A tab doing arithmetic on a DataFrame is a bug.
- **New charts go in `ChartsTab.charts`** — the dict mapping a name to the method that draws
  it. Add an entry, add a method; nothing else changes.
- **Every new class gets tests** in `tests/`. The suite runs in ~1 second; keep it that way.
- **New recommenders subclass `BaseRecommender` and override `score_movie()` only.** The
  filter → score → sort → cut steps are written once in `recommend()`. Add the class to
  `RecommendTab.ENGINE_CLASSES` and the dropdown picks it up by itself.
- **Scoring weights stay as class attributes at the top of the class.** They are the first
  thing to point at when asked how the recommender works.
- **Never put an API key in the source, or in a test.** It is read at runtime from the
  environment or `.env`. Tests fake the `requests` module; none of them touch the network.
- **Keep it explainable.** Anything that cannot be explained line-by-line in a viva is worth
  less than a simpler thing that can.

## 8. Traps already hit

All of these were caught by the tests, and all of them are easy to hit again.

**Never give a Tkinter widget class a `__str__` method.** Tkinter calls `str(widget)` internally
to get the widget's *path name*. Overriding it makes `notebook.add(tab)` fail with
`bad window path name` — the app will not even open. Override `__repr__` instead. Guarded by
`test_tabs_do_not_override_str`.

**A widget must not fire its callback while still being built.** `MoviePicker` selected a film
inside `__init__`, calling back into a tab that was only half constructed. It now takes
`notify=False` during setup.

**`x or default` is a trap on any class that defines `__len__`.** `BaseRecommender` wrote
`self.preference = preference or UserPreference()`. `UserPreference` defines `__len__`, so a
real profile with no films ticked yet is **falsy** — and the user's genres and year range were
silently replaced with an empty profile. Now `UserPreference() if preference is None else
preference`. Guarded by `test_an_empty_profile_is_not_thrown_away`. The same trap is waiting in
`MovieCollection`, which also defines `__len__`.

**`tree.selection_set()` does not fire `<<TreeviewSelect>>` straight away.** It queues the
event for the next trip round the event loop, so code that runs immediately afterwards sees
the old state. `RecommendTab.recommend()` calls `show_reasons()` itself instead of waiting.

**Reading a CSV in chunks keeps the file open between chunks.** `TMDBLoader.load()` can stop
early (`max_movies`) or raise part-way through, and the `pd.read_csv(chunksize=...)` reader
leaks its file handle either way. It is now used as a `with` block. Caught by running the
tests with `-W error::ResourceWarning`.

**Only the main thread may touch Tkinter — and that includes `after()` itself.** The first
version had the worker thread call `self.after(0, ...)` to hand its answer back. That raises
`RuntimeError: main thread is not in main loop` whenever the main thread is not sitting inside
`mainloop()`, the exception was swallowed, and the button stayed disabled forever with no
error anywhere. The worker now puts its answer in a `queue.Queue` — safe to use from any
thread — and the main thread polls that queue every 100 ms with an `after()` it scheduled
itself. Guarded by GUI tests that press the real button and wait for `_ai_busy` to clear.

**A test that skips the handoff cannot catch a handoff bug.** The GUI tests originally called
`_ai_worker()` directly and then `update()`. That passed happily while the real button was
broken. They now press the button, let the real thread run, and pump the event loop.

**Hard-coding one half of a colour pair breaks in dark mode.** The explanation box set
`background="#FAFAFA"` and left the foreground alone. In macOS dark mode the default text
colour is white, so the AI's answer rendered white on white — invisible, with every test still
green because the words were in the widget. Tkinter's defaults are right in both modes; the fix
was to stop overriding them. `base_tab.muted_colour()` picks the secondary grey from the
window's measured brightness rather than a hard-coded `#555555`. Guarded by
`test_the_explanation_is_actually_readable`, which compares the two colours rather than the text.

**A slow call with no visible feedback looks like a crash.** A reasoning model takes 5–10
seconds and the window showed nothing at all. Pressing the button now relabels it, starts an
indeterminate `ttk.Progressbar`, writes a placeholder into the box and ticks a seconds counter.

**A timing test that races the thing it measures is worse than no test.** The first version of
`test_the_user_can_see_that_the_ai_is_working` let a 0.6 s fake race a 300 ms counter and passed
four runs in five. It now drops `TICK_MILLISECONDS` to 50 for the duration.

**"Reasoning" models spend your token budget thinking, then take forever.**
`z-ai/glm-5.3-flash` thinks before answering, and the thinking is billed against the same
`max_tokens`. At 220 it used 219 thinking and returned `content: None` with
`finish_reason: "length"` — an empty answer. `MAX_TOKENS` is now 800 so any model has room.
Setting `reasoning: {"enabled": false}` is **not** a fix; that model answers HTTP 400,
*"Reasoning is mandatory for this endpoint and cannot be disabled"*. It also took **30–40
seconds** per reply, so the project settled on `google/gemini-2.5-flash-lite` at **~1.6 s**.
The model is one line in `.env`, so this is a setting, not a rewrite.

**A text box cannot render Markdown.** Gemini wrapped film titles in `*asterisks*`, which
appeared on screen as literal asterisks. The system prompt now demands plain text, and also
forbids mentioning "the algorithm" — an early reply read *"the algorithm noted that you tend
to enjoy movies around this runtime"*, which rather gives the game away.

**Bonus, not a bug:** macOS with numpy 2.x prints a false *"divide by zero encountered in
matmul"* during normal matrix multiplication. Verified false — sklearn's output matches a
hand-calculated matmul exactly, difference `0.0`. Suppressed narrowly in
`utils.quiet_blas_warning()`.

## 9. Running it

```bash
python3 main.py                                      # the desktop app
python3 main.py data/tmdb.csv                        # ...on the big Kaggle dataset
jupyter notebook notebooks/01_movie_analysis.ipynb   # Part 1
python3 -m unittest discover tests                   # 220 tests
```

Python 3.12 with `pandas`, `numpy`, `matplotlib`, `seaborn`, `scikit-learn`, `requests` and
`tkinter` (`pip install -r requirements.txt`). **No internet needed** — the dataset ships in
`data/`, and the only networked feature is the optional AI explanation, which falls back to the
offline one when there is no key or no connection.

To switch the AI explanation on: `cp .env.example .env`, then paste an OpenRouter key into it.
`.env` is in `.gitignore`.

The GUI tests skip themselves automatically on a machine with no screen.

## 10. Three things to say plainly if asked

**The model is 59% right, and that is the honest ceiling.** The remaining 41% is the script,
the cast, the marketing and the luck — none of which a spreadsheet can measure. The Predict tab
shows R² on screen for exactly this reason, so nobody mistakes an estimate for a promise.

**Budget does almost all of the work.** Genre, rating and month add under 0.01 R². That is not a
failed model; it is a real result about the film industry, and it is more interesting reported
than buried.

**The AI writes the explanation; it does not make the recommendation.** Our own code picks the
films and works out why, and those reasons are on screen before the AI is ever called. The AI
is handed them and asked to phrase them nicely. Pull the plug out of the wall and the tab still
works — it says so on screen and shows the built-in reasons instead. That is the whole point of
`BaseExplainer` having two subclasses.
