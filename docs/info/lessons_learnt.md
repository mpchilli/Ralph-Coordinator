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
