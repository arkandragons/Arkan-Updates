#!/usr/bin/env python3
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import posixpath
import re
import stat
import zipfile

MAX_FILES = 100_000
MAX_UNCOMPRESSED = 64 * 1024**3
MAX_FILE = 4 * 1024**3
MAX_RATIO = 250
FORBIDDEN_ROOTS = {
    "saves", "logs", "crash-reports", "screenshots", "backups",
    "webcache", "cache", ".git", ".idea", ".vscode"
}
FORBIDDEN_NAMES = {
    ".env", "accounts.json", "launcher_accounts.json", "launcher_profiles.json",
    "usercache.json", "usernamecache.json", "servers.dat", "knownkeys.txt",
    "optionsof.txt.bak"
}
WINDOWS_DEVICES = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}


def digest_stream(stream):
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        sha1.update(chunk)
        sha256.update(chunk)
    return size, sha1.hexdigest(), sha256.hexdigest()


def canonical_path(raw):
    if not isinstance(raw, str) or not raw or "\\" in raw or raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
        raise ValueError(f"invalid path: {raw!r}")
    normalized = posixpath.normpath(raw)
    if normalized in (".", "..") or normalized.startswith("../") or normalized != raw:
        raise ValueError(f"non-canonical path: {raw!r}")
    parts = normalized.split("/")
    if any(not part or part in (".", "..") for part in parts):
        raise ValueError(f"invalid path segment: {raw!r}")
    if parts[0].casefold() in FORBIDDEN_ROOTS:
        raise ValueError(f"forbidden root: {raw}")
    if parts[-1].casefold() in FORBIDDEN_NAMES:
        raise ValueError(f"forbidden account/secret file: {raw}")
    if any(part.split(".")[0].casefold() in WINDOWS_DEVICES for part in parts):
        raise ValueError(f"reserved Windows name: {raw}")
    if any(ord(char) < 32 for char in raw):
        raise ValueError(f"control character in path: {raw!r}")
    return normalized


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


