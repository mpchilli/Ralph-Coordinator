import os
import time
import re
from .safety import Referee
from .state import PlanManager
from .llm import generate, see_and_critique

from .tools import Toolbelt

class MicroRatchet:
    def __init__(self):
        self.referee = Referee(["git", "npm", "node", "python", "ls", "echo", "npx"])
        self.state = PlanManager()
        self.tools = Toolbelt()

    def run_cycle(self, task_id):
        # 1. Lock
        lock_file = 'coordinator.lock'
        if os.path.exists(lock_file):
            return
        with open(lock_file, 'w') as f: f.write("LOCKED")

        try:
            # 2. Plan & Context
            plan = self.state.load_plan()
            if not plan:
                print("⚠️ No Plan found. Run initialization first.")
                return

            self.state.update_badge(task_id, "THINKING")
            
            # 3. Select Hat & Prompt
            role = "developer"
            prompt_suffix = ""
            
            if "[UI]" in task_id:
                role = "designer"
                prompt_suffix = " You have Vision capabilities. Use them."
            
            # 4. Generate Code
            context = f"Current Plan:\n{plan}\n\nCurrent Task: {task_id}"
            print(f"🤖 Generating code for {task_id} as {role}...")
            
            # INSTRUCTION INJECTION: Tell LLM how to format files
            system_instruction = (
                "You are a coding agent. "
                "To save files, you MUST use this format:\n"
                "### FILE: src/filename.js\n"
                "```javascript\ncode\n```"
            )
            
            action = generate(f"{system_instruction}\n{context}\nWrite the code.{prompt_suffix}", role=role)
            
            # 4.5 ACTUATION (The Fix)
            print("💾 Applying Code Changes...")
            written_files = self.tools.apply_code_changes(action)
            if not written_files:
                print("⚠️ No files were written! Checking output...")
            
            # 5. Verify (The Captain)
            self.state.update_badge(task_id, "VERIFYING")
            
            if role == "designer":
                # VISION WORKFLOW
                print("🎨 Designer Hat: Taking Screenshot...")
                # (Assuming a capture script exists or using npx playwright)
                try:
                    self.referee.run_safe("npx playwright screenshot --url http://localhost:3000 --path snapshot.png")
                    critique = see_and_critique("snapshot.png", f"Does this match the task: {task_id}?")
                    if "MATCH" in critique:
                        success = True
                    else:
                        print(f"Vision Critique Failed: {critique}")
                        success = False
                except Exception as e:
                    print(f"Vision Error: {e}")
                    success = False
            else:
                # TDD WORKFLOW
                print("🧪 Running Tests...")
                try:
                    self.referee.run_safe("npm test")
                    success = True
                except:
                    success = False

            # 6. Commit or Reset
            if success:
                print("✅ GREEN: Committing...")
                self.referee.run_safe(f"git commit -am 'feat: {task_id}'")
                self.state.update_badge(task_id, "SUCCESS")
            else:
                print("❌ RED: Resetting...")
                self.referee.run_safe("git reset --hard")
                self.state.update_badge(task_id, "FAILED")

        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file)
