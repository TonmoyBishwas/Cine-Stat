# 2. The files, one by one

[← what the project does](01-what-the-project-does.md) · [back to index](README.md) · [next: how it fits together →](03-how-it-all-fits-together.md)

---

Every Python file in the project, what it does, and why it exists.

The project has **three groups** of files:

- **The core** (`cinestat/`) — all the thinking. No windows, no buttons.
- **The interface** (`cinestat/gui/`) — all the clicking. No thinking.
- **The tests** (`tests/`) — proof that the first two work.

---

## Quick map

| File | Lines | Its one job |
|---|---:|---|
| **The core — `cinestat/`** | | |
| `exceptions.py` | 52 | The list of things that can go wrong |
| `movie.py` | 169 | One film |
| `collection.py` | 139 | All the films together |
| `loaders.py` | 310 | Reading and cleaning the data file |
| `analyzers.py` | 164 | The statistics |
| `predictor.py` | 207 | The prediction model |
| `preferences.py` | 257 | What one person likes |
| `recommenders.py` | 319 | Choosing films to suggest |
| `explainers.py` | 383 | Writing the suggestion up in words |
| `utils.py` | 142 | Small shared helpers |
| `__init__.py` | 54 | The package's front door |
| **The interface — `cinestat/gui/`** | | |
| `app.py` | 319 | The window itself |
| `base_tab.py` | 123 | What every tab has in common |
| `widgets.py` | 77 | Our own film-picker widget |
| `browse_tab.py` | 225 | The Browse tab |
| `charts_tab.py` | 195 | The Charts tab |
| `compare_tab.py` | 136 | The Compare tab |
| `predict_tab.py` | 207 | The Predict tab |
| `recommend_tab.py` | 572 | The Recommend tab |
| `platform_ui.py` | 322 | Talking to Windows *(Windows branch)* |
| `theme.py` | 622 | Every colour and size *(Windows branch)* |
| **Starting it** | | |
| `main.py` | 49 | The thing you actually run |

---

# The core

This is the half that would still make sense if the window were deleted
tomorrow.

---

## `exceptions.py` — the list of things that can go wrong

**Its job:** define the project's own error types.

Python has built-in errors like `ValueError`. This file adds errors that mean
something specific to *this* project:

```
MovieDataError                  <- the parent of all of them
    ├── InvalidBudgetError      "that budget is negative or isn't a number"
    ├── InvalidGrossError       "same, for box office"
    ├── MovieNotFoundError      "no film by that name"
    ├── ModelNotTrainedError    "you asked for a prediction before training"
    ├── DataFileError           "the data file is missing or unreadable"
    ├── InvalidPreferenceError  "a minimum IMDb score of 15 is impossible"
    └── AIServiceError          "the AI service could not be reached"
```

**Why bother?** Because of the arrow shape. Every one of them is a kind of
`MovieDataError`. So the window can write:

```python
except MovieDataError as error:
    messagebox.showerror("Something went wrong", str(error))
```

...and catch all seven with one line. A bad budget, a missing file and a dead
internet connection all end up as a polite dialog box instead of a crash.

It is the first file to read because it imports nothing. Everything else
depends on it; it depends on nothing.

---

## `movie.py` — one film

**Its job:** turn one row of the spreadsheet into one object.

A row of the CSV is just text. A `Movie` is that row with a brain: it knows how
to validate itself, it can work out its own profit, and it can be compared to
another film.

**What it holds:** name, year, genre, rating, runtime, score, votes, director,
star, company, month — plus budget and box office.

**The three interesting parts:**

**1. Budget and box office are protected.** They are stored as `__budget` and
`__gross` — the two underscores make Python hide them. You cannot reach in and
set a negative budget. If you try:

```python
movie.budget = -5      # raises InvalidBudgetError
```

The check runs every single time, because reading and writing `movie.budget`
secretly runs a method. From the outside it still looks like an ordinary
attribute, which is the nice part — the protection costs the person using it
nothing.

**2. Some things are calculated, not stored.** Profit, ROI and the verdict are
worked out on demand:

```python
profit  = gross - budget
roi     = gross / budget
verdict = "Hit" if roi >= 2 else "Break-even" if roi >= 1 else "Flop"
```

They are never saved anywhere, so they can never disagree with the numbers they
come from. Change the budget and the profit changes with it, automatically.

