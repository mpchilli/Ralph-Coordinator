"""
coordinator/loop.py — The Micro-Ratchet Engine.

Production execution loop that replaces LLMStub with real Gemini calls.
Implements: Hat Selection, TDD Enforcement (Red/Green/Refactor),
Vision Verification, and Captain Consultation (Ambiguity Traps).
"""

import os
import re
import json
import subprocess
import time

from .llm import generate, generate_vision, load_config, get_usage_summary
from .safety import Referee
from .state import PlanManager


# ── Constants ─────────────────────────────────────────────────────────

MAX_RETRIES = 3  # Tighter loop for TDD
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, "templates", "roles")


# ── Hat System ────────────────────────────────────────────────────────

def _load_role_template(role_name):
    """Load a role system prompt from templates/roles/<role_name>.md."""
    path = os.path.join(TEMPLATES_DIR, f"{role_name}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return (
        f"You are a Senior {role_name.title()}. "
        "Write clean, production-grade code. Follow best practices. "
        "Return ONLY the code, no commentary."
    )


def select_hat(task_tags):
    """
    Return role name and system prompt based on tags.
    Injects the 'Ambiguity Trap' instruction into the prompt.
    """
    tag_to_role = {
        "UI": "designer",
        "Test": "tester",
        "Backend": "developer",
        "Frontend": "developer",
        "Setup": "architect",
        "Docs": "developer",
    }

    role = "developer"
    for tag in task_tags:
        if tag in tag_to_role:
            role = tag_to_role[tag]
            break

    base_prompt = _load_role_template(role)
    
    # Inject Ambiguity Trap instruction
    ambiguity_instruction = (
        "\n\nCRITICAL: If the requirements are too vague or ambiguous to proceed safely, "
        "output a JSON object instead of code:\n"
        "```json\n"
        '{ "type": "OPTION", "choices": ["Option A...", "Option B..."] }\n'
        "```"
    )
    
    return role, base_prompt + ambiguity_instruction


# ── Captain Consultation ──────────────────────────────────────────────

def consult_captain(task_text, issue_description, options=None):
    """
    Pause and ask the user for guidance.
    Handles both error recovery and proactive options.
    """
    prompt_path = os.path.join(PROJECT_ROOT, ".ralph-captain-prompt.md")
    response_path = os.path.join(PROJECT_ROOT, ".ralph-captain-response.md")

    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write("# Captain's Attention Required\n\n")
        f.write(f"**Task:** {task_text}\n\n")
        if options:
            f.write("**Ambiguity Detected - Please Select an Option:**\n")
            for i, opt in enumerate(options, 1):
                f.write(f"{i}. {opt}\n")
            f.write("\n**Or write custom guidance below.**\n")
        else:
            f.write(f"**Issue:** {issue_description}\n\n")
        f.write("---\n")
        f.write("Write your guidance in `.ralph-captain-response.md` and save.\n")

    print(f"\n{'='*60}")
    print("CAPTAIN INTERVENTION REQUIRED")
    print(f"Task: {task_text}")
    if options:
        print("Ambiguity Detected. See .ralph-captain-prompt.md for options.")
    else:
        print(f"Issue: {issue_description}")
    print(f"Write response to: {response_path}")
    print(f"{'='*60}\n")

    # Poll for response
    for _ in range(600):  # Wait up to 50 minutes (user might be away)
        if os.path.exists(response_path):
            with open(response_path, "r", encoding="utf-8") as f:
                guidance = f.read().strip()
            # Clean up files
            try:
                os.remove(response_path)
                os.remove(prompt_path)
            except OSError:
                pass
            return guidance
        time.sleep(5)

    return "SKIP"


# ── Visual Verification (Designer Hat) ────────────────────────────────

def verify_visuals(description):
    """Take a screenshot and verify with vision model."""
    screenshot_dir = os.path.join(PROJECT_ROOT, ".ralph", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "latest.png")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            try:
                page.goto("http://localhost:5173", wait_until="networkidle", timeout=15000)
            except Exception:
                # If networkidle times out, try capturing anyway
                pass
            page.screenshot(path=screenshot_path, full_page=True)
            browser.close()
    except Exception as e:
        return False, f"Playwright failed: {e}"

    vision_prompt = (
        "You are a UI/UX Quality Auditor.\n"
        f"Expected behavior: {description}\n\n"
        "Analyze the screenshot and respond with EXACTLY one of:\n"
        "PASS: <brief reason>\n"
        "FAIL: <brief reason>\n"
    )

    try:
        result = generate_vision(vision_prompt, screenshot_path)
        passed = result.strip().upper().startswith("PASS")
        return passed, result.strip()
    except Exception as e:
        return False, f"Vision analysis failed: {e}"


class AmbiguityException(Exception):
    def __init__(self, options):
        self.options = options


# ── The Micro-Ratchet ─────────────────────────────────────────────────

