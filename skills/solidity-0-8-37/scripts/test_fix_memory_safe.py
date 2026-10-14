#!/usr/bin/env python3
"""Tests for fix_memory_safe.py (run: python3 scripts/test_fix_memory_safe.py)."""

import importlib.util
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location("fix_memory_safe", Path(__file__).with_name("fix_memory_safe.py"))
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load fix_memory_safe.py next to this test")
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
FixError = _MOD.FixError
convert = _MOD.convert
main = _MOD.main


class ConvertTest(unittest.TestCase):
    def test_plain_block(self):
        src = "    /// @solidity memory-safe-assembly\n    assembly {\n        x := 1\n    }\n"
        out, n = convert(src)
        self.assertEqual(n, 1)
        self.assertEqual(out, '    assembly ("memory-safe") {\n        x := 1\n    }\n')

    def test_star_comment(self):
        out, n = convert('/** @solidity memory-safe-assembly */\nassembly { }\n')
        self.assertEqual((out, n), ('assembly ("memory-safe") { }\n', 1))

    def test_existing_dialect_flag_kept(self):
        out, n = convert('/// @solidity memory-safe-assembly\nassembly ("evmasm") {\n}\n')
        self.assertEqual((out, n), ('assembly ("evmasm", "memory-safe") {\n}\n', 1))

    def test_already_annotated_drops_redundant_comment(self):
        out, n = convert('/// @solidity memory-safe-assembly\nassembly ("memory-safe") {\n}\n')
        self.assertEqual((out, n), ('assembly ("memory-safe") {\n}\n', 1))

    def test_blank_lines_between_kept(self):
        out, n = convert("/// @solidity memory-safe-assembly\n\nassembly {\n}\n")
        self.assertEqual((out, n), ('\nassembly ("memory-safe") {\n}\n', 1))

    def test_untouched_when_absent(self):
        src = "assembly {\n}\n// memory-safe in prose\n"
        self.assertEqual(convert(src), (src, 0))

    def test_not_followed_by_assembly_is_error(self):
        with self.assertRaises(FixError):
            convert("/// @solidity memory-safe-assembly\nuint256 x = 1;\n")

    def test_embedded_in_longer_natspec_is_error(self):
        with self.assertRaises(FixError):
            convert("/// @dev foo @solidity memory-safe-assembly bar\nassembly {\n}\n")

    def test_single_quoted_flag_is_kept(self):
        out, n = convert("/// @solidity memory-safe-assembly\nassembly ('memory-safe') {\n}\n")
        self.assertEqual(n, 1)
        self.assertEqual(out, "assembly ('memory-safe') {\n}\n")

    def test_string_literal_is_not_a_marker(self):
        src = 'string constant S = "@solidity memory-safe-assembly";\n'
        self.assertEqual(convert(src), (src, 0))

    def test_write_stops_before_any_file_when_a_later_file_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            good = root / "a.sol"
            bad = root / "b.sol"
            original = "/// @solidity memory-safe-assembly\nassembly {\n}\n"
            good.write_text(original, encoding="utf-8")
            bad.write_text("/// @dev foo @solidity memory-safe-assembly bar\nassembly {\n}\n", encoding="utf-8")
            self.assertEqual(main(["--write", str(good), str(bad)]), 2)
            self.assertEqual(good.read_text(encoding="utf-8"), original)

    def test_non_sol_path_is_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "a.txt"
            original = "/// @solidity memory-safe-assembly\nassembly {\n}\n"
            path.write_text(original, encoding="utf-8")
            self.assertEqual(main(["--check", str(path)]), 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_multiple_blocks(self):
        src = ("/// @solidity memory-safe-assembly\nassembly { a := 1 }\n"
               "/// @solidity memory-safe-assembly\nassembly { b := 2 }\n")
        out, n = convert(src)
        self.assertEqual(n, 2)
        self.assertNotIn("@solidity", out)


if __name__ == "__main__":
    unittest.main()