**3. Films can be compared with `>` and `<`.** Because the file defines what
those symbols mean for a film (bigger box office wins), the Compare tab can
simply write `film_a > film_b` instead of
`film_a.gross > film_b.gross`, and `sorted(movies)` just works.

**Also worth knowing:** `Movie.count` quietly counts how many films have ever
been created, and `Movie.HIT_RATIO = 2.0` is the rule for what counts as a hit.
Both belong to the class as a whole, not to any one film — change `HIT_RATIO`
once and every film in the project re-judges itself.

---

## `collection.py` — all the films together

**Its job:** hold thousands of `Movie` objects and make them easy to work with.

You could just use a plain Python list. This is better, because it behaves
*like* a list while also knowing things a list could not:

```python
len(movies)                    # how many films
movies[0]                      # the first one
for film in movies: ...        # loop through them
film in movies                 # is this one in here?
movies_a + movies_b            # glue two collections together
```

All of that works because the file says what each of those operations means.

On top of that it adds the things a film library actually needs:

| Method | What it gives you |
|---|---|
| `find("Titanic")` | one film by name (or a clear error) |
| `search("star")` | every film with "star" in the title |
| `filter_by(genre="Horror")` | every horror film |
| `in_year_range(1990, 1999)` | everything from the nineties |
| `top_by("gross", 10)` | the ten biggest earners |
| `genres()` / `ratings()` | the distinct values, for filling dropdowns |
| `year_bounds()` | the earliest and latest year |
| `to_dataframe()` | back to pandas, for charts and statistics |

**One detail worth understanding**, because it comes up in the viva:
`search`, `filter_by` and `in_year_range` use `yield` instead of building a
list. That makes them **generators** — they hand back films one at a time as
you ask for them, instead of building a second complete copy of the library in
memory first. With 5,418 films it hardly matters; with the optional million-row
dataset it matters a great deal.

---

## `loaders.py` — reading and cleaning the data

**Its job:** get from a file on disk to a `MovieCollection`.

This is the most structurally interesting file in the project, so it is worth
slowing down.

There are **three** loaders, and they share one parent:

```
DataLoader  (the parent - cannot be used on its own)
   ├── CSVLoader     reads a normal .csv
   ├── JSONLoader    reads a .json
   └── TMDBLoader    reads the enormous Kaggle file
```

**The parent writes down the cleaning steps once**, and all three inherit them:

- drop duplicate rows
- drop films with no budget, box office, runtime, rating or genre
- drop films where budget or box office is zero
- pull the month out of text like `"June 13, 1980 (United States)"`
- calculate `profit` and `roi`
- group rare genres together as `"Other"` so charts stay readable

**Each child only writes the one bit that differs** — how to physically read
the file. `CSVLoader` calls `pd.read_csv`. `JSONLoader` calls `pd.read_json`.
That is the entire difference between them.

**The clever bit: you never choose the loader yourself.**

```python
movies = DataLoader.for_file("data/movies.csv").to_collection()
movies = DataLoader.for_file("data/tmdb.csv").to_collection()
```

`for_file` peeks at the first line of the file, looks at the column names, and
hands back whichever loader is right. Both lines above work, and **the rest of
the program cannot tell the difference**. Every analyzer, the model, all five
tabs — none of them know or care which file was opened.

**`TMDBLoader` solves two real problems**, and they are good ones to mention:

1. *The file is too big to open.* Several million rows would fill the
   computer's memory. So it is read in **chunks** of 200,000 rows, each chunk
   is filtered down immediately, and the rejects are thrown away. Memory use
   stays flat no matter how large the file is.
2. *The column names are wrong.* TMDB calls the box office `revenue` and the
   title `title`. A small translation dictionary renames them into the names
   the rest of CineStat already understands.

---

## `analyzers.py` — the statistics

**Its job:** answer the analytical questions.

Three analyzers, all built the same way:

| Class | Answers |
|---|---|
| `GenreAnalyzer` | Which genre earns most? Which is safest? Best return? |
| `TrendAnalyzer` | How has the industry changed since 1980? |
| `FinancialAnalyzer` | Profit, risk, and the effect of the age rating |

They share a parent, `BaseAnalyzer`, which handles everything they have in
common — holding the data, running, printing a report — and forces each child
to supply exactly two things:

