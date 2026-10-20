import tkinter as tk
from tkinter import Menu

from .usage_fetcher import UsageSnapshot

GREEN = "#2ecc71"
YELLOW = "#f1c40f"
RED = "#e74c3c"
NEUTRAL = "#888888"
BG = "#1e1e1e"


def color_for_percent(percent):
    if percent is None:
        return NEUTRAL
    if percent < 50:
        return GREEN
    if percent <= 80:
        return YELLOW
    return RED


def compute_position(position, window_w, window_h, screen_w, screen_h, margin=20):
    positions = {
        "top-right": (screen_w - window_w - margin, margin),
        "top-left": (margin, margin),
        "bottom-right": (screen_w - window_w - margin, screen_h - window_h - margin),
        "bottom-left": (margin, screen_h - window_h - margin),
    }
    return positions[position]


def format_bar_text(last_session, last_week, has_error):
    """Returns (session_text, week_text) given the last known-good
    percentages and whether the latest fetch errored.

    Keeps showing the last known-good percentages across a failed
    refresh; only appends a small warning marker (to the session text
    only), never blanks the numbers out.
    """
    session_text = (
        f"Session: {last_session}%" if last_session is not None else "Session: --%"
    )
    week_text = f"Week: {last_week}%" if last_week is not None else "Week: --%"

    if has_error:
        session_text += " ⚠"

    return session_text, week_text


class FloatingBar:
    def __init__(self, root: tk.Tk, position: str = "top-right", on_exit=None):
        self.root = root
        self._position = position
        self._drag_data = {"x": 0, "y": 0}
        self._last_session_percent = None
        self._last_week_percent = None
        self._on_exit = on_exit or self.root.destroy

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.configure(bg=BG)

        self.session_label = tk.Label(
            root, text="Session: --%", fg=NEUTRAL, bg=BG, font=("Sans", 11)
        )
        self.session_label.pack(side="left", padx=(10, 4), pady=6)

        self.week_label = tk.Label(
            root, text="Week: --%", fg=NEUTRAL, bg=BG, font=("Sans", 11)
        )
        self.week_label.pack(side="left", padx=(4, 10), pady=6)

        for widget in (root, self.session_label, self.week_label):
            widget.bind("<ButtonPress-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)
            widget.bind("<Button-3>", self._show_context_menu)

        root.bind("<Escape>", lambda event: self._on_exit())

        self._menu = Menu(self.root, tearoff=0)
        self._menu.add_command(label="結束", command=self._on_exit)

        root.update_idletasks()
        self._place_at_default_position()
        self.root.focus_force()

    def _place_at_default_position(self):
        window_w = self.root.winfo_width()
        window_h = self.root.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x, y = compute_position(self._position, window_w, window_h, screen_w, screen_h)
        self.root.geometry(f"+{x}+{y}")

    def _on_drag_start(self, event):
        self._drag_data["x"] = event.x_root - self.root.winfo_x()
        self._drag_data["y"] = event.y_root - self.root.winfo_y()

    def _on_drag_motion(self, event):
        x = event.x_root - self._drag_data["x"]
        y = event.y_root - self._drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def _show_context_menu(self, event):
        try:
            self._menu.tk_popup(event.x_root, event.y_root)
        finally:
            self._menu.grab_release()

    def update_snapshot(self, snapshot: UsageSnapshot) -> None:
        # Keep showing the last known-good percentages across a failed
        # refresh; only append a warning marker, never blank the numbers out.
        if snapshot.session_percent is not None:
            self._last_session_percent = snapshot.session_percent
        if snapshot.week_percent is not None:
            self._last_week_percent = snapshot.week_percent

        session_text, week_text = format_bar_text(
            self._last_session_percent, self._last_week_percent, bool(snapshot.error)
        )

        self.session_label.config(text=session_text, fg=color_for_percent(self._last_session_percent))
        self.week_label.config(text=week_text, fg=color_for_percent(self._last_week_percent))
