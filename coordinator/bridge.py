import os
import sys
import time
import argparse

# Path injection
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from coordinator.loop import MicroRatchet
from coordinator.state import PlanManager

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", help="Initialize project with a prompt", type=str)
    parser.add_argument("--task", help="Run a specific task ID", type=str)
    args = parser.parse_args()

    # MODE A: ARCHITECT (Initialize Plan)
    if args.init:
        print(f"🚀 Initializing Project: {args.init}")
        planner = PlanManager()
        planner.initialize_from_intent(args.init)
        print("✅ Initialization Complete. Plan generated.")
        return

    # MODE B: LOOP (Run Ratchet)
    ratchet = MicroRatchet()
    
    # If task provided via CLI
    if args.task:
        ratchet.run_cycle(args.task)
        return

    # Default: Bridge Mode (Watch for file trigger)
    print("🌉 Bridge started. Waiting for 'start_trigger' file...")
    while True:
        if os.path.exists("start_trigger"):
            try:
                with open("start_trigger", "r") as f:
                    task_id = f.read().strip()
                print(f"⚡ Trigger detected for: {task_id}")
                ratchet.run_cycle(task_id or "next_task")
            finally:
                if os.path.exists("start_trigger"):
                    os.remove("start_trigger")
        time.sleep(1)

if __name__ == "__main__":
    main()
