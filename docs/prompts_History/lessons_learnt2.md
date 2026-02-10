# Debugging Log: LoopsManager & Ralph CLI Bridge Integration

**Date:** 2026-02-10
**Component:** Ralph Orchestrator (Backend)
**Issue:** LoopsManager failing to spawn `ralph` process (ENOENT, EINVAL, unrecognized command)

## Synopsis

The backend server's `LoopsManager` and `PlanningService` were configured to spawn a `ralph` command, expecting a Rust-compiled binary on the system PATH. However, the project had transitioned to a Python-based coordinator (`bridge.py`) invoked via `ralph.cmd` in the repository root. This mismatch caused repeated process crashes.

We iteratively debugged and fixed the integration to allow the Node.js backend to successfully control the Python coordinator on Windows.

## Trial & Error Log

### 1. Initial Error Investigation
- **Trial:** Analyzed terminal output showing `Error: spawn ralph ENOENT`.
- **Finding:** The server was trying to execute `ralph` directly, but no such binary existed in the PATH. The repository uses `ralph.cmd` as a wrapper.
- **Lesson:** Always verify the existence and location of external binaries when migrating between project structures (Rust -> Python).

### 2. Bridge Implementation
- **Trial:** Updated `coordinator/bridge.py` to handle CLI arguments.
- **Action:** Expanded the script from a simple file-trigger loop to a full CLI entrypoint supporting `loops`, `run`, `list`, etc.
- **Result:** The Python script can now accept the subcommands that `LoopsManager` sends (e.g., `ralph loops process`), acting as a drop-in replacement.
- **Lesson:** When replacing a component, the new implementation must satisfy the existing interface (CLI arguments) to avoid breaking dependent services.

### 3. Path Configuration
- **Trial:** Updated `backend/.../serve.ts` to point to the absolute path of `ralph.cmd` instead of assuming "ralph" is on the PATH.
- **Action:** Defined `RALPH_CLI_PATH` resolving to the repo root's `ralph.cmd`.
- **Result:** `ENOENT` error resolved, but replaced by `EINVAL` on Windows.
- **Lesson:** Hardcoded command strings ("ralph") are fragile. Always use absolute paths for project-local executables.

### 4. Windows Process Spawning Fixes
- **Trial:** Attempted to fix `EINVAL` by adding `{ shell: true }` to the `spawn` options in `LoopsManager.ts`.
- **Finding:** This fixed `EINVAL`, but caused a new error: `'C:\Users\...\Ai' is not recognized`. The path contained spaces ("Ai Tools"), and the shell was splitting the command incorrectly.
- **Lesson:** On Windows, `shell: true` is often required for `.cmd/.bat` files, but it introduces argument parsing hazards.

### 5. Final Fix - Quoting Paths
- **Trial:** Modified `LoopsManager.ts` and `PlanningService.ts` to wrap the command path in quotes when on Windows.
- **Code Change:** `const command = process.platform === "win32" ? "\"${this.ralphPath}\"" : this.ralphPath;`
- **Result:** success! The server now successfully spawns the Python coordinator, and "Merge queue processed successfully" logs confirm stability.
- **Lesson:** Always quote file paths when executing shell commands, especially on Windows where spaces in directory names (e.g., "Program Files", "Ai Tools") are common.

## Summary of Changes

| File | Change |
|---|---|
| `coordinator/bridge.py` | Implemented CLI command handling to mock the original Rust binary. |
| `serve.ts` | Configured `LoopsManager` and `PlanningService` to use the local `ralph.cmd`. |
| `LoopsManager.ts` | Added Windows-specific spawn logic (shell: true + path quoting). |
| `PlanningService.ts` | Added Windows-specific spawn logic (shell: true + path quoting). |
