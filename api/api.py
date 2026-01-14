# Built-ins
import json
import os
import requests
import time

# Flask imports
from flask import Flask, request
from flask.json import jsonify


app = Flask(__name__)


@app.route("/logs")
def get_logs():
    """
    The user calls this endpoint to fetch logs from the camera.

    It can take the optional query parameters:
      - startTimestamp: (float) Fetch logs with timestamp >= this parameter.
      - endTimestamp: (float) Fetch logs with timestamp <= this parameter.

    Response (JSON):
    - logs: list of log objects, containing camera logs.

    The response must have the "logs" field in the payload, but feel free
    to add others if you need them.
    """
    start_timestamp = request.args.get("startTimestamp")
    end_timestamp = request.args.get("endTimestamp")
    resp_payload = {"logs": []}
    # TODO: Write code here to set resp_payload.logs
    return jsonify(resp_payload)


@app.route("/send_logs", methods=["POST"])
def send_logs():
    """
    This endpoint is used by the camera to send logs back to the API.

    Request payload (JSON):
    - logs: (array of log objects) the logs being sent from the camera.

    The request must have the above fields in the payload, but feel free
    to add others if you need them.

    Also feel free to add any fields to the response that you'd like.
    """
    req_payload = request.get_json()
    logs = req_payload["logs"]
    # TODO: Write code here to process logs
    return jsonify({})


@app.route("/poll_for_command")
def poll_for_command():
    """
    This is the endpoint that implements long polling. The camera calls this
    endpoint to be notified when the api server wants event logs.
    (i.e., when the api server gets a /logs GET request from the user).

    Conceivably, it could be used to poll for other command besides "get logs",
    but here we will only be implementing that command.

    Feel free to structure the response payload however you see fit.
    """
    resp_payload = {}
    # TODO: Write code here to correctly set resp_payload (the command returned to the camera)
    return jsonify(resp_payload)


if __name__ == '__main__':
    app.run(debug=True, port=8080)
