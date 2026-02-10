# Ralph-Coordinator User Guide (v1.1)

**Welcome to the Ralph-Coordinator.**

This system is a **Hybrid Consolidator** that implements the "Frankenstein" architecture—combining the best features of five AI workflows into a "Software Factory."

---

## 1. Theory of Operation

We have cherry-picked the specific architectural breakthroughs from each predecessor:

| Source | Breakthrough | Why? |
| :--- | :--- | :--- |
| **BMAD-METHOD** | **Architect's Brain** | Solves the "Blank Page Problem" with high-fidelity PRDs/Specs. |
| **Conductor** | **System of Record** | Uses `plan.md` as a crash-proof database. |
| **Ralph-Orchestrator**| **Managed Runtime** | Persona-based "Hats" and Node.js Dashboard visualization. |
| **Ralph-Loop** | **Micro-Ratchet** | Atomic `Code -> Test -> Commit` loop. |
| **Commander** | **Auto-Approval** | Replaces human confirmation with automated test verification. |

---

## 2. The Core Workflow: The "Captain" Method ⚓

### Step 0: The "Handshake" (Architect Phase)
**Logic:** `state.PlanManager().initialize_project(intent)`
1.  Provide a raw goal (e.g., "Build a dashboard").
2.  Ralph generates `PRD.md` (What), `ARCHITECTURE.md` (How), and `plan.md` (Tasks).

### Step 1: The Plan (State Persistence)
**File:** `plan.md`
*   **Database:** This file tracks every task.
*   **Resume:** Run `npm start`. Ralph scans for the first `[ ]` and continues.

### Step 2: The Micro-Ratchet (Execution)
**Logic:** `coordinator/loop.py`
1.  **Lock:** Acquires `coordinator.lock` for process safety.
2.  **Hat Selection:** Parses task tags (e.g., `[Backend]`, `[UI]`) to load role-specific system prompts.
3.  **Verify:** Runs `npm test` (or vision analysis for UI).
    *   **PASS:** Git commit and check `[x]` in `plan.md`.
    *   **FAIL:** Reverts (`git reset --hard`) and retries up to 5 times.

### Step 3: Steering (Captain Consultation) 🧭
**File:** `.ralph-captain-response.md`
If Ralph fails multiple retries or hits ambiguity, he will pause and write a prompt to `.ralph-captain-prompt.md`. 
*   **Action:** Write your instructions in `.ralph-captain-response.md` and save.
*   **Result:** Ralph reads your guidance and applies it to the next retry.

### Step 4: Visibility (HUD & Dashboard) 🛡️
1.  **The Badge:** Open `.ralph-status.md` in VS Code Markdown Preview for a live Heads-Up Display of tokens, cost, and task status.
2.  **The Dashboard:** Launch the Electron app for the full multi-process monitor.

---

## 3. The "Designer" Workflow (Vision Mode) 🎨

**Trigger:** Add the **`[UI]`** tag to a task in `plan.md`.

### Behavior
1.  **Execution:** Agent writes CSS/React code.
2.  **Vision Loop:**
    *   Launches Playwright headless.
    *   Captures a full-page screenshot to `.ralph/screenshots/`.
    *   Calls the **Vision Model** (`gemini-2.0-flash-exp`) to compare the render against the task description.
3.  **Judgment:** Only commits if the visual review results in a `PASS`.

---

## 4. Setup & Operations

### Prerequisites
*   Node.js v20+, Python 3.10+, Git, Playwright (`playwright install`).

### Commands
| Goal | Command |
| :--- | :--- |
| **Start Everything** | `npm start` |
| **Inject Brain** | `python upgrade_ralph.py` |
| **Hydrate Env** | `pip install -r requirements.txt` |
| **Legacy Tools** | `npm run legacy -- <args>` |

---

## 5. System Architecture for Builders 🧬

### File Tree
*   **`coordinator/`**: The Python Core.
    *   `llm.py`: API Client (Text/Vision) + Budget tracking.
    *   `loop.py`: Micro-Ratchet Engine & Hat Selection.
    *   `safety.py`: The Referee & IDE Badge generator.
    *   `state.py`: Plan parser & Architect Phase logic.
*   **`templates/roles/`**: Markdown-based system prompts for Personas.
*   **`PRD.md` / `ARCHITECTURE.md`**: Derived sources of truth.

### Data Flow
`User Intent` → `Architect` → `plan.md` → `Developer/Designer` → `Referee (Tests/Vision)` → `Git Commit` → `IDE Badge/Dashboard`.

---
*"Ship working code while you sleep."*
