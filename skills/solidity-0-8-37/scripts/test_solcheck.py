#!/usr/bin/env python3
"""Regression tests for solcheck.py. Run: python3 scripts/test_solcheck.py

Pins the two AST-backend defects found during development so they cannot silently return:
  1. solc (--stop-after parsing) attaches no `documentation` node to state variables, so documented
     public state variables were reported as undocumented (NATSPEC006 false positives).
  2. solc fills in `public` for a function declared without visibility, so the omission (VIS001) was missed.
Also asserts the AST and regex backends agree finding-for-finding on the fixtures, including file-level
errors, nested parameter lists, captured versus unchecked calls, `now` as an identifier, and `__gap`.
"""
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECK = HERE / "solcheck.py"
FIX = HERE / "fixtures"


def run(path: Path, *args: str) -> tuple[int, list[str], str]:
    p = subprocess.run([sys.executable, str(CHECK), str(path), *args], capture_output=True, text=True)
    lines = [re.sub(r"^.*?\.sol", "", l) for l in p.stdout.splitlines() if "[" in l and "]" in l]
    summary = next((l for l in p.stdout.splitlines() if l.startswith("solcheck:")), "")
    return p.returncode, sorted(lines), summary


def codes(lines: list[str]) -> list[str]:
    return [re.search(r"\[(\w+)\]", l).group(1) for l in lines]


failures = []


def expect(cond: bool, msg: str) -> None:
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


have_solc = shutil.which("solc") is not None
backends = ["regex"] + (["ast"] if have_solc else [])
if not have_solc:
    print("NOTE solc not found: AST-backend assertions skipped (not verified)")

for b in backends:
    rc, lines, summary = run(FIX / "Escrow.sol", "--profile", "repo", "--backend", b)
    expect(rc == 0 and not lines, f"[{b}] Escrow.sol is clean under the repo profile ({summary})")
    expect("NATSPEC006" not in codes(lines), f"[{b}] documented public state variables are not flagged")

    rc, lines, summary = run(FIX / "Vault.sol", "--profile", "repo", "--backend", b)
    expect(rc == 0 and not lines, f"[{b}] Vault.sol is clean under the repo profile ({summary})")

    rc, lines, _ = run(FIX / "Bad.sol", "--backend", b)
    c = codes(lines)
    expect(rc == 1, f"[{b}] Bad.sol fails")
    expect(any(l.startswith(":5:") and "[VIS001]" in l for l in lines), f"[{b}] missing visibility on line 5 is reported")
    for code in ("SPDX001", "DEPR001", "DEPR002", "DEPR004", "DEPR005", "ERR004", "CALL001", "NAME001", "NAME003"):
        expect(code in c, f"[{b}] Bad.sol reports {code}")

if have_solc:
    _, ast_lines, _ = run(FIX / "Bad.sol", "--backend", "ast")
    _, rx_lines, _ = run(FIX / "Bad.sol", "--backend", "regex")
    expect(ast_lines == rx_lines, "AST and regex backends agree finding-for-finding on Bad.sol")
    _, ast_lines, _ = run(FIX / "Agree.sol", "--backend", "ast")
    _, rx_lines, _ = run(FIX / "Agree.sol", "--backend", "regex")
    expect(ast_lines == rx_lines, "AST and regex backends agree finding-for-finding on Agree.sol")

spec = importlib.util.spec_from_file_location("solcheck", CHECK)
mod = importlib.util.module_from_spec(spec)
sys.modules["solcheck"] = mod
spec.loader.exec_module(mod)
expect(
    mod.param_names("function set(mapping(address => uint256) storage m, uint256 amount)") == ["m", "amount"],
    "nested mapping parameters keep both names",
)
expect(
    mod.param_names("function take(function(uint256) external cb)") == ["cb"],
    "function-type parameters keep the callback name",
)

