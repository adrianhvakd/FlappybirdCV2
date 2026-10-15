from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading


class VisionProcess:

    def __init__(self, camera=0, mirror=True, max_hands=1, gesture="pinch",
                 pinch_threshold=0.25, window=True, python=None, script=None):
        self._camera = camera
        self._mirror = mirror
        self._max_hands = max_hands
        self._gesture = gesture
        self._pinch_threshold = pinch_threshold
        self._window = window
        self._python = python or sys.executable
        self._script = script or os.path.join(os.path.dirname(__file__), "camera_view.py")

        self._lock = threading.Lock()
        self._proc = None
        self._reader = None
        self._server = None
        self._stop = threading.Event()

        self._status = "iniciando"
        self._gesture_name = "sin mano"
        self._hand_visible = False
        self._fingers = 0
        self._flap_pending = False

    def start(self):
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.bind(("127.0.0.1", 0))
        self._server.listen(1)
        self._server.settimeout(0.5)
        port = self._server.getsockname()[1]

        if getattr(sys, "frozen", False):
            base = [sys.executable, "--run-camera-process"]
        else:
            base = [self._python, self._script]

        cmd = base + [
            "--camera", str(self._camera),
            "--max-hands", str(self._max_hands),
            "--gesture", self._gesture,
            "--pinch-threshold", str(self._pinch_threshold),
            "--camera-port", str(port),
        ]
        if not self._mirror:
            cmd.append("--no-mirror")
        if not self._window:
            cmd.append("--no-window")

        self._proc = subprocess.Popen(cmd, stderr=subprocess.DEVNULL)
        self._reader = threading.Thread(target=self._read_loop, name="vision-reader", daemon=True)
        self._reader.start()

    def stop(self):
        self._stop.set()
        proc = self._proc
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
        if self._reader is not None:
            self._reader.join(timeout=1.5)
        if self._server is not None:
            self._server.close()

    @property
    def status(self):
        with self._lock:
            return self._status

    @property
    def gesture(self):
        with self._lock:
            return self._gesture_name

    @property
    def hand_visible(self):
        with self._lock:
            return self._hand_visible

    def poll(self):
        with self._lock:
            flap = self._flap_pending
            self._flap_pending = False
            return flap

    def _read_loop(self):
        conn = None
        try:
            while not self._stop.is_set() and conn is None:
                try:
                    conn, _ = self._server.accept()
                except socket.timeout:
                    if self._proc is not None and self._proc.poll() is not None:
                        self._set_status("error al iniciar el proceso de cámara")
                        return
            if conn is None:
                return
            conn.settimeout(0.5)
            buffer = b""
            while not self._stop.is_set():
                try:
                    chunk = conn.recv(4096)
                except socket.timeout:
                    continue
                if not chunk:
                    break
                buffer += chunk
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    self._handle_line(line.decode("utf-8", "replace"))
        except OSError:
            pass
        finally:
            if conn is not None:
                conn.close()
            with self._lock:
                if self._status == "ok":
                    self._status = "cerrada"
                elif self._status == "iniciando":
                    self._status = "error al iniciar el proceso de cámara"

    def _set_status(self, value):
        with self._lock:
            self._status = value

    def _handle_line(self, line):
        line = line.strip()
        if not line:
            return
        try:
            event = json.loads(line)
        except ValueError:
            return
        kind = event.get("type")
        with self._lock:
            if kind == "status":
                self._status = event.get("value", "ok")
            elif kind == "gesture":
                self._gesture_name = event.get("value", "sin mano")
                self._hand_visible = bool(event.get("hand", False))
                self._fingers = int(event.get("fingers", 0))
            elif kind == "flap":
                self._flap_pending = True
