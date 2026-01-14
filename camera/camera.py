from enum import Enum
import os
from random import randrange
import time
from threading import Event, Lock, Thread

import requests

from common.utils.logging_utils import logger


class CameraEvents(Enum):
    motion_detected = 'motion detected'
    user_started_viewing = 'user started viewing live video'
    brightness_adjusted = 'brightness adjusted'


_API_BASE_URL = os.environ['API_BASE_URL']
_LOG_PERIOD = 10
_EVENT_LIST = [e for e in CameraEvents]


class Camera:
    """
    Implements a video camera that can be asked to send logs to a client
    on demand without opening any ports, via HTTP long-polling.
    """
    def __init__(self):
        self._logs = []
        self._saved_log = None
        self._log_lock = Lock()
        self._stop = Event()
        self._generate_logs_thread = None

    def __del__(self):
        # Clean up the log generation thread.
        # First tell it to stop.
        self._stop.set()
        # Then wait for the thread to complete.
        if self._generate_logs_thread:
            self._generate_logs_thread.join()

    def _generate_log_description(self):
        """
        Randomly generates one log description (string).
        """
        event = _EVENT_LIST[randrange(len(CameraEvents))]
        if event  == CameraEvents.motion_detected:
            coordinates = (randrange(100), randrange(100))
            return f"{event.value} at {coordinates}"
        if event == CameraEvents.brightness_adjusted:
            adjustment = randrange(-10, 11)
            return f"{event.value} {adjustment}"
        return event.value

    def _generate_log(self):
        """
        Randomly generates one log entry, which includes description (string)
        and UTC timestamp.
        """
        return {
            "timestamp": time.time(),
            "description": self._generate_log_description()
        }

    def _add_log(self):
        """
        Adds one entry to the logs.
        """
        self._saved_log = self._saved_log or self._generate_log()
        self._logs.append(self._saved_log)
        self._saved_log = None

    def _generate_logs(self, iterations=None):
        """
        Generates a new log entry every _LOG_PERIOD until the Camera object is
        destroyed (iterations is for testing).
        """
        i = 0
        while (not self._stop.is_set()
               and (iterations is None or i < iterations)):
            with self._log_lock:
                self._add_log()
            i += 1
            time.sleep(_LOG_PERIOD)

    def _poll_for_command(self):
        """
        Makes the poll_for_command request to the API via HTTP long
        polling.  

        Returns the command returned by the API, if any.
        """
        logger.debug("Polling for command...")
        # Request the command from the server (long-poll)
        resp = requests.get(f"{_API_BASE_URL}/poll_for_command", timeout=60)
        resp.raise_for_status()
        return resp.json()

    def _respond_to_command(self, command):
        """
        Responds to the API's command to send logs.
        """
        cmd = command.get("command")
        if cmd != "send_logs":
            # noop or unknown command
            return

        request_id = command.get("requestId")
        start_timestamp = command.get("startTimestamp")
        end_timestamp = command.get("endTimestamp")

        if request_id is None:
            logger.error("Missing requestId in command")
            return
        if start_timestamp is None or end_timestamp is None:
            logger.error("Missing startTimestamp/endTimestamp in command")
            return

        # Filter logs safely (under lock to avoid concurrent mutation while filtering)
        with self._log_lock:
            logs = list(
                filter(
                    lambda x: (x["timestamp"] >= start_timestamp and x["timestamp"] <= end_timestamp),
                    self._logs,
                )
            )

        logger.debug(
            "Responding to command %s. Logs between %f and %f: %s",
            request_id,
            start_timestamp,
            end_timestamp,
            logs
        )
        resp = requests.post(
            f"{_API_BASE_URL}/send_logs",
            json={"requestId": request_id, "logs": logs}
        )
        resp.raise_for_status()

    def run(self):
        """
        Runs camera in an infinite loop, generating logs and waiting for
        commands from the API.
        """
        self._generate_logs_thread = Thread(target=self._generate_logs)
        self._generate_logs_thread.start()

        while True:
            try:
                command = self._poll_for_command()
            except Exception as e:
                logger.error("Camera error on wait for command request attempt: %s", str(e))
                continue

            try:
                self._respond_to_command(command)
            except Exception as e:
                logger.error("Camera error on command response: %s", str(e))



def main():
    camera = Camera()
    camera.run()


if __name__ == "__main__":
    main()
