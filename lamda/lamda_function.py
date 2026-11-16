import base64
import json
import os
import uuid
from datetime import datetime, timezone

import boto3

TABLE = boto3.resource("dynamodb").Table(os.environ.get("TABLE_NAME", "Appointments"))
COLD = True  # True only for the first request in a new execution environment

REQUIRED = ("patient_id", "doctor_id", "slot")


def reply(status, body, cold):
    body["cold_start"] = cold
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    global COLD
    cold, COLD = COLD, False
    method = event.get("requestContext", {}).get("http", {}).get("method", "")

    if method == "POST":
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return reply(400, {"error": "body is not valid JSON"}, cold)
        if not isinstance(data, dict):
            return reply(400, {"error": "body must be a JSON object"}, cold)
        bad = [k for k in REQUIRED if not isinstance(data.get(k), str) or not data[k].strip()]
        if bad:
            return reply(400, {"error": "missing or invalid fields", "fields": bad}, cold)
        item = {
            "appointment_id": str(uuid.uuid4()),
            "patient_id": data["patient_id"],
            "doctor_id": data["doctor_id"],
            "slot": data["slot"],
            "status": "BOOKED",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        TABLE.put_item(Item=item)
        return reply(201, item, cold)

    if method == "GET":
        appt_id = (event.get("pathParameters") or {}).get("id")
        if not appt_id:
            return reply(400, {"error": "appointment id required"}, cold)
        found = TABLE.get_item(Key={"appointment_id": appt_id}).get("Item")
        if not found:
            return reply(404, {"error": "appointment not found"}, cold)
        return reply(200, found, cold)

    return reply(405, {"error": "method not allowed"}, cold)
