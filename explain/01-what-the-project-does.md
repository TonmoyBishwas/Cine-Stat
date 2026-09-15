# 1. What the project does

[← back to the index](README.md) · [next: the files, one by one →](02-the-files-one-by-one.md)

---

## The idea

Films are expensive and risky. About a third of them never make their money
back. So two questions are worth asking:

1. **What makes a film make money?** Does spending more work? Which genre pays
   best? When should you release it?
2. **What should I watch next?** Given a few films someone enjoyed, can we
   suggest more — and *explain* each suggestion rather than just asserting it?

CineStat answers both, from the same data, with the same code.

---

## The data

**Movie Industry**, a public dataset scraped from IMDb.
Source: <https://www.kaggle.com/datasets/danielgrijalvas/movies>

- **7,668 films** in the raw file, released between 1980 and 2020
- 15 columns: name, rating, genre, year, released, score, votes, director,
  writer, star, country, budget, gross, company, runtime
- After cleaning — dropping films with no budget or no box-office figure —
  **5,418 films** remain

That cleaning step is not a technicality. A film with no budget recorded
cannot tell us anything about whether budgets matter, so keeping it would
quietly poison every average in the project.

The file ships with the repository (`data/movies.csv`, about 1.3 MB), so
nothing has to be downloaded and nothing needs an internet connection.

---

## The two halves

The project is delivered in two pieces, and this confuses people, so it is
worth being clear:

| | **Part 1** | **Part 2** |
|---|---|---|
| What it is | A Jupyter notebook | A desktop application |
| Where | `notebooks/01_movie_analysis.ipynb` | `python main.py` |
| What it shows | The analysis, written out with charts and commentary | The same analysis, but you click instead of scroll |
| Who it is for | Someone reading the findings | Someone exploring the data themselves |

**Both of them import the same classes from `cinestat/`.**

This is the single most important structural fact about the project. The
notebook does not have its own copy of the genre analysis, and the app does not
have its own copy either. Both say `from cinestat import GenreAnalyzer` and
use the one that already exists.

Why that matters: if you find a mistake in how flop rate is calculated, you fix
it in exactly one place, and the notebook and the app are both fixed. In a
copy-pasted project you would fix it twice, or — much more likely — fix it once
and never notice the other one is now wrong.

---

## What we found

These are real results from the real data. Every one can be reproduced by
running the notebook.

| # | Question | Answer |
|---|---|---|
| 1 | Which genre gives the best return? | **Horror** — typically **3.08×** its budget |
| 2 | Which genre is safest? | **Animation** — only **15.5%** lose money |
| 3 | Does a bigger budget mean a *better* film? | **No.** Correlation with IMDb score is **0.07** |
| 4 | Does a bigger budget mean *more money*? | **Yes.** Correlation **0.74** |
| 5 | Does the age rating matter? | **Yes.** G and PG films out-earn R-rated ones |
| 6 | Best time to release? | **Summer and December.** January is the worst |
| 7 | How risky is film making? | **32.1%** of films never earn back their budget |
| 8 | Can we predict box office in advance? | **Partly** — R² **0.588** |

### The two findings worth leading with

**Money does not buy a good film.** Budget and IMDb score have a correlation of
**0.072**. That is statistically indistinguishable from zero. Spending more
buys you an *audience*, not a better film — which is a genuinely interesting
thing to be able to say with evidence.

**Horror is the best business in cinema.** Not the biggest earner — that is
Animation — but the best *return*. Horror films are cheap to make and reliably
make several times their budget back. A superhero film earns far more in
absolute dollars, but it also costs a fortune, so per dollar spent it is a
worse investment.

---

## What the app looks like

Five tabs, each answering a different question:

| Tab | What you do | What it gives you |
|---|---|---|
| **Browse** | Search and filter the films, click a column to sort | The raw data, explorable |
| **Charts** | Pick one of eight charts | The notebook's charts, interactive |
| **Compare** | Choose two films | Their numbers side by side, better figure highlighted |
| **Predict** | Type a budget, genre, rating, runtime, year, month | Predicted box office, profit, and a Hit / Break-even / Flop verdict |
| **Recommend** | Tick films you liked | Suggestions, each with a plain-English reason |

Plus a **File** menu that exports whatever the open tab is showing to CSV or
JSON.

---

## A note on the prediction model

The Predict tab uses **linear regression** — the simplest respectable model
there is. That was a deliberate choice, and if asked "why not something
fancier?", the answer is:

- It scores **R² 0.588**, which is honest for this problem.
- Every coefficient can be read and explained. Nobody has to take the model on
  faith.
- The interesting result here is not "we squeezed out another 2%". It is
  *budget does nearly all the work*, and a simple model shows that far more
  clearly than a complicated one would.

The model is trained **only on information that exists before a film comes
out**: budget, runtime, year, genre, age rating and release month.

It deliberately does **not** use the IMDb score or the vote count, even though
both correlate strongly with box office — because both only exist *after* the
film has been released. Using them to predict an unmade film would be cheating.
That mistake has a name, **data leakage**, and avoiding it on purpose is one of
the better things to be able to point at in this project.

---

[← back to the index](README.md) · [next: the files, one by one →](02-the-files-one-by-one.md)
