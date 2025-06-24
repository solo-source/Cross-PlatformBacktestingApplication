# src/data/stream.py
"""
LiveStreamer: provide real-time data via REST polling and WebSocket.
"""

import json
import threading
import time
import requests
from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWebSockets import QWebSocket


class RestStreamer(QObject):
    """Poll REST endpoint periodically and emit new data."""
    new_data = Signal(dict)

    def __init__(self, url: str, interval_s: int = 5, parent=None):
        super().__init__(parent)
        self.url = url
        self.interval_s = interval_s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.fetch)

    def start(self):
        self._timer.start(self.interval_s * 1000)

    def stop(self):
        self._timer.stop()

    def fetch(self):
        try:
            resp = requests.get(self.url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            self.new_data.emit(data)
        except Exception as e:
            print(f"[RestStreamer] Error fetching {self.url}: {e}")


class WebSocketStreamer(QObject):
    """Subscribe to a WebSocket feed and emit incoming messages."""
    new_data = Signal(dict)

    def __init__(self, url: str, subscribe_msg: dict, parent=None):
        super().__init__(parent)
        self.socket = QWebSocket()
        self.socket.connected.connect(self._on_connected)
        self.socket.textMessageReceived.connect(self._on_message)
        self.url = url
        self.subscribe_msg = subscribe_msg

    def start(self):
        self.socket.open(self.url)

    def _on_connected(self):
        self.socket.sendTextMessage(json.dumps(self.subscribe_msg))

    def _on_message(self, msg: str):
        try:
            data = json.loads(msg)
            self.new_data.emit(data)
        except Exception as e:
            print(f"[WebSocketStreamer] Invalid JSON: {e}")
