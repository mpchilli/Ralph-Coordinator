import os
import json
import tempfile

class PlanManager:
    def __init__(self, plan_path='plan.md'):
        # Fix: Ensure plan_path is absolute to avoid CWD confusion
        self.plan_path = os.path.abspath(plan_path)

    def load_plan(self):
        if not os.path.exists(self.plan_path):
            return "# Default Plan\n- [ ] Initialize"
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