- `analyze()` — do the calculation, return a DataFrame
- `summary()` — say what it means, in short English sentences

The payoff is that **all three are used identically**:

```python
for analyzer in [GenreAnalyzer(movies), TrendAnalyzer(movies),
                 FinancialAnalyzer(movies)]:
    analyzer.report()
```

The loop has no idea which one it is holding. Adding a fourth kind of analysis
means writing one small class and adding it to that list — no other file
changes.

The calculations themselves are ordinary pandas — `groupby`, `agg`, `mean`,
`median` — so the data-analysis part will look completely familiar.

`FinancialAnalyzer` also gains a `.export()` method by inheriting from a second
small class called `ExportMixin`. A "mixin" is a class whose only purpose is to
lend one ability to another class.

---

## `predictor.py` — the prediction model

**Its job:** "if I spend this much on this kind of film, what will it earn?"

This is the Predict tab's engine. It is a **linear regression** from
scikit-learn.

**What it learns from:** budget, runtime, year, genre, age rating, release
month — and nothing else. As explained in
[part 1](01-what-the-project-does.md), IMDb score and vote count are left out
on purpose, because they only exist after release. Using them would be **data
leakage**.

**How it works, step by step:**

1. Text columns (genre, rating, month) become 0/1 columns — "one-hot encoding",
   because a regression can only do arithmetic, not read words.
2. Every column is put on the **same scale** (see the warning below).
3. 80% of the films train the model; **20% are held back** and used to test it.
   Testing on the same films it learned from would flatter it enormously.
4. The result is scored with **R²** — how much of the variation between real
   films the model explains.

**The numbers:**

| | |
|---|---|
| Full model | **R² 0.588** |
| Budget only | **R² 0.579** |
| Average error | about **$67 million** |

**Why the budget-only number is reported too:** because the honest conclusion
of this project is that *budget does almost all of the work*. Genre, rating and
month together add less than 0.01. Hiding that would make the project look
better and be dishonest, and an examiner who spots it costs far more than the
honesty does.

> ### ⚠ A real bug that was found and fixed here
>
> This is worth knowing, because it is a good story and shows the tests
> earning their keep.
>
> Budget is measured in hundreds of millions. The genre columns are 0 or 1.
> That is a spread of about **eight zeroes**, and it makes the arithmetic
> behind least-squares unstable. The solver quietly threw the small columns
> away as if they were rounding noise.
>
> The symptom: every coefficient except budget came back as essentially zero —
> runtime's was **0.00000046 dollars per minute** — and the full model scored
> **0.578563**, which was *exactly*, to six decimal places, the budget-only
> score. Genre, rating, month, runtime and year were not weak contributors.
> **They were not being used at all.** Nothing crashed. No warning appeared.
>
> The fix is one line: put every column on the same scale first
> (`StandardScaler`) before fitting. R² then rises to the 0.588 the project
> always claimed, and the coefficients become meaningful.
>
> Two tests now guard it: one checks the full model actually beats budget
> alone, and one checks the coefficients have not been crushed to zero.

---

## `preferences.py` — what one person likes

**Its job:** hold a "taste profile".

When someone ticks three films they enjoyed, this class works out what those
films have in common:

- the genres that keep coming up (the top 3)
- their average IMDb score, minus 1 point of slack
- their typical runtime
- their typical era

```python
me = UserPreference.from_movies([the_shining, the_thing, aliens])
print(me)
# genres: Action, Drama, Horror | IMDb 7.3+ | around 131 min | 3 films ticked
```

That `from_movies` is an **alternative constructor** — a second way of building
the object. Instead of asking the user to describe their own taste, it works it
out by looking at their choices, which is both easier for them and more honest.

The profile is **printed on screen in the app**, so the user can see exactly
what was inferred about them. Nothing is hidden.

Like `Movie`, the important values are protected: a minimum IMDb score of 15 is
rejected, because the scale only goes to 10.

> **A nasty bug lives here**, and it is a good one to mention. The recommender
> used to say `preference or UserPreference()`. Because this class defines
> `__len__`, a brand-new profile with no films ticked yet counts as **False** in
> Python — so a real profile carrying the user's genres and year range was
> silently thrown away and replaced with an empty one. It is now written as
> `UserPreference() if preference is None else preference`, and a test guards
> it.

