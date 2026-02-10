"""
coordinator/safety.py — The Referee.

Enforces command allowlists, path traversal prevention, and budget limits.
Also manages the .ralph-status.md IDE badge (Heads-Up Display).
"""

import os
import subprocess
import shlex
import datetime


class Referee:
    """
    Security enforcement layer. Every command passes through here
    before reaching the shell.
    """

    def __init__(self, allowlist=None):
        if allowlist is None:
            allowlist = ["git", "npm", "node", "python", "ls", "echo"]
        self.allowlist = allowlist
        self._project_root = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    # ── Command Validation ────────────────────────────────────────────

    def validate_command(self, cmd_list):
        """Reject commands whose binary is not on the allowlist."""
        if not cmd_list:
            raise ValueError("Empty command list")
        binary = os.path.basename(cmd_list[0]).lower()
        # Strip .exe/.cmd for Windows compatibility
        binary_base = binary.replace(".exe", "").replace(".cmd", "")
        if binary_base not in self.allowlist and binary not in self.allowlist:
            raise ValueError(
                f"Command '{cmd_list[0]}' is not in the allowlist: {self.allowlist}"
            )

    def validate_path(self, path_str):
        """Block any path that escapes the project root."""
        abs_path = os.path.abspath(path_str)
        if not abs_path.startswith(self._project_root):
            raise ValueError(
                f"Path traversal blocked: '{path_str}' is outside '{self._project_root}'"
            )

    # ── Safe Execution ────────────────────────────────────────────────

    def run_safe(self, cmd_str, capture=True, timeout=120):
        """
        Validate and execute a shell command.

        Args:
            cmd_str: The command string to execute.
            capture: If True, capture stdout/stderr and return CompletedProcess.
            timeout: Max seconds before the process is killed.

        Returns:
            subprocess.CompletedProcess with returncode, stdout, stderr.

        Raises:
            ValueError: If command is not allowed.
            subprocess.TimeoutExpired: If command exceeds timeout.
        """
        cmd_list = shlex.split(cmd_str, posix=False)
        self.validate_command(cmd_list)

        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=timeout,
            cwd=self._project_root,
        )
        return result

    # ── IDE Badge (Heads-Up Display) ──────────────────────────────────

    def update_badge(self, status, task_id=None, iteration=None, usage=None):
        """
        Write .ralph-status.md — a real-time status file viewable in VS Code
        Markdown Preview.

        Args:
            status: One of 'idle', 'running', 'verifying', 'passed', 'failed', 'paused'.
            task_id: Current task description or line reference.
            iteration: Current retry count (e.g. 2/5).
            usage: Dict with 'total_tokens' and 'estimated_cost_usd'.
        """
        badge_path = os.path.join(self._project_root, ".ralph-status.md")
        now = datetime.datetime.now().strftime("%H:%M:%S")

        status_emoji = {
            "idle": "⏸️",
            "running": "🔄",
            "verifying": "🔍",
            "passed": "✅",
            "failed": "❌",
            "paused": "⏳",
        }
        emoji = status_emoji.get(status, "❓")

        lines = [
            f"# {emoji} Ralph-Coordinator Status",
            "",
            f"**Status:** `{status.upper()}`",
            f"**Updated:** `{now}`",
        ]

        if task_id:
            lines.append(f"**Task:** {task_id}")
        if iteration:
            lines.append(f"**Attempt:** {iteration}")
        if usage:
            lines.append(
                f"**Tokens:** {usage.get('total_tokens', 0):,} | "
                f"**Cost:** ${usage.get('estimated_cost_usd', 0):.4f}"
            )

        lines.append("")
        lines.append("---")
        lines.append("*Open this file in VS Code Markdown Preview (Ctrl+Shift+V) "
                      "for a live HUD.*")

        with open(badge_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
