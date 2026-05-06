#!/usr/bin/env python3
"""Simple Windows desktop client for openfortivpn.

This script provides a lightweight Tkinter UI to start and stop openfortivpn
using an existing configuration file.
"""

from __future__ import annotations

import queue
import shutil
import signal
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext


class OpenFortiVpnClient:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("OpenFortiVPN")
        self.root.geometry("760x460")
        self.root.minsize(680, 400)

        self.process: subprocess.Popen[str] | None = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.config_var = tk.StringVar(value=str(Path.home() / "openfortivpn" / "config.ini"))
        self.status_var = tk.StringVar(value="Idle")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 8}

        title = tk.Label(self.root, text="OpenFortiVPN", font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w", **pad)

        config_frame = tk.Frame(self.root)
        config_frame.pack(fill="x", padx=12)

        tk.Label(config_frame, text="Config file:").pack(side="left")
        tk.Entry(config_frame, textvariable=self.config_var).pack(side="left", fill="x", expand=True, padx=8)
        tk.Button(config_frame, text="Browse", command=self._browse_config).pack(side="left")

        control_frame = tk.Frame(self.root)
        control_frame.pack(fill="x", **pad)

        self.connect_button = tk.Button(control_frame, text="Connect", width=14, command=self.connect)
        self.connect_button.pack(side="left")

        self.disconnect_button = tk.Button(
            control_frame,
            text="Disconnect",
            width=14,
            command=self.disconnect,
            state="disabled",
        )
        self.disconnect_button.pack(side="left", padx=8)

        tk.Label(control_frame, textvariable=self.status_var).pack(side="left", padx=16)

        tk.Label(self.root, text="Activity").pack(anchor="w", padx=12)
        self.log_box = scrolledtext.ScrolledText(self.root, state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _browse_config(self) -> None:
        chosen = filedialog.askopenfilename(title="Select openfortivpn config file")
        if chosen:
            self.config_var.set(chosen)

    def _append_log(self, line: str) -> None:
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _queue_log(self, line: str) -> None:
        self.log_queue.put(line)

    def _drain_log_queue(self) -> None:
        while not self.log_queue.empty():
            self._append_log(self.log_queue.get_nowait())
        self.root.after(100, self._drain_log_queue)

    def _set_connected_state(self, connected: bool) -> None:
        self.connect_button.configure(state="disabled" if connected else "normal")
        self.disconnect_button.configure(state="normal" if connected else "disabled")

    def connect(self) -> None:
        if self.process and self.process.poll() is None:
            self._append_log("Already connected.")
            return

        binary = shutil.which("openfortivpn")
        if not binary:
            self.status_var.set("Missing binary")
            messagebox.showerror("openfortivpn not found", "openfortivpn executable was not found in PATH.")
            return

        config = Path(self.config_var.get()).expanduser()
        if not config.exists():
            self.status_var.set("Invalid config")
            messagebox.showerror("Config not found", f"Config file does not exist:\n{config}")
            return

        self.status_var.set("Connecting...")
        self._append_log(f"Starting: {binary} -c {config}")

        self.process = subprocess.Popen(
            [binary, "-c", str(config)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        self._set_connected_state(True)
        self.status_var.set("Connected")

        threading.Thread(target=self._read_output, daemon=True).start()
        threading.Thread(target=self._wait_for_exit, daemon=True).start()

    def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            self._queue_log(line.rstrip())

    def _wait_for_exit(self) -> None:
        if not self.process:
            return
        code = self.process.wait()
        self.process = None
        self.root.after(0, self._on_disconnected, code)

    def _on_disconnected(self, code: int) -> None:
        self.status_var.set("Disconnected")
        self._set_connected_state(False)
        self._append_log(f"VPN process exited with code {code}.")

    def disconnect(self) -> None:
        if not self.process or self.process.poll() is not None:
            self._append_log("No active connection.")
            return

        self.status_var.set("Disconnecting...")
        self._append_log("Disconnect requested by user.")

        try:
            self.process.send_signal(signal.SIGTERM)
        except OSError:
            pass

    def on_close(self) -> None:
        if self.process and self.process.poll() is None:
            self.disconnect()
        self.root.after(250, self.root.destroy)


def main() -> None:
    root = tk.Tk()
    OpenFortiVpnClient(root)
    root.mainloop()


if __name__ == "__main__":
    main()
