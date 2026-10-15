#!/usr/bin/env python3
"""solcheck — rule checker for Solidity 0.8.37 sources (stdlib only).

Enforces the official Style Guide (layout order, function order, naming, line length, indentation),
NatSpec coverage of the ABI, deprecated 0.8.37 constructs and failure-safety smells.

Two front-ends feed one rule engine:
  * AST   — `solc --ast-compact-json --stop-after parsing` when a solc binary is available (default). Structure,
            names, visibility, mutability, parameters and NatSpec come from the compiler's own parse tree.
  * regex — brace-walking fallback when no solc is found or parsing fails (e.g. unresolved imports). Weaker;
            the report says which backend ran.
Textual checks (line length, tabs, TODOs, deprecated calls, bare reverts, empty catch, unchecked low-level
calls) are regex-based in both modes because they are about source text, not structure.

File-level events and errors are members of the file, not only order tokens: CapWords and NatSpec apply.
`now` is a legal identifier in 0.8 and is not flagged; the compiler reports an undeclared `now`.
`__gap` (the upgrade-gap slot) is an allowed non-constant state name.

Usage:
    python3 solcheck.py FILE_OR_DIR [...] [--profile repo] [--backend auto|ast|regex] [--max-line 120]
                        [--base-path DIR] [--remappings FILE] [--quiet]

Exit status: 0 = clean, 1 = at least one error (repo profile: a warning fails too), 2 = usage problem.
The summary says `warnings=allowed` or `warnings=fail`.

`--profile repo` escalates string-reason requires / bare reverts / non-exact pragma / assert-as-validation to
errors, and warnings fail the exit. `@uniswap/v4-core` imports are allowed.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

CAPWORDS = re.compile(r"^[A-Z][A-Za-z0-9]*$")
MIXED = re.compile(r"^_?[a-z][A-Za-z0-9]*_?$")
# Non-constant state: mixedCase, optional single trailing underscore, up to two leading underscores
# so the upgrade slot `__gap` is not NAME005. UPPER_CASE is reserved for constants.
STATE_NAME = re.compile(r"^_{0,2}[a-z][A-Za-z0-9]*_?$")
UPPER = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
VISIBILITIES = ("external", "public", "internal", "private")
VIS_RANK = {"constructor": 0, "receive": 1, "fallback": 2, "external": 3, "public": 4, "internal": 5, "private": 6}
MUT_RANK = {"": 0, "nonpayable": 0, "payable": 0, "view": 1, "pure": 2}
FILE_ORDER = {"pragma": 0, "import": 1, "event": 2, "error": 3, "interface": 4, "library": 5, "contract": 6}
FILE_ORDER_NAMES = ["pragmas", "imports", "events", "errors", "interfaces", "libraries", "contracts"]
MEMBER_ORDER = {"type": 0, "state": 1, "event": 2, "error": 3, "modifier": 4, "function": 5}
MEMBER_ORDER_NAMES = ["type declarations", "state variables", "events", "errors", "modifiers", "functions"]
AVOID_NAMES = ("l", "O", "I")


@dataclass
class Finding:
    path: str
    line: int
    code: str
    level: str  # error | warning | info
    msg: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: [{self.code}] {self.level}: {self.msg}"


@dataclass
class Member:
    kind: str                     # type | state | event | error | modifier | function | using
    name: str
    line: int
    vis: str = ""
    mut: str = ""
    params: list[str] = field(default_factory=list)
    returns: int = 0
    is_constant: bool = False
    is_public_state: bool = False
    is_virtual: bool = False
    doc: list[str] = field(default_factory=list)   # NatSpec lines, tags intact


@dataclass
class Unit:
    kind: str          # contract | interface | library
    name: str
    line: int
    doc: list[str]
    members: list[Member]


@dataclass
class Model:
    top_order: list[tuple[str, int]]   # (kind, line) for file-level declarations
    units: list[Unit]
    backend: str
    file_members: list[Member] = field(default_factory=list)  # file-level events and errors


# ----------------------------------------------------------------------------------------------- helpers

def mask(src: str) -> str:
    """Blank out comment bodies and string contents (preserve newlines and length)."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if src.startswith("//", i):
            j = src.find("\n", i); j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2); j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j])); i = j
        elif c in "\"'":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            j = min(j + 1, n)
            out.append(c + " " * (j - i - 2) + c if j - i >= 2 else src[i:j]); i = j
        else:
            out.append(c); i += 1
    return "".join(out)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def natspec_lines(doc_text: str) -> list[str]:
    return [l.strip().lstrip("*").strip() for l in doc_text.split("\n") if l.strip().lstrip("*").strip()]


_LOCATION_WORDS = {
    "indexed", "memory", "calldata", "storage", "payable", "constant",
    "external", "public", "internal", "private", "pure", "view",
}
_TYPE_INTRODUCERS = {"function", "mapping"}


