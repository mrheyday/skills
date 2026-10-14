# Audit Severity Matrix (likelihood × impact)

> **Provenance:** adapted from a local "hashlock-style-audit" skill, `/Volumes/extern/dev-projects/claude/hashlock-style-audit./severity-matrix.md`.
> That folder holds 6 files, all read in full on 2026-10-10, and they are byte-identical to its `.skill` archive. No
> licence file was present. Imported **as methodology**, under this skill's rules (docs win on conflict). Changes:
> the firm-branded rating names are neutralised, and repo-profile calibration is added at the end.

## Dimensions

Severity = **Likelihood** (how easily the issue triggers) × **Impact** (the damage when it does).

### Likelihood

| Level | Criteria |
|---|---|
| **High** | Any external actor with no special permissions, low capital and publicly known techniques can exploit it. It can be automated, and will likely be found and used quickly. |
| **Medium** | Needs specific conditions: timing, moderate capital, knowledge of protocol internals, or interaction with other protocols. Not trivially automatable. |
| **Low** | Needs highly unlikely conditions: admin key compromise, a multi-step attack with tight timing, extreme markets, or collusion between trusted actors. |

### Impact

| Level | Criteria |
|---|---|
| **High** | Direct loss of user funds, permanent bricking, unauthorised minting or draining, governance takeover, or total loss of protocol value. |
| **Medium** | Temporary fund locking, partial value extraction, griefing that degrades usability, broken invariants needing an emergency response, or loss of yield without loss of principal. |
| **Low** | Inconvenience, minor gas waste, cosmetic issues, a non-critical information leak, or issues that only affect the attacker. |

## Classification

```
                    Impact
                 Low    Med    High
Likelihood High │ Low  │ Med  │ Crit │
           Med  │ Low  │ Med  │ High │
           Low  │ Info │ Low  │ Med  │
```

- **Critical** (H×H). Direct theft, unlimited minting, protocol destruction. **Must** fix before deploy; halt if live.
  Examples: unprotected `withdraw()`, a reentrancy that drains a vault, an uninitialised proxy anyone can take.
- **High** (H×M or M×H). Funds at conditional risk, or protocol stability threatened. **Must** fix before deploy.
  Examples: a price oracle exploitable by flash loan, a user swap without slippage protection, a front-runnable
  initialisation.
- **Medium** (M×M, L×H or H×L). A real issue with conditions or a limited blast radius. **Should** fix.
  Examples: a first-depositor inflation attack on a low-value pool, a stale-oracle path, an unbounded loop with a
  realistic upper bound.
- **Low** (L×M, M×L, borderline L×L). Edge cases and minor leakage. **Recommended** fix, or accepted with
  documentation.
- **Gas.** No security impact. Optional. Give the measured saving (`forge snapshot` / `--gas-report`), never a guess.
- **Informational.** Best practice, code quality, documentation.

## Edge-case calibration

- Needs admin key compromise and the admin is a **multisig** → Low likelihood. If the admin is an **EOA** → Medium.
- Price manipulation by flash loan on a major DEX → High likelihood.
- Oracle failure → Low likelihood, but the impact can be High.
- A compiler bug in the pinned version → check `known-bugs.md` by `introduced`/`fixed`. If the build is exposed,
  Medium.
- MEV that only costs users gas → usually Low impact, unless it breaks the UX entirely.

**Upward modifiers:** a widely forked contract; deposited user funds at risk; the same bug actively exploited in
similar protocols; no monitoring or circuit breaker.

**Downward modifiers:** a narrow time window (for example, the first block after deploy); active monitoring plus a
pause; only the attacker's own funds are affected; more than $10M of capital needed for less than $1K of profit.

## Overall rating (neutral names)

| Rating | Meaning |
|---|---|
| **Clean** | No Critical or High findings, strong code quality, security practices in place. |
| **Secure** | No Critical findings; Highs resolved; acceptable risk profile. |
| **Partially secure** | Some High findings remain. Do not deploy until they are fixed. |
| **Unsecure** | Critical findings present. Do not deploy. |

## Calibration (repo profile)

- **Owner-only paths.** The owner gate is the trust boundary. A bug reachable only by the owner is usually Low or
  Info, unless the owner is an unscoped 7702 wallet, or the bug survives into a third-party-callable path.
  - If the repo's treasury multisig has a low threshold (for example 1-of-N), treat its compromise as **EOA-like (Medium) likelihood**, not
    multisig-Low.
- **§0D silent failure.** A path that fails quietly, such as default-on-error, a zero read as good, or an empty
  `catch`, is at least **Low** even with no theft path. A doctrine defect is never just Informational.
- **Deploy-time misconfiguration** (for example, an immutable delay that overflows) is Low when only the owner can
  set it, and becomes Medium if the result cannot be undone and blocks upgrades.
- **Verification label.** Mark every finding **CONFIRMED** (traced end to end, or tested) or **HYPOTHESIS**. Never
  inflate severity to look thorough.
