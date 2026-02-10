import os
import subprocess
import shlex

class Referee:
    """
    Enforces security policies for command execution and file access.
    """
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
