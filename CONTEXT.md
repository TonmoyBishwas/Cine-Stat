# CineStat — complete project context for an LLM

> **To the model reading this:** this file is the full reference for the CineStat repository. Answer questions about the project from it. Figures were computed from the code on the shipped dataset. If something is not covered here, say so; do not guess. Longer human-facing docs: `README.md`, `PROJECT.md` (decisions, backlog), `explain/` (plain-English walkthrough, viva Q&A).

## 1. Identity
- **What:** a Python movie-analysis project. It answers (1) *what makes a film make money?* (predict box office before production) and (2) *what should I watch next?* (an explainable recommender).
- **Course:** DS 1116, Object Oriented Programming for Data Science Laboratory, Section BA, Spring 2026. United International University, B.Sc. Data Science. The code is written to showcase the syllabus's OOP topics (see §10).
- **Repo:** github.com/TonmoyBishwas/Cine-Stat. Branch `main`. The `windows` branch is identical except for an older `setup.bat`/`run.bat`. Package version `cinestat.__version__ = "1.1"`.
- **Two parts, one core:** Part 1 is a Jupyter notebook (`notebooks/01_movie_analysis.ipynb`). Part 2 is a 5-tab Tkinter desktop app (`main.py`). Both `import` the same classes from `cinestat/`, so the analysis is written once and used twice.
- **Stack:** Python 3.12 (3.11 works), pandas, numpy, matplotlib, seaborn, scikit-learn, notebook, requests, tkinter (stdlib). Everything works offline. The only network feature is the optional AI explanation, via OpenRouter.

## 2. Running it
- **Windows:** double-click `setup.bat` once. It finds `py -3` (or `python`), creates `.venv`, pip-installs `requirements.txt`, checks Tkinter and runs the tests. Then use `run.bat` (optional arg: a data file).
  - `setup.bat` test-runs an existing `.venv`. If it's dead (for example, copied from another PC; error "No Python at 'C:\Users\<other>\…'"), it deletes and rebuilds it.
  - `run.bat` prefers `.venv`. It skips a dead one and falls back to `py -3`, then `python`, and keeps the window open on error.
  - Both `.bat` files are pinned to CRLF line endings by `.gitattributes`, because LF breaks cmd's `goto`.
- **Terminal:** `py main.py [data\tmdb.csv]` (macOS/Linux: `python3 main.py`). Tests: `py -m unittest discover tests`. Notebook: `jupyter notebook notebooks/01_movie_analysis.ipynb`.
- `main.py` defaults to `data/movies.csv`. If the file is missing it prints a hint and exits 1. Otherwise it runs `MovieApp(data_file).mainloop()`.
- **Environment variables:**
  - `CINESTAT_THEME=light|dark` forces the look.
  - `CINESTAT_UI_SCALE=1.5` fakes a high-DPI screen (clamped 1–4).
  - `OPENROUTER_API_KEY` and `OPENROUTER_MODEL` are read from the environment first, then from `.env`.
  - To enable the AI: `copy .env.example .env` and paste a key. `.env` is gitignored.

## 3. Data
- **`data/movies.csv`:** Kaggle "Movie Industry" (danielgrijalvas/movies), scraped from IMDb, 1980–2020. It has 7,668 rows and 15 columns (1.3 MB, committed so the project runs offline). Columns: `name, rating, genre, year, released, score, votes, director, writer, star, country, budget, gross, company, runtime`.
- **Cleaning** (`DataLoader.clean()`, shared by every loader):
  1. Drop duplicate rows.
  2. Drop rows with NaN budget, gross, runtime, rating or genre.
  3. Keep only rows with budget > 0 and gross > 0.
  4. Set `month` = first word of `released` (e.g. "June 13, 1980 (United States)"). Rows where that word isn't a real month name are dropped: some rows hold a year there, which would poison the seasonality analysis.
  5. Add `profit = gross − budget` and `roi = gross / budget`.
  6. Set `genre_group` = `genre`, except genres with fewer than 100 films (`MIN_GENRE_COUNT`) become "Other".
  - Result: **5,418 films** (29.3% dropped, mostly the 2,171 rows with no budget).
- **`genre_group` values:** Action 1415, Comedy 1495, Drama 862, Crime 399, Adventure 327, Biography 311, Animation 277, Horror 251, Other 81. Raw genres folded into Other: Family, Fantasy, Mystery, Romance, Sci-Fi, Thriller, Western.
- **Caveats the project admits:**
  - "Profit" ignores marketing spend, so it overstates real profitability.
  - Gross is worldwide box office, not profit.