---

## `recommenders.py` — choosing what to suggest

**Its job:** score every film against the user's taste and pick the best.

Three recommenders, one parent:

| Class | What it does |
|---|---|
| `ContentRecommender` | Scores every film against your whole profile |
| `SimilarityRecommender` | Compares everything against **one** film instead |
| `PopularityRecommender` | **Ignores your taste completely** — best reviewed, most watched |

**The parent writes the recipe once.** Every recommendation works the same way:

1. **filter** — throw out films they already ticked, and anything their
   settings rule out
2. **score** — give every survivor a mark out of 100
3. **sort** — best first
4. **cut** — keep the top 15

Only **step 2** differs between the three. So the parent writes steps 1, 3 and
4, and each child supplies one method: `score_movie()`.

**How `ContentRecommender` spends its 100 points:**

| Test | Points | The question it asks |
|---|---:|---|
| Genre | 40 | Is this one of the genres you keep picking? |
| IMDb score | 25 | Is it well reviewed? |
| Age rating | 15 | Does it match the ratings you chose? |
| Runtime | 10 | Is it about as long as the films you like? |
| Era | 10 | Did it come out around the same time? |

Every mark is traceable to one line of code, and each one **records its reason
in plain English** as it is awarded — `"Drama is one of your favourite
genres"`. Those reasons are what the user sees, and what the AI later rewrites.

**Why the "most popular" baseline exists.** It deliberately ignores everything
the user said. It is there as a fair comparison — exactly like the budget-only
model in the Predict tab. If "the most famous film in the database" satisfies
you just as well as the clever recommender, then the clever one is not earning
its keep, and we would rather find that out than hide it.

---

## `explainers.py` — writing the suggestion up in words

**Its job:** turn a recommendation into a sentence a human wants to read.

Two ways to do it, used through exactly the same method call:

| Class | How | Needs internet? |
|---|---|---|
| `RuleExplainer` | Joins up the reasons our code already produced | No |
| `AIExplainer` | Sends those same reasons to an AI to phrase nicely | Yes |

**The critical point, and the one to say out loud: the AI does not choose the
films.** `recommenders.py` chooses them and works out why. The AI is handed
those reasons and asked to write them prettily. It is a writer, not a decider.

Three consequences, all of them good:

- Every suggestion is explainable **without** the AI. The reasons are on screen
  before the AI is ever called.
- **Nothing breaks without a key or without internet.** If the call fails, the
  offline explanation is shown instead and the app says on screen that it did
  so.
- **The AI cannot invent a film.** It only ever rephrases facts it was given,
  and it is explicitly told not to add plot details, awards or cast members.

The file also reads the API key from a `.env` file, so the key never appears in
the source code and never reaches GitHub.

---

## `utils.py` — small shared helpers

**Its job:** four small things that several other files need.

| Thing | What it does |
|---|---|
| `money()` | turns `138400000` into `"$138.4M"` so tables stay readable |
| `@timed` | a **decorator** — prints how long a function took, without changing the function |
| `ExportSession` | saves rows to CSV or JSON, and guarantees the file gets closed |
| `quiet_blas_warning()` | hides one specific misleading numpy warning |

`ExportSession` is used with `with`:

```python
with ExportSession("exports/horror.csv") as export:
    export.write(rows)
```

The `with` guarantees the file is closed properly **even if writing fails
halfway through**. That is the whole point of it.

---

## `__init__.py` — the package's front door

**Its job:** let people write short imports.

Because of this file you can say:

```python
from cinestat import CSVLoader, SuccessPredictor, GenreAnalyzer
```

instead of having to know that `CSVLoader` lives in `cinestat/loaders.py` and
`SuccessPredictor` lives in `cinestat/predictor.py`. It is a convenience, but
it is also a statement about which classes are the public ones.

---

# The interface

This is the half that draws things. **None of it calculates anything.**

---

## `app.py` — the window itself

**Its job:** build the window, load the data **once**, and hand it to the tabs.

The order matters:

1. open the window
2. load the CSV → a `MovieCollection`
3. train the prediction model
4. build the five tabs, handing each one the data and the model
5. build the menus and keyboard shortcuts

**No tab loads its own copy of the data**, and no tab trains its own model.
They are done once, here, and shared. Five copies of 5,418 films would be
wasteful and — worse — they could drift apart.

