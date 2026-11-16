import csv
import http.client
import json
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

API_URL = "PASTE_INVOKE_URL_HERE"
LEVELS = [1, 5, 10, 25]
BODY = json.dumps({"patient_id": "P001", "doctor_id": "D101", "slot": "2026-11-20T10:30"})
HOST = urlparse(API_URL).netloc


def connect(_):
    conn = http.client.HTTPSConnection(HOST, timeout=30)
    conn.request("GET", "/warmup-connection")
    conn.getresponse().read()
    return conn


def call(conn):
    start = time.perf_counter()
    conn.request("POST", "/appointments", body=BODY,
                 headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = resp.read()
    ms = (time.perf_counter() - start) * 1000
    try:
        cold = json.loads(data).get("cold_start")
    except ValueError:
        cold = None
    conn.close()
    return round(ms, 2), resp.status, cold


rows = []
for level in LEVELS:
    with ThreadPoolExecutor(level) as pool:
        conns = list(pool.map(connect, range(level)))
        results = list(pool.map(call, conns))
    for ms, status, cold in results:
        rows.append([level, ms, status, cold])
    times = sorted(r[0] for r in results)
    print(f"{level:>2} concurrent: median {times[len(times) // 2]:.0f} ms, max {times[-1]:.0f} ms, "
          f"cold starts {sum(1 for r in results if r[2] is True)}, "
          f"errors {sum(1 for r in results if r[1] != 201)}")
    time.sleep(3)

with open("scaling.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["concurrency", "latency_ms", "status", "cold_start"])
    writer.writerows(rows)
print("Saved scaling.csv")