- **Optional big dataset:** the Kaggle TMDB export (asaniczka, ~1M rows), loaded by `TMDBLoader`.
  - It streams in 200,000-row chunks inside `with pd.read_csv(chunksize=…)` so memory stays flat and the file handle closes.
  - `COLUMN_MAP` renames columns: title→name, revenue→gross, vote_average→score, vote_count→votes, genres→genre, production_companies→company.
  - It keeps only rows with status "Released", budget and gross > 0, and votes ≥ 10.
  - It takes the first listed genre and company, and converts the ISO date into "Month D, YYYY (United States)" so the parent `clean()` still works.
  - It has **no age rating** (rating = "NC-17" if adult, else "Not Rated"), no director and no star.
  - Optional `max_movies` cap.
  - Honest framing: only a small share of the million rows survive (several times 5,418, nowhere near 1M). `movies.csv` stays the default because it's richer per row.

## 4. Architecture
```
CSV → DataLoader.for_file() → MovieCollection → analyzers / SuccessPredictor → notebook or GUI
                                            └→ recommenders → explainers → GUI (Recommend tab)
```
- **Layer rule:** `cinestat/gui/` may import the core; no core module imports `gui/`. This holds today but no test enforces it (backlog B4).
- **"MVC-lite":** tabs ask the core for answers and never compute analysis themselves.
- **GUI internal order:** `platform_ui` (imports nothing from the project) → `theme` → `base_tab` → tabs → `app`.
- **Size:** about 2,120 lines of core, 2,809 of GUI, 2,815 of tests. 300 tests.

| File | Contents |
|---|---|
| `cinestat/exceptions.py` | `MovieDataError` base. Subclasses: `InvalidBudgetError`, `InvalidGrossError`, `MovieNotFoundError`, `ModelNotTrainedError`, `DataFileError`, `InvalidPreferenceError`, `AIServiceError`. Callers catch one base type. |
| `movie.py` | `Movie` |
| `collection.py` | `MovieCollection` |
| `loaders.py` | `DataLoader(ABC)` → `CSVLoader`, `JSONLoader`, `TMDBLoader`. The `for_file()` factory. |
| `analyzers.py` | `ExportMixin`, `BaseAnalyzer(ABC)` → `GenreAnalyzer`, `TrendAnalyzer`, `FinancialAnalyzer(BaseAnalyzer, ExportMixin)` |
| `predictor.py` | `SuccessPredictor` (linear regression) |
| `preferences.py` | `UserPreference` (taste profile) |
| `recommenders.py` | `Recommendation`, `BaseRecommender(ABC)` → `ContentRecommender`, `SimilarityRecommender`, `PopularityRecommender` |
| `explainers.py` | `read_env_file`, `load_setting`, `BaseExplainer(ABC)` → `RuleExplainer`, `AIExplainer`; `build_explainer()` |
| `utils.py` | `@timed`, `ExportSession` (context manager), `quiet_blas_warning()` (`@contextmanager`), `money()` |
| `gui/app.py` | `MovieApp(tk.Tk)`: window, menu, shortcuts, status bar, tabs, export |
| `gui/base_tab.py` | `BaseTab(ttk.Frame, ABC)`, `muted_colour()`, `palette_of()` |
| `gui/widgets.py` | `MoviePicker(ttk.LabelFrame)`: search box plus a list (≤200 results) |
| `gui/{browse,charts,compare,predict,recommend}_tab.py` | One class per tab |
| `gui/platform_ui.py` | Windows integration via `ctypes`/`winreg` |
| `gui/theme.py` | `Palette`, `LIGHT`, `DARK`, `WindowsTheme` |
| `tools/make_icon.py` | Draws the icon with matplotlib; writes `assets/cinestat.png` and a hand-built multi-size `.ico` (16/32/256 PNG-in-ICO) |
| `tests/` | 300 unittest tests; `helpers.py` has `make_movie()` and `make_collection(60)` fixtures |

## 5. Core classes (API)
**`Movie`** (`movie.py`)
- Class attributes: `count` (instances created), `HIT_RATIO = 2.0`.
- `__init__(name, year, genre, rating, budget, gross, score=0, votes=0, runtime=0, director, star, company, month, genre_group)`. `genre_group` defaults to `genre`.
- `__budget` and `__gross` are private, name-mangled (`_Movie__budget`), and exposed through `@property` setters. The setters raise `InvalidBudgetError` / `InvalidGrossError` for non-numeric or negative values.
- Read-only properties:
  - `profit`
  - `roi` (0 if budget is 0)
  - `verdict`: "Hit" if roi ≥ 2, "Break-even" if roi ≥ 1, else "Flop"
- Dunders:
  - `__str__`: "Name (year) - genre, $gross gross"
  - `__repr__`
  - `__eq__`/`__hash__`: by (name, year)
  - `__lt__`/`__gt__`: compare **gross**
- `to_dict()`; `@classmethod from_row(row)` is an alternative constructor.

