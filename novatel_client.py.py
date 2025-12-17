import socket
import threading
import time
from collections import deque


class NovatelClient:
    """
    lat/lon  : BESTPOSA
    yaw      : INSPVA (AZIMUTH)

    get_pose():
      - returns time-aligned (lat, lon, yaw)
      - yaw must be within max_yaw_dt seconds of position timestamp
    """

    def __init__(
        self,
        host="192.168.3.22",
        port=2000,
        max_yaw_dt=0.05,   # seconds
        yaw_buffer_sec=2.0
    ):
        self.host = host
        self.port = port
        self.max_yaw_dt = max_yaw_dt

        self._lock = threading.Lock()
        self._stop_evt = threading.Event()
        self._thread = None

        # Latest position
        self._lat = None
        self._lon = None
        self._pos_ts = None

        # Yaw buffer: [(timestamp, yaw), ...]
        self._yaw_buf = deque()
        self._yaw_buffer_sec = yaw_buffer_sec

    # ---------- Public API ----------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_evt.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_evt.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def get_pose(self):
        """
        Returns (lat, lon, yaw) or (None, None, None)
        Yaw is time-aligned to the BESTPOSA timestamp.
        """
        with self._lock:
            if self._lat is None or self._lon is None or self._pos_ts is None:
                return None, None, None

            pos_ts = self._pos_ts
            lat = self._lat
            lon = self._lon

            best_yaw = None
            best_dt = None

            for ts, yaw in self._yaw_buf:
                dt = abs(ts - pos_ts)
                if best_dt is None or dt < best_dt:
                    best_dt = dt
                    best_yaw = yaw

            if best_dt is None or best_dt > self.max_yaw_dt:
                return lat, lon, None

            return lat, lon, best_yaw

    # ---------- Internal TCP Loop ----------
    def _run(self):
        sock = None
        buf = ""

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            sock.settimeout(1.0)

            while not self._stop_evt.is_set():
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    buf += chunk.decode("ascii", errors="ignore")
                except socket.timeout:
                    continue

                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip("\r").strip()
                    if not line:
                        continue

                    now = time.time()

                    if line.startswith("#BESTPOSA"):
                        pos = self._parse_bestposa_latlon(line)
                        if pos:
                            with self._lock:
                                self._lat = pos["lat"]
                                self._lon = pos["lon"]
                                self._pos_ts = now

                    elif line.startswith("#INSPVA"):
                        yaw = self._parse_inspva_yaw(line)
                        if yaw is not None:
                            with self._lock:
                                self._yaw_buf.append((now, yaw))
                                self._prune_yaw_buf(now)

        finally:
            if sock:
                sock.close()

    # ---------- Parsing Helpers ----------
    @staticmethod
    def _split_novatel_ascii(line: str):
        if ";" not in line:
            return None
        body = line.split(";", 1)[1].split("*", 1)[0].strip()
        return body.split(",")

    def _parse_bestposa_latlon(self, s: str):
        body = self._split_novatel_ascii(s)
        if not body or len(body) < 4:
            return None
        try:
            return {
                "lat": float(body[2]),
                "lon": float(body[3]),
            }
        except ValueError:
            return None

    def _parse_inspva_yaw(self, s: str):
        body = self._split_novatel_ascii(s)
        if not body or len(body) < 12:
            return None
        try:
            return float(body[11])  # AZIMUTH
        except ValueError:
            return None

    def _prune_yaw_buf(self, now):
        while self._yaw_buf and (now - self._yaw_buf[0][0]) > self._yaw_buffer_sec:
            self._yaw_buf.popleft()
