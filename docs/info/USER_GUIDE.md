# Ralph-Coordinator User Guide (v1.0)

**Welcome to the Ralph-Coordinator.**

This system is a **Hybrid Consolidator** that implements the "Frankenstein" architecture described in the [Historic Analysis](file:///c:/Users/ukchim01/Downloads/Ai%20Tools/Ralph-Coordinator/docs/prompts/00_prior_conversation_history.md). It combines the best features of five different AI workflows into a "Software Factory."

---

## 1. Theory of Operation (The "Frankenstein" Architecture)

We have cherry-picked the specific architectural breakthroughs from each predecessor:

| Source | Feature Adopted | Why? |
| :--- | :--- | :--- |
| **BMAD-METHOD** | **The "Architect's Brain"** | Solves the "Blank Page Problem" by forcing a high-fidelity PRD/Spec before coding. |
| **Conductor** | **The "System of Record"** | Uses `plan.md` as a crash-proof database. If the system dies, it resumes from the last unchecked box. |
| **Ralph-Orchestrator** | **The "Managed Runtime"** | Uses "Hats" (Personas) and a Node.js Dashboard to manage the lifecycle and visualization. |
| **Ralph-Loop** | **The "Micro-Ratchet"** | The `while(true)` loop that commits *only* on green tests (`Code -> Test -> Commit` or `Reset`). |
| **Commander** | **The "Auto-Approval"** | Replaces human "OK" clicks with automated test verification for velocity. |

---

## 2. The Core Workflow: The "Captain" Method ⚓

### Step 0: The "Handshake" (Input Fidelity)
**Context:** Generate your specifications using a high-level reasoning model or BMAD.
1.  Save `PRD.md` and `ARCHITECTURE.md` in the root.
2.  Ralph reads these to ground its "Planner Hat".

### Step 1: The Plan (State Persistence)
**Context:** The Coordinator parses your input into a **`plan.md`** checklist.
*   **Behavior:** This file is the **Database**.
*   **Pause/Resume:** Kill the terminal to pause. Run `npm start` to resume from the first `[ ]`.

### Step 2: The Micro-Ratchet (Execution)
**Context:** The **Python Coordinator** (`coordinator/loop.py`) operates the feedback loop:
1.  **Lock:** Acquires `coordinator.lock`.
2.  **Generate:** The "Builder Hat" writes code.
3.  **Verify:** The "Referee" runs the gatekeeper command (e.g., `npm test`).
    *   **PASS:** Triggers **Auto-Approval**. (`git commit`, check `[x]`).
    *   **FAIL:** Triggers **Self-Correction**. (Feed error -> Retry -> `git reset` if stuck).

### Step 3: Visibility (The Captain's Badge) 🛡️
**Context:** Real-time monitoring without switching windows.
1.  Open `.ralph-status.md` in VS Code.
2.  Toggle **Markdown Preview** (`Ctrl+Shift+V`).
3.  **Heads-Up Display:** This file updates in real-time with the current Loop Status, Token Usage, and Task ID.

### Step 4: Visualizing (The Dashboard)
**Context:** Deep inspection.
*   The **Electron App** is the primary visualizer.
*   It polls `dashboard_state.json` to show live logs and "Hat" state.

---

## 3. The "Designer" Workflow (UI/UX Mode) 🎨

**Context:** Ralph isn't just a coder; he is a designer with vision capabilities.

### Triggers
Add a task with the **`[UI]`** tag in your `plan.md`:
```markdown
- [ ] [UI] Style the login button with a glassmorphism effect
```

### Behavior
1.  **Hat Switch:** The Agent switches to the **Designer Hat**.
2.  **Visual Feedback Loop:**
    *   Writes CSS/React code.
    *   Launches the app locally via Playwright.
    *   **Takes a Screenshot.**
    *   Compares the screenshot to the request using the `vision` model (Gemini Pro Vision).
3.  **Commit:** Only commits if the visual diff matches the "Premium Aesthetic" requirements.

---

## 4. Installation & Startup

### Prerequisites
*   **Node.js v20+**
*   **Python 3.10+** (Added to PATH)
*   **Playwright:** `playwright install`

### Bootstrap Sequence
1.  **Inject the Brain:** `python upgrade_ralph.py`
2.  **Hydrate:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Awaken:**
    ```bash
    npm install
    npm start  # Runs Backend + Frontend + Electron
    ```

**Note:** The `ralph` command in the terminal now talks directly to the **Python Bridge**. Legacy Node.js commands (like `hats`) are accessed via the Dashboard or `npm run Ralph:legacy`.

---

## 5. Configuration

### `coordinator/config.yaml` (The Brain) 🧠
Controls Intelligence and Safety.

```yaml
system:
  mode: "hybrid"
  budget_max_usd: 5.00

models:
  planner: "gemini-2.0-pro-exp-02-05"    # Architect
  executor: "gemini-2.5-flash-preview-09-25" # Builder
  vision: "gemini-2.0-flash-exp"         # Designer

security:
  allowlist: ["git", "npm", "node", "python", "ls"]
```

---

## 6. System Architecture for Builders 🧬

For AIs replicating this system, here is the spec:

### File Tree
*   **`coordinator/`**: The Python Brain.
    *   `loop.py`: The Main Event Loop (Micro-Ratchet).
    *   `safety.py`: The Referee (Path/Command validation).
    *   `state.py`: The State Manager (update `plan.md` & `dashboard_state.json`).
*   **`templates/`**: The Skills & Roles.
    *   `roles/*.md`: Persona definitions (Architect, Developer, Designer).
*   **`dist/`**: Compiled Electron/React assets.

### Data Flow
1.  **Read:** `loop.py` reads `plan.md` (Objective).
2.  **Think:** Sends context to Gemini.
3.  **Act:** Executes command via `safety.py`.
4.  **Write:**
    *   Updates `plan.md` (Progress).
    *   Updates `.ralph-status.md` (Badge).
    *   Updates `dashboard_state.json` (UI).
5.  **Render:** Electron reads JSON and updates the progress bar.

---
*"Ship working code while you sleep."*
