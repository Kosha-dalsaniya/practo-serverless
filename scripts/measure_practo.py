import csv
import http.client
import json
import statistics
import time
from urllib.parse import urlparse

API_URL = "PASTE_INVOKE_URL_HERE"
RUNS = 5
REQUESTS_PER_RUN = 100
BODY = json.dumps({"patient_id": "P001", "doctor_id": "D101", "slot": "2026-11-20T10:30"})

url = urlparse(API_URL)
base = url.path.rstrip("/")
rows = []

for run in range(1, RUNS + 1):
    input(f"\nRun {run}: set the Lambda environment variable RUN={run}, "
          "wait for 'Successfully updated', then press Enter...")
    conn = http.client.HTTPSConnection(url.netloc, timeout=30)
    # Open the HTTPS connection first. This path has no route, so API Gateway
    # answers 404 itself and Lambda is not invoked.
    conn.request("GET", base + "/warmup-connection")
    conn.getresponse().read()

    for n in range(1, REQUESTS_PER_RUN + 1):
        start = time.perf_counter()
        conn.request("POST", base + "/appointments", body=BODY,
                     headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        data = resp.read()
        ms = (time.perf_counter() - start) * 1000
        try:
            cold = json.loads(data).get("cold_start")
        except ValueError:
            cold = None
        rows.append([run, n, round(ms, 2), resp.status, cold])
    conn.close()
    first = rows[-REQUESTS_PER_RUN]
    print(f"  request 1: {first[2]} ms, cold_start={first[4]}")

with open("latency.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["run", "request_no", "latency_ms", "status", "cold_start"])
    writer.writerows(rows)

cold = [r[2] for r in rows if r[4] is True]
warm = [r[2] for r in rows if r[4] is False]
print(f"\nCold starts: {len(cold)}  values: {cold}")
if warm:
    warm.sort()
    print(f"Warm requests: {len(warm)}")
    print(f"  mean {statistics.mean(warm):.1f} ms, median {statistics.median(warm):.1f} ms")
    print(f"  min {warm[0]:.1f} ms, max {warm[-1]:.1f} ms, p95 {warm[int(len(warm) * 0.95) - 1]:.1f} ms")
print("Saved latency.csv")
