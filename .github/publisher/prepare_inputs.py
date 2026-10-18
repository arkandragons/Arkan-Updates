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
edition = data.get("edition") or {}
edition_id = str(edition.get("id", ""))
manifest_filename = str(edition.get("manifestFilename", ""))
if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", edition_id):
    raise SystemExit("invalid edition id")
if manifest_filename != f"manifest-{edition_id}.json":
    raise SystemExit("invalid edition manifest")
print(f"edition_id={edition_id}")
print(f"edition_name={edition.get('displayName', edition_id)}")
print(f"manifest_filename={manifest_filename}")

for name in ("archive", "inventory"):
    entry = data.get(name) or {}
    key = str(entry.get("key", ""))
    if not key.startswith(f"launcher-promotions/{data['promotionId']}/"):
        raise SystemExit(f"invalid staging key: {name}")
    print(f"{name}_key={key}")
print(f"revision={data['revision']}")
