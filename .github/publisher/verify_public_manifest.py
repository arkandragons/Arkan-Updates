#!/usr/bin/env python3
import hashlib
import pathlib
import sys
import time
import urllib.request

RAW_MANIFEST_BASE = "https://raw.githubusercontent.com/arkandragons/Arkan-Updates/main"


def public_manifest_url(manifest_path: pathlib.Path) -> str:
    filename = manifest_path.name
    if filename in ("", ".", ".."):
        raise ValueError("manifest path must name a file")
    return f"{RAW_MANIFEST_BASE}/{filename}"


def main(argv: list[str]) -> None:
    if len(argv) != 2:
        raise SystemExit(f"usage: {pathlib.Path(argv[0]).name} <manifest-path>")

    manifest_path = pathlib.Path(argv[1])
    local = manifest_path.read_bytes()
    expected = hashlib.sha256(local).hexdigest()
    url = public_manifest_url(manifest_path)

    for attempt in range(12):
        request = urllib.request.Request(
            url + f"?verify={time.time_ns()}",
            headers={"Cache-Control": "no-cache"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                actual = hashlib.sha256(response.read()).hexdigest()
            if actual == expected:
                print(expected)
                return
        except Exception:
            pass
        time.sleep(5)
    raise SystemExit("public manifest did not converge to the promoted pointer")


if __name__ == "__main__":
    main(sys.argv)