**`MovieCollection`** (`collection.py`)
- Composition: *has a* `_movies` list; it is not a subclass of `Movie`.
- Dunders:
  - `__len__`, `__iter__`, `__contains__`
  - `__getitem__`: a slice returns a `MovieCollection`
  - `__add__`: concatenates two collections
  - `__str__`, `__repr__`
- `add()` rejects anything that isn't a `Movie` (`TypeError`).
- `find(name)`: case-insensitive exact match; raises `MovieNotFoundError`.
- `names()`
- **Generators:** `filter_by(**criteria)`, `search(text)`, `in_year_range(a, b)`.
- `top_by(attr, n)`, `genres()`, `ratings()`, `year_bounds()`, `to_dataframe()`.

**`DataLoader(ABC)`** (`loaders.py`)
- `__init__` raises `DataFileError` if the path is missing.
- `@abstractmethod load()`.
- Inherited `clean()`, `load_clean()`, `to_collection()` (one `Movie.from_row` per row).
- `@classmethod for_file(path)` is a **factory method**:
  - `.json` → `JSONLoader`
  - otherwise it reads the header line: `revenue` present and `name` absent → `TMDBLoader`, else `CSVLoader`.
- Loaders wrap read errors in `DataFileError`.

**Analyzers** (`analyzers.py`)
- `BaseAnalyzer(collection)` stores `df = collection.to_dataframe()`.
- Abstract `analyze()` and `summary()`.
- `@timed run()` sets `self.results`; `report()` prints the title and findings.
- Subclasses:
  - `GenreAnalyzer`: per `genre_group`, the columns movies, avg_budget, avg_gross, avg_profit, median_roi, avg_score, flop_rate%. Sorted by median_roi.
  - `TrendAnalyzer`: per year.
  - `FinancialAnalyzer`: per rating, sorted by avg_gross. Also exports, via `ExportMixin.export(path)` → `ExportSession`.
- The polymorphism: all of them answer `.run()`.

**`UserPreference`** (`preferences.py`)
- Class attributes: `SCORE_MIN=0`, `SCORE_MAX=10`, `TOP_GENRES=3`, `SCORE_SLACK=1.0`.
- Private `__genres`, `__ratings`, `__min_score`, each behind a validating property. The validation raises `InvalidPreferenceError`: a bare string instead of a list, a score outside 0–10, non-integer years, or `year_from > year_to`.
- Public: `year_from=1900`, `year_to=2100`, `preferred_runtime`, `preferred_year`, `liked_titles` (a list that keeps order).
- Properties `is_empty` and `last_liked`. Methods `add_liked`, `remove_liked`.
- `allows(movie)` applies the **hard filters**: year range, score ≥ min_score, rating in ratings (if any are set).
- `likes_genre()`.
- Dunders: `__contains__` (title ticked?), `__len__` (films ticked), `__str__` (e.g. "genres: … | IMDb 7.3+ | around 131 min | 3 films ticked").
- `@classmethod from_movies(movies, top_genres=None, use_ratings=False)` infers the profile:
  - the top 3 `genre_group`s by count;
  - min_score = average score − 1 (rounded to 0.1);
  - preferred_runtime and preferred_year = the averages;
  - ratings are copied only if `use_ratings` is set.

**`utils.py`**
- `@timed` prints "[timed] func took X ms" (it uses `functools.wraps`).
- `ExportSession(path)`:
  - `__enter__` makes the parent directories and opens the file (wrapping `OSError` in `DataFileError`).
  - `write(rows)` writes JSON if the suffix is `.json`, otherwise CSV via `DictWriter`.
  - `__exit__` closes the file and returns False, so exceptions still propagate.
- `quiet_blas_warning()` suppresses only the "…encountered in matmul" `RuntimeWarning`. That warning is false and comes from macOS Accelerate with numpy 2.x; it's a no-op on Windows/OpenBLAS.
- `money(v)` formats as `$1.23B`, `$138.4M`, `$250K`, `$12`.

## 6. The prediction model (`SuccessPredictor`)
- **Features:** `NUMERIC = [budget, runtime, year]` and `CATEGORICAL = [genre_group, rating, month]`, one-hot encoded with `pd.get_dummies(drop_first=True)`. Target: `gross`.
- **Model:** `make_pipeline(StandardScaler(), LinearRegression())`.
- **`train(test_size=0.2, random_state=42)`:** an 80/20 split. It sets `r2`, `mae`, `columns`, `coefficients` (a Series of dollars per standard deviation) and `is_trained`, and returns R².
- **`budget_only_r2()`:** the same pipeline with budget as the only feature. This is the honest comparison.
- **`predict(budget, genre, rating, runtime, year, month)`:**
  - raises `ModelNotTrainedError` before training;
  - raises `InvalidBudgetError` if budget isn't numeric or ≤ 0;
  - reindexes the one-hot columns to the training columns, clamps gross ≥ 0;
  - returns `{gross, profit, roi, verdict, r2, mae}`. The verdict uses the same thresholds as `Movie`.
