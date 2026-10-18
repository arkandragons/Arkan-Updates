#!/usr/bin/env python3
import hashlib
import pathlib
import sys
import time
import urllib.request

local = pathlib.Path(sys.argv[1]).read_bytes()
expected = hashlib.sha256(local).hexdigest()
url = f"https://raw.githubusercontent.com/arkandragons/Arkan-Updates/main/{path.name}"
for attempt in range(12):
    request = urllib.request.Request(url + f"?verify={time.time_ns()}", headers={"Cache-Control": "no-cache"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            actual = hashlib.sha256(response.read()).hexdigest()
        if actual == expected:
            print(expected)
            raise SystemExit(0)
    except Exception:
        pass
    time.sleep(5)
raise SystemExit("public manifest did not converge to the promoted pointer")