parser = argparse.ArgumentParser()
parser.add_argument("--descriptor", required=True)
parser.add_argument("--archive", required=True)
parser.add_argument("--inventory", required=True)
parser.add_argument("--repository", required=True)
parser.add_argument("--mode", choices=("validate", "publish"), required=True)
parser.add_argument("--current-manifest", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

descriptor_path = pathlib.Path(args.descriptor)
archive_path = pathlib.Path(args.archive)
inventory_path = pathlib.Path(args.inventory)
current_path = pathlib.Path(args.current_manifest)
descriptor = load_json(descriptor_path)
inventory = load_json(inventory_path)

if descriptor.get("protocol") != 1 or descriptor.get("edition") != "standard":
    raise SystemExit("descriptor protocol or edition rejected")
if not re.fullmatch(r"\d{10,20}", str(descriptor.get("revision", ""))):
    raise SystemExit("invalid canonical revision")
expected_pointer = str(descriptor.get("expectedCurrentManifestSha256", "")).lower()
if hashlib.sha256(current_path.read_bytes()).hexdigest() != expected_pointer:
    raise SystemExit("CURRENT_MANIFEST_CHANGED")

for path, metadata in ((archive_path, descriptor.get("archive") or {}), (inventory_path, descriptor.get("inventory") or {})):
    size = path.stat().st_size
    if size != int(metadata.get("size", -1)):
        raise SystemExit(f"size mismatch: {path.name}")
    if hashlib.sha256(path.read_bytes()).hexdigest() != str(metadata.get("sha256", "")).lower():
        raise SystemExit(f"sha256 mismatch: {path.name}")

files = inventory.get("files") if isinstance(inventory, dict) else None
if not isinstance(files, list) or not files or len(files) > MAX_FILES:
    raise SystemExit("inventory file count rejected")
if len(files) != int(descriptor["inventory"].get("fileCount", len(files))):
    raise SystemExit("inventory summary file count mismatch")

expected = {}
casefolded = set()
declared_total = 0
for item in files:
    if not isinstance(item, dict):
        raise SystemExit("invalid inventory entry")
    try:
        item_path = canonical_path(item.get("path"))
    except ValueError as error:
        raise SystemExit(str(error))
    folded = item_path.casefold()
    if item_path in expected or folded in casefolded:
        raise SystemExit(f"duplicate or case-colliding path: {item_path}")
    size = item.get("size")
    checksum = str(item.get("sha256", "")).lower()
    if not isinstance(size, int) or size < 0 or size > MAX_FILE or not re.fullmatch(r"[a-f0-9]{64}", checksum):
        raise SystemExit(f"invalid inventory metadata: {item_path}")
    expected[item_path] = {"size": size, "sha256": checksum}
    casefolded.add(folded)
    declared_total += size

if declared_total != int(descriptor["inventory"].get("totalUncompressedBytes", declared_total)):
    raise SystemExit("inventory uncompressed size mismatch")
if declared_total > MAX_UNCOMPRESSED:
    raise SystemExit("uncompressed package exceeds policy")

actual = {}
pack_descriptor = None
with zipfile.ZipFile(archive_path) as archive:
    members = [entry for entry in archive.infolist() if not entry.is_dir()]
    if len(members) != len(expected):
        raise SystemExit("archive and inventory file counts differ")
    compressed_total = sum(max(0, entry.compress_size) for entry in members)
    if compressed_total and declared_total / compressed_total > MAX_RATIO:
        raise SystemExit("archive compression ratio rejected")
    seen = set()
    seen_casefolded = set()
    for entry in members:
        try:
            item_path = canonical_path(entry.filename)
        except ValueError as error:
            raise SystemExit(str(error))
        mode = (entry.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            raise SystemExit(f"symbolic link rejected: {item_path}")
        if item_path in seen or item_path.casefold() in seen_casefolded:
            raise SystemExit(f"duplicate archive entry: {item_path}")
        declared = expected.get(item_path)
        if not declared:
            raise SystemExit(f"undeclared archive entry: {item_path}")
        if entry.file_size != declared["size"] or entry.file_size > MAX_FILE:
            raise SystemExit(f"file size mismatch: {item_path}")
        with archive.open(entry, "r") as stream:
            size, sha1, sha256 = digest_stream(stream)
        if size != declared["size"] or sha256 != declared["sha256"]:
            raise SystemExit(f"file digest mismatch: {item_path}")
        actual[item_path] = {
            "name": pathlib.PurePosixPath(item_path).name,
            "path": item_path,
            "hash": sha1,
            "sha256": sha256,
            "size": size,
        }
        if item_path == ".arkan-pack.json":
            with archive.open(entry, "r") as stream:
                try:
                    pack_descriptor = json.load(stream)
                except Exception as error:
                    raise SystemExit(f"invalid .arkan-pack.json: {error}")
        seen.add(item_path)
        seen_casefolded.add(item_path.casefold())

for required in (".arkan-pack.json", "options.txt"):
    if required not in actual:
        raise SystemExit(f"required file missing: {required}")
if not any(name.startswith("mods/") and name.endswith(".jar") for name in actual):
    raise SystemExit("no managed mods found")

revision = str(descriptor["revision"])
tag = f"standard-{revision}"
bundle_url = f"https://github.com/{args.repository}/releases/download/{tag}/instance.zip"
inventory_url = f"https://github.com/{args.repository}/releases/download/{tag}/inventory.json"
generated = {
    "version": revision,
    "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    "edition": "standard",
    "runtime": descriptor.get("runtime"),
    "pack": pack_descriptor,
    "bundle": {
        "format": "zip",
        "url": bundle_url,
        "size": archive_path.stat().st_size,
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "inventoryUrl": inventory_url,
        "fileCount": len(actual),
        "totalUncompressedBytes": declared_total,
    },
    "files": [actual[name] for name in sorted(actual, key=lambda value: value.casefold())],
}
pathlib.Path(args.output).write_text(json.dumps(generated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"validated {len(actual)} files for Standard revision {revision}")
