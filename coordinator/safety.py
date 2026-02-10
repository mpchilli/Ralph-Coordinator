"""
coordinator/safety.py — The Referee.

Spec-compliant: Enforces allowlists and broadcasts status via Captain's Badge.
"""

import os
import subprocess
import shlex
import time


class Referee:
    """
    The Safety Layer: Enforces allowlists and broadcasts status.
    """

    def __init__(self, allowlist):
        self.allowlist = allowlist
        self.root_dir = os.getcwd()

    def update_badge(self, task_id, status, message):
        """
        Writes the 'Heads-Up Display' badge for VS Code.

        Args:
            task_id: Current task identifier.
            status: One of 'ACTIVE', 'ERROR', 'SUCCESS'.
            message: Human-readable status message.
        """
        badge_path = os.path.join(self.root_dir, ".ralph-status.md")

        icon = "⚪"
        if status == "ACTIVE":
            icon = "🟢"
        if status == "ERROR":
            icon = "🔴"
        if status == "SUCCESS":
            icon = "✅"

        content = f"""
# {icon} Ralph Status: {status}
**Task:** `{task_id}`
**Message:** {message}
**Last Update:** {time.strftime('%H:%M:%S')}

---
*Enable Markdown Preview (Ctrl+Shift+V) to monitor.*
"""
        try:
            with open(badge_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass  # Never crash on status update

    def validate_command(self, cmd_list):
        """Reject commands whose binary is not on the allowlist."""
        if not cmd_list:
            raise ValueError("Empty command")
        binary = cmd_list[0]
        if binary not in self.allowlist:
            if not any(binary.endswith(a) for a in self.allowlist):
                raise ValueError(f"Command '{binary}' blocked by Referee.")

    def run_safe(self, cmd_str):
        """
        Executes a command ONLY if it is in the allowlist.
        """
        cmd_list = shlex.split(cmd_str, posix=False)
        self.validate_command(cmd_list)
        # Check=True raises CalledProcessError on non-zero exit
        subprocess.run(cmd_str, shell=True, check=True)
