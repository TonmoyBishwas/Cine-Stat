# 5. The Windows version

[← OOP explained](04-oop-explained.md) · [back to index](README.md) · [next: questions you might get asked →](06-questions-you-might-get-asked.md)

---

The project has two branches:

| Branch | What it is |
|---|---|
| `main` | The original. Written and designed on a Mac. |
| `windows` | The same project, with a proper Windows interface. |

**The analysis is identical in both.** Not similar — identical. Every file in
`cinestat/` outside the `gui/` folder is the same. Only the window changed.

---

## Why a Windows version was needed at all

Tkinter borrows widgets from the operating system. On a Mac it borrows quite a
lot, so a program looks at home without being asked. On Windows it borrows much
less, and four things were wrong — none of them a matter of taste:

### 1. There was no dark mode

Windows 11 has a dark mode. Tkinter does not know about it. So on a machine set
to dark — which is most of them now — the program opened a sheet of bright
white paper in the middle of a dark desktop.

Worse, the **title bar** is drawn by Windows itself, not by the program. So
even after darkening everything inside the window, there would still be a white
strip across the top. It has to be asked for separately.

### 2. The text was blurred

Most Windows laptops run their display at 125% or 150%. A program that has not
told Windows *"I will handle my own scaling"* gets drawn at 100% and then
**stretched like a photograph**. Every letter goes soft. It makes a program look
cheap, and almost nobody can say why.

### 3. The font and the shortcuts were wrong

The original asked for `("Helvetica", 15)`. Windows does not have Helvetica —
it has **Segoe UI**, which is what every other program on the machine uses.
And ⌘E is a Mac shortcut. On Windows it is **Ctrl+E**.

### 4. The program had no identity

It borrowed `python.exe`'s icon and shared its taskbar button.

---

## What was added

Everything Windows-specific lives in **two files**, and only two:

| File | What it does |
|---|---|
| `cinestat/gui/platform_ui.py` | Talks to Windows directly: DPI, dark mode, the accent colour, the dark title bar, the icon, the taskbar identity, keyboard shortcuts |
| `cinestat/gui/theme.py` | `Palette` (the colours of one look) and `WindowsTheme` (where each colour goes), plus scaling and the chart colours |

Every tab reaches them through `BaseTab`, which now offers `self.theme`,
`self.palette` and `self.px()` — exactly the way it already offered
`self.movies` and `self.predictor`.

---

## The two ideas worth explaining

### `Palette` and `WindowsTheme` — composition again

A **`Palette`** is one object holding the sixteen colours one look needs. There
are two of them: `LIGHT` and `DARK`.

A **`WindowsTheme`** *has a* `Palette` and knows where each colour goes — this
background, that text, those table stripes.

That is **composition**, the same relationship as `MovieCollection` *has a*
list of films. A theme is not a kind of colour; it is the thing that knows what
to do with colours.

**The rule that makes it work:** no file in `cinestat/gui/` outside `theme.py`
is allowed to write a colour down. Tabs ask for `self.palette.positive`, never
for `"#2E6E3E"`.

This is enforced by a test that reads every file with Python's own tokeniser
and fails if it finds one. Without that rule, dark mode would break every time
anyone added a widget — and it would break *invisibly*, because a colour typed
on a light-mode machine looks perfectly fine to whoever typed it.

### `px()` — one method for high-DPI screens

Once the program tells Windows *"stop stretching me"*, every measurement
written in pixels is suddenly too small on a 150% laptop. So every pixel size
in the interface goes through one method:

```python
self.tree.column(key, width=self.px(width))
```

On an ordinary screen `px(250)` is 250. On a 150% laptop it is 375. One method,
applied everywhere, and the whole interface scales together.

---

## Why the theme is "clam" and not "vista"

This is the design question most likely to be asked, so it is worth knowing.

Tk ships a theme called **vista**, and reaching for it is the obvious move. It
is wrong twice over:

1. **It copies Windows 7** — glossy gradient buttons, a blue glow around
   whatever has the keyboard focus. Next to Windows 11, which is flat, it looks
   like a program nobody has updated in a decade.
2. **It cannot be recoloured at all.** Windows itself does the drawing, so a
   dark vista button does not exist. Using it would mean **no dark mode,
   ever**.

So the Windows build uses **clam** — the one built-in theme whose every colour
can be set — and repaints it to look like Windows 11: flat surfaces, thin
borders, and the accent colour the user picked in their own Settings.

The payoff: light mode and dark mode are **the same program**, not two
different-looking ones.

---

## The small Windows habits

None of these is worth a paragraph alone. Together they are the difference
between a program that *runs* on Windows and one that *belongs* there.

- A **resize grip** in the corner of the status bar
- **Striped table rows**, as Explorer has drawn them since 2001
- **Sort arrows in the column heading** (▲ ▼), not just in text underneath
- **Headings aligned with their own figures** — money columns right-aligned
- **Underlined menu letters**, so Alt+F opens File
- An **accent-coloured button** on each tab for that tab's main action
- **"All files (\*.\*)"** at the bottom of every Save dialog

Plus `run.bat` and `setup.bat`, so the program can be started by
double-clicking instead of by typing.

---

## Two Windows traps worth knowing

**A menu shortcut is two separate things.** Writing `accelerator="Ctrl+E"` only
*prints the words* in the menu. It binds nothing. Tk has to be told separately.
If the two drift apart, the menu advertises a key that does nothing — and it
fails silently. One function now produces both, and a test walks the real menu
checking every advertised shortcut is genuinely bound.

**Colours must be set in pairs.** The explanation box once asked for a
near-white background and left the text colour alone. In dark mode the default
text colour is **white** — so the explanation rendered white on white and was
completely invisible, while every test still passed, because the words really
were in the widget. Now the theme hands over both halves of the pair together,
so the bug cannot be written one colour at a time.

---

## Seeing both looks

The program follows whatever Windows is set to. To see the other one without
changing your whole computer:

```bat
set CINESTAT_THEME=light
run.bat
```

And to check the high-DPI scaling on an ordinary monitor:

```bat
set CINESTAT_UI_SCALE=1.5
run.bat
```

Screenshots of both are in [`docs/`](../docs/).

---

[← OOP explained](04-oop-explained.md) · [back to index](README.md) · [next: questions you might get asked →](06-questions-you-might-get-asked.md)
