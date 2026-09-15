# 6. Questions you might get asked

[← the Windows version](05-the-windows-version.md) · [back to index](README.md) · [next: glossary →](07-glossary.md)

---

Answers you can give in your own words. Read them, then close the file and try
saying each one out loud — if you can do that, you understand the project.

---

## About the project

### "Explain your project in thirty seconds."

> It analyses 40 years of film data to answer two questions: what makes a film
> make money, and what should I watch next.
>
> It comes in two parts that share the same code — a Jupyter notebook with the
> analysis, and a five-tab desktop app that does the same thing by clicking.
> The analysis classes are written once and used by both.
>
> The main findings are that budget predicts box office well but has almost no
> relationship with quality, that Horror gives the best return on investment,
> and that about a third of all films never make their money back.

### "Why two parts? Isn't that duplication?"

> It is the opposite of duplication — that is the point. Both halves
> `import` the same classes from `cinestat/`. The notebook calls
> `GenreAnalyzer(movies).report()` and it prints; the app calls the same class
> and draws a chart. There is only one copy of the arithmetic, so the two can
> never disagree with each other.

### "Walk me through what happens when the program starts."

> `main.py` checks the data file exists and opens the window. The window asks
> `DataLoader.for_file()` to read the CSV — that peeks at the column names and
> picks the right loader. The loader reads 7,668 rows, cleans them down to
> 5,418, and turns each one into a `Movie` object inside a `MovieCollection`.
> Then the prediction model trains on that collection, once. Finally the five
> tabs are built and handed the same collection and the same trained model.
>
> Everything is loaded once and shared. No tab loads its own copy.

---

## About the data and the analysis

### "How did you clean the data, and why?"

> We drop duplicates, then drop any film missing a budget, box office, runtime,
> rating or genre, and any where budget or box office is zero. That takes 7,668
> films down to 5,418.
>
> It is not just tidiness. A film with no budget recorded cannot tell us
> anything about whether budgets matter, so keeping it would quietly poison
> every average in the project.
>
> We also group rare genres together as "Other", so that a genre with four
> films in it does not produce a wild-looking average that means nothing.

### "What is your most interesting finding?"

> That money does not buy a good film. Budget and IMDb score correlate at
> **0.072**, which is statistically indistinguishable from zero. But budget and
> box office correlate at **0.74**. So spending more buys you an *audience*,
> not a better film.

### "Why is Horror the best return if Animation earns more?"

> Because those are two different questions. Animation earns the most in
> absolute dollars, but it also costs the most to make. Horror films are cheap
> and reliably make about three times their budget back. Per dollar spent,
> Horror is the better investment — which is exactly why so many get made.

---

## About the prediction model

### "Why linear regression? Why not something more powerful?"

> Three reasons. It scores R² 0.588, which is honest for this problem. Every
> coefficient can be read and explained, so nobody has to take the model on
> faith. And the interesting result here is not squeezing out another 2% — it
> is that budget does nearly all the work, and a simple model shows that far
> more clearly than a complicated one would.

### "Why doesn't the model use the IMDb score? It correlates strongly."

> Because it would be cheating. A film only has a score and a vote count
> *after* it has been released. Using them to predict a film that has not been
> made yet is **data leakage** — the model would look excellent and be useless
> in practice.
>
> We train only on what is knowable in advance: budget, runtime, year, genre,
> age rating and release month.

### "Your model is only 59% accurate. Isn't that bad?"

> It is the honest ceiling. The other 41% is the script, the cast, the
> marketing and luck — none of which a spreadsheet can measure. That is why the
> Predict tab shows the R² on screen and says how far off it is on average
> (about $67 million), so nobody mistakes an estimate for a promise.
>
> A model claiming 95% on this data would mean we had made a mistake somewhere.

### "What does budget-only R² 0.579 next to full 0.588 tell us?"

> That budget does almost all the work. Genre, age rating and release month
> together add less than 0.01.
>
> We report it deliberately. Hiding it would make the project look better and
> be dishonest, and it is a real result about the film industry — more
> interesting reported than buried.

### "Did anything go wrong with the model?" *(a good story to have ready)*

> Yes, and it was invisible. Budget is measured in hundreds of millions and the
> genre columns are 0 or 1 — a spread of about eight zeroes. That makes the
> arithmetic behind least-squares unstable, and the solver was quietly throwing
> the small columns away as rounding noise.
>
> The symptom was that the full model scored **0.578563** and the budget-only
> model scored **0.578563** — identical to six decimal places. Genre, rating
> and month were not weak contributors; they were not being used at all.
> Nothing crashed and nothing warned us.
>
> The fix is one line: put every column on the same scale before fitting. R²
> went to 0.588. There are now two tests that fail if it ever happens again —
> one checks the full model actually beats budget alone, the other checks the
> coefficients have not been crushed to zero.

---

## About the recommender

### "How does the recommendation actually work?"

> You tick films you liked. `UserPreference.from_movies()` works out what they
> have in common — the genres that keep coming up, the average IMDb score, the
> usual runtime, the usual era. That profile is printed on screen so you can
> see exactly what was inferred.
>
> Then a recommender scores every other film out of 100 against that profile:
> 40 points for genre, 25 for IMDb score, 15 for age rating, 10 for runtime, 10
> for era. Every point recorded its reason in plain English as it was awarded,
> and those reasons are what you see.

### "Why is there a 'most popular' option that ignores my taste?"

> It is a baseline, for the same reason we report the budget-only model. If
> "the most famous film in the database" satisfies you just as well as the
> clever recommender, then the clever one is not earning its keep — and we
> would rather find that out than hide it.

### "Does the AI choose the films?"

