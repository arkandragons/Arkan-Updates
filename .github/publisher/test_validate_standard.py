#!/usr/bin/env python3
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
import zipfile

VALIDATOR = pathlib.Path(__file__).with_name("validate_standard.py")
RUNTIME = {
    "minecraftVersion": "1.20.1",
    "loader": "fabric",
    "loaderVersion": "0.16.14",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fixture(root, mutate=None):
    pack = {
        "packId": "arkan",
        "edition": "standard",
        "version": "Autumn Release",
        "minecraftVersion": RUNTIME["minecraftVersion"],
        "modLoader": RUNTIME["loader"],
        "modLoaderVersion": RUNTIME["loaderVersion"],
    }
    if mutate:
        mutate(pack)

    archive = root / "instance.zip"
    contents = {
        ".arkan-pack.json": json.dumps(pack, sort_keys=True).encode(),
        "options.txt": b"lang:pt_br\n",
        "mods/example.jar": b"not-a-real-jar-but-managed",
    }
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zip_file:
        for name, value in contents.items():
            zip_file.writestr(name, value)

    files = [
        {"path": name, "size": len(value), "sha256": hashlib.sha256(value).hexdigest()}
        for name, value in contents.items()
    ]
    inventory = root / "inventory.json"
    inventory.write_text(json.dumps({"files": files}), encoding="utf-8")
    descriptor = {
        "protocol": 2,
        "edition": {
            "id": "standard",
            "displayName": "Padrão",
            "manifestFilename": "manifest-standard.json",
        },
        "revision": "202610180001",
        "expectedCurrentManifestSha256": None,
        "runtime": RUNTIME,
        "archive": {"size": archive.stat().st_size, "sha256": sha256(archive)},
        "inventory": {
            "size": inventory.stat().st_size,
            "sha256": sha256(inventory),
            "fileCount": len(files),
            "totalUncompressedBytes": sum(len(value) for value in contents.values()),
        },
    }
    descriptor_path = root / "promotion.json"
    descriptor_path.write_text(json.dumps(descriptor), encoding="utf-8")
    return descriptor_path, archive, inventory


def run_validator(root, mutate=None):
    descriptor, archive, inventory = write_fixture(root, mutate)
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--descriptor", str(descriptor),
            "--archive", str(archive),
            "--inventory", str(inventory),
            "--repository", "arkandragons/Arkan-Updates",
            "--mode", "validate",
            "--current-manifest", str(root / "manifest-standard.json"),
            "--output", str(root / "generated-manifest.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


class ValidatePackDescriptorContractTests(unittest.TestCase):
    def test_accepts_matching_identity_and_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_validator(pathlib.Path(temp))
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_mismatched_identity_or_runtime(self):
        cases = [
            ("packId", "other"),
            ("edition", "low"),
            ("minecraftVersion", "1.21.1"),
            ("modLoader", "quilt"),
            ("modLoaderVersion", "0.17.0"),
        ]
        for field, value in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                result = run_validator(pathlib.Path(temp), lambda pack: pack.__setitem__(field, value))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"pack descriptor mismatch: {field}", result.stderr)

    def test_rejects_missing_editorial_version(self):
        with tempfile.TemporaryDirectory() as temp:
            result = run_validator(pathlib.Path(temp), lambda pack: pack.__setitem__("version", "   "))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pack descriptor version rejected", result.stderr)


if __name__ == "__main__":
    unittest.main()
