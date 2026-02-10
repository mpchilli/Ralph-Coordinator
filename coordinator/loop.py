import os
import time
# Fix: Use relative imports for intra-package dependencies
from .safety import Referee
from .state import PlanManager

# Stub for LLM
class LLMStub:
    def generate(self, prompt):
        return "echo 'Hello World'"

class MicroRatchet:
    """
    The core execution loop (The Micro-Ratchet).
    """
    def __init__(self):
        self.referee = Referee(["git", "npm", "ls", "echo"])
        self.state = PlanManager()
        self.llm = LLMStub()

    def run_cycle(self, task_id):
        # 1. Lock
        lock_file = 'coordinator.lock'
        if os.path.exists(lock_file):
            print("Locked. Skipping cycle.")
            return
        
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))

        try:
            # 2. Plan
            plan = self.state.load_plan()
            print(f"Loaded plan for task {task_id}")

            # 3. Generate
            command = self.llm.generate(f"Generate command for {task_id}")
            print(f"Generated command: {command}")

            # 4. Verify
            try:
                self.referee.run_safe("npm test") 
            except Exception as e:
                print(f"Verification failed: {e}")
                return

            # 5. Commit/Revert
            success = True 
            
            if success:
                self.referee.run_safe("git commit -m 'Auto-commit'")
            else:
                self.referee.run_safe("git reset --hard")

        finally:
            if os.path.exists(lock_file):
                os.remove(lock_file)
