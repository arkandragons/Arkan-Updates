#!/usr/bin/env python3
import json
import re
import sys

data = json.load(open(sys.argv[1], encoding="utf-8"))
required = {
    "promotionId": r"^[0-9a-f-]{36}$",
    "revision": r"^\d{10,20}$",
}
for key, pattern in required.items():
    value = str(data.get(key, ""))
    if not re.fullmatch(pattern, value, re.I):
        raise SystemExit(f"invalid descriptor field: {key}")
for name in ("archive", "inventory"):
    entry = data.get(name) or {}
    key = str(entry.get("key", ""))
    if not key.startswith(f"launcher-promotions/{data['promotionId']}/"):
        raise SystemExit(f"invalid staging key: {name}")
    print(f"{name}_key={key}")
print(f"revision={data['revision']}")
