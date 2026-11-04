#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import pathlib
import urllib.request
import time

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--secret", required=True)
parser.add_argument("--promotion", required=True)
parser.add_argument("--state", required=True)
parser.add_argument("--run-id", required=True)
parser.add_argument("--manifest")
parser.add_argument("--failure")
parser.add_argument("--failure-file")
args = parser.parse_args()

payload = {"promotionId": args.promotion, "state": args.state, "runId": args.run_id}
if args.manifest and pathlib.Path(args.manifest).exists():
    payload["manifestSha256"] = hashlib.sha256(pathlib.Path(args.manifest).read_bytes()).hexdigest()
failure_message = args.failure
if args.failure_file and pathlib.Path(args.failure_file).exists():
    lines = pathlib.Path(args.failure_file).read_text(encoding="utf-8", errors="replace").splitlines()
    details = next((line.strip() for line in reversed(lines) if line.strip()), "")
    if details:
        failure_message = details[:500]
if failure_message:
    payload["failure"] = {"message": failure_message}
body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
signature = hmac.new(args.secret.encode(), body, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    args.url,
    data=body,
    method="POST",
    headers={"Content-Type": "application/json", "X-Arkan-Publisher-Signature": f"sha256={signature}"},
)
last_error = None
for attempt in range(6):
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            if response.status in (200, 204):
                raise SystemExit(0)
            last_error = f"HTTP {response.status}"
    except Exception as error:
        last_error = str(error)
    time.sleep(min(30, 2 ** attempt))
raise SystemExit(f"callback failed after retries: {last_error}")
