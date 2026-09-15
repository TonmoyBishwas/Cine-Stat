"""Everything the program needs to ask Windows about itself.

This is the Windows edition of CineStat. The analysis classes in `cinestat/`
are the same on every operating system - they only read numbers out of a CSV -
but a *window* is not. A program that looks at home on a Mac looks wrong on
Windows, and the differences are not a matter of taste:

  * Windows draws the window itself. Its title bar has to be told separately
    to go dark, or a dark application ends up wearing a white hat.
  * Windows stretches whole windows on a high-DPI screen unless the program
    says it would rather do the scaling itself. Left alone, every letter in
    the program is blurred.
  * Windows has its own idea of which key means "export" (Ctrl, not Command)
    and which font a program should be written in (Segoe UI, not Helvetica).

Every one of those questions is answered here, in one file, with `ctypes` and
`winreg` - the two standard-library ways of talking to Windows directly. Every
function is written so that it still returns a sensible answer on a machine
that is not Windows at all, so the same source runs unchanged on macOS and
Linux; it simply stops asking Windows-only questions.

Syllabus topics demonstrated here:
  Class 9  - reading a file (the icon) and the registry, and choosing which
             errors to swallow: every OS call here is allowed to fail
  Class 11 - functions as objects, and constants held at module level
"""

import os
import sys
import ctypes
from pathlib import Path


# ---------------------------------------------------------------------------
# Which machine are we on?
# ---------------------------------------------------------------------------
IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"

# Windows groups taskbar buttons by this string. Without it our window is
# grouped under "python.exe" and borrows the Python icon; with it, CineStat
# gets its own taskbar button and its own icon.
APP_ID = "UIU.DS1116.CineStat.Windows"

ASSETS = Path(__file__).resolve().parent.parent.parent / "assets"
ICON_ICO = ASSETS / "cinestat.ico"
ICON_PNG = ASSETS / "cinestat.png"

# Where Windows keeps "is the user using light mode or dark mode?".
PERSONALIZE_KEY = (r"Software\Microsoft\Windows\CurrentVersion"
                   r"\Themes\Personalize")
DWM_KEY = r"Software\Microsoft\Windows\DWM"

# Two escape hatches, so the look can be checked without changing the whole
# computer's settings:
#     set CINESTAT_THEME=light      (or dark)
#     set CINESTAT_UI_SCALE=1.5
SCALE_VARIABLE = "CINESTAT_UI_SCALE"
THEME_VARIABLE = "CINESTAT_THEME"


# ---------------------------------------------------------------------------
# Things that must happen BEFORE the first window is created
# ---------------------------------------------------------------------------
def prepare_process():
    """Tell Windows what kind of program this is. Call it before Tk starts.

    Returns True if we managed to claim DPI awareness. Both jobs here have to
    be done before the first window exists, because Windows decides how to
    treat a process the moment it draws anything for it.
    """
    if not IS_WINDOWS:
        return False
    aware = set_dpi_awareness()
    set_app_user_model_id()
    return aware


def set_dpi_awareness():
    """Ask Windows to stop magnifying our window for us.

    On a laptop set to 125% or 150% - which most Windows laptops now are - a
    program that has not said this gets drawn at 100% and then stretched like
    a photograph. Text goes soft and the whole program looks cheap. Saying it
    means we get real pixels and have to do the scaling ourselves, which is
    what `WindowsTheme.px()` in theme.py is for.

    1 is PROCESS_SYSTEM_DPI_AWARE. The older SetProcessDPIAware() below says
    the same thing on Windows 7 and 8, where shcore.dll does not exist.
    """
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return True
    except (AttributeError, OSError):
        pass
    try:
        ctypes.windll.user32.SetProcessDPIAware()
        return True
    except (AttributeError, OSError):
        return False


def set_app_user_model_id(app_id=APP_ID):
    """Claim our own taskbar button instead of sharing python.exe's."""
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        return True
    except (AttributeError, OSError):
        return False


# ---------------------------------------------------------------------------
# How big is everything, and what colour is the user's Windows?
# ---------------------------------------------------------------------------
def screen_scale(window=None):
    """How many real pixels Windows puts inside one "logical" pixel.

    1.0 on an ordinary monitor, 1.5 on a laptop set to 150%. Every hard-coded
    pixel measurement in the interface - column widths, the window size, the
    height of a table row - is multiplied by this, or the program comes out
    postage-stamp sized on a high-DPI screen once we have claimed DPI
    awareness above.
    """
    forced = os.environ.get(SCALE_VARIABLE, "").strip()
    if forced:
        try:
            return max(1.0, min(4.0, float(forced)))
        except ValueError:
            pass                      # nonsense in the variable - ignore it

    if not IS_WINDOWS:
        return 1.0

    dots_per_inch = 0
    if window is not None:
        try:
            # GetDpiForWindow is per-monitor and exact, but only exists on
            # Windows 10 1607 and later.
            dots_per_inch = ctypes.windll.user32.GetDpiForWindow(
                int(window.winfo_id()))
        except (AttributeError, OSError, ValueError, TypeError):
            dots_per_inch = 0

    if not dots_per_inch:
        try:
            screen = ctypes.windll.user32.GetDC(0)
            dots_per_inch = ctypes.windll.gdi32.GetDeviceCaps(screen, 88)
            ctypes.windll.user32.ReleaseDC(0, screen)
        except (AttributeError, OSError):
            dots_per_inch = 96

    return round((dots_per_inch or 96) / 96.0, 4)