- `top_coefficients(n)`, `options()` (the dropdown choices), `__str__`.
- **Results:**

| | Value |
|---|---|
| Full-model test R² | **0.5884** |
| Budget-only R² | **0.5786** |
| MAE | **$66.9M** |
| Top standardized coefficients | budget +123.3M, runtime +16.4M, Animation +15.8M, Horror +9.7M, year +8.6M, June +8.0M, July +7.6M, May +7.3M |
| Log₁₀(gross) variant (notebook only) | R² 0.436 |

  - Genre, rating and month together add under 0.01 R². Budget does almost all the work.
  - Example: $50M, Action, PG-13, 120 min, 2020, July (the Predict tab defaults) predicts about $159.1M gross, $109.1M profit, ROI 3.18 → **Hit**.
- **Why this design:**
  - **Leakage:** `score` and `votes` are excluded because they only exist after release.
  - It predicts gross and then derives the verdict, because regressing ROI directly gives R² ≈ 0.05 (noise).
  - Linear regression was chosen because it's explainable; the goal is to show that budget dominates, not to squeeze out accuracy.
  - The remaining ~41% is script, cast, marketing and luck.
- **The scaler bug (a key story):**
  - Without scaling, budget (~1e8) next to 0/1 dummy columns made the feature matrix ill-conditioned (condition number 3.5e10).
  - The solver zeroed every coefficient except budget (runtime's coefficient was 0.00000046 $/min). The full model scored exactly the budget-only score, 0.578563, to six decimals.
  - Nothing crashed and nothing warned. Fixed by adding `StandardScaler`.
  - That ill-conditioning was also the real cause of the matmul warning.
  - Guarded by `test_the_extra_features_are_actually_being_used` and `test_the_coefficients_are_not_all_crushed_to_zero`.

## 7. Recommender and explainers
**`Recommendation(movie, score, reasons, source)`**
- A value object. `score` is clamped to 0–100.
- `match` → "82%".
- `__lt__` compares by score, so `sorted()` ranks them. `__eq__`/`__hash__` go by movie.
- `to_dict()` adds `match_score`, `reasons` (joined with " ; ") and `recommender`.

**`BaseRecommender(collection, preference=None)`: the template-method pattern**
- `@abstractmethod score_movie(movie) → (score, [reasons])`.
- `candidates()` is a generator that skips ticked films (`movie in preference`) and films failing `preference.allows()`.
- `@timed recommend(n=10, min_score=1.0)`: filter → score → drop anything under min_score → sort descending → take the top n. Subclasses override only `score_movie`.
- It uses `UserPreference() if preference is None else preference`, not `preference or …`. `UserPreference` defines `__len__`, so a profile with no ticked films is falsy and would be silently discarded (the bug is documented, and a test guards it).

| Recommender (`title`) | Scoring (points out of 100; every point appends an English reason) |
|---|---|
| `ContentRecommender` ("Matches my taste", the default) | **Genre 40** (in the favourite genres; 20 if the user has no genre preference) · **IMDb quality 25** (score/10×25; reason given if ≥ 7.5) · **Rating 15** (in the preferred ratings) · **Runtime 10** (linear falloff to 0 at 45 min away; reason if ≤ 15) · **Era 10** (falloff to 0 at 30 years; reason if ≤ 5). Fallback reason: "a reasonable all-round match". The weights are class attributes. |
| `SimilarityRecommender` ("Similar to my last pick") | Compares against one seed film (default: `preference.last_liked`): same genre 35, same rating 15, score closeness 25 (falloff at 2.5 points), runtime 15 (falloff at 40 min), era 10 (falloff at 20 years). Its `__init__(…, seed=None)` calls `super().__init__`. Without a seed it scores 0, and the GUI shows "Pick a film first". |
| `PopularityRecommender` ("Most popular (baseline)") | Ignores taste: score/10×60 + min(1, votes/500,000)×40. It exists as an honest baseline, the same idea as the budget-only R². |

**Explainers**
- `BaseExplainer(ABC)`: abstract `explain(rec, pref)`, `is_available`, `header()`.
- `RuleExplainer` works offline and is the default. Its output is a header, "Why you might like it:", the capitalised reason bullets, and "Based on the films you ticked: …" (up to 4 titles).
- `AIExplainer`:
  - Calls OpenRouter: `POST https://openrouter.ai/api/v1/chat/completions`, `DEFAULT_MODEL="google/gemini-2.5-flash-lite"` (~1.6 s), `TIMEOUT_SECONDS=60`, `MAX_TOKENS=800`.
  - `import requests` happens inside the method, so the app runs even without the library.
  - The system prompt asks for 2–4 plain-text sentences, no invented facts, no scores, no mention of "the algorithm", no Markdown.
  - `build_prompt()` sends the film's facts, the reasons and up to 6 liked titles.
  - Errors are raised as `AIServiceError` with hints: 401 bad key, 402 no credit, 404 retired model slug ("NOT a problem with your key"), 429 rate limit. An empty reply with `finish_reason=length` gets a "raise MAX_TOKENS" message.
  - `explain_or_fallback()` catches `AIServiceError`, stores `last_error`, and returns the `RuleExplainer` text. It has the fallback by composition.
- `build_explainer()` is a factory: AI if a key exists, else Rule.
- **Principle:** the AI never chooses films. It only rephrases reasons our own code computed. As a result:
  - every suggestion is explainable;
  - the tab works with no key or internet;
  - the AI can't invent a film.
- **Model history:**
  - The old default, `anthropic/claude-3.5-haiku`, was retired (HTTP 404, which looked like a bad key). A test now keeps the default in sync with README and `.env.example`.
  - `z-ai/glm-5.3-flash` was rejected. It's a reasoning model: at 220 tokens it spent 219 thinking and returned empty content, it took 30–40 s, and it can't disable reasoning (HTTP 400).

## 8. GUI (`MovieApp`, Tkinter/ttk)
- **Startup:**
  1. `platform_ui.prepare_process()` sets DPI awareness and the AppUserModelID.
  2. `tk.Tk`, then `WindowsTheme(...).apply()`, the icon, and centring (1180×760 window, minimum 980×660, all through `px()`).
  3. The status bar ("Loading…").
  4. `_load_data()`: `DataLoader.for_file().to_collection()`, then `SuccessPredictor.train()`. A `MovieDataError` shows an error dialog and destroys the window.
  5. Status "Ready - 5,418 films from 1980 to 2020 | model R-squared 0.588".
  6. The menu, tabs and shortcuts are built. Data is loaded once and shared by every tab.
- **`BaseTab(ttk.Frame, ABC)`:**
  - abstract `build_ui()`;
  - properties `movies`, `predictor`, `theme`, `palette`, `px()`;
  - `add_heading()`;
  - it overrides `__repr__`, **never `__str__`**: Tk uses `str(widget)` as the widget path, so overriding it breaks `notebook.add` with "bad window path name".
- **Tabs** (`TAB_CLASSES`, built polymorphically in one loop):
  - **Browse:** a Treeview (Title, Year, Genre, Rating, Runtime, IMDb, Budget, Box office, Profit, ROI, Verdict). Title search; filters for genre, rating and year range; reset; clicking a heading sorts, with ▲/▼ in the heading; striped rows. Exposes `current_rows()`.
  - **Charts:** a Combobox over `self.charts`, a dict mapping a name to a method (functions as objects). The 8 charts:
    - average box office by genre
    - ROI by genre
    - flop rate by genre
    - budget and box office over time
    - budget vs box office scatter
    - budget vs IMDb score
    - average gross by release month
    - budget vs box office by age rating
    
    Uses `FigureCanvasTkAgg` and `NavigationToolbar2Tk` (zoom/save), themed. Figure dpi = 100 × scale.
  - **Compare:** two `MoviePicker`s and a 14-row table (year, genre, rating, runtime, director, star, studio, IMDb, votes, budget, box office, profit, ROI, verdict). The bigger value is highlighted for box office, profit, ROI, IMDb and votes. The winner line uses `first > second` (`Movie.__gt__`), e.g. "X took $…M - 2.3x more than Y". Same film twice and equal gross are special-cased.
  - **Predict:** a form with budget (default 50000000), genre (Action), rating (PG-13), runtime (120), year (latest) and month (July). Output: predicted gross, budget, profit (green/red), ROI, the Hit/Break-even/Flop verdict coloured via palette names (positive/warning/negative), a sentence explaining the verdict, and a "how much to trust this" note showing R² and MAE. Bad input shows a message box, never a crash.
  - **Recommend:**
    - Left panel: a MoviePicker, then Add, Remove and Clear, the liked list, and the inferred profile (`str(UserPreference)`).
    - Settings: Method combobox (`ENGINES = {cls.title: cls}` from `ENGINE_CLASSES`), minimum IMDb spinbox (0–10, step 0.5; it can only *raise* the inferred floor), and a year range.
    - The Recommend button shows the top 15 (`HOW_MANY`) in a table (Match, Title, Year, Genre, Rating, IMDb, Runtime). The top row is selected, and `show_reasons()` is called directly, because `selection_set()` only queues `<<TreeviewSelect>>`.
    - Selecting a row shows the `RuleExplainer` text instantly.
    - **Explain with AI** runs `AIExplainer.explain_or_fallback` on a daemon `threading.Thread`. The worker never touches Tk: it puts `(text, problem, model)` on a `queue.Queue`, and the main thread polls it every 100 ms via `after()`.
    - While waiting, the button is relabelled, an indeterminate progress bar runs, and a seconds counter ticks every 300 ms.
    - The result shows "Written by <model> in Ns", or the built-in reasons plus the failure reason.
    - Exports its results.
- **Menu:**
  - File: Export current view as CSV (Ctrl+E) / JSON (Ctrl+Shift+E), Exit (Alt+F4).
  - View: 5 tabs (Ctrl+1–5).
  - Help: About (F1).
  - Also Ctrl+Tab / Ctrl+Shift+Tab to cycle tabs. Menus have underlined Alt letters, with no duplicates within a menu (`_free_mnemonic`).
  - Export uses **duck typing**: `active_tab()` returns the current tab if it has `current_rows()` (Browse, Recommend), else Browse. It writes through `ExportSession`.
  - `platform_ui.shortcut(key, shift)` returns both the menu label and the Tk sequence, so the advertised and bound keys can't drift (`accelerator=` only draws text; `bind_all` does the binding). Tk needs a capital letter after Shift: `<Control-Shift-E>` vs `<Control-e>`.

## 9. Windows edition (`platform_ui.py` + `theme.py`)
- **Problems it solves on Windows:**
  - no dark mode;
  - blurry text at 125–150% scaling;
  - Mac fonts and ⌘ shortcuts;
  - the python.exe icon and taskbar grouping.
- **`platform_ui`:**
  - `set_dpi_awareness()`: `shcore.SetProcessDpiAwareness(1)`, falling back to `user32.SetProcessDPIAware()`.
  - `set_app_user_model_id("UIU.DS1116.CineStat.Windows")`.
  - `screen_scale()`: `GetDpiForWindow`/96, or `GetDeviceCaps(88)`, or the env override.
  - `system_theme()`: registry `AppsUseLightTheme` under HKCU `…\Themes\Personalize`.
  - `accent_colour()`: from the DWM registry.
  - `readable_on()` picks black or white text by brightness.
  - `use_dark_titlebar()`: `DwmSetWindowAttribute`.
  - `set_window_icon()`, `centre_on_screen()`, `shortcut()` (Cmd on macOS, Ctrl elsewhere).
  - Every call checks `sys.platform` and catches `OSError`/`AttributeError`, so the same source runs on macOS, Linux and old Windows.
- **`theme`:**
  - `Palette` holds named colours: window, surface, field, text, muted, border, button, hover, pressed, accent, accent_text, positive, negative, warning, stripe, first_wins, second_wins.
  - `LIGHT` (window #F3F3F3, accent #0078D4) and `DARK` (window #202020, text #F2F2F2).
  - `WindowsTheme(root, mode, scale)` *has a* `Palette` (composition). The system accent replaces the palette accent.
  - Fonts fall back in order: Segoe UI / Semibold / Light, then Helvetica Neue, DejaVu Sans, Helvetica.
  - Methods: `px()`, `font()`, `apply()`, `text_options()`/`listbox_options()` (always return both halves of a colour pair), `menu_options()`, `prepare_table()`/`stripe_row()`, `chart()`, `style_axes`/`style_legend`/`style_toolbar` (for the matplotlib toolbar icons).
  - It uses ttk's **"clam"** theme repainted to look like Windows 11, not "vista". Vista imitates Windows 7 and can't be recoloured (Windows draws it), so it could never have a dark mode.
- **Rules the tests enforce:**
  - No file in `gui/` other than `theme.py` writes a colour literal (checked with Python's `tokenize`).
  - Every pixel size goes through `px()`.
  - Both palettes define the same keys and are readable.
  - Every advertised shortcut is bound.
- **Small Windows habits:** a resize grip, striped rows, sort arrows in headings, heading alignment matching the column, an accent-coloured primary button per tab, "All files (*.*)" in Save dialogs, and a fixed `selectbackground` on read-only comboboxes.

## 10. Syllabus / OOP map (lecture "Class" → where it lives)
| Class | Topic | Location |
|---|---|---|
| 2 | Classes, constructors, instance variables | `Movie.__init__` |
| 3 | Encapsulation, name mangling | `Movie.__budget/__gross`; `UserPreference.__genres/__ratings/__min_score` with validating properties |
| 3 | Static vs instance members | `Movie.count`, `Movie.HIT_RATIO`; recommender weights |
| 3 | Composition | `MovieCollection` has Movies; `WindowsTheme` has a `Palette`; `AIExplainer` has a `RuleExplainer` |
| 4 | Abstraction, inheritance, overriding | `DataLoader`, `BaseAnalyzer`, `BaseRecommender`, `BaseExplainer`, `BaseTab` (all ABCs) |
| 4 | Template method | `BaseRecommender.recommend()` |
| 4 | Factory | `DataLoader.for_file()`, `build_explainer()`; alternative constructors `Movie.from_row`, `UserPreference.from_movies` |
| 5 | Polymorphism | `.run()` on the analyzers; `.recommend()`; `.explain()`; `.load()`; the tabs built in one loop |
| 5 | Duck typing | `MovieApp.active_tab()` / `current_rows()` |
| 5 | Operator overloading | dunders on `Movie`, `MovieCollection`, `UserPreference`, `Recommendation` |
| 5 | Multiple inheritance, mixin | `FinancialAnalyzer(BaseAnalyzer, ExportMixin)`; `BaseTab(ttk.Frame, ABC)` |
| 7 | Tkinter widgets, layout, callbacks, theming | `cinestat/gui/`; `WindowsTheme.apply()` |
| 8 | MVC-lite, multi-file GUI | core vs `gui/` |
| 9 | Custom exceptions; file I/O; pathlib; context managers | `exceptions.py`; `ExportSession`, `quiet_blas_warning`, `with pd.read_csv(chunksize)`, `read_env_file`; ctypes/winreg OS calls |
| 10 | unittest, modules, packages | `tests/`; the `cinestat` and `cinestat.gui` packages |
| 11 | Decorators | `@timed` on `BaseAnalyzer.run` and `BaseRecommender.recommend` |
| 11 | Iterators, generators | `MovieCollection.__iter__`, `filter_by`, `search`, `in_year_range`, `candidates()` |
| 11 | Functions as objects | `ChartsTab.charts` (name → method); `RecommendTab.ENGINES` (label → class) |
| 12 | Multithreading | the AI call in `recommend_tab.py` (thread + queue) |

Deliberately uses pandas and scikit-learn rather than hand-written maths, which matches the syllabus reading (McKinney) and CO3, "framework-specific libraries".

## 11. Findings (on the 5,418 cleaned films)
| Question | Answer |
|---|---|
| Does budget buy box office? | Yes: correlation **0.74**, regression slope about **$3.33 per $1** |
| Does budget buy quality? | No: budget vs IMDb score correlation **0.072** (about zero) |
| Best ROI genre | **Horror**, median ROI **3.08×** (251 films); then Animation 2.92×; worst Crime 1.30× |
| Safest genre | **Animation**, **15.5%** flop rate (Horror 19.9%; worst Crime 44.1%, Drama 39.8%) |
| Highest average gross genre | Animation, $281M per film; Action $168M |
| Overall risk | **32.1%** of films gross less than their budget. Verdicts: Hit 2,567 · Break-even 1,110 · Flop 1,741 |
| Age rating (meaningful sample sizes) | G $189M avg gross (median ROI 2.71) > PG-13 $154M > PG $138M ≫ R $56M (1.56). R is the most common rating (2,595). `FinancialAnalyzer.summary()` literally names TV-MA ($350M), which is only 2 films. |
| Release month (mean gross) | Best May $169.7M, June $167.2M, December $154.4M, July $151.9M. Worst **September $53.8M**, then October $60.0M, January $63.3M. By median, June is best and September worst. |
| Trend | Average budget $11.6M (1980) → $107.7M (2020), 9.3×. Average IMDb score 6.51 → 6.61. |
| Biggest | Top gross: Avatar $2.85B, Avengers: Endgame $2.80B, Titanic $2.20B. Most profitable: Avatar, $2.61B. |
| Predictability | R² 0.588 overall vs 0.579 for budget alone; MAE about $67M |

## 12. Notebook (Part 1)
54 cells, executed with outputs saved. Sections:
- 0 Setup
- 1 Load and inspect
- 2 Clean (including the `released` month trap)
- 3 Budget/revenue distributions
- 4 Leaderboards
- 5 Which genre to invest in
- 6 Industry change since 1980
- 7 Age rating vs money
- 8 Correlations
- 9 Budget vs box office
- 10 Does money buy a better film
- 11 Release timing and risk
- 12 Linear regression (leakage, the budget-only comparison, the log variant)
- Summary of findings

It uses the same `cinestat` classes as the app.

## 13. Bugs found and fixed (the "traps", each guarded by a test)
1. **The scaler bug** (§6): the model silently ignored every feature except budget.
2. **`__str__` on a Tk widget** breaks the widget path ("bad window path name"). Override `__repr__` instead.
3. **`x or default` on a class with `__len__`** threw away an empty but real `UserPreference`. The same risk exists with `MovieCollection`.
4. **`MoviePicker` fired its callback during `__init__`** into a half-built tab. It now takes `notify=False` during setup.
5. **`tree.selection_set()` doesn't fire `<<TreeviewSelect>>` immediately.** The code calls `show_reasons()` directly.
6. **The chunked `read_csv` leaked its file handle** on an early stop or error. It's now a `with` block (caught with `-W error::ResourceWarning`).
7. **Tk from a worker thread:** the first version called `self.after(0, …)` from the worker. That raises "main thread is not in main loop", the error was swallowed, and the button stayed disabled forever. The fix is the Queue plus main-thread polling. The tests press the real button, let the real thread run, and pump the event loop (the earlier tests bypassed the handoff and missed the bug).
8. **White on white:** hard-coding only the background of the explanation box made the text invisible in dark mode. Colours are now always set in pairs (`text_options()`); a test compares the actual colours.
9. **No feedback during a slow AI call** looked like a crash. Added a progress bar, a relabelled button and a counter.
10. **A flaky timing test:** a 0.6 s fake raced a 300 ms tick. The test now sets `TICK_MILLISECONDS=50`.
11. **Reasoning models** returned empty replies at `MAX_TOKENS=220`. It's now 800, and the default is a non-reasoning model.
12. **Markdown asterisks** appeared literally in the Tk text box. The prompt now demands plain text and forbids mentioning "the algorithm".
13. **A retired model slug** gave a 404 that looked like a bad key. There's now a hint message and a test pinning the default model to the docs.
14. **Windows-specific:**
    - `accelerator=` doesn't bind anything;
    - Shift needs a capital letter in the sequence;
    - clam's `style.map` padding overrode `style.configure` on the selected notebook tab;
    - matplotlib chose black toolbar icons before the repaint, so they re-render;
    - disabled toolbar buttons were stippled white.
15. **A `.venv` copied from another PC** (a dead interpreter path) broke `setup.bat`. It's now detected and rebuilt (§2).

## 14. Tests
300 unittest tests in about 5 s (`py -m unittest discover tests`). Counts per file:

| File | Tests |
|---|---|
| test_gui | 46 |
| test_explainers | 44 |
| test_collection | 31 |
| test_theme | 31 |
| test_preferences | 28 |
| test_recommenders | 30 |
| test_platform_ui | 24 |
| test_predictor | 24 |
| test_movie | 23 |
| test_loaders | 19 |

- **No test touches the network.** A fake `requests` module in `sys.modules` simulates success, 401, a dead connection, a malformed reply and an empty reply.
- GUI tests build real windows and skip when there's no screen or no `data/movies.csv`.
- The suite passes in light mode, dark mode and at 1.5× scale. 71 tests were added with the Windows edition.

## 15. Limitations and backlog
- **Limitations:**
  - R² is capped at about 0.59.
  - The profit figure excludes marketing.
  - The recommender is content-based only (no user-history data exists).
  - The TMDB dataset lacks ratings, directors and stars.
  - Loading and training run on the main thread, so there's a startup pause.
- **Backlog** (from PROJECT.md, priority order):
  - **B1** a predictor hierarchy, `BasePredictor(ABC)` → `AveragePredictor` / `BudgetOnlyPredictor` / `FullPredictor`. The model layer currently has no ABC or polymorphism; this is the top item.
  - **B2b** threaded startup with a progress bar.
  - **B3** model serialization.
  - **B4** an architecture test (the core never imports `gui`).
  - **B5** "why this prediction", a per-feature contribution breakdown.
  - **B6** a console mode (`python -m cinestat.console`).
  - **B9** "because you liked X" reasons.
  - **B8** an insights tab, deliberately cut.
  - Done: B2 (the AI thread), B7 (the similarity recommender), W1 (the Windows UI).
- **Rules for new code:**
  - Analysis goes in `cinestat/`, never in a tab.
  - New charts: add an entry to `ChartsTab.charts`.
  - New recommenders: subclass `BaseRecommender`, override only `score_movie`, add to `ENGINE_CLASSES`.
  - Keep weights as class attributes.
  - No API key in source code or tests.
  - No colour literals or raw pixels in tabs.
  - Shortcuts come only from `shortcut()`.
  - Every class gets tests.

## 16. Known doc inconsistencies (trust the code and this file)
- README's findings table and the notebook's takeaway text say "January is the worst" month to release. The data (and the notebook's own printed output) says **September** is worst; January is third-lowest by mean.
- README's syllabus table says the AI thread hands its reply back with `self.after(0, …)`. The actual code uses a `queue.Queue` polled by the main thread; `after(0)` from the worker was the bug that got fixed (§13.7).
- The README and PROJECT.md headers still say "you are reading the `windows` branch". That content is merged into `main`.
