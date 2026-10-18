#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import pathlib
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--secret", required=True)
parser.add_argument("--promotion", required=True)
parser.add_argument("--state", required=True)
parser.add_argument("--run-id", required=True)
parser.add_argument("--manifest")
parser.add_argument("--failure")
args = parser.parse_args()

payload = {"promotionId": args.promotion, "state": args.state, "runId": args.run_id}
if args.manifest and pathlib.Path(args.manifest).exists():
    payload["manifestSha256"] = hashlib.sha256(pathlib.Path(args.manifest).read_bytes()).hexdigest()
if args.failure:
    payload["failure"] = {"message": args.failure}
body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
signature = hmac.new(args.secret.encode(), body, hashlib.sha256).hexdigest()
request = urllib.request.Request(
    args.url,
    data=body,
    method="POST",
    headers={"Content-Type": "application/json", "X-Arkan-Publisher-Signature": f"sha256={signature}"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    if response.status not in (200, 204):
        raise SystemExit(f"callback failed: {response.status}")
