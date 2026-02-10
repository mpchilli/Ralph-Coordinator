"""
coordinator/loop.py — The Micro-Ratchet Engine.

Spec-compliant: Lock -> Context -> Detect Hat -> Generate -> Verify -> Commit/Reset.
Single entry point: run_cycle(task_id).
"""

import os
import time
from .safety import Referee
from .state import PlanManager
from .llm import generate, generate_vision
# Import Playwright sync API
from playwright.sync_api import sync_playwright


class MicroRatchet:
    def __init__(self):
        # Tools allowed to touch the system
        self.referee = Referee(["git", "npm", "node", "python", "ls", "echo", "npx"])
        self.state = PlanManager()

    def run_cycle(self, task_id):
        """
        Execute a single task cycle: Lock -> Generate -> Verify -> Commit/Reset.

        Args:
            task_id: The task description string from plan.md.
        """
        # 1. Lock & Badge
        lock_file = 'coordinator.lock'
        if os.path.exists(lock_file):
            return  # Prevent overlap
        with open(lock_file, 'w') as f:
            f.write("LOCKED")

        self.referee.update_badge(task_id, "ACTIVE", "Initializing Cycle...")

        try:
            # 2. Context
            plan = self.state.load_plan()

            # 3. Detect Hat (UI vs Code)
            is_ui_task = "[UI]" in task_id

            # 4. Generate Code (The Brain)
            role = "vision" if is_ui_task else "executor"
            prompt = f"""
            ROLE: {'UI Designer' if is_ui_task else 'Senior Developer'}
            TASK: {task_id}
            CONTEXT: {plan}

            Write the code to solve this task.
            Output ONLY the code blocks (filename and content).
            """
            response = generate(prompt, role)
            print(f"Generated Code for {task_id}")
            self.referee.update_badge(task_id, "ACTIVE", "Code Generated")

            # (In production, we need a parser here to actually write the files from 'response')
            # For now, we assume the Agent is running a command to write files.

            # 5. Verify (The Eyes)
            try:
                if is_ui_task:
                    self._verify_ui(task_id)
                else:
                    self.referee.run_safe("npm test")

                # 6. Commit (Green — The Ratchet)
                self.referee.run_safe(f"git commit -am 'feat: {task_id}'")
                self.referee.update_badge(task_id, "SUCCESS", "Committed")

            except Exception as e:
                # 7. Reset (Red — The Safety Net)
                print(f"Verification Failed: {e}")
                self.referee.run_safe("git reset --hard")
                self.referee.update_badge(task_id, "ERROR", f"Reverted: {str(e)}")

        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file)

    def _verify_ui(self, task_id):
        """Designer Hat: Take screenshot and verify with Vision model."""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("http://localhost:3000")  # Assume dev server running
            page.screenshot(path="snapshot.png")
            browser.close()

        # Check with Vision Model
        verdict = generate_vision(
            f"Does this UI satisfy: {task_id}? Reply MATCH or MISMATCH.",
            "snapshot.png"
        )
        if "MISMATCH" in verdict:
            raise ValueError(f"Visual Regression: {verdict}")
