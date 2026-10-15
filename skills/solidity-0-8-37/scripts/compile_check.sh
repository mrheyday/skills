#!/usr/bin/env bash
# compile_check.sh — verify Solidity sources actually compile under 0.8.37 / osaka.
#
# Usage: scripts/compile_check.sh [FILE.sol ...]
#   - No files and foundry.toml present: `forge build` (the project config wins).
#   - Files given: `solc --via-ir --evm-version osaka`. Remappings come from
#     `forge remappings` when foundry.toml and forge are available, otherwise from
#     remappings.txt. This script does not call solc-select and does not change
#     the compiler selected for later commands.
#   - No files and no foundry.toml: usage.
#   - COMPILER selects the backend: unset or `solc` (default), or a solx binary name or path
#     (`solx`, `solx-slang`, /path/to/solx). Foundry mode passes it as `forge build --use <bin>`.
#     solx optimizes by default (no --optimize); a Slang-front-end solx also ignores --via-ir.
#     solx is a build backend, not the language gate: solc remains the authority for diagnostics.
#   - FORGE_JOBS sets `forge build -j` (default 10).
#
# Exit codes: 0 clean, 1 compiler errors, 2 warnings or usage, 3 no compiler.
# The RESULT line distinguishes warnings from usage.
set -euo pipefail

EVM_VERSION="${EVM_VERSION:-osaka}"
SOLC_VERSION="${SOLC_VERSION:-0.8.37}"
COMPILER="${COMPILER:-solc}"
FORGE_JOBS="${FORGE_JOBS:-10}"

has_line_prefix() {
  local text="$1"
  local prefix="$2"
  local line
  while IFS= read -r line; do
    case "$line" in
      "${prefix}"*) return 0 ;;
    esac
  done <<<"$text"
  return 1
}

has_forge_warning() {
  local line
  while IFS= read -r line; do
    case "$line" in
      Warning:*) return 0 ;;
    esac
    if [[ "$line" == warning\[* ]]; then
      return 0
    fi
  done <<<"$1"
  return 1
}

solc_version() {
  local line rest
  while IFS= read -r line; do
    case "$line" in
      "Version:"*)
        rest="${line#"Version: "}"
        rest="${rest%%+*}"
        printf '%s\n' "${rest%% *}"
        return 0
        ;;
    esac
  done < <("$COMPILER" --version 2>&1 || true)
  return 0
}

# Prints "solc", "solx" or "solx-slang" for the selected binary.
compiler_kind() {
  local text
  text="$("$COMPILER" --version 2>&1 || true)"
  case "$text" in
    *"Front end: Slang"*) echo "solx-slang" ;;
    *"LLVM-based Solidity compiler"*) echo "solx" ;;
    *) echo "solc" ;;
  esac
}

load_remappings() {
  local line count=0
  if [[ -f foundry.toml ]] && command -v forge >/dev/null 2>&1; then
    while IFS= read -r line; do
      case "$line" in
        *"="*)
          printf '%s\n' "$line"
          count=$((count + 1))
          ;;
      esac
    done < <(forge remappings 2>/dev/null || true)
  fi
  if [[ $count -eq 0 && -f remappings.txt ]]; then
    while IFS= read -r line; do
      case "$line" in
        ""|\#*) ;;
        *) printf '%s\n' "$line" ;;
      esac
    done < remappings.txt
  fi
}

if [[ $# -eq 0 && -f foundry.toml ]]; then
  if command -v forge >/dev/null 2>&1; then
    fargs=(build -j "$FORGE_JOBS")
    if [[ "$COMPILER" != "solc" ]]; then
      bin="$(command -v "$COMPILER" || true)"
      if [[ -z "$bin" ]]; then
        echo "RESULT: NOT VERIFIED — compiler '$COMPILER' not found."
        exit 3
      fi
      fargs+=(--use "$bin")
      echo "== forge build -j $FORGE_JOBS --use $bin (foundry.toml governs evm_version/via_ir) =="
    else
      echo "== forge build -j $FORGE_JOBS (foundry.toml governs solc/evm_version/via_ir) =="
    fi
    rc=0
    out="$(forge "${fargs[@]}" 2>&1)" || rc=$?
    printf '%s\n' "$out"
    if [[ $rc -ne 0 ]]; then
      echo "RESULT: compiler errors"
      exit 1
    fi
    if has_forge_warning "$out"; then
      echo "RESULT: compiled WITH WARNINGS"
      exit 2
    fi
    echo "RESULT: compiled clean"
    exit 0
  fi
  echo "foundry.toml present but forge not installed; pass explicit .sol files to use solc." >&2
fi

if [[ $# -eq 0 ]]; then
  echo "usage: $0 FILE.sol [...]  (or run with no args inside a Foundry project)" >&2
  echo "RESULT: usage"
  exit 2
fi

if ! command -v "$COMPILER" >/dev/null 2>&1; then
  echo "RESULT: NOT VERIFIED — no $COMPILER on PATH."
  exit 3
fi

ver="$(solc_version)"
kind="$(compiler_kind)"
case "$kind" in
  solc) args=(--via-ir --evm-version "$EVM_VERSION" --optimize --bin) ;;
  solx) args=(--via-ir --evm-version "$EVM_VERSION" --bin) ;;
  solx-slang) args=(--evm-version "$EVM_VERSION" --bin) ;;
esac
echo "== $kind ($COMPILER) language ${ver:-unknown} ${args[*]%--bin} =="
if [[ -n "$ver" && "$ver" != "$SOLC_VERSION" ]]; then
  echo "NOTE: compiler is $ver, not $SOLC_VERSION; results are for $ver."
fi
if [[ "$kind" != "solc" ]]; then
  echo "NOTE: $kind is a build backend; run with solc for language diagnostics."
fi
remaps=()
while IFS= read -r line; do
  [[ -n "$line" ]] && remaps+=("$line")
done < <(load_remappings)
if [[ ${#remaps[@]} -gt 0 ]]; then
  args+=(--base-path . --allow-paths . "${remaps[@]}")
fi

rc=0
# Drop --bin bytecode on stdout. Keep diagnostics, which solc and solx write to stderr.
out="$("$COMPILER" "${args[@]}" "$@" 2>&1 >/dev/null)" || rc=$?
printf '%s\n' "$out"
if [[ $rc -ne 0 ]] || has_line_prefix "$out" "Error:"; then
  echo "RESULT: compiler errors"
  exit 1
fi
if has_line_prefix "$out" "Warning:"; then
  echo "RESULT: compiled WITH WARNINGS (fix them; do not suppress)"
  exit 2
fi
echo "RESULT: compiled clean"
exit 0