class MicroRatchet:
    def __init__(self):
        config = load_config()
        self.referee = Referee(config.get("security", {}).get("allowlist"))
        self.state = PlanManager()
        self.lock_file = os.path.join(PROJECT_ROOT, "coordinator.lock")

    def _acquire_lock(self):
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, "r") as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                return False
            except (ValueError, OSError):
                pass
        with open(self.lock_file, "w") as f:
            f.write(str(os.getpid()))
        return True

    def _release_lock(self):
        if os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
            except OSError:
                pass

    def run_all(self):
        """Run the loop over all tasks."""
        if not self._acquire_lock():
            print("Layout locked.")
            return

        try:
            self.referee.update_badge("running", usage=get_usage_summary())
            while True:
                task = self.state.get_next_task()
                if not task:
                    self.referee.update_badge("idle", usage=get_usage_summary())
                    print("\nAll tasks complete.")
                    break
                
                if not self._run_single_task(task):
                    print(f"\nTask failed: {task['text']}")
                    self.referee.update_badge("failed", task_id=task["text"])
                    break
        finally:
            self._release_lock()

    def _run_single_task(self, task):
        task_text = task["text"]
        task_tags = task.get("tags", [])
        line_number = task["line_number"]
        role_name, system_prompt = select_hat(task_tags)
        is_ui_task = "UI" in task_tags

        print(f"\n{'─'*60}\nTask: {task_text} ({role_name})\n{'─'*60}")

        # Standard TDD Loop: Red -> Green -> Refactor
        # Designer Loop: Generate -> Vision Verify

        for attempt in range(1, MAX_RETRIES + 1):
            self.referee.update_badge("running", task_id=task_text, iteration=f"{attempt}/{MAX_RETRIES}", usage=get_usage_summary())
            
            try:
                if is_ui_task:
                    success = self._run_designer_flow(task_text, system_prompt)
                else:
                    success = self._run_tdd_flow(task_text, system_prompt, attempt)
                
                if success:
                    self.state.mark_task_done(line_number)
                    self.referee.update_badge("passed", task_id=task_text)
                    return True
                
                # If not success, loop will retry
                print(f"  [{attempt}] Retry...")
                self._git_reset()
                
            except AmbiguityException as e:
                # Handle Ambiguity Trap
                guidance = consult_captain(task_text, "Ambiguity Detected", e.options)
                if guidance == "SKIP":
                    return False
                system_prompt += f"\n\nUser Guidance: {guidance}"
                continue

        # Final consultation if all retries failed
        guidance = consult_captain(task_text, "Max retries exhausted.")
        return False

    def _run_tdd_flow(self, task_text, system_prompt, attempt):
        """
        Execute strict Red -> Green -> Refactor flow.
        """
        context = self.state.load_plan()

        # 1. RED: Write failing test
        print("  [RED] Generating test...")
        red_prompt = (
            f"Task: {task_text}\nContext:\n{context}\n\n"
            "Phase 1 (RED): Write a test file that fails because the feature is missing. "
            "Output ```filename.py blocks."
        )
        self._generate_and_apply(red_prompt, system_prompt)
        
        # Verify it FAILS (if it passes, the test is invalid or feature exists)
        passed, _ = self._run_tests(quiet=True)
        if passed:
            print("  [RED] Error: Test passed immediately. It must fail first.")
            return False

        # 2. GREEN: Write implementation to pass test
        print("  [GREEN] Implementing feature...")
        green_prompt = (
            f"Task: {task_text}\n"
            "Phase 2 (GREEN): Write the implementation code to pass the test you just created. "
            "Output ```filename.py blocks."
        )
        self._generate_and_apply(green_prompt, system_prompt)

        # Verify it PASSES
        passed, feedback = self._run_tests()
        if not passed:
            print(f"  [GREEN] Failed: {feedback}")
            return False

        # 3. REFACTOR (Optional, skipped for speed in v1, but good practice)
        # Commit on Green
        print("  [GREEN] Passed. Committing.")
        self._git_commit(task_text)
        return True

    def _run_designer_flow(self, task_text, system_prompt):
        """
        Execute Designer flow: Code -> Vision Verify.
        """
        context = self.state.load_plan()
        
        print("  [DESIGN] Generating UI...")
        prompt = (
            f"Task: {task_text}\nContext:\n{context}\n\n"
            "Generate React/CSS code. Output ```filename blocks."
        )
        self._generate_and_apply(prompt, system_prompt)

        print("  [DESIGN] Verifying...")
        passed, feedback = verify_visuals(task_text)
        
        if passed:
            print(f"  [DESIGN] PASS: {feedback}")
            self._git_commit(task_text)
            return True
        else:
            print(f"  [DESIGN] FAIL: {feedback}")
            return False

    def _generate_and_apply(self, prompt, system_prompt):
        """Generate code and check for Ambiguity Trap."""
        output = generate(prompt, system_instruction=system_prompt)
        
        # Check for JSON Ambiguity Trap
        if output.strip().startswith("{") and '"type": "OPTION"' in output:
            try:
                data = json.loads(output)
                if data.get("type") == "OPTION":
                    raise AmbiguityException(data.get("choices", []))
            except json.JSONDecodeError:
                pass

        self._apply_generated_code(output)

    def _run_tests(self, quiet=False):
        try:
            result = self.referee.run_safe("npm test", capture=True, timeout=120)
            if result.returncode == 0:
                return True, "Tests passed."
            return False, "Tests failed."
        except Exception as e:
            return False, str(e)

    def _apply_generated_code(self, llm_output):
        pattern = re.compile(r"```(\S+)\n(.*?)```", re.DOTALL)
        for match in pattern.finditer(llm_output):
            filename = match.group(1).strip()
            content = match.group(2)
            if "/" in filename or "." in filename:
                filepath = os.path.join(PROJECT_ROOT, filename)
                try:
                    self.referee.validate_path(filepath)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"  Wrote: {filename}")
                except Exception as e:
                    print(f"  Skipped {filename}: {e}")

    def _git_commit(self, message):
        self.referee.run_safe("git add -A")
        safe_msg = message.replace('"', "'")[:72]
        self.referee.run_safe(f'git commit -m "feat: {safe_msg}"')

    def _git_reset(self):
        self.referee.run_safe("git checkout -- .")
        self.referee.run_safe("git clean -fd")
        
    def run_cycle(self, task_id):
        # Backward compatibility stub
        self.run_all()