def first_paren_group(s: str) -> str | None:
    """Interior of the first parenthesis group, respecting nesting. None if unbalanced or absent."""
    start = s.find("(")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "(":
            depth += 1
        elif s[i] == ")":
            depth -= 1
            if depth == 0:
                return s[start + 1:i]
    return None


def split_top_level(s: str, sep: str = ",") -> list[str]:
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in s:
        if ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf)
    if parts or tail.strip():
        parts.append(tail)
    return parts


def param_name(raw: str) -> str:
    """Parameter name, or "" when the parameter is unnamed (`uint256`, `address`)."""
    stripped = raw
    while True:
        nxt = re.sub(r"\([^()]*\)", " ", stripped)
        if nxt == stripped:
            break
        stripped = nxt
    toks = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", stripped)
    had_introducer = any(t in _TYPE_INTRODUCERS for t in toks)
    kept = [t for t in toks if t not in _LOCATION_WORDS and t not in _TYPE_INTRODUCERS]
    if len(kept) >= 2:
        return kept[-1]
    if len(kept) == 1 and had_introducer:
        return kept[0]
    return ""


def param_names(head: str) -> list[str]:
    """Names in the first parameter list of a function, event, error, or modifier header."""
    inner = first_paren_group(head)
    if inner is None:
        return []
    return [name for name in (param_name(p) for p in split_top_level(inner)) if name]


def returns_count(head: str) -> int:
    m = re.search(r"\breturns\s*\(", head)
    if not m:
        return 0
    inner = first_paren_group(head[m.start():])
    if inner is None:
        return 0
    return len([p for p in split_top_level(inner) if p.strip()])


