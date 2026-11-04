#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

SCRIPT_PATH = pathlib.Path(__file__).with_name("verify_public_manifest.py")
SPEC = importlib.util.spec_from_file_location("verify_public_manifest", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class VerifyPublicManifestTests(unittest.TestCase):
    def test_uses_the_explicit_manifest_path_filename(self):
        manifest_path = pathlib.Path("nested") / "manifest-low-end.json"
        self.assertEqual(
            MODULE.public_manifest_url(manifest_path),
            "https://raw.githubusercontent.com/arkandragons/Arkan-Updates/main/manifest-low-end.json",
        )

    def test_rejects_a_path_without_a_filename(self):
        with self.assertRaises(ValueError):
            MODULE.public_manifest_url(pathlib.Path("."))


if __name__ == "__main__":
    unittest.main()
