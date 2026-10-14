# Audit Report Template

> **Provenance:** adapted from the local "hashlock-style-audit" skill (`report-template.md` + the finding template in
> its `SKILL.md`, read in full 2026-10-10; no licence file present). Firm branding is **removed**: a report from this
> skill is an AI-assisted review and must not be presented as any audit firm's work. A verification label and
> `file:line` evidence are added (repo §1A).

Replace the bracketed values and drop sections that do not apply. Save the report as Markdown. Make Word or PDF only
on request.

```markdown
# Smart Contract Security Review

**Scope:** [protocol / unit]   **Commit:** [git sha]   **Date:** [YYYY-MM-DD]
**Compiler:** solc [x.y.z], evm [target], via-IR [yes/no]   **Chain:** [target]
**Reviewer:** AI-assisted review (Claude); tools: [solcheck, forge build/test, Slither x.y, …]

> **Disclaimer:** This is an AI-assisted, preliminary security review. It is not a substitute for a manual audit by
> professional security researchers. It can miss complex logic bugs, cross-contract interactions and economic
> attacks. Every finding is labelled CONFIRMED (traced end to end or tested) or HYPOTHESIS.

## Executive summary
[2–3 sentences: what the code does, what was reviewed.]

| Severity | Count |
|---|---|
| Critical | X |
| High | X |
| Medium | X |
| Low | X |
| Gas | X |
| Informational | X |
| **Total** | **X** |

**Overall rating:** [Clean / Secure / Partially secure / Unsecure], with 1–2 sentences of justification.

## Scope
| # | File | Lines | SHA-256 (8) |
|---|---|---|---|
| 1 | [path/File.sol] | [n] | [hash] |

Out of scope: [tests, scripts, vendored libraries (assumed audited, but their licence closure is still scanned), …]

Methodology:
1. Line-by-line review against `audit-vulnerability-checklist.md`.
2. Control-flow analysis for reentrancy and state consistency.
3. An access-control map of privileged operations.
4. Token-integration analysis.
5. Gas review.
6. 0.8.37 rule gate (`solcheck.py`, `compile_check.sh`).
7. Static analysis, triaged.

## Findings
<!-- Sort by severity. IDs: C-01, H-01, M-01, L-01, G-01, I-01 -->

### [C-01] [Title]
| Field | Value |
|---|---|
| Severity | Critical |
| Type | [SWC / category] |
| Location | [File.sol:L42-L58] |
| Status | CONFIRMED / HYPOTHESIS |

**Description.** What is wrong, and the exact execution path, citing `file:line`.

**Impact.** What an attacker gains. Quantify where possible.

**Proof of concept.** A Foundry test (`test_RevertWhen_…` / `testFork_…`) or a step sequence. Fork tests run at a
pinned block against verified addresses.

**Recommended fix.** Drop-in code that follows this skill's rules: named errors, Solady first, NatSpec.

**References.** SWC, EIP, or a primary doc URL.

## Gas optimisations
### [G-01] [Title]: `File.sol:Lx-Ly`; saving: [measured gas, `forge snapshot --diff`]
[Description and code.]

## Informational
### [I-01] [Title]: `File.sol:Lx`
[One paragraph.]

## Conclusion
[Key recommendations and next steps: fix C/H → re-review → professional audit before mainnet.]
```

## Presenting results
- Give the most severe confirmed findings first.
- Offer to deep-dive any finding.
- Suggest the next step: fix, then re-scan, then consider a professional audit.
- Do not publish or share the report externally without the owner's OK.