def mapping_key_names_src(decl: str) -> list[str]:
    """Named mapping keys (`mapping(address account => ...)`) in a state-variable declaration."""
    keys: list[str] = []
    for m in re.finditer(r"\bmapping\s*\(", decl):
        inner = first_paren_group(decl[m.start():])
        if inner is None:
            continue
        depth = 0
        idx = None
        i = 0
        while i < len(inner):
            ch = inner[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            elif depth == 0 and inner.startswith("=>", i):
                idx = i
                break
            i += 1
        if idx is None:
            continue
        left = inner[:idx]
        while True:
            nxt = re.sub(r"\([^()]*\)", " ", left)
            if nxt == left:
                break
            left = nxt
        toks = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", left) if t not in _LOCATION_WORDS]
        if len(toks) >= 2:
            keys.append(toks[-1])
    return keys


def mapping_key_names_ast(type_name) -> list[str]:
    if not isinstance(type_name, dict):
        return []
    nt = type_name.get("nodeType")
    if nt == "Mapping":
        keys: list[str] = []
        if type_name.get("keyName"):
            keys.append(type_name["keyName"])
        keys.extend(mapping_key_names_ast(type_name.get("valueType")))
        return keys
    if nt == "ArrayTypeName":
        return mapping_key_names_ast(type_name.get("baseType"))
    return []


# ----------------------------------------------------------------------------------------------- AST backend

def ast_model(path: Path, base_path: str | None, remappings: list[str]) -> Model | None:
    solc = shutil.which("solc")
    if not solc:
        return None
    cmd = [solc, "--ast-compact-json", "--stop-after", "parsing", str(path)]
    if base_path:
        cmd += ["--base-path", base_path, "--allow-paths", base_path]
    cmd += remappings
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if res.returncode != 0:
        return None
    m = re.search(r"=======\s*" + re.escape(str(path)) + r"\s*=======\n(\{.*?)(?=\n=======|\Z)", res.stdout, re.S)
    if not m:
        m = re.search(r"=======.*?=======\n(\{.*?)(?=\n=======|\Z)", res.stdout, re.S)
    if not m:
        return None
    try:
        ast = json.loads(m.group(1))
    except json.JSONDecodeError:
        return None
    raw = path.read_bytes()

    def ln(node) -> int:
        start = int(node["src"].split(":")[0])
        return raw[:start].count(b"\n") + 1

    def doc_of(node) -> list[str]:
        d = node.get("documentation")
        if isinstance(d, dict):
            return natspec_lines(d.get("text", ""))
        if isinstance(d, str):
            return natspec_lines(d)
        return []

    src_lines = raw.decode("utf-8", "replace").split("\n")

    def doc_above(line: int) -> list[str]:
        """NatSpec read from the source above `line`.

        solc does not attach a `documentation` node to state-variable declarations at
        --stop-after parsing (it does for contracts, functions, events, errors), so the AST
        alone cannot tell a documented public state variable from an undocumented one.
        """
        return natspec_above(src_lines, line)

    def explicit_visibility(node, kind: str) -> str:
        """Visibility as written in the source header, or "" if omitted.

        At --stop-after parsing solc fills in `public` for a function declared without a
        visibility specifier (a compile error in 0.8.x), so the AST value cannot reveal the
        omission. Read the header text between the node start and its body instead.
        """
        if kind in ("constructor", "receive", "fallback"):
            return node.get("visibility") or ""
        start, length = (int(x) for x in node["src"].split(":")[:2])
        header = mask(raw[start:start + length].decode("utf-8", "replace")).split("{", 1)[0]
        return next((v for v in VISIBILITIES if re.search(rf"\b{v}\b", header)), "")

    def params_of(node, key="parameters") -> list[str]:
        pl = node.get(key) or {}
        return [p.get("name", "") for p in pl.get("parameters", [])]

    def file_abi(node, kind: str) -> Member:
        line = ln(node)
        return Member(kind, node.get("name", ""), line, params=params_of(node), doc=doc_of(node) or doc_above(line))

    top: list[tuple[str, int]] = []
    units: list[Unit] = []
    file_members: list[Member] = []
    for node in ast.get("nodes", []):
        t = node.get("nodeType")
        if t == "PragmaDirective":
            top.append(("pragma", ln(node)))
        elif t == "ImportDirective":
            top.append(("import", ln(node)))
        elif t == "EventDefinition":
            top.append(("event", ln(node)))
            file_members.append(file_abi(node, "event"))
        elif t == "ErrorDefinition":
            top.append(("error", ln(node)))
            file_members.append(file_abi(node, "error"))
        elif t == "ContractDefinition":
            ck = node.get("contractKind", "contract")
            top.append((ck, ln(node)))
            members: list[Member] = []
            for sub in node.get("nodes", []):
                st = sub.get("nodeType")
                if st in ("StructDefinition", "EnumDefinition", "UserDefinedValueTypeDefinition"):
                    members.append(Member("type", sub.get("name", ""), ln(sub)))
                elif st == "UsingForDirective":
                    members.append(Member("using", "", ln(sub)))
                elif st == "VariableDeclaration":
                    public = sub.get("visibility") == "public"
                    members.append(Member("state", sub.get("name", ""), ln(sub),
                                          vis=sub.get("visibility", ""),
                                          params=mapping_key_names_ast(sub.get("typeName")) if public else [],
                                          returns=1 if public else 0,
                                          is_constant=sub.get("mutability") == "constant" or sub.get("constant", False),
                                          is_public_state=public,
                                          doc=doc_of(sub) or doc_above(ln(sub))))
                elif st == "EventDefinition":
                    members.append(Member("event", sub.get("name", ""), ln(sub), params=params_of(sub), doc=doc_of(sub)))
                elif st == "ErrorDefinition":
                    members.append(Member("error", sub.get("name", ""), ln(sub), params=params_of(sub), doc=doc_of(sub)))
                elif st == "ModifierDefinition":
                    members.append(Member("modifier", sub.get("name", ""), ln(sub), params=params_of(sub),
                                          is_virtual=bool(sub.get("virtual")), doc=doc_of(sub)))
                elif st == "FunctionDefinition":
                    kind = sub.get("kind", "function")
                    name = sub.get("name") or kind
                    if kind in ("constructor", "receive", "fallback"):
                        name = kind
                    members.append(Member("function", name, ln(sub),
                                          vis=explicit_visibility(sub, kind),
                                          mut=sub.get("stateMutability", ""),
                                          params=params_of(sub),
                                          returns=len(params_of(sub, "returnParameters")),
                                          is_virtual=bool(sub.get("virtual")),
                                          doc=doc_of(sub)))
            units.append(Unit(ck, node.get("name", ""), ln(node), doc_of(node), members))
    return Model(top, units, "ast", file_members)


# ----------------------------------------------------------------------------------------------- regex backend

def natspec_above(lines: list[str], line: int) -> list[str]:
    """NatSpec comment lines immediately above 1-based source `line` (/// or /** */)."""
    i, out = line - 2, []
    while i >= 0:
        l = lines[i].strip()
        if l.startswith("///"):
            out.append(l[3:].strip()); i -= 1; continue
        if l.endswith("*/"):
            block = []
            while i >= 0:
                t = lines[i].strip()
                block.append(t.lstrip("/*").rstrip("*/").strip().lstrip("*").strip())
                if t.startswith("/*"):
                    break
                i -= 1
            if i < 0 or not lines[i].strip().startswith("/**"):
                return [x for x in reversed(out) if x]
            out.extend(block); i -= 1; continue
        break
    return [x for x in reversed(out) if x]


def regex_model(src: str, lines: list[str]) -> Model:
    text = mask(src)
    n = len(text)

    def natspec_before(line: int) -> list[str]:
        return natspec_above(lines, line)

    def classify(chunk: str, pos: int) -> Member | None:
        s = chunk.strip(); line = line_of(text, pos); head = s.split("{", 1)[0]
        kw = re.match(r"^(struct|enum|type|using|event|error|modifier|function|constructor|receive|fallback)\b", s)
        k = kw.group(1) if kw else ""
        if k in ("struct", "enum", "type"):
            return Member("type", re.match(rf"^{k}\s+(\w+)", s).group(1), line)
        if k == "using":
            return Member("using", "", line)
        if k in ("event", "error"):
            return Member(k, re.match(rf"^{k}\s+(\w+)", s).group(1), line, params=param_names(head), doc=natspec_before(line))
        if k == "modifier":
            return Member("modifier", re.match(r"^modifier\s+(\w+)", s).group(1), line, params=param_names(head),
                          is_virtual=bool(re.search(r"\bvirtual\b", head)), doc=natspec_before(line))
        if k in ("function", "constructor", "receive", "fallback"):
            if k == "function":
                nm = re.match(r"^function\s+(\w+)", s); name = nm.group(1) if nm else ""
            else:
                name = k
            vis = next((v for v in VISIBILITIES if re.search(rf"\b{v}\b", head)), "")
            mut = next((m for m in ("pure", "view", "payable") if re.search(rf"\b{m}\b", head)), "")
            return Member("function", name, line, vis=vis, mut=mut, params=param_names(head), returns=returns_count(head),
                          is_virtual=bool(re.search(r"\bvirtual\b", head)), doc=natspec_before(line))
        if s.endswith(";"):
            decl = re.sub(r"(?<![=!<>])=(?![>=]).*$", "", s[:-1], flags=re.S).strip()
            while True:
                nxt = re.sub(r"\([^()]*\)", " ", decl)
                if nxt == decl:
                    break
                decl = nxt
            toks = decl.split()
            if toks:
                public = " public " in f" {decl} "
                return Member("state", toks[-1], line, vis=next((v for v in VISIBILITIES if f" {v} " in f" {decl} "), ""),
                              params=mapping_key_names_src(s) if public else [],
                              returns=1 if public else 0,
                              is_constant=" constant " in f" {decl} ", is_public_state=public,
                              doc=natspec_before(line))
        return None

    def split_members(body: str, base: int) -> list[Member]:
        members, i, m = [], 0, len(body)
        while i < m:
            while i < m and body[i].isspace():
                i += 1
            if i >= m:
                break
            start, depth = i, 0
            while i < m:
                ch = body[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1; break
                elif ch == ";" and depth == 0:
                    i += 1; break
                i += 1
            mem = classify(body[start:i], base + start)
            if mem:
                members.append(mem)
        return members

    top: list[tuple[str, int]] = []
    depth, i = 0, 0
    while i < n:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        elif depth == 0 and (i == 0 or text[i - 1] in "\n;}") and ch.isalpha():
            mm = re.match(r"(abstract\s+contract|contract|interface|library|pragma|import|event|error)\b", text[i:])
            if mm:
                top.append((mm.group(1).replace("abstract ", "").split()[0], line_of(text, i)))
        i += 1

    units: list[Unit] = []
    for cm in re.finditer(r"\b(abstract\s+contract|contract|interface|library)\s+(\w+)([^{;]*)\{", text):
        ck = cm.group(1).replace("abstract ", "").strip()
        cline = line_of(text, cm.start())
        d, j = 1, cm.end()
        while j < n and d:
            d += {"{": 1, "}": -1}.get(text[j], 0); j += 1
        units.append(Unit(ck, cm.group(2), cline, natspec_before(cline), split_members(text[cm.end():j - 1], cm.end())))

    file_members: list[Member] = []
    depth, i = 0, 0
    while i < n:
        ch = text[i]
        if ch == "{":
            depth += 1
            i += 1
            continue
        if ch == "}":
            depth = max(0, depth - 1)
            i += 1
            continue
        if depth == 0 and (i == 0 or text[i - 1] in "\n;}"):
            mm = re.match(r"(event|error)\b", text[i:])
            if mm:
                kind = mm.group(1)
                j = i
                pdepth = 0
                while j < n:
                    if text[j] == "(":
                        pdepth += 1
                    elif text[j] == ")":
                        pdepth -= 1
                    elif text[j] == ";" and pdepth <= 0:
                        j += 1
                        break
                    elif text[j] == "{" and pdepth <= 0:
                        break
                    j += 1
                chunk = text[i:j]
                nm = re.match(rf"{kind}\s+(\w+)", chunk)
                if nm:
                    line = line_of(text, i)
                    file_members.append(Member(kind, nm.group(1), line, params=param_names(chunk), doc=natspec_above(lines, line)))
                i = j
                continue
        i += 1
    return Model(top, units, "regex", file_members)


# ----------------------------------------------------------------------------------------------- rule engine

def has_notice(doc: list[str]) -> bool:
    # A tagless NatSpec line is @notice (docs §3.30).
    return any(d.startswith("@notice") or (d and not d.startswith("@")) for d in doc)


def check_param_names(mem: Member, add) -> None:
    for prm in mem.params:
        if prm and not MIXED.match(prm):
            add(mem.line, "NAME002", "warning", f"parameter `{prm}` of `{mem.name}` should be mixedCase")
        if prm in AVOID_NAMES:
            add(mem.line, "NAME006", "error", f"parameter `{prm}` is a name to avoid (style guide §3.34.4)")


def check_abi_natspec(mem: Member, add, *, require_returns: bool) -> None:
    """@notice, one @param per named parameter, one @return per return. Missing tags are errors."""
    label = mem.name or mem.kind
    if mem.kind == "state":
        missing_code = "NATSPEC006"
    elif mem.kind in ("event", "error"):
        missing_code = "NATSPEC005"
    else:
        missing_code = "NATSPEC001"
    if not mem.doc:
        add(mem.line, missing_code, "error", f"`{label}` is in the ABI but has no NatSpec (docs §3.30, style guide §3.34.5)")
        return
    if any(d.startswith("@inheritdoc") for d in mem.doc):
        return
    if not has_notice(mem.doc):
        add(mem.line, "NATSPEC001", "error", f"`{label}` lacks `@notice`")
    documented = {m.group(1) for d in mem.doc if (m := re.match(r"@param\s+(\w+)", d))}
    for prm in mem.params:
        if prm and prm not in documented:
            add(mem.line, "NATSPEC002", "error", f"`{label}` is missing `@param {prm}`")
    if require_returns and mem.returns:
        nret = sum(1 for d in mem.doc if d.startswith("@return"))
        if nret < mem.returns:
            add(mem.line, "NATSPEC003", "error", f"`{label}` returns {mem.returns} value(s) but has {nret} `@return` line(s)")


def structural_checks(model: Model, path: Path, add) -> None:
    last_rank, last_kind = -1, ""
    for k, line in model.top_order:
        r = FILE_ORDER.get(k)
        if r is None:
            continue
        if r < last_rank:
            add(line, "ORDER001", "warning",
                f"file-level `{k}` appears after {last_kind}; expected: {', '.join(FILE_ORDER_NAMES)} (style guide §3.34.3)")
        if r >= last_rank:
            last_rank, last_kind = r, k

    for mem in model.file_members:
        if mem.kind in ("type", "event", "error") and not CAPWORDS.match(mem.name):
            add(mem.line, "NAME001", "error", f"{mem.kind} `{mem.name}` should be CapWords (style guide §3.34.4)")
        check_param_names(mem, add)
        check_abi_natspec(mem, add, require_returns=False)

    core_name_matched = False
    for u in model.units:
        if not CAPWORDS.match(u.name):
            add(u.line, "NAME001", "error", f"{u.kind} `{u.name}` should be CapWords (style guide §3.34.4)")
        if u.name == path.stem:
            core_name_matched = True
        if not any(d.startswith(("@title", "@notice")) or (d and not d.startswith("@")) for d in u.doc):
            add(u.line, "NATSPEC004", "warning", f"{u.kind} `{u.name}` has no NatSpec `@title`/`@notice` (docs §3.30)")

        last_r, last_fn = -1, (-1, -1)
        for mem in u.members:
            if mem.kind == "using":
                continue
            r = MEMBER_ORDER[mem.kind]
            if r < last_r:
                add(mem.line, "ORDER002", "warning",
                    f"`{mem.name or mem.kind}` ({MEMBER_ORDER_NAMES[r]}) declared after {MEMBER_ORDER_NAMES[last_r]}; "
                    f"expected: {' → '.join(MEMBER_ORDER_NAMES)} (style guide §3.34.3)")
            last_r = max(last_r, r)

            if mem.kind in ("type", "event", "error") and not CAPWORDS.match(mem.name):
                add(mem.line, "NAME001", "error", f"{mem.kind} `{mem.name}` should be CapWords (style guide §3.34.4)")
            if mem.kind == "modifier":
                if not MIXED.match(mem.name):
                    add(mem.line, "NAME004", "error", f"modifier `{mem.name}` should be mixedCase (style guide §3.34.4)")
                if mem.is_virtual:
                    add(mem.line, "DEPR004", "error", "`virtual` modifiers are deprecated and scheduled for removal (docs §3.9.11)")
            if mem.kind == "state":
                if mem.is_constant:
                    if not UPPER.match(mem.name):
                        add(mem.line, "NAME003", "error", f"constant `{mem.name}` should be UPPER_CASE_WITH_UNDERSCORES (style guide §3.34.4)")
                elif not STATE_NAME.match(mem.name):
                    add(mem.line, "NAME005", "error", f"state variable `{mem.name}` should be mixedCase (style guide §3.34.4)")
                if mem.name in AVOID_NAMES:
                    add(mem.line, "NAME006", "error", f"`{mem.name}` is a name to avoid (style guide §3.34.4)")
                if mem.is_public_state:
                    check_param_names(mem, add)
                    check_abi_natspec(mem, add, require_returns=True)
            if mem.kind in ("event", "error"):
                check_param_names(mem, add)
                check_abi_natspec(mem, add, require_returns=False)
            if mem.kind == "function":
                special = mem.name in ("constructor", "receive", "fallback")
                if not special:
                    if not MIXED.match(mem.name):
                        add(mem.line, "NAME002", "error", f"function `{mem.name}` should be mixedCase (style guide §3.34.4)")
                    if u.kind != "interface" and not mem.vis:
                        add(mem.line, "VIS001", "error", f"function `{mem.name}` has no visibility specifier (docs §3.9.2)")
                    if u.kind == "interface" and mem.vis and mem.vis != "external":
                        add(mem.line, "IFACE001", "error", f"interface function `{mem.name}` must be `external` (docs §3.9.13)")
                check_param_names(mem, add)
                key = mem.name if special else mem.vis
                fr = (VIS_RANK.get(key, 99), MUT_RANK.get(mem.mut, 0) if key in VISIBILITIES else 0)
                if fr < last_fn:
                    add(mem.line, "ORDER003", "warning",
                        f"function `{mem.name}` ({key}{' ' + mem.mut if mem.mut and mem.mut != 'nonpayable' else ''}) is out of order; "
                        "expected constructor, receive, fallback, external, public, internal, private with view/pure last in each group (style guide §3.34.2)")
                last_fn = max(last_fn, fr)
                if (mem.vis in ("external", "public") or special) and mem.name not in ("receive", "fallback"):
                    check_abi_natspec(mem, add, require_returns=True)
    if model.units and not core_name_matched:
        add(1, "NAME007", "warning", f"no contract/library/interface named `{path.stem}` matches the file name (style guide §3.34.4)")


def _call_sites(stmt: str) -> list[int]:
    """Indexes of `.call` / `.delegatecall` / `.staticcall` invocations in one statement."""
    sites = []
    for m in re.finditer(r"\.(call|delegatecall|staticcall)\b", stmt):
        j = m.end()
        while j < len(stmt) and stmt[j].isspace():
            j += 1
        if j < len(stmt) and stmt[j] == "{":
            depth = 0
            while j < len(stmt):
                if stmt[j] == "{":
                    depth += 1
                elif stmt[j] == "}":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            while j < len(stmt) and stmt[j].isspace():
                j += 1
        if j < len(stmt) and stmt[j] == "(":
            sites.append(m.start())
    return sites


def _statement_captures_call(stmt: str, call_at: int) -> bool:
    """True when this statement binds the low-level call's success flag or returns/requires it."""
    before = stmt[:call_at]
    if "=" in before or re.search(r"\(\s*bool\b", stmt):
        return True
    if re.search(r"\brequire\s*\(", stmt) or re.search(r"\breturn\b", stmt):
        return True
    return False


def _iter_statements(masked_src: str):
    buf: list[str] = []
    depth = 0
    line = 1
    start = 1
    for ch in masked_src:
        buf.append(ch)
        if ch == "\n":
            line += 1
        # Brace depth does not hide semicolons: a function body is many statements.
        # Parentheses do: `for (uint i = 0; i < n; ++i)`.
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch == ";" and depth == 0:
            yield start, "".join(buf)
            buf = []
            start = line


def _header_until_brace(masked_src: str, start: int) -> str:
    depth = 0
    i = start
    while i < len(masked_src):
        ch = masked_src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "{" and depth == 0:
            return masked_src[start:i]
        i += 1
    return masked_src[start:]


def _scan_revert_require(masked_src: str, sev: str, add) -> None:
    for m in re.finditer(r"\b(require|revert)\s*\(", masked_src):
        kind = m.group(1)
        i = m.end()
        depth = 1
        buf: list[str] = []
        args: list[str] = []
        while i < len(masked_src) and depth:
            ch = masked_src[i]
            if ch == "(":
                depth += 1
                buf.append(ch)
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    args.append("".join(buf))
                    break
                buf.append(ch)
            elif ch == "," and depth == 1:
                args.append("".join(buf))
                buf = []
            else:
                buf.append(ch)
            i += 1
        if depth != 0:
            continue
        line = masked_src.count("\n", 0, m.start()) + 1
        stripped = [a.strip() for a in args]
        if kind == "revert" and (not stripped or stripped == [""]):
            add(line, "ERR001", sev, "bare `revert()` gives no reason; use a named custom error (docs §3.8.8)")
        elif kind == "revert" and stripped and stripped[0].startswith('"'):
            add(line, "ERR001", sev, '`revert("string")`; prefer `revert CustomError(...)` (cheaper, ABI-decodable)')
        elif kind == "require" and len(stripped) >= 2 and stripped[1].startswith('"'):
            add(line, "ERR002", sev, '`require(cond, "string")`; prefer `require(cond, CustomError(...))` (docs §3.8.8)')
        elif kind == "require" and len([a for a in stripped if a]) <= 1:
            add(line, "ERR006", sev, "`require(cond)` with no reason reverts with empty data; use `require(cond, CustomError(...))` (docs §3.8.8)")


def textual_checks(src: str, lines: list[str], profile: str, max_line: int, add) -> None:
    masked_src = mask(src)
    masked = masked_src.split("\n")
    first = next((i for i, l in enumerate(lines) if l.strip()), None)
    if first is None or not lines[first].strip().startswith("// SPDX-License-Identifier:"):
        add(1, "SPDX001", "error", "first line must be `// SPDX-License-Identifier: <id>` (docs §3.4.1)")
    pragmas = [(i, l) for i, l in enumerate(lines, 1) if re.match(r"\s*pragma\s+solidity", l)]
    if not pragmas:
        add(1, "PRAGMA001", "error", "missing `pragma solidity` (docs §3.4.2)")
    elif profile == "repo":
        # Exact pin, or a floor inside the supported 0.8.34-0.8.37 window capped below 0.9.0 (lets an
        # alternative compiler with an older front end, such as solx, build the file; the build's own
        # `solc_version` still decides the compiler that ships).
        allowed = r"\s*pragma\s+solidity\s+(0\.8\.37|>=\s*0\.8\.3[4-7]\s+<\s*0\.9\.0)\s*;"
        for i, l in pragmas:
            if not re.match(allowed, l):
                add(
                    i,
                    "PRAGMA002",
                    "error",
                    "repo profile requires `pragma solidity 0.8.37;` or `>=0.8.3[4-7] <0.9.0;`",
                )
    sev = "error" if profile == "repo" else "warning"
    for i, (l, ml) in enumerate(zip(lines, masked), 1):
        if "\t" in l:
            add(i, "INDENT001", "error", "tab character; use 4 spaces (style guide §3.34.2)")
        lead = len(l) - len(l.lstrip(" "))
        if lead % 4 and l.strip() and not l.lstrip().startswith(("*", "//", "/*")):
            add(i, "INDENT002", "warning", f"indentation of {lead} spaces is not a multiple of 4 (style guide §3.34.2)")
        if len(l) > max_line:
            add(i, "LINE001", "warning", f"line length {len(l)} > {max_line} (style guide §3.34.2)")
        if re.search(r"\b(TODO|FIXME|XXX|HACK)\b", l) and l.strip().startswith(("//", "*", "/*")):
            add(i, "TODO001", "error", "unfinished-work marker in completed path (resolve or track as a named-error entrypoint)")
        # The deprecated annotation is the whole comment. A mention inside a longer note is not.
        if re.match(r"\s*(///\s*@solidity\s+memory-safe-assembly\s*|/\*\*\s*@solidity\s+memory-safe-assembly\s*\*/\s*)$", l):
            add(i, "DEPR003", "error", "`memory-safe-assembly` comment is deprecated; use `assembly (\"memory-safe\") { }` (docs §3.10.5)")
        if re.match(r"\s*pragma\s+abicoder\s+v1", l):
            add(i, "DEPR007", "error", "`abicoder v1` is deprecated and scheduled for removal (docs §3.4.2)")
        if re.match(r"\s*pragma\s+experimental\s+SMTChecker", l):
            add(i, "DEPR007", "warning", "`pragma experimental SMTChecker` is deprecated; select the engine via compiler settings")
        # masked-text patterns
        if re.search(r"\bselfdestruct\s*\(", ml):
            add(i, "DEPR002", "error", "`selfdestruct` is deprecated (since 0.8.18) and no longer destroys code on Cancun+ chains (docs §3.1.3)")
        if re.search(r"\.send\s*\(", ml) and ml.count(",") == 0:
            add(i, "DEPR001", "error", "`.send()` is deprecated and scheduled for removal; use `call{value: v}(\"\")` and check the result (docs §3.6.1)")
        tr = re.search(r"\.transfer\s*\(([^)]*)\)", ml)
        if tr and "," not in tr.group(1):
            add(i, "DEPR001", "error", "`.transfer()` is deprecated and scheduled for removal; use `call{value: v}(\"\")` and check the result (docs §3.6.1)")
        if re.search(r"\bblock\.difficulty\b", ml):
            add(i, "DEPR006", "warning", "`block.difficulty` is a deprecated alias of `block.prevrandao` on EVM ≥ paris")
        if re.search(r"\brevert\s*\(\s*0\s*,\s*0\s*\)", ml):
            add(i, "ERR003", "error", "`revert(0, 0)` in assembly swallows the reason; encode a custom error selector")
        if re.search(r"\bassert\s*\(", ml) and re.search(r"(==|!=|<=|>=|<|>)", ml):
            add(i, "ERR005", sev, "`assert` must only guard invariants; use `require`/custom error for validation (docs §3.8.8)")
        if re.search(r"\btx\.origin\b", ml):
            add(i, "SEC001", "warning", "`tx.origin` used in an authorisation check (security §3.24.1; also unreliable after EIP-7702)")
        if re.search(r"\bassembly\s*\{", ml):
            add(i, "ASM001", "info", "assembly block without `(\"memory-safe\")`; annotate it if it respects Solidity's memory model (docs §3.10.5)")
    _scan_revert_require(masked_src, sev, add)
    for m in re.finditer(r"\bconstructor\s*\(", masked_src):
        header = _header_until_brace(masked_src, m.start())
        if re.search(r"\b(public|internal)\b", header):
            add(masked_src.count("\n", 0, m.start()) + 1, "DEPR005", "error", "constructor visibility is deprecated; omit it (docs §3.9.1)")
    for start, stmt in _iter_statements(masked_src):
        for at in _call_sites(stmt):
            if _statement_captures_call(stmt, at):
                continue
            add(start + stmt[:at].count("\n"), "CALL001", "error",
                "low-level call result is not captured; it returns `false` instead of reverting (docs §3.6.1)")
    for m in re.finditer(r"\bcatch\b[^{]*\{\s*\}", masked_src):
        add(line_of(src, m.start()), "ERR004", "error", "empty `catch` block swallows the failure; handle it or re-revert")


def check_file(path: Path, profile: str, max_line: int, backend: str, base_path: str | None, remappings: list[str]):
    findings: list[Finding] = []
    src = path.read_text(encoding="utf-8", errors="replace")
    lines = src.split("\n")

    def add(line, code, level, msg):
        findings.append(Finding(str(path), line, code, level, msg))

    model = None
    if backend in ("auto", "ast"):
        model = ast_model(path, base_path, remappings)
        if model is None and backend == "ast":
            add(1, "BACKEND", "error", "AST backend requested but solc parse failed or solc not found")
    if model is None:
        model = regex_model(src, lines)
    structural_checks(model, path, add)
    textual_checks(src, lines, profile, max_line, add)
    return findings, model.backend


def main(argv: list[str]) -> int:
    profile, max_line, quiet, backend, base_path, remappings, paths = "generic", 120, False, "auto", None, [], []
    it = iter(argv)
    for a in it:
        if a == "--profile":
            profile = next(it, "generic")
        elif a == "--max-line":
            max_line = int(next(it, "120"))
        elif a == "--backend":
            backend = next(it, "auto")
        elif a == "--base-path":
            base_path = next(it, None)
        elif a == "--remappings":
            f = Path(next(it, "remappings.txt"))
            remappings = [x.strip() for x in f.read_text().splitlines() if x.strip()] if f.exists() else []
        elif a == "--quiet":
            quiet = True
        elif a.startswith("-"):
            print(__doc__); return 2
        else:
            paths.append(Path(a))
    if not paths or backend not in ("auto", "ast", "regex"):
        print(__doc__); return 2
    if base_path is None and Path("remappings.txt").exists() and not remappings:
        remappings = [x.strip() for x in Path("remappings.txt").read_text().splitlines() if x.strip()]
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            for x in sorted(p.rglob("*.sol")):
                rel_parts = x.relative_to(p).parts
                if any(part in ("lib", "node_modules") for part in rel_parts):
                    continue
                files.append(x)
        elif p.suffix == ".sol":
            files.append(p)
    findings: list[Finding] = []
    backends = set()
    for f in files:
        fs, b = check_file(f, profile, max_line, backend, base_path, remappings)
        findings += fs; backends.add(b)
    findings.sort(key=lambda x: (x.path, x.line, x.code))
    for f in findings:
        if quiet and f.level == "info":
            continue
        print(f)
    errs = sum(1 for f in findings if f.level == "error")
    warns = sum(1 for f in findings if f.level == "warning")
    gate = "warnings=fail" if profile == "repo" else "warnings=allowed"
    print(f"\nsolcheck: {len(files)} file(s), {errs} error(s), {warns} warning(s), profile={profile}, {gate}, backend={'+'.join(sorted(backends)) or 'none'}")
    return 1 if errs or (profile == "repo" and warns) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
