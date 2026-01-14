# Built-ins
import time
import uuid
from collections import deque
from dataclasses import dataclass
from threading import Condition, Event, Lock
from typing import Deque, Dict, Optional, Tuple, Any

# Flask imports
from flask import Flask, request
from flask.json import jsonify

app = Flask(__name__)

# ----------------------------
# Data model / shared state
# ----------------------------

@dataclass
class LogRequest:
    request_id: str
    start_ts: float
    end_ts: float
    done: Event
    result_logs: Optional[list] = None
    error: Optional[str] = None


# Queue for pending user /logs requests
_pending: Deque[LogRequest] = deque()

# In-flight request that has been handed to the camera but not yet answered
_in_flight: Dict[str, LogRequest] = {}

# Condition variable for coordinating /logs and /poll_for_command
_cv = Condition(Lock())


def _parse_timestamps() -> Tuple[float, float]:
    """
    Parse optional query params startTimestamp/endTimestamp.
    If not provided, choose wide-enough numeric bounds (JSON doesn't support inf).
    """
    start_raw = request.args.get("startTimestamp")
    end_raw = request.args.get("endTimestamp")

    # Default: "all logs"
    start_ts = 0.0
    # 100 years into the future is "effectively infinite" for epoch timestamps.
    end_ts = time.time() + 100 * 365 * 24 * 60 * 60

    if start_raw is not None:
        try:
            start_ts = float(start_raw)
        except ValueError:
            raise ValueError("startTimestamp must be a float")

    if end_raw is not None:
        try:
            end_ts = float(end_raw)
        except ValueError:
            raise ValueError("endTimestamp must be a float")

    # Boundary sanity
    if start_ts > end_ts:
        raise ValueError("startTimestamp must be <= endTimestamp")

    return start_ts, end_ts


@app.route("/logs")
def get_logs():
    """
    User endpoint: enqueue a log request, wait for camera to respond via /send_logs,
    then return the logs.
    """
    try:
        start_ts, end_ts = _parse_timestamps()
    except ValueError as e:
        return jsonify({"error": str(e), "logs": []}), 400

    lr = LogRequest(
        request_id=str(uuid.uuid4()),
        start_ts=start_ts,
        end_ts=end_ts,
        done=Event(),
    )

    # Enqueue request, notify any waiting camera poll
    with _cv:
        _pending.append(lr)
        _cv.notify_all()

    # Wait for camera response
    # Camera poll timeout is 60s; give ourselves a bit more time end-to-end.
    ok = lr.done.wait(timeout=75)

    if not ok:
        # Timed out waiting for camera.
        # Clean up if still pending/in-flight.
        with _cv:
            # remove from pending if still there
            try:
                _pending.remove(lr)
            except ValueError:
                pass
            _in_flight.pop(lr.request_id, None)
        return jsonify({"error": "Timed out waiting for camera logs", "logs": []}), 504

    if lr.error:
        return jsonify({"error": lr.error, "logs": []}), 500

    return jsonify({"logs": lr.result_logs or [], "requestId": lr.request_id})


@app.route("/poll_for_command")
def poll_for_command():
    """
    Camera endpoint: long-poll until there's a pending /logs request.
    Returns either:
      - {"command": "send_logs", "requestId": "...", "startTimestamp": ..., "endTimestamp": ...}
      - {"command": "noop"}  (when no pending request before timeout)
    """
    deadline = time.time() + 55  # keep < camera 60s timeout margin

    with _cv:
        while not _pending:
            remaining = deadline - time.time()
            if remaining <= 0:
                return jsonify({"command": "noop"})
            _cv.wait(timeout=remaining)

        lr = _pending.popleft()
        _in_flight[lr.request_id] = lr

    return jsonify(
        {
            "command": "send_logs",
            "requestId": lr.request_id,
            "startTimestamp": lr.start_ts,
            "endTimestamp": lr.end_ts,
        }
    )


@app.route("/send_logs", methods=["POST"])
def send_logs():
    """
    Camera callback: send logs back for a specific requestId.
    Payload:
      - requestId: str
      - logs: list
    """
    req_payload: Dict[str, Any] = request.get_json(silent=True) or {}
    request_id = req_payload.get("requestId")
    logs = req_payload.get("logs")

    if not request_id or logs is None:
        return jsonify({"error": "Missing requestId or logs"}), 400

    with _cv:
        lr = _in_flight.pop(request_id, None)

    if lr is None:
        # Could happen if /logs timed out and cleaned up
        return jsonify({"status": "ignored", "reason": "unknown_or_expired_requestId"}), 200

    lr.result_logs = logs
    lr.done.set()
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Important: threaded=True so /poll_for_command can block without starving others
    app.run(host="0.0.0.0", debug=True, port=8080, threaded=True)
