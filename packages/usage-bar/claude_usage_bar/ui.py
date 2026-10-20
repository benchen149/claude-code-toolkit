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


class FloatingBar:
    def __init__(self, root: tk.Tk, position: str = "top-right"):
        self.root = root
        self._position = position
        self._drag_data = {"x": 0, "y": 0}
        self._last_session_percent = None
        self._last_week_percent = None

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

        root.bind("<Escape>", lambda event: root.destroy())

        root.update_idletasks()
        self._place_at_default_position()

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
        menu = Menu(self.root, tearoff=0)
        menu.add_command(label="結束", command=self.root.destroy)
        menu.tk_popup(event.x_root, event.y_root)

    def update_snapshot(self, snapshot: UsageSnapshot) -> None:
        # Keep showing the last known-good percentages across a failed
        # refresh; only append a warning marker, never blank the numbers out.
        if snapshot.session_percent is not None:
            self._last_session_percent = snapshot.session_percent
        if snapshot.week_percent is not None:
            self._last_week_percent = snapshot.week_percent

        warn = " ⚠" if snapshot.error else ""

        session_text = (
            f"Session: {self._last_session_percent}%{warn}"
            if self._last_session_percent is not None
            else f"Session: --%{warn}"
        )
        week_text = (
            f"Week: {self._last_week_percent}%{warn}"
            if self._last_week_percent is not None
            else f"Week: --%{warn}"
        )

        self.session_label.config(text=session_text, fg=color_for_percent(self._last_session_percent))
        self.week_label.config(text=week_text, fg=color_for_percent(self._last_week_percent))
