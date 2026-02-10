"""
coordinator/state.py — State Manager for Ralph-Coordinator.

Manages plan.md (the crash-proof database), project initialization,
and dashboard state synchronization.
"""

import os
import re
import json
import tempfile


class PlanManager:
    """
    Reads, writes, and tracks progress in plan.md.
    Also handles project initialization (Architect Phase).
    """

    def __init__(self, plan_path="plan.md"):
        self.plan_path = os.path.abspath(plan_path)
        self._project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    # ── Plan I/O ──────────────────────────────────────────────────────

    def load_plan(self):
        """Load plan.md contents. Returns a default stub if file is missing."""
        if not os.path.exists(self.plan_path):
            return "# Plan\n- [ ] Initialize project"
        with open(self.plan_path, "r", encoding="utf-8") as f:
            return f.read()

    def save_plan(self, content):
        """Atomically save content to plan.md (crash-safe write)."""
        dir_name = os.path.dirname(self.plan_path) or "."
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=dir_name, suffix=".md", encoding="utf-8"
        ) as tf:
            tf.write(content)
            temp_name = tf.name
        try:
            os.replace(temp_name, self.plan_path)
        except OSError:
            os.remove(temp_name)
            raise

    # ── Task Parsing ──────────────────────────────────────────────────

    def get_next_task(self):
        """
        Scan plan.md for the first unchecked task (- [ ]).

        Returns:
            A dict with 'line_number', 'text', and 'tags' (e.g. ['UI']),
            or None if all tasks are complete.
        """
        plan = self.load_plan()
        pattern = re.compile(r"^(\s*)-\s*\[ \]\s*(.+)$", re.MULTILINE)

        for i, line in enumerate(plan.splitlines(), start=1):
            m = pattern.match(line)
            if m:
                text = m.group(2).strip()
                # Extract tags like [UI], [Test], [Backend]
                tags = re.findall(r"\[([A-Za-z]+)\]", text)
                return {"line_number": i, "text": text, "tags": tags}
        return None

    def mark_task_done(self, line_number):
        """Check off a task at the given line number: [ ] -> [x]."""
        plan = self.load_plan()
        lines = plan.splitlines()
        if 1 <= line_number <= len(lines):
            lines[line_number - 1] = lines[line_number - 1].replace(
                "- [ ]", "- [x]", 1
            )
            self.save_plan("\n".join(lines) + "\n")

    def count_progress(self):
        """Return (done, total) task counts."""
        plan = self.load_plan()
        done = len(re.findall(r"-\s*\[x\]", plan, re.IGNORECASE))
        total = done + len(re.findall(r"-\s*\[ \]", plan))
        return done, total

    # ── Project Initialization (Architect Phase) ──────────────────────

    def initialize_project(self, user_intent):
        """
        Phase 1: The Architect.

        Takes a raw user intent string and generates:
        - PRD.md
        - ARCHITECTURE.md
        - plan.md (checklist derived from the PRD)

        Requires coordinator.llm to be functional.
        """
        from .llm import generate_with_planner

        # 1. Generate PRD
        prd_prompt = (
            "You are a Senior Product Owner. Given the following user intent, "
            "generate a comprehensive Product Requirements Document (PRD) in Markdown.\n\n"
            "Include: Objective, Scope, Functional Requirements (numbered), "
            "Non-Functional Requirements, Constraints, and Acceptance Criteria.\n\n"
            f"User Intent: {user_intent}\n\n"
            "Output ONLY the PRD markdown, no commentary."
        )
        prd_content = generate_with_planner(prd_prompt)
        prd_path = os.path.join(self._project_root, "PRD.md")
        with open(prd_path, "w", encoding="utf-8") as f:
            f.write(prd_content)

        # 2. Generate Architecture
        arch_prompt = (
            "You are a Senior Solutions Architect. Given the following PRD, "
            "generate an Architecture Document in Markdown.\n\n"
            "Include: Tech Stack, Directory Structure, Component Diagram (Mermaid), "
            "Data Flow, API Contracts, and Deployment Strategy.\n\n"
            f"PRD:\n{prd_content}\n\n"
            "Output ONLY the Architecture markdown, no commentary."
        )
        arch_content = generate_with_planner(arch_prompt)
        arch_path = os.path.join(self._project_root, "ARCHITECTURE.md")
        with open(arch_path, "w", encoding="utf-8") as f:
            f.write(arch_content)

        # 3. Generate plan.md (Checklist)
        plan_prompt = (
            "You are a Tech Lead. Given the following PRD and Architecture, "
            "produce a Markdown checklist of discrete, testable implementation tasks.\n\n"
            "Rules:\n"
            "- Each task must be one line: `- [ ] [Tag] Description`\n"
            "- Tags: [Setup], [Backend], [Frontend], [UI], [Test], [Docs]\n"
            "- Order tasks by dependency (setup first, tests last)\n"
            "- Keep each task small enough to complete in one coding session\n\n"
            f"PRD:\n{prd_content}\n\n"
            f"Architecture:\n{arch_content}\n\n"
            "Output ONLY the checklist markdown starting with `# Plan`, no commentary."
        )
        plan_content = generate_with_planner(plan_prompt)
        self.save_plan(plan_content)

        return {"prd": prd_path, "architecture": arch_path, "plan": self.plan_path}

    # ── Dashboard Sync ────────────────────────────────────────────────

    def update_dashboard(self, status):
        """Write status dict to dashboard_state.json for the Electron UI."""
        dashboard_path = os.path.join(self._project_root, "dashboard_state.json")
        os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)
        with open(dashboard_path, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
