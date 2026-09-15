# 3. How it all fits together

[← the files, one by one](02-the-files-one-by-one.md) · [back to index](README.md) · [next: OOP explained →](04-oop-explained.md)

---

Knowing what each file does is one thing. Knowing how they hand work to each
other is what makes you able to answer follow-up questions. This page follows
real actions through the whole program.

---

## The one rule that shapes everything

> **The interface may use the core. The core may never use the interface.**

`cinestat/gui/` imports from `cinestat/`. Nothing in `cinestat/` imports from
`cinestat/gui/` — not one line.

Why that matters, in practical terms:

- The notebook can use every analysis class **without a window existing**.
- You could delete the entire interface and the analysis would still run.
- You could replace Tkinter with a website tomorrow and not touch the core.
- Tests can test the analysis on a machine with no screen at all.

If you are asked to name one design decision you are pleased with, this is a
good one to pick.

---

## Journey 1: starting the program

What happens between double-clicking and seeing a window.

```
 you run:  py main.py
     |
     v
 main.py            checks data/movies.csv exists
     |
     v
 gui/app.py         opens the window
     |
     v
 loaders.py         DataLoader.for_file() reads the first line of the CSV,
     |              sees the column names, and picks CSVLoader
     |
     v
 loaders.py         load()  -> pandas reads the file    (7,668 rows)
     |              clean() -> drops the unusable rows   (5,418 left)
     |
     v
 movie.py           every surviving row becomes a Movie object
     |              (budgets and box offices validated on the way in)
     |
     v
 collection.py      all 5,418 Movie objects go into one MovieCollection
     |
     v
 predictor.py       SuccessPredictor trains on that collection
     |              (~1 second, R2 0.588)
     |
     v
 gui/app.py         builds the five tabs, handing each one
     |              the SAME collection and the SAME trained model
     v
 the window appears
```

**The thing to notice:** the data is read once, cleaned once, and the model is
trained once. Everything after that shares them.

---

## Journey 2: clicking "Recommend films for me"

This is the best journey to know, because it touches the most files.

Suppose the user has ticked *The Shining*, *The Thing* and *Aliens*, and
presses the button.

### Step 1 — the tab collects what the user said
`gui/recommend_tab.py` gathers the three ticked films and the settings
(minimum IMDb score, year range). **It does no thinking.**

### Step 2 — the taste profile is worked out
`preferences.py` — `UserPreference.from_movies()` looks at the three films and
works out:

```
genres: Action, Drama, Horror | IMDb 7.3+ | around 131 min | 3 films ticked
```

It also notes that those films average out to about **1983**, which becomes the
"era you watch most".

That profile is printed on screen, so the user can see exactly what was
inferred about them. Nothing is hidden.

### Step 3 — every other film is scored
`recommenders.py` — `ContentRecommender` walks the collection:

- skip the three they ticked (using `in`, defined in `preferences.py`)
- skip anything their settings rule out
- score each survivor out of 100, recording the reason for every point
- sort best-first, keep the top 15

### Step 4 — the results are drawn
Back in `gui/recommend_tab.py`, the 15 suggestions fill the table. The top one
is selected automatically.

### Step 5 — the reasons appear
`explainers.py` — `RuleExplainer` turns the recorded reasons into readable
lines:

```
Star Wars: Episode VI - Return of the Jedi (1983) - 81% match,
Action, rated PG, IMDb 8.3

Why you might like it:
  - Action is one of your favourite genres
  - Well reviewed - IMDb 8.3 out of 10
  - 131 minutes long, about the length you like
  - From 1983, the era you watch most

Based on the films you ticked: The Shining, The Thing, Aliens.
```

That really is the top suggestion for those three films — you can reproduce it
by ticking them in the app.

This is **instant** and needs no internet.

### Step 6 — only if the user presses "Explain with AI"
A **second thread** starts, so the window does not freeze. It sends those same
reasons to the AI, which sends back a friendlier paragraph. Meanwhile the main
thread keeps the window alive, running a progress bar and a counter.

If anything goes wrong — no key, no internet, the service is down — the offline
explanation from step 5 is shown instead, and the app says so honestly on
screen.

```
recommend_tab.py  ->  preferences.py   (what do they like?)
                  ->  recommenders.py  (which films match, and why?)
                  ->  explainers.py    (say it in words)
                  ->  back to recommend_tab.py to draw it
```

Every arrow points **from** the interface **to** the core. None point back.

---

## Journey 3: clicking "Predict"

```
predict_tab.py       reads six boxes: budget, genre, rating,
     |               runtime, year, month
     v
predictor.py         validates the budget
     |               turns the words into 0/1 columns
     |               puts every column on the same scale
     |               runs the regression
     |               returns {gross, profit, roi, verdict, r2, mae}
     v
predict_tab.py       draws the number, colours the verdict,
                     and prints how much to trust it
```

**If the budget is not a number**, `predictor.py` raises
`InvalidBudgetError`. The tab catches it and shows a polite dialog. The program
does not crash — and there is a test that proves it.

Notice that the tab never touches scikit-learn. It asks a question and draws an
answer.

---

## Journey 4: File → Export

This one is small but it is the neatest trick in the project.

```
app.py    "which tab is open?"
   |
   v
   asks that tab for current_rows()
   |
   v
utils.py  ExportSession writes them to CSV or JSON
```

The export code **does not know or care** which tab it is talking to. Browse
and Recommend both happen to provide a method called `current_rows()`, and
that is enough. If you add a sixth tab tomorrow and give it a `current_rows()`
method, exporting will work on it immediately — with no change to `app.py`.

Python calls that **duck typing**: "if it answers `current_rows()`, it is
exportable."

---

## The same core, used twice

This is the fact that ties Part 1 and Part 2 together.

```
                 cinestat/   (the core)
                      |
         +------------+------------+
         |                         |
   the notebook              the desktop app
   (Part 1)                  (Part 2)

   GenreAnalyzer(movies)     GenreAnalyzer(movies)
        .report()                  .run()
   prints the findings        draws them as a chart
```

The notebook and the app call **the same class**. One prints, one draws. The
calculation exists in exactly one place.

If asked "how do you know the notebook and the app agree with each other?", the
answer is: they cannot disagree. There is only one copy of the arithmetic.

---

## What depends on what

Reading order, top to bottom. Each file only knows about the ones above it.

```
exceptions.py       knows nothing
utils.py            knows exceptions
movie.py            knows exceptions
collection.py       knows movie
loaders.py          knows movie, collection, exceptions
analyzers.py        knows collection, utils
predictor.py        knows movie, utils, exceptions
preferences.py      knows exceptions
recommenders.py     knows preferences, utils
explainers.py       knows exceptions
------------------------------------------- the line no core file crosses
gui/theme.py        knows platform_ui
gui/base_tab.py     knows theme
gui/widgets.py      knows nothing from the core
gui/*_tab.py        know base_tab + whichever core classes they need
gui/app.py          knows every tab, plus loaders and predictor
main.py             knows gui/app
```

There are **no circular imports** anywhere. That is not an accident; it is what
keeps the project comprehensible.

---

[← the files, one by one](02-the-files-one-by-one.md) · [back to index](README.md) · [next: OOP explained →](04-oop-explained.md)
