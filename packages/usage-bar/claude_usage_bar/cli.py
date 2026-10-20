import argparse
import queue
import threading
import tkinter as tk
from tkinter import messagebox

from .ui import FloatingBar
from .usage_fetcher import fetch_usage

POSITIONS = ["top-right", "top-left", "bottom-right", "bottom-left"]


def positive_int(value):
    n = int(value)
    if n < 1:
        raise argparse.ArgumentTypeError(f"must be a positive integer, got {value}")
    return n


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="claude-usage-bar",
        description="浮動視窗顯示 Claude Code 的 /usage 額度使用狀況",
    )
    parser.add_argument("--interval", type=positive_int, default=60, help="刷新間隔秒數(預設 60)")
    parser.add_argument(
        "--position", choices=POSITIONS, default="top-right", help="視窗位置(預設 top-right)"
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    result_queue: "queue.Queue" = queue.Queue()
    stop_event = threading.Event()

    def worker():
        while not stop_event.is_set():
            snapshot = fetch_usage()
            result_queue.put(snapshot)
            if snapshot.fatal:
                return
            stop_event.wait(args.interval)

    root = tk.Tk()

    exit_code = [0]

    def on_close():
        stop_event.set()
        root.destroy()

    bar = FloatingBar(root, position=args.position, on_exit=on_close)

    def poll_queue():
        try:
            while True:
                snapshot = result_queue.get_nowait()
                if snapshot.fatal:
                    messagebox.showerror("claude-usage-bar", snapshot.error or "發生無法復原的錯誤")
                    exit_code[0] = 1
                    on_close()
                    return
                bar.update_snapshot(snapshot)
        except queue.Empty:
            pass
        root.after(200, poll_queue)

    root.protocol("WM_DELETE_WINDOW", on_close)
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    root.after(200, poll_queue)
    root.mainloop()
    return exit_code[0]


if __name__ == "__main__":
    raise SystemExit(main())
