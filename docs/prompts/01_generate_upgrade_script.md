# AGENT INSTRUCTION: BUILD THE BOOTSTRAP SCRIPT

**Role:** Principal DevOps Engineer & Python Architect
**Task:** Write a Python script named `upgrade_ralph.py` in the workspace root.
**Objective:** This script will inject the "Ralph-Coordinator" engine (Python backend) into the existing "Ralph-Orchestrator" (Electron frontend).

## 1. Context & Paths

* **Workspace Root:** `.` (Current Directory)
* **Target Repo:** `./ralph-orchestrator` (Existing folder)
* **Operating System:** Windows x64 (Must use `os.path.join`, `subprocess.run`, and handle `\` correctly).

## 2. The Script Logic (`upgrade_ralph.py`)

The script must perform these steps sequentially when run:

1. **Validation:** Check if `./ralph-orchestrator/package.json` exists. If not, exit with error "Target repo not found."
2. **Safety Backup:** Copy `./ralph-orchestrator/src/backend` to `./ralph-orchestrator/_backup_backend`.
3. **Dependency Injection:** * Create a `requirements.txt` in `./ralph-orchestrator` containing: `google-generativeai`, `playwright`, `pyyaml`, `colorama`.
4. **Module Injection:** Write the following Python files into `./ralph-orchestrator/coordinator/`:

   * **`__init__.py`**: Empty marker file.
   * **`config.yaml`**:

     ```yaml
     system:
       mode: "hybrid"
       budget_max_usd: 5.00
     models:
       planner: "gemini-2.0-pro-exp-02-05"
       executor: "gemini-2.5-flash-preview-09-25"
       vision: "gemini-2.0-flash-exp" # For Designer Hat
     security:
       allowlist: ["git", "npm", "node", "python", "ls", "echo", "mkdir", "npx"]
     ```

     yaml
   * **`safety.py` (The Referee):**

     * Implement `class Referee`.
     * **Function `validate_command(cmd_list)`**: Check if binary is in `allowlist`.
     * **Function `validate_path(path_str)`**: Use `os.path.abspath` to ensure path starts with `os.getcwd()`. Raise error if traversing up (`..`).
     * **Function `run_safe(cmd_str)`**: Parse string to list, validate, then run using `subprocess.run(..., shell=True)`.
   * **`state.py` (The Spine):**

     * Implement `class PlanManager`.
     * **Function `load_plan()`**: Read `plan.md`. If missing, return default template.
     * **Function `save_snapshot()`**: Atomic write to `plan.md` (write to temp -> os.replace).
     * **Function `update_dashboard()`**: Write status to `./src/frontend/public/dashboard_state.json` (or equivalent path) so Electron sees it.
   * **`loop.py` (The Micro-Ratchet):**

     * Implement `run_cycle(task_id)`.
     * **Logic:**
       1. **Lock:** Check `coordinator.lock`.
       2. **Plan:** Read Task.
       3. **Generate:** Call LLM (Stub `llm.generate`).
       4. **Verify:** Call `safety.run_safe("npm test")`.
       5. **Commit/Revert:** If exit_code=0 -> `git commit`. Else -> `git reset`.
   * **`bridge.py` (The Connector):**

     * A script that starts the loop and listens for a "Start" signal (simple loop checking a file trigger or CLI arg).

## 3. Implementation Requirements

* **Docstrings:** Every function must have a clear docstring explaining inputs/outputs.
* **Windows Compatibility:** Use `encoding='utf-8'` for all file operations. Use `shell=True` for subprocess calls on Windows, but ONLY after `safety.py` validation.
* **No placeholders:** Write functional, working code for the file generation parts.

**ACTION:** Generate the `upgrade_ralph.py` file now.