agree = (FIX / "Agree.sol").read_text(encoding="utf-8").splitlines()
unchecked_line = next(i for i, line in enumerate(agree, 1) if "to.call{value: x}" in line)
captured_line = next(i for i, line in enumerate(agree, 1) if "to.call{value: 1}" in line)
for b in backends:
    rc, lines, _ = run(FIX / "Agree.sol", "--backend", b)
    c = codes(lines)
    expect(rc == 1, f"[{b}] Agree.sol fails")
    expect(any("zero_amount" in line and "[NAME001]" in line for line in lines), f"[{b}] file-level error name is checked")
    expect(any("zero_amount" in line and "[NATSPEC002]" in line for line in lines), f"[{b}] file-level error parameters need @param")
    expect("DEPR003" not in c, f"[{b}] a note that mentions memory-safe-assembly is not the deprecated comment")
    expect("DEPR006" not in c, f"[{b}] identifier now is not the removed keyword")
    expect("NAME005" not in c, f"[{b}] __gap is an allowed state name")
    expect(any(line.startswith(f":{unchecked_line}:") and "[CALL001]" in line for line in lines), f"[{b}] unchecked call is CALL001")
    expect(not any(line.startswith(f":{captured_line}:") and "[CALL001]" in line for line in lines), f"[{b}] (ok,) = call is captured")
    expect(any("[NATSPEC002]" in line and "`take`" in line for line in lines), f"[{b}] callback parameter is named cb")

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    long_line = "    // " + ("x" * 120)
    src = (
        "// SPDX-License-Identifier: MIT\n"
        "pragma solidity 0.8.37;\n"
        "/// @title T\n"
        "/// @notice t\n"
        "contract T {\n"
        "    /// @notice f\n"
        "    function f() external {}\n"
        f"{long_line}\n"
        "}\n"
    )
    path = root / "T.sol"
    path.write_text(src, encoding="utf-8")
    rc, lines, summary = run(path, "--backend", "regex")
    expect(rc == 0 and codes(lines) == ["LINE001"], f"generic profile allows a line-length warning ({summary})")
    expect("warnings=allowed" in summary, "generic summary says warnings are allowed")
    rc, lines, summary = run(path, "--profile", "repo", "--backend", "regex")
    expect(rc == 1 and codes(lines) == ["LINE001"], f"repo profile fails on a warning ({summary})")
    expect("warnings=fail" in summary, "repo summary says warnings fail")

    upper = root / "Upper.sol"
    upper.write_text(
        "// SPDX-License-Identifier: MIT\n"
        "pragma solidity 0.8.37;\n"
        "/// @title Upper\n"
        "/// @notice t\n"
        "contract Upper {\n"
        "    uint256 TOTAL;\n"
        "    /// @notice f\n"
        "    function f() external {}\n"
        "}\n",
        encoding="utf-8",
    )
    _, lines, _ = run(upper, "--backend", "regex")
    expect("NAME005" in codes(lines), "non-constant UPPER_CASE state is NAME005")

    proj = root / "proj"
    proj.mkdir()
    lib = proj / "lib"
    lib.mkdir()
    (lib / "Foo.sol").write_text("contract Foo { function f() {} }\n", encoding="utf-8")
    (proj / "Bar.sol").write_text(
        "// SPDX-License-Identifier: MIT\n"
        "pragma solidity 0.8.37;\n"
        "/// @title Bar\n"
        "/// @notice t\n"
        "contract Bar {\n"
        "    /// @notice f\n"
        "    function f() external {}\n"
        "}\n",
        encoding="utf-8",
    )
    rc, lines, summary = run(proj, "--backend", "regex")
    expect(rc == 0 and not lines and "1 file" in summary, f"directory walk skips lib/ ({summary})")
    rc, lines, _ = run(lib / "Foo.sol", "--backend", "regex")
    expect(rc == 1, "an explicit lib file is still checked")

# Repo-profile pragma rule: the exact pin or a 0.8.34-0.8.37 floor capped below 0.9.0 passes; anything else fails.
escrow = (FIX / "Escrow.sol").read_text(encoding="utf-8")
with tempfile.TemporaryDirectory() as td:
    for pragma, ok in [
        ("pragma solidity >=0.8.34 <0.9.0;", True),
        ("pragma solidity >=0.8.37 <0.9.0;", True),
        ("pragma solidity ^0.8.37;", False),
        ("pragma solidity >=0.8.33 <0.9.0;", False),
        ("pragma solidity >=0.8.34;", False),
    ]:
        f = Path(td) / "Escrow.sol"
        f.write_text(escrow.replace("pragma solidity 0.8.37;", pragma, 1), encoding="utf-8")
        rc, lines, _ = run(f, "--profile", "repo", "--backend", "regex")
        flagged = "PRAGMA002" in codes(lines)
        expect(flagged != ok, f"repo profile {'accepts' if ok else 'rejects'} `{pragma}`")

print(f"\n{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