It also handles the **File → Export** menu, and does so in a neat way: it asks
whichever tab is currently open for its rows. Browse and Recommend both happen
to provide a method called `current_rows()`, so the export code just calls it
without needing to know which tab it is talking to.

---

## `base_tab.py` — what every tab has in common

**Its job:** be the parent of all five tabs.

It gives every tab, for free:

- `self.movies` — the film collection
- `self.predictor` — the trained model
- `self.theme` / `self.palette` / `self.px()` — colours and sizes *(Windows branch)*
- `add_heading()` — the title and subtitle at the top of each tab

And it **demands** one thing: every tab must provide a `build_ui()` method that
creates its own widgets. A tab that forgets will refuse to be created at all.

> **A famous trap is documented in this file.** Never give a Tkinter widget
> class a `__str__` method. Tkinter calls `str(widget)` internally to get the
> widget's *path name*, so overriding it makes the app fail to open with
> `bad window path name`. There is a test guarding against anyone adding one
> back.

---

## `widgets.py` — our own film-picker

**Its job:** a search box plus a dropdown, for choosing one film.

The full list has 5,418 titles, which is far too many for a plain dropdown. So
this small widget narrows the list as you type.

It exists as its own class because **it is needed twice** — the Compare tab
uses two of them, and the Recommend tab uses another. Writing it once means
those three are guaranteed to behave identically.

---

## The five tabs

| File | What it draws | What it asks the core for |
|---|---|---|
| `browse_tab.py` | A searchable, sortable table | `movies.search()`, `movies.filter_by()` |
| `charts_tab.py` | Eight charts with a zoom/save toolbar | the three analyzers |
| `compare_tab.py` | Two films side by side | two `Movie` objects, compared with `>` |
| `predict_tab.py` | A form and a prediction | `predictor.predict(...)` |
| `recommend_tab.py` | Suggestions with explanations | the recommenders and explainers |

**Notice the second column.** Every tab is a thin layer of buttons over a
question asked of the core. None of them calculate anything themselves. A tab
doing arithmetic on a DataFrame would be a bug.

Two of them are worth a closer look:

**`compare_tab.py`** is where the `>` operator earns its keep. To decide which
film did better, it writes `first > second` — not
`first.gross > second.gross`. The meaning of `>` was defined once in
`movie.py`, so it reads like English here.

**`recommend_tab.py`** is the biggest file in the interface, because it does
the most. It also contains the project's only **threading**: the AI call can
take several seconds, and if it ran on the same thread that draws the window,
the whole program would freeze and look crashed. So it runs on a second thread,
and the answer is passed back through a `Queue`. The window stays usable, with
a moving progress bar and a counter, while you wait.

---

## `main.py` — the thing you actually run

**Its job:** start the app. Barely a dozen lines of actual code — the rest of
the file is the comment explaining how to run it.

```
py main.py                  # the dataset that ships with the project
py main.py data\tmdb.csv    # the big optional one
```

It checks the file exists, prints a clear message if not, builds the window and
hands control to Tkinter.

---

# The tests

`tests/` holds **300 tests** that run in about five seconds.

| File | Tests |
|---|---|
| `test_movie.py` | validation rules, every operator, the calculated properties |
| `test_collection.py` | the list-like behaviour, the generators |
| `test_loaders.py` | all three loaders, the factory, the chunked reading |
| `test_predictor.py` | training, prediction, and the two scaling guards |
| `test_preferences.py` | the taste profile and its validation |
| `test_recommenders.py` | all three recommenders |
| `test_explainers.py` | both explainers, and every way the AI call can fail |
| `test_gui.py` | all five tabs, built for real |
| `test_theme.py` · `test_platform_ui.py` | the Windows look *(Windows branch)* |

**Two things worth knowing about them:**

**No test ever touches the internet.** A fake stand-in for the network library
is slipped in, so the AI code is tested against a success, an HTTP 401, a dead
connection, a malformed reply and an empty reply — with no key and no network.

**The GUI tests build real windows.** They create the actual application,
click things, and check what happened — then skip themselves automatically on a
machine with no screen.

---

[← what the project does](01-what-the-project-does.md) · [back to index](README.md) · [next: how it fits together →](03-how-it-all-fits-together.md)