def system_theme():
    """'dark' or 'light' - whichever the user has set Windows to.

    Windows writes this into the registry as AppsUseLightTheme, so reading it
    means the program matches the rest of the desktop without being asked to.
    """
    forced = os.environ.get(THEME_VARIABLE, "").strip().lower()
    if forced in ("dark", "light"):
        return forced

    if not IS_WINDOWS:
        return "light"

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, PERSONALIZE_KEY) as key:
            uses_light, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return "light" if uses_light else "dark"
    except (ImportError, OSError):
        # No such key on an older Windows, which only had a light mode.
        return "light"


def accent_colour():
    """The accent colour the user picked in Windows Settings, as '#rrggbb'.

    Returns None if it cannot be read, and the caller falls back to the
    standard Windows blue.
    """
    if not IS_WINDOWS:
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DWM_KEY) as key:
            packed, _ = winreg.QueryValueEx(key, "AccentColor")
    except (ImportError, OSError):
        return None
    # Windows stores it the other way round from everyone else: 0xAABBGGRR.
    blue = (packed >> 16) & 0xFF
    green = (packed >> 8) & 0xFF
    red = packed & 0xFF
    return f"#{red:02X}{green:02X}{blue:02X}"


def brightness(hex_colour):
    """How light a '#rrggbb' colour is, 0 (black) to 255 (white).

    Used to decide whether writing on top of a colour should be black or
    white. Green channels look brighter to the eye than blue ones, which is
    what the 0.299 / 0.587 / 0.114 weights are for - they are the standard
    way of turning a colour into a grey.
    """
    text = hex_colour.lstrip("#")
    if len(text) != 6:
        return 255
    red, green, blue = (int(text[i:i + 2], 16) for i in (0, 2, 4))
    return 0.299 * red + 0.587 * green + 0.114 * blue


def readable_on(hex_colour):
    """Black or white - whichever can actually be read on this colour."""
    return "#000000" if brightness(hex_colour) > 150 else "#FFFFFF"


# ---------------------------------------------------------------------------
# Dressing the window Windows itself draws
# ---------------------------------------------------------------------------
def use_dark_titlebar(window, dark=True):
    """Make the title bar match the program underneath it.

    Tk draws everything inside the window, but the title bar belongs to
    Windows. Nothing we do to the widgets touches it, so a dark application
    ends up with a bright white strip across the top unless we ask the Desktop
    Window Manager directly.

    Attribute 20 is DWMWA_USE_IMMERSIVE_DARK_MODE. It was numbered 19 before
    Windows 10 version 2004, so we try the new number and then the old one.
    """
    if not IS_WINDOWS:
        return False
    try:
        window.update_idletasks()
        # Tk's own window is a child; the title bar belongs to its parent.
        handle = ctypes.windll.user32.GetParent(window.winfo_id())
        if not handle:
            handle = window.winfo_id()
        wanted = ctypes.c_int(1 if dark else 0)
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                handle, attribute, ctypes.byref(wanted), ctypes.sizeof(wanted))
            if result == 0:
                return True
    except (AttributeError, OSError, ValueError, TypeError):
        pass
    return False


def set_window_icon(window):
    """Give the window, the taskbar and Alt-Tab our own icon.

    Windows wants a .ico file; iconbitmap(default=...) applies it to this
    window and every dialog box opened from it. The .png is the fallback for
    every other operating system, where .ico means nothing.
    """
    if IS_WINDOWS and ICON_ICO.exists():
        try:
            window.iconbitmap(default=str(ICON_ICO))
            return True
        except Exception:
            pass                      # a corrupt icon must not stop the app
    if ICON_PNG.exists():
        try:
            import tkinter as tk
            image = tk.PhotoImage(file=str(ICON_PNG), master=window)
            # Tk throws away an image nothing is holding on to, and the icon
            # silently disappears. Keeping it on the window keeps it alive.
            window._cinestat_icon = image
            window.iconphoto(True, image)
            return True
        except Exception:
            pass
    return False


def centre_on_screen(window, width, height):
    """Open in the middle of the screen, the way Windows programs do.

    Tk puts a new window wherever the window manager feels like, which on
    Windows is usually the top left corner underneath everything else.
    """
    try:
        left = max(0, (window.winfo_screenwidth() - width) // 2)
        # Slightly above the true middle: a window centred by measurement
        # looks low, because the eye counts the taskbar as part of the screen.
        top = max(0, (window.winfo_screenheight() - height) // 2 - 30)
        window.geometry(f"{width}x{height}+{left}+{top}")
    except Exception:
        window.geometry(f"{width}x{height}")


# ---------------------------------------------------------------------------
# Keyboard shortcuts, written the way this operating system writes them
# ---------------------------------------------------------------------------
#: What the menu should *say*, and what Tk should *listen for*. On a Mac the
#: same shortcut is Command; on Windows and Linux it is Ctrl. Keeping the pair
#: together in one place is what stops the menu promising a shortcut that was
#: never bound - a bug you cannot see in the code, only by pressing the keys.
MODIFIER_LABEL = "Cmd" if IS_MACOS else "Ctrl"
MODIFIER_KEY = "Command" if IS_MACOS else "Control"


def shortcut(key, shift=False):
    """Return (what the menu shows, what bind() listens for).

        shortcut("e")             -> ("Ctrl+E", "<Control-e>")
        shortcut("e", shift=True) -> ("Ctrl+Shift+E", "<Control-Shift-E>")

    Tk is fussy here: with Shift the letter in the event must be upper case,
    and without it, lower case. Getting that wrong binds nothing at all and
    fails silently, so it is worth having in one tested function.
    """
    if shift:
        label = f"{MODIFIER_LABEL}+Shift+{key.upper()}"
        sequence = f"<{MODIFIER_KEY}-Shift-{key.upper()}>"
    else:
        label = f"{MODIFIER_LABEL}+{key.upper()}"
        sequence = f"<{MODIFIER_KEY}-{key.lower()}>"
    return label, sequence
