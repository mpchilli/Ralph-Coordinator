import os
import sys
import json
import time

# Fix: Add parent directory to sys.path to allow 'coordinator' module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from coordinator.loop import MicroRatchet


def handle_loops(args):
    """
    Handle 'loops' subcommands.
    These are no-ops for now since the Python coordinator doesn't use
    worktree-based parallel loops yet, but returning success (exit 0)
    prevents the LoopsManager from error-spamming.
    """
    if not args:
        print("Usage: ralph loops <process|list|prune|retry|discard|stop|merge>")
        sys.exit(1)

    subcommand = args[0]

    if subcommand == "process":
        # No-op: merge queue processing not needed yet
        pass
    elif subcommand == "list":
        # Return empty JSON array (no active loops)
        if "--json" in args:
            print(json.dumps([]))
        else:
            print("No active loops.")
    elif subcommand == "prune":
        # No-op: nothing to prune
        pass
    elif subcommand in ("retry", "discard", "stop", "merge", "merge-button-state"):
        # These require a loop ID; no-op for now
        if len(args) < 2:
            print(f"Usage: ralph loops {subcommand} <loop-id>", file=sys.stderr)
            sys.exit(1)
        if subcommand == "merge-button-state":
            print(json.dumps({"state": "blocked", "reason": "Loops not yet implemented in Python coordinator"}))
        # Otherwise no-op success
    else:
        print(f"Unknown loops subcommand: {subcommand}", file=sys.stderr)
        sys.exit(1)


def handle_run(args):
    """
    Handle 'run' subcommand — starts the MicroRatchet for a single cycle.
    """
    ratchet = MicroRatchet()
    ratchet.run_cycle("task-from-server")


def handle_bridge():
    """
    Legacy bridge mode: listen for start_trigger file.
    """
    ratchet = MicroRatchet()
    print("Bridge started. Waiting for trigger...")

    while True:
        if os.path.exists("start_trigger"):
            print("Trigger detected!")
            ratchet.run_cycle("task-001")
            os.remove("start_trigger")

        time.sleep(1)


def main():
    """
    CLI entrypoint — drop-in replacement for the Rust 'ralph' binary.
    Routes subcommands to the appropriate handler.
    """
    args = sys.argv[1:]

    if not args:
        # No subcommand: fall back to legacy bridge mode
        handle_bridge()
        return

    command = args[0]

    if command == "loops":
        handle_loops(args[1:])
    elif command == "run":
        handle_run(args[1:])
    elif command == "--version":
        print("ralph-coordinator 0.1.0 (Python bridge)")
    elif command == "--help":
        print("ralph-coordinator: Python bridge for ralph-orchestrator")
        print("Usage: ralph <command> [args...]")
        print("")
        print("Commands:")
        print("  loops    Manage parallel execution loops")
        print("  run      Execute a task cycle")
        print("  --version  Show version info")
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
