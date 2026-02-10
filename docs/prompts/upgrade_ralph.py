import os
import sys
import shutil
import subprocess

def main():
    """
    Main execution function for upgrading Ralph Orchestrator.
    Injects the Python backend (Coordinator) into the existing Electron frontend.
    """
    print("Starting Ralph Orchestrator Upgrade...")

    # 1. Validation
    target_repo = os.path.join(os.getcwd(), 'ralph-orchestrator')
    package_json = os.path.join(target_repo, 'package.json')

    if not os.path.exists(package_json):
        print(f"Error: Target repo not found at {target_repo}")
        sys.exit(1)
    
    print(f"Target repository found: {target_repo}")

    # 2. Safety Backup
    src_backend = os.path.join(target_repo, 'src', 'backend')
    backup_backend = os.path.join(target_repo, '_backup_backend')

    if os.path.exists(src_backend):
        print(f"Backing up {src_backend} to {backup_backend}...")
        if os.path.exists(backup_backend):
            shutil.rmtree(backup_backend)
        shutil.copytree(src_backend, backup_backend)
    else:
        print(f"Warning: {src_backend} does not exist. Skipping backup.")

    # 3. Dependency Injection
    requirements_path = os.path.join(target_repo, 'requirements.txt')
    requirements_content = (
        "google-generativeai\n"
        "playwright\n"
        "pyyaml\n"
        "colorama\n"
    )
    
    print(f"Creating {requirements_path}...")
    with open(requirements_path, 'w', encoding='utf-8') as f:
        f.write(requirements_content)

    # 4. Module Injection
    coordinator_dir = os.path.join(target_repo, 'coordinator')
    if not os.path.exists(coordinator_dir):
        os.makedirs(coordinator_dir)
        print(f"Created directory: {coordinator_dir}")

    # 4.1 __init__.py
    init_file = os.path.join(coordinator_dir, '__init__.py')
    with open(init_file, 'w', encoding='utf-8') as f:
        pass # Empty marker file

    # 4.2 config.yaml
    config_file = os.path.join(coordinator_dir, 'config.yaml')
    config_content = """system:
  mode: "hybrid"
  budget_max_usd: 5.00
models:
  planner: "gemini-2.0-pro-exp-02-05"
  executor: "gemini-2.5-flash-preview-09-25"
  vision: "gemini-2.0-flash-exp" # For Designer Hat
security:
  allowlist: ["git", "npm", "node", "python", "ls", "echo", "mkdir", "npx"]
"""
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(config_content)
    print(f"Created {config_file}")

    # 4.3 safety.py
    safety_file = os.path.join(coordinator_dir, 'safety.py')
    safety_content = """import os
import subprocess
import shlex

class Referee:
    \"\"\"
    Enforces security policies for command execution and file access.
    \"\"\"
    def __init__(self, allowlist):
        self.allowlist = allowlist

    def validate_command(self, cmd_list):
        if not cmd_list:
            raise ValueError("Empty command list")
        binary = cmd_list[0]
        if binary not in self.allowlist:
            if not any(binary.endswith(allowed) for allowed in self.allowlist):
                raise ValueError(f"Command '{binary}' is not allowed.")

    def validate_path(self, path_str):
        abs_path = os.path.abspath(path_str)
        cwd = os.getcwd()
        if not abs_path.startswith(cwd):
            raise ValueError(f"Path traversal detected: {path_str} is outside {cwd}")

    def run_safe(self, cmd_str):
        cmd_list = shlex.split(cmd_str, posix=False) 
        self.validate_command(cmd_list)
        # Check=True ensures we catch failures (non-zero exit codes)
        subprocess.run(cmd_str, shell=True, check=True)
"""
    with open(safety_file, 'w', encoding='utf-8') as f:
        f.write(safety_content)
    print(f"Created {safety_file}")

    # 4.4 state.py
    state_file = os.path.join(coordinator_dir, 'state.py')
    state_content = """import os
import json
import tempfile

class PlanManager:
    def __init__(self, plan_path='plan.md'):
        # Fix: Ensure plan_path is absolute to avoid CWD confusion
        self.plan_path = os.path.abspath(plan_path)

    def load_plan(self):
        if not os.path.exists(self.plan_path):
            return "# Default Plan\\n- [ ] Initialize"
        with open(self.plan_path, 'r', encoding='utf-8') as f:
            return f.read()

    def save_snapshot(self, content):
        dir_name = os.path.dirname(self.plan_path)
        with tempfile.NamedTemporaryFile('w', delete=False, dir=dir_name, encoding='utf-8') as tf:
            tf.write(content)
            temp_name = tf.name
        try:
            os.replace(temp_name, self.plan_path)
        except OSError:
            os.remove(temp_name)
            raise

    def update_dashboard(self, status):
        # Fix: Resolve project root dynamically based on this file's location
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dashboard_path = os.path.join(base_dir, 'src', 'frontend', 'public', 'dashboard_state.json')
        
        os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
"""
    with open(state_file, 'w', encoding='utf-8') as f:
        f.write(state_content)
    print(f"Created {state_file}")

    # 4.5 loop.py
    loop_file = os.path.join(coordinator_dir, 'loop.py')
    loop_content = """import os
import time
# Fix: Use relative imports for intra-package dependencies
from .safety import Referee
from .state import PlanManager

# Stub for LLM
class LLMStub:
    def generate(self, prompt):
        return "echo 'Hello World'"

class MicroRatchet:
    \"\"\"
    The core execution loop (The Micro-Ratchet).
    \"\"\"
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
"""
    with open(loop_file, 'w', encoding='utf-8') as f:
        f.write(loop_content)
    print(f"Created {loop_file}")

    # 4.6 bridge.py
    bridge_file = os.path.join(coordinator_dir, 'bridge.py')
    bridge_content = """import os
import sys
import time

# Fix: Add parent directory to sys.path to allow 'coordinator' module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from coordinator.loop import MicroRatchet

def main():
    \"\"\"
    Starts the bridge loop, listening for start signals.
    \"\"\"
    ratchet = MicroRatchet()
    print("Bridge started. Waiting for trigger...")
    
    while True:
        if os.path.exists("start_trigger"):
            print("Trigger detected!")
            ratchet.run_cycle("task-001")
            os.remove("start_trigger")
        
        time.sleep(1)

if __name__ == "__main__":
    main()
"""
    with open(bridge_file, 'w', encoding='utf-8') as f:
        f.write(bridge_content)
    print(f"Created {bridge_file}")

    print("Upgrade script completed successfully.")

if __name__ == "__main__":
    main()

