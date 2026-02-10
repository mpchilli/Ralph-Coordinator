"""
coordinator/loop.py — The Micro-Ratchet Engine.

Production execution loop that replaces LLMStub with real Gemini calls.
Implements: Hat Selection, TDD Enforcement, Vision Verification, and
Captain Consultation.
"""

import os
import re
import subprocess

from .llm import generate, generate_vision, load_config, get_usage_summary
from .safety import Referee
from .state import PlanManager


# ── Constants ─────────────────────────────────────────────────────────

MAX_RETRIES = 5
CONFIDENCE_THRESHOLD = 80
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates", "roles")


# ── Hat System ────────────────────────────────────────────────────────

def _load_role_template(role_name):
    """
    Load a role system prompt from templates/roles/<role_name>.md.

    Returns:
        The file contents as a string, or a sensible default.
    """
    path = os.path.join(TEMPLATES_DIR, f"{role_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    # Fallback: generic developer prompt
    return (
        f"You are a Senior {role_name.title()}. "
        "Write clean, production-grade code. Follow best practices. "
        "Return ONLY the code, no commentary."
    )


def select_hat(task_tags):
    """
    Given a list of task tags (e.g. ['UI', 'Test']), return the
    appropriate role name and system prompt.

    Priority: UI > Test > Backend > Developer (default).
    """
    tag_to_role = {
        "UI": "designer",
        "Test": "tester",
        "Backend": "developer",
        "Frontend": "developer",
        "Setup": "architect",
        "Docs": "developer",
    }

    for tag in task_tags:
        if tag in tag_to_role:
            role = tag_to_role[tag]
            return role, _load_role_template(role)

    return "developer", _load_role_template("developer")


# ── Captain Consultation ──────────────────────────────────────────────

def consult_captain(task_text, issue_description):
    """
    Pause and ask the user for guidance when the agent is stuck.

    Writes a prompt file and waits for user response.

    Args:
        task_text: The current task being worked on.
        issue_description: What went wrong or what is ambiguous.

    Returns:
        The user's guidance string, or 'SKIP' if timed out.
    """
    prompt_path = os.path.join(PROJECT_ROOT, ".ralph-captain-prompt.md")
    response_path = os.path.join(PROJECT_ROOT, ".ralph-captain-response.md")

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write("# Captain's Attention Required\n\n")
        f.write(f"**Task:** {task_text}\n\n")
        f.write(f"**Issue:** {issue_description}\n\n")
        f.write("---\n")
        f.write("Write your guidance in `.ralph-captain-response.md` and save.\n")

    print(f"\n{'='*60}")
    print("CAPTAIN INTERVENTION REQUIRED")
    print(f"Task: {task_text}")
    print(f"Issue: {issue_description}")
    print(f"Write response to: {response_path}")
    print(f"{'='*60}\n")

    # Wait for user to create response file (poll every 5 seconds, max 5 minutes)
    import time
    for _ in range(60):
        if os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as f:
                guidance = f.read().strip()
            os.remove(response_path)
            os.remove(prompt_path)
            return guidance
        time.sleep(5)

    # Timeout
    if os.path.exists(prompt_path):
        os.remove(prompt_path)
    return "SKIP"


# ── Visual Verification (Designer Hat) ────────────────────────────────

def verify_visuals(description):
    """
    Take a screenshot of the running app and ask the vision model
    if it matches the task description.

    Args:
        description: What the UI should look like after the change.

    Returns:
        (passed: bool, feedback: str)
    """
    screenshot_dir = os.path.join(PROJECT_ROOT, ".ralph", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "latest.png")

    try:
        # Use Playwright to capture a screenshot
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto("http://localhost:5173", wait_until="networkidle", timeout=15000)
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
    except Exception as e:
        return False, f"Playwright screenshot failed: {e}"

    # Send to vision model
    vision_prompt = (
        "You are a UI/UX Quality Auditor.\n\n"
        f"Expected behavior: {description}\n\n"
        "Analyze the screenshot and respond with EXACTLY one of:\n"
        "PASS: <brief reason>\n"
        "FAIL: <brief reason>\n\n"
        "Be strict. If the expected UI element is missing or broken, respond FAIL."
    )

    try:
        result = generate_vision(vision_prompt, screenshot_path)
        passed = result.strip().upper().startswith("PASS")
        return passed, result.strip()
    except Exception as e:
        return False, f"Vision analysis failed: {e}"


# ── The Micro-Ratchet ─────────────────────────────────────────────────

class MicroRatchet:
    """
    The core execution engine.

    For each task in plan.md:
    1. Lock
    2. Select Hat
    3. Generate code
    4. Verify (test or vision)
    5. Commit or Reset
    6. Update badge
    """

    def __init__(self):
        config = load_config()
        allowlist = config.get("security", {}).get(
            "allowlist", ["git", "npm", "node", "python", "ls", "echo"]
        )
        self.referee = Referee(allowlist)
        self.state = PlanManager()
        self.lock_file = os.path.join(PROJECT_ROOT, "coordinator.lock")

    def _acquire_lock(self):
        """Acquire the coordinator lock. Returns False if already locked."""
        if os.path.exists(self.lock_file):
            # Check if the PID in the lock is still alive
            try:
                with open(self.lock_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Check if process exists
                return False  # Process alive, lock is valid
            except (ValueError, OSError):
                pass  # Stale lock, reclaim it

        with open(self.lock_file, "w") as f:
            f.write(str(os.getpid()))
        return True

    def _release_lock(self):
        """Release the coordinator lock."""
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)

    def run_all(self):
        """
        Run the Micro-Ratchet loop over ALL unchecked tasks in plan.md.
        This is the primary entry point.
        """
        if not self._acquire_lock():
            print("Another coordinator instance is running. Exiting.")
            return

        try:
            self.referee.update_badge("running", usage=get_usage_summary())

            while True:
                task = self.state.get_next_task()
                if task is None:
                    print("\nAll tasks complete.")
                    self.referee.update_badge("idle", usage=get_usage_summary())
                    break

                success = self._run_single_task(task)
                if not success:
                    print(f"\nTask failed after {MAX_RETRIES} retries. Stopping.")
                    self.referee.update_badge(
                        "failed",
                        task_id=task["text"],
                        usage=get_usage_summary(),
                    )
                    break
        finally:
            self._release_lock()

    def _run_single_task(self, task):
        """
        Execute a single task with up to MAX_RETRIES attempts.

        Returns True on success, False on exhausted retries.
        """
        task_text = task["text"]
        task_tags = task.get("tags", [])
        line_number = task["line_number"]

        role_name, system_prompt = select_hat(task_tags)
        is_ui_task = "UI" in task_tags

        print(f"\n{'─'*60}")
        print(f"Task: {task_text}")
        print(f"Hat:  {role_name.title()}")
        print(f"Line: {line_number}")
        print(f"{'─'*60}")

        for attempt in range(1, MAX_RETRIES + 1):
            self.referee.update_badge(
                "running",
                task_id=task_text,
                iteration=f"{attempt}/{MAX_RETRIES}",
                usage=get_usage_summary(),
            )

            # 1. Generate code
            context = self.state.load_plan()
            code_prompt = (
                f"Task: {task_text}\n\n"
                f"Current plan.md:\n{context}\n\n"
                "Generate the code changes needed to complete this task. "
                "Output file paths and their full contents. "
                "Use ```filename.ext blocks for each file."
            )

            try:
                output = generate(code_prompt, system_instruction=system_prompt)
            except Exception as e:
                print(f"  [{attempt}] Generation failed: {e}")
                continue

            # 2. Parse and write files from the LLM output
            files_written = self._apply_generated_code(output)
            if not files_written:
                print(f"  [{attempt}] No files extracted from output. Retrying.")
                continue

            # 3. Verify
            self.referee.update_badge(
                "verifying",
                task_id=task_text,
                iteration=f"{attempt}/{MAX_RETRIES}",
                usage=get_usage_summary(),
            )

            if is_ui_task:
                passed, feedback = verify_visuals(task_text)
            else:
                passed, feedback = self._run_tests()

            if passed:
                # 4. Commit
                print(f"  [{attempt}] PASS: {feedback}")
                self._git_commit(task_text)
                self.state.mark_task_done(line_number)
                self.referee.update_badge(
                    "passed",
                    task_id=task_text,
                    usage=get_usage_summary(),
                )

                # Update dashboard
                done, total = self.state.count_progress()
                self.state.update_dashboard({
                    "status": "running",
                    "task": task_text,
                    "progress": f"{done}/{total}",
                    "usage": get_usage_summary(),
                })
                return True
            else:
                # 5. Reset and retry
                print(f"  [{attempt}] FAIL: {feedback}")
                self._git_reset()

                # Captain consultation on final retry
                if attempt == MAX_RETRIES - 1:
                    guidance = consult_captain(
                        task_text,
                        f"Failed {attempt} times. Last error: {feedback}",
                    )
                    if guidance == "SKIP":
                        print("  Captain timed out. Marking as failed.")
                        return False
                    # Inject guidance into next attempt via modified prompt
                    code_prompt += f"\n\nUser guidance: {guidance}"

        return False

    def _run_tests(self):
        """Run `npm test` and return (passed, feedback)."""
        try:
            result = self.referee.run_safe("npm test", capture=True, timeout=120)
            if result.returncode == 0:
                return True, "All tests passed."
            else:
                # Truncate output to avoid blowing context
                stderr = (result.stderr or "")[:500]
                stdout = (result.stdout or "")[:500]
                return False, f"Tests failed:\n{stderr}\n{stdout}"
        except subprocess.TimeoutExpired:
            return False, "Test suite timed out (120s)."
        except Exception as e:
            return False, f"Test execution error: {e}"

    def _apply_generated_code(self, llm_output):
        """
        Parse LLM output for ```filename.ext code blocks and write them.

        Returns a list of files written.
        """
        pattern = re.compile(
            r"```(\S+)\n(.*?)```", re.DOTALL
        )
        files_written = []

        for match in pattern.finditer(llm_output):
            filename = match.group(1).strip()
            content = match.group(2)

            # Skip non-file code blocks (like 'bash', 'json' without paths)
            if "/" not in filename and "\\" not in filename and "." not in filename:
                continue

            filepath = os.path.join(PROJECT_ROOT, filename)

            # Safety check
            try:
                self.referee.validate_path(filepath)
            except ValueError:
                print(f"  Path blocked: {filename}")
                continue

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            files_written.append(filename)
            print(f"  Wrote: {filename}")

        return files_written

    def _git_commit(self, message):
        """Stage all changes and commit."""
        try:
            self.referee.run_safe("git add -A", capture=True)
            safe_msg = message.replace('"', "'")[:72]
            self.referee.run_safe(f'git commit -m "feat: {safe_msg}"', capture=True)
        except Exception as e:
            print(f"  Git commit failed: {e}")

    def _git_reset(self):
        """Revert all uncommitted changes."""
        try:
            self.referee.run_safe("git checkout -- .", capture=True)
            self.referee.run_safe("git clean -fd", capture=True)
        except Exception as e:
            print(f"  Git reset failed: {e}")

    # ── Legacy single-cycle API (for bridge.py compatibility) ─────────

    def run_cycle(self, task_id):
        """
        Backward-compatible single-cycle entry point called by bridge.py.
        Runs ONE task from plan.md.
        """
        if not self._acquire_lock():
            print("Locked. Skipping cycle.")
            return

        try:
            task = self.state.get_next_task()
            if task is None:
                print("No pending tasks in plan.md.")
                return
            self._run_single_task(task)
        finally:
            self._release_lock()
