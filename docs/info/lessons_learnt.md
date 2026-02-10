# Lessons Learnt

## [ISSUE]: spawn ralph ENOENT on Windows
**Date:** 2026-02-10
**Description:** The Ralph Orchestrator backend (Node.js) failed to launch the Python Coordinator bridge. It attempted to spawn `ralph` without a file extension and without a shell on Windows, resulting in an `ENOENT` error.

**[FIX]:**
1. Updated `backend/ralph-web-server/src/serve.ts` to use the absolute path to `ralph.cmd` (`RALPH_CLI_PATH`).
2. Updated `backend/ralph-web-server/src/runner/ProcessSupervisor.ts` to include `{ shell: true }` when spawning processes on Windows. This is required for executing `.cmd` files.
3. Verified the fix using a standalone test script `scripts/test-ralph-spawn.js`.

**[LESSON]:**
On Windows, `child_process.spawn` cannot execute `.cmd` or `.bat` files directly unless they are in the PATH and `shell: true` is specified. Always use absolute paths for critical system binaries and ensure shell execution is enabled for batch script wrappers on Windows.

---

## Audit Remediation [2026-02-10]

**Context:** An external audit (critic_analysis_v2.md) compared the codebase against the original spec (project_goals.md) and found significant deviations introduced during V2 refactoring.

### Corrections Applied

| File | Issue | Fix |
|:---|:---|:---|
| `coordinator/llm.py` | Signature drift: `generate(prompt, model_name, system_instruction)` | Reverted to spec's `generate(prompt, role="executor")` |
| `coordinator/llm.py` | Feature creep: budget tracking, `generate_with_planner`, `see_and_critique` | Removed — not in spec |
| `coordinator/llm.py` | Vision used `genai.upload_file()` | Replaced with inline `{'mime_type', 'data'}` per spec |
| `coordinator/safety.py` | `update_badge(status, **kwargs)` | Reverted to spec's `update_badge(task_id, status, message)` |
| `coordinator/safety.py` | Feature creep: `validate_path()`, datetime, project_root | Removed — not in spec |
| `coordinator/loop.py` | Architecture: TDD phases, Ambiguity Traps, Captain Consultation, `run_all()` | Replaced with spec's `run_cycle(task_id)` single-entry flow |
| `coordinator/loop.py` | Feature creep: `select_hat`, `consult_captain`, `AmbiguityException` | Removed — not in spec |

**[LESSON]:**
When implementing production logic, always cross-reference against the original spec before adding features. V2 innovations (TDD, Ambiguity Traps) were valuable but introduced signature drift that broke spec-compliance. Features should be added as documented extension layers, not as modifications to spec-mandated interfaces.