> No, and this is the most important thing about that feature. Our own code in
> `recommenders.py` chooses the films and works out why. The AI is handed those
> reasons and asked to phrase them nicely. It is a writer, not a decider.
>
> Three things follow. Every suggestion is explainable without the AI — the
> reasons are on screen before it is ever called. Nothing breaks without a key
> or without internet; it falls back to the offline explanation and says so on
> screen. And the AI cannot invent a film, because it only ever rephrases facts
> it was given.

### "What happens if the internet is down?"

> The recommendations still work, because they never needed it. Pressing
> "Explain with AI" catches the failure, shows the built-in reasons instead,
> and says on screen that it did so. There is a test for exactly that — the
> AI code is tested against a success, an HTTP 401, a dead connection, a
> malformed reply and an empty reply, all without a key and without a network.

---

## About the OOP

### "Show me polymorphism in your project."

> The Recommend tab has a dropdown with three methods in it. When you press the
> button, the tab looks up whichever class the user picked and calls
> `.recommend()` on it. It genuinely does not know whether it is holding a
> `ContentRecommender`, a `SimilarityRecommender` or a `PopularityRecommender`
> — all three answer the same call in their own way.
>
> Adding a fourth means adding one name to one list. The dropdown picks it up
> by itself.

### "Where is encapsulation, and why did you need it?"

> `Movie` stores budget and box office as `__budget` and `__gross`. The two
> underscores make Python rename them behind the scenes, so outside code cannot
> reach them by accident. You get at them through properties that validate
> every write — a negative budget raises `InvalidBudgetError`.
>
> It matters because a film with a negative budget is nonsense that would
> silently corrupt every average downstream. Rather than hoping nobody writes
> one, the class makes it impossible.

### "Why is `MovieCollection` not a subclass of `Movie`?"

> Because a library is not a kind of book. It is a thing that *holds* books.
> That is composition — has-a — not inheritance — is-a. Inheriting would say
> "a collection is a film", which is nonsense, and it would give the collection
> a budget and a box office it has no use for.

### "Why use an abstract base class instead of just writing three classes?"

> Two reasons. It puts the shared work in one place — all the data cleaning is
> written once in `DataLoader` and inherited by all three loaders. And it turns
> "please remember to write a `load()` method" into a rule the computer
> enforces: forget it and the class refuses to be created at all, immediately
> and loudly, instead of failing mysteriously later.

### "What's the difference between `__str__` and `__repr__`?"

> `__str__` is for humans — it is what `print()` uses. `__repr__` is for
> programmers — it is what you see in a list or in the shell.
>
> There is a real trap here, and it is documented in the project. You must
> **never** give a Tkinter widget a `__str__` method, because Tkinter calls
> `str(widget)` internally to get the widget's path name. Overriding it makes
> the app fail to open with `bad window path name`. We override `__repr__`
> instead, and there is a test guarding against anyone adding one back.

---

## About the code and the process

### "Did you write this yourself, or did AI write it?"

Answer this honestly — your teacher permitted AI, so there is nothing to
defend. What you are being marked on is whether you understand it.

> AI was used to write a lot of the code, as we were told it could be. What I
> can do is explain every design decision in it and why it is that way rather
> than some other way.

Then offer something concrete, because that is what proves it:

> For example, the recommender uses a template method — the parent writes the
> four steps that never change, filter, score, sort, cut, and each subclass
> fills in only the scoring. That is why adding a fourth recommender touches
> one list and nothing else.

If you can answer three or four follow-up questions from this page in your own
words, the authorship question stops mattering.

### "What part of this was hardest?"

Pick a real one. Good candidates, all documented in the project:

- **The model bug above.** Two numbers that matched to six decimal places, no
  error message, and a model that had quietly stopped using five of its six
  inputs.
- **The white-on-white bug.** The explanation box set a near-white background
  and left the text colour alone. In dark mode the default text colour is
  white, so the box rendered white on white and was completely invisible —
  while every test passed, because the words really were in the widget. It
  taught us to always set colours in pairs.
- **`x or default` with `__len__`.** The recommender wrote
  `preference or UserPreference()`. Because `UserPreference` defines `__len__`,
  a profile with no films ticked counts as `False` — so a real profile carrying
  the user's genres was silently thrown away and replaced with an empty one.

### "How do you know it works?"

> There are 300 tests that run in about five seconds. They cover the validation
> rules, every operator, the generators, the abstract base classes, the model,
> all three recommenders, both explainers, and all five GUI tabs — which are
> built for real, clicked, and checked.
>
> No test touches the internet. The GUI tests skip themselves on a machine with
> no screen.

### "If you had another week, what would you add?"

> A predictor hierarchy. Right now `SuccessPredictor` is one standalone class
> with no abstract parent, so the model layer is the one place with no
> inheritance or polymorphism in it. I would make a `BasePredictor` with an
> average-guess baseline, a budget-only model and the full model as three
> subclasses, then train and score all three in one loop. That turns the
> budget-only comparison we already report into a real demonstration of
> polymorphism doing work.

---

## Quick numbers to have ready

| | |
|---|---|
| Films in the raw file | 7,668 |
| Films after cleaning | **5,418** |
| Years covered | 1980–2020 |
| Full model R² | **0.588** |
| Budget-only R² | 0.579 |
| Average prediction error | ~$67 million |
| Films that never make their budget back | **32.1%** |
| Budget ↔ box office correlation | **0.74** |
| Budget ↔ IMDb score correlation | **0.072** |
| Best return on investment | Horror, **3.08×** |
| Safest genre | Animation, 15.5% lose money |
| Tests | **300**, about 5 seconds |

---

[← the Windows version](05-the-windows-version.md) · [back to index](README.md) · [next: glossary →](07-glossary.md)
