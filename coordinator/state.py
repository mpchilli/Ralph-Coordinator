import os
import json
import tempfile
from .llm import generate

class PlanManager:
    def __init__(self, plan_path='plan.md'):
        # Ensure absolute path resolution
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.plan_path = os.path.join(self.root_dir, 'plan.md')

    def load_plan(self):
        if not os.path.exists(self.plan_path):
            return None # Signal that we need initialization
        with open(self.plan_path, 'r', encoding='utf-8') as f:
            return f.read()

    def initialize_from_intent(self, user_intent):
        """The Architect Phase: Converts intent to Plan."""
        print(f"🏛️ Architecting plan for: {user_intent}")
        
        # 1. Generate PRD
        prd_prompt = f"Act as a Product Owner. Create a concise PRD for: {user_intent}"
        prd = generate(prd_prompt, role="architect")
        with open(os.path.join(self.root_dir, 'PRD.md'), 'w', encoding='utf-8') as f:
            f.write(prd)
            
        # 2. Generate Tech Stack
        arch_prompt = f"Act as a Tech Lead. Based on this PRD, define the stack (ARCHITECTURE.md): \n{prd}"
        arch = generate(arch_prompt, role="architect")
        with open(os.path.join(self.root_dir, 'ARCHITECTURE.md'), 'w', encoding='utf-8') as f:
            f.write(arch)

        # 3. Generate Checkbox Plan
        plan_prompt = f"Convert this PRD into a strict Markdown Checklist (plan.md). Use '- [ ] TaskName' format. \n{prd}"
        plan = generate(plan_prompt, role="architect")
        
        self.save_snapshot(plan)
        return plan

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

    def update_badge(self, task_id, status="ACTIVE"):
        """Updates the Captain's Badge (.ralph-status.md)"""
        badge_path = os.path.join(self.root_dir, '.ralph-status.md')
        content = f"""# 🛡️ Ralph Captain's Badge
**Task:** `{task_id}`
**Status:** {status}
**Mode:** Hybrid (Python/Node)
"""
        with open(badge_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def update_dashboard(self, status):
        # Writes to the frontend public folder
        dashboard_path = os.path.join(self.root_dir, 'src', 'frontend', 'public', 'dashboard_state.json')
        os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
