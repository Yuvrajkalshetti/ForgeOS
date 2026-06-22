# Implementation Report — V1.1 Usability Layer (friction reduction)

- **Date:** 2026-06-22 · **Status:** ✅ build complete, gates green, STOP for approval.
- **Scope:** approved V1.1 friction-reduction set — `doctor`, `status`, console alias,
  improved init guidance, first-run wizard. **Thin UX layers only; V1 core frozen.**

## Executive Summary
Added five thin, additive UX surfaces over the existing CLI/services. **No new AI/memory/
graph/learning/orchestration/provider/MCP/dashboard capability; no schema/storage change.**
Every surface is read-only or guidance-only and routes through the same stores/config as
the rest of the CLI.

## Files Added
- `cli/doctor.py` — `forge/forgeos doctor`: read-only setup diagnostics (initialized?
  store opens? provider selected? credential present? Python ≥3.12?), JSON + exit 1 on FAIL.
- `cli/status.py` — `forge/forgeos status`: project knowledge counts + active provider.
- `cli/wizard.py` — `forge/forgeos wizard`: non-interactive getting-started walkthrough.
- `tests/unit/test_v11_usability.py` — 7 tests.

## Files Modified
- `cli/portability.py` — `init` JSON now includes a `next_steps` guidance array (existing
  `created`/dir contract preserved).
- `cli/app.py` — register `doctor`, `status`, `wizard`.
- `pyproject.toml` — add `forgeos` console script (same entrypoint; **`forge` retained**).

## Friction Demonstrated (per the required criteria)
- **Reduced installation friction:** single brand name `forgeos` (alias) removes the
  `forge` vs `forgeos` ambiguity from the very first command.
- **Reduced onboarding friction:** `init` now tells you the next 3 commands; `wizard`
  narrates the full happy path with copy-pasteable commands.
- **Reduced support burden:** `doctor` turns silent failures (missing key, uninitialized,
  wrong Python) into one diagnostic with explicit remediation — fewer "why doesn't it
  work?" tickets.
- **Faster time-to-first-value:** new users self-diagnose and follow the guided path
  instead of guessing the command sequence or hitting opaque provider errors.

## Architecture Compliance
- Diagnostics/status are **read-only**; wizard is **print-only** (no interactive prompts →
  safe in CI). No core packages touched; no new node/edge/provider/storage types. `doctor`
  deliberately makes **no live provider call** (that's the smoke test's role).

## Acceptance Criteria
- ✅ console alias declared (`forge` == `forgeos` entrypoint; both present)
- ✅ `init` emits non-empty `next_steps` (mentions `doctor`); prior contract intact
- ✅ `doctor` healthy (ollama) → ok, exit 0; uninitialized → FAIL+`init` hint, exit 1;
  claude default w/o key → `credentials` FAIL naming `ANTHROPIC_API_KEY`, exit 1
- ✅ `status` reports correct counts + provider
- ✅ `wizard` prints ordered navigation (init/doctor/scan/mentor)

## Tests / Gates
- `tests/unit/test_v11_usability.py` — 7 tests (red→green).
- `scripts/check.py` → OK (164 files); `pytest -W error::UserWarning` → **242 passed**
  (235 → 242, +7). All prior tests green. CLI assembles with new commands registered.
- Synced to `~/code/forgeos`; verified via Read tool.

## Risks
- **Low.** `doctor`/`status` open the store read-only (store open is non-destructive and
  rebuilds index from snapshots). `next_steps` is additive JSON. Console alias is packaging
  only — unverifiable as an installed entrypoint in-sandbox, so the test asserts the
  `pyproject` declaration (both scripts → same target).

## Deviations From Plan
- **Wizard is non-interactive** (prints the guided path) rather than a prompt-driven flow,
  to stay deterministic and CI-safe. Functionally satisfies "first-run navigation."

## Confidence
**High.** Additive thin layers, fully tested, deterministic, full suite green.

## Remaining
V1.1 approved scope complete. (Console-alias entrypoint should be confirmed once on a real
`uv tool install` / `pip install`, alongside the V1 release gates.)
