#!/usr/bin/env python3
"""Rewrite the deprecated `/// @solidity memory-safe-assembly` comment to the current `assembly ("memory-safe")` form.

Solidity docs §3.10.5 (0.8.37): "The memory-safe-assembly special comment is deprecated and scheduled for removal";
new code uses the block annotation `assembly ("memory-safe") { ... }`. The two mark the same block and give the same
promise to the compiler, so the conversion is meant to be semantics-neutral. Prove that per project: compile before
and after, and compare the deployed bytecode with the metadata trailer stripped (see SKILL.md).

What it rewrites: a line that is only the special comment (`/// @solidity memory-safe-assembly`, or a
`/** @solidity memory-safe-assembly */` block). It must be followed, after optional blank lines, by an `assembly`
statement:
  - `assembly {`              -> `assembly ("memory-safe") {`
  - `assembly ("dialect") {`  -> `assembly ("dialect", "memory-safe") {`
  - `assembly ("memory-safe") {` is left as is; only the redundant comment line is dropped.

Anything else is a hard error, reported with file:line. Nothing is silently skipped (failing quietly is forbidden):
  - a special comment not followed by an `assembly` statement;
  - the comment embedded in a longer NatSpec block (comment text only; a string literal is ignored).

`--write` converts every file in memory first and writes only after the whole batch converts, so one
failure does not leave earlier files already rewritten. A single-quoted `memory-safe` flag counts as
already annotated. An explicit path that is not `.sol` is an error.

Usage:
  fix_memory_safe.py --check PATH...   exit 1 if any file needs a rewrite (prints file:line); writes nothing
  fix_memory_safe.py --write PATH...   rewrite in place; prints a per-file count and the total
PATH may be a file or a directory (only `*.sol` files are visited).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

COMMENT_LINE = re.compile(r"^(?P<indent>[ \t]*)(?:///\s*@solidity\s+memory-safe-assembly\s*|/\*\*\s*@solidity\s+memory-safe-assembly\s*\*/\s*)$")
ASSEMBLY = re.compile(r"^(?P<indent>[ \t]*)assembly(?P<ws>\s*)(?P<flags>\((?P<inner>[^)]*)\))?(?P<rest>\s*\{.*)$")
EMBEDDED = re.compile(r"@solidity\s+memory-safe-assembly")


class FixError(Exception):
    """A special comment that cannot be converted mechanically (reported, never skipped)."""


def _flag_value(flag: str) -> str:
    flag = flag.strip()
    if len(flag) >= 2 and flag[0] == flag[-1] and flag[0] in "\"'":
        return flag[1:-1]
    return flag


def _marker_in_comment(line: str, in_block: bool) -> tuple[bool, bool]:
    """Whether this line's comments contain the marker, and whether a block comment stays open."""
    i, n = 0, len(line)
    found = False
    while i < n:
        if in_block:
            end = line.find("*/", i)
            chunk = line[i:] if end < 0 else line[i:end]
            if EMBEDDED.search(chunk):
                found = True
            if end < 0:
                return found, True
            in_block = False
            i = end + 2
            continue
        if line.startswith("//", i):
            if EMBEDDED.search(line[i + 2:]):
                found = True
            return found, False
        if line.startswith("/*", i):
            in_block = True
            i += 2
            continue
        if line[i] in "\"'":
            q = line[i]
            i += 1
            while i < n and line[i] != q:
                i += 2 if line[i] == "\\" else 1
            i = min(i + 1, n)
            continue
        i += 1
    return found, in_block


def convert(text: str, path: str = "<string>") -> tuple[str, int]:
    """Return (new_text, rewrites). Raise FixError on any comment that cannot be converted safely."""
    lines = text.split("\n")
    out: list[str] = []
    rewrites = 0
    i = 0
    in_block = False
    while i < len(lines):
        line = lines[i]
        if COMMENT_LINE.match(line):
            in_block = False
            j = i + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            m = ASSEMBLY.match(lines[j]) if j < len(lines) else None
            if m is None:
                raise FixError(f"{path}:{i + 1}: memory-safe-assembly comment not followed by an `assembly` block")
            inner = (m.group("inner") or "").strip()
            flags = [f.strip() for f in inner.split(",") if f.strip()] if inner else []
            if not any(_flag_value(f) == "memory-safe" for f in flags):
                flags.append('"memory-safe"')
            rest = m.group("rest").lstrip()  # always starts with "{"
            new_asm = f'{m.group("indent")}assembly ({", ".join(flags)}) {rest}'
            out.extend(lines[i + 1 : j])  # keep any blank lines between
            out.append(new_asm)
            rewrites += 1
            i = j + 1
            continue
        found, in_block = _marker_in_comment(line, in_block)
        if found:
            raise FixError(f"{path}:{i + 1}: memory-safe-assembly marker inside a longer comment; convert by hand")
        out.append(line)
        i += 1
    return "\n".join(out), rewrites


def iter_sol(paths: list[str]) -> list[Path]:
    """Expand files and directories into a sorted list of `.sol` files."""
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(path.rglob("*.sol")))
        elif path.is_file():
            if path.suffix != ".sol":
                raise FixError(f"{p}: not a .sol file")
            files.append(path)
        else:
            raise FixError(f"{p}: no such file or directory")
    return files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report files needing a rewrite; exit 1 if any")
    mode.add_argument("--write", action="store_true", help="rewrite files in place")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args(argv)
    try:
        files = iter_sol(args.paths)
        planned: list[tuple[Path, str, str, int]] = []
        total = 0
        for f in files:
            text = f.read_text(encoding="utf-8")
            new, n = convert(text, str(f))
            if n == 0:
                continue
            planned.append((f, text, new, n))
            total += n
        # Convert the whole batch before writing, so a later FixError leaves earlier files untouched.
        if args.write:
            for f, _text, new, n in planned:
                f.write_text(new, encoding="utf-8")
                print(f"{f}: {n} rewritten")
        else:
            for f, text, _new, _n in planned:
                for ln, line in enumerate(text.split("\n"), 1):
                    if COMMENT_LINE.match(line):
                        print(f"{f}:{ln}: deprecated memory-safe-assembly comment")
        print(f"fix_memory_safe: {len(planned)} file(s), {total} block(s) {'to rewrite' if args.check else 'rewritten'}")
        return 1 if (args.check and total) else 0
    except FixError as e:
        print(f"fix_memory_safe: ERROR {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
