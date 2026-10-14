#!/usr/bin/env bash
# Exercise compile_check.sh exit codes. Run: bash scripts/test_compile_check.sh
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
check="$root/scripts/compile_check.sh"
tmp="$(mktemp -d)"
# Invoked by trap, which shellcheck does not count as a use.
# shellcheck disable=SC2329
cleanup() {
  python3 -c 'import shutil, sys; shutil.rmtree(sys.argv[1])' "$tmp"
}
trap cleanup EXIT

failures=0
expect() {
  local got="$1"
  local want="$2"
  local msg="$3"
  if [[ "$got" -eq "$want" ]]; then
    printf 'PASS %s\n' "$msg"
  else
    printf 'FAIL %s (got %s want %s)\n' "$msg" "$got" "$want"
    failures=$((failures + 1))
  fi
}

set +e
(cd "$tmp" && bash "$check") >"$tmp/usage" 2>&1
rc=$?
set -e
expect "$rc" 2 "no files and no foundry.toml is usage"

bash_bin="$(command -v bash)"
set +e
env PATH="/usr/bin:/bin" "$bash_bin" "$check" "$root/scripts/fixtures/Vault.sol" >"$tmp/nocomp" 2>&1
rc=$?
set -e
expect "$rc" 3 "files given and solc absent is not verified"

if ! command -v solc >/dev/null 2>&1; then
  echo "NOTE solc not found: compile cases skipped"
else
  set +e
  bash "$check" "$root/scripts/fixtures/Vault.sol" >"$tmp/vault" 2>&1
  rc=$?
  set -e
  expect "$rc" 0 "Vault.sol compiles clean"

  set +e
  bash "$check" "$root/scripts/fixtures/Escrow.sol" >"$tmp/escrow" 2>&1
  rc=$?
  set -e
  expect "$rc" 0 "Escrow.sol compiles clean"

  set +e
  bash "$check" "$root/scripts/fixtures/Bad.sol" >"$tmp/bad" 2>&1
  rc=$?
  set -e
  expect "$rc" 1 "Bad.sol is a compiler error"

  cat >"$tmp/Warn.sol" <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;
contract Warn {
    function f() external pure {
        uint256 unused = 1;
    }
}
EOF
  set +e
  bash "$check" "$tmp/Warn.sol" >"$tmp/warn" 2>&1
  rc=$?
  set -e
  expect "$rc" 2 "unused local is a warning"

  cat >"$tmp/Other.sol" <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;
contract Other {}
EOF
  cat >"$tmp/Main.sol" <<'EOF'
// SPDX-License-Identifier: MIT
pragma solidity 0.8.37;
import "extra/Other.sol";
contract Main {}
EOF
  printf 'extra/=./\n' >"$tmp/remappings.txt"
  set +e
  (cd "$tmp" && bash "$check" Main.sol) >"$tmp/remap" 2>&1
  rc=$?
  set -e
  expect "$rc" 0 "remappings.txt is passed to solc"
fi

printf '\n%s failure(s)\n' "$failures"
exit "$([[ "$failures" -eq 0 ]] && printf '0' || printf '1')"
