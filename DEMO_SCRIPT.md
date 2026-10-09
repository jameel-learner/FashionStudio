# Demo script: first 60 minutes

**Idea in one line:** two layers of agents. The crew inside the app does the shopping work. Claude Code in VS Code then edits that crew live. The audience sees agents doing a job, then an agent changing the agents.

Everything below the "Say" label is a suggested line. Change the wording to your own.

---

## Before the session

### One-time setup (VS Code 1.94.0 or later, Python 3.10 or newer)

1. Unzip the project. In VS Code: **File > Open Folder**, choose `ai-cohort-fashion-studio`.
2. Install the extension: press `Ctrl+Shift+X` (Mac: `Cmd+Shift+X`), search **Claude Code**, click **Install**. Sign in with your Claude account when asked (a paid Claude subscription or a Claude Console account).
3. Open a terminal inside VS Code (**Terminal > New Terminal**) and run:

   Mac/Linux
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
   Windows (PowerShell)
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env
   ```
4. Open `.env` and paste one provider key (OpenAI by default, or the Groq lines for a free key).
5. Run `python app.py`. `Ctrl+click` (Mac: `Cmd+click`) the URL it prints.
6. Open Claude Code: open `crew.py`, then click the **Spark icon** at the top-right of the editor. If you do not see it, click **✻ Claude Code** in the status bar at the bottom right.
7. At the bottom of Claude's prompt box, click the **mode indicator** and pick **Manual**. In Manual mode every edit appears as a side-by-side diff that you accept. If you leave it on Auto, edits happen without the audience seeing them.

### Mock-run checklist (do this once, tonight)

- [ ] Run 1 returns a sensible outfit and a total
- [ ] The "forced correction" run shows `check_budget` more than once in the activity box
- [ ] The "break it" run does not invent a product
- [ ] The Claude Code live edit works end to end, and you know how long it takes
- [ ] `backup/crew_with_trend_advisor.py` copied over `crew.py` still runs
- [ ] Record a 2-minute screen capture of Runs 1 and 2 as a fallback
- [ ] Increase VS Code font size (`Ctrl/Cmd +`) and browser zoom so the back row can read

---

## Run of show

| Time | Segment | AHA moment |
|---|---|---|
| 0-5 | Hook: the real store | "This is a real store." |
| 5-13 | Run 1: the crew builds an outfit | "Nobody told it which products to pick." |
| 13-21 | Run 2: budget forces a correction | "It checked its own work and fixed it." |
| 21-28 | Volunteer run | "It works on my request, not a canned one." |
| 28-33 | Break it | "It cannot make products up." |
| 33-40 | Code tour in VS Code | "An agent is a role, a goal and a tool." |
| 40-55 | Claude Code adds a fifth agent live | "An agent just added an agent." |
| 55-60 | Bridge to the curriculum | "I could build this." |

---

## Step by step

### 1. Hook (0-5 min)

**Do:** Open the Fouzia Design Studio site in a browser tab. Scroll the 8 products. Switch to the app tab (empty).

**Say:** "This is a real boutique store. A shopper has to browse and guess. Let's give it a stylist team that does that for them."

**Point at:** the empty app and the Agent activity box.

### 2. Run 1: the crew builds an outfit (5-13 min)

**Type:**
- Occasion: `Cousin's mehendi on Saturday evening, soft colours, nothing heavy`
- Budget: `6000`
- Click **Style me**.

**While it runs, say:** "Four agents are working. A stylist writes a brief, a curator searches the catalog, a budget controller checks the total, a writer explains the choice. Watch this box."

**Point at:** the activity lines as they appear (tool calls, then each agent finishing).

**Expected:** Blush Wrap Midi Dress + Jhumkas + Potli Bag = Rs 5,600 (the model may choose differently; any real, in-budget outfit is fine).

**AHA #1:** "Nobody told it which products to pick. It searched the catalog and decided."

**Concept shown:** agents that choose tools and act on the result. **Cohort:** Day 9 (AI agents and tools).

### 3. Run 2: the budget forces a correction (13-21 min)

**Type:**
- Occasion: `Reception tonight, I want something rich and traditional`
- Budget: `5000`
- Click **Style me**.

**Say:** "The richest piece in this store costs more than my budget. Watch what the budget controller does."

**Point at:** the activity box. Look for `check_budget` being called, then a search for a cheaper item, then `check_budget` again.

**Expected:** a first choice over Rs 5,000, then a swap to something that fits (for example the Blush Midi Dress with an accessory).

**AHA #2:** "It checked its own work, found it was over, and fixed it."

**If the log shows no correction on your model:** change the budget to `4000` and retry. Say what actually happened; do not claim a self-correction that did not occur.

**Concept shown:** act, observe, adjust. **Cohort:** Day 9-10 (agents and sequential agents).

### 4. Volunteer run (21-28 min)

**Do:** Ask one attendee for an occasion and a budget. Type exactly what they say. Click **Style me**.

**Say:** "Your request, not mine."

**AHA #3:** the result matches something personal.

### 5. Break it (28-33 min)

**Type:**
- Occasion: `Wedding outfit`
- Budget: `1500`
- Click **Style me**.

**Say:** "No formal outfit in this store fits Rs 1,500. Let's see if it makes something up."

**Expected:** an honest answer that nothing formal fits, or a small real outfit. The cards only ever show products from `catalog.json`.

**AHA #4:** "It cannot invent a product, and the total is calculated in code, not guessed."

**Concept shown:** grounding an agent in tools and data. **Cohort:** Day 5-6 (RAG).

### 6. Code tour (33-40 min)

**Do:** In VS Code, open `crew.py` and scroll to the agent definitions. Then open `tools.py`.

**Say:** "Each agent is a role, a goal and a short backstory. The curator has one tool, the budget controller has two. That is the whole idea."

**Point at:**
- `role`, `goal`, `backstory` of one agent
- `tools=[search_catalog]` on the curator
- `search_catalog` in `tools.py`: "This is plain keyword search over a JSON file. In the cohort, this is where retrieval over documents comes in."
- `.env`: "One line, `MODEL=`, switches the provider."

**Do not explain** RAG, LangGraph or prompt engineering. Name the day and move on.

**AHA #5:** "That is only three small files."

### 7. Claude Code adds a fifth agent live (40-55 min)

**Do:**
1. Click into Claude's prompt box. Confirm the mode indicator shows **Manual**.
2. Type this exactly:

   ```
   /plan In crew.py, add a fifth agent called "Trend Advisor" that runs after the Budget Controller and before the Fashion Copywriter. It should give one short styling tip for the occasion, referring only to the items already chosen. Pass the tip to the Copywriter so the final note includes it. Keep the JSON output format unchanged.
   ```
3. The plan opens as a Markdown document in the editor. Read two or three lines aloud. Optionally add an inline comment (for example "keep the tip under 20 words"). Approve the plan when prompted.
4. Edits appear as side-by-side diffs. Walk through one diff, then accept the changes.
5. In the terminal, press `Ctrl+C`, run `python app.py` again, and reload the browser tab.
6. Run Run 1 again. A new `Trend Advisor` line should appear in the activity box, and the note should include a tip.

**Say while Claude works:** "This is a coding agent. It read the project, wrote a plan, and now it is editing the code. I stay in control: I approve the plan and every change."

**AHA #6:** "An agent just added an agent to the app."

**Concept shown:** AI-led coding, plan before acting, human approval. **Cohort:** Day 9 (code-generating agents) and Day 12 (an agent that modifies a project).

**Why it knows the project:** Claude Code reads `CLAUDE.md` in the project root. Open it for 10 seconds: "These are the rules it follows in this project."

**If the edit goes wrong:**
- Hover over your message in Claude's panel and click the rewind button, then choose **Rewind code to here**.
- Or copy the prepared file over the broken one:
  - Mac/Linux: `cp backup/crew_with_trend_advisor.py crew.py`
  - Windows: `copy /Y backup\crew_with_trend_advisor.py crew.py`
  - Then restart `python app.py`. Say: "I prepared a version of this earlier," and keep going.

### 8. Bridge to the curriculum (55-60 min)

**Say:** "What you saw has four layers: prompts, tools, agents, and a coding agent that edits them. In 14 days you build each layer yourself, and you finish with a product of your own. Build something better than this."

**Do:** Switch to the curriculum PDF for the second hour.

**Optional teaser lines:**
- "It forgets the shopper between runs. Memory is Day 11."
- "I cannot see what each run cost. Tracing and cost monitoring are Day 10."

---

## Concepts used in the demo and where they appear in the cohort

| Used in the demo | Where | Cohort day |
|---|---|---|
| Role, goal and backstory prompts per agent | `crew.py` | Day 1: prompt engineering |
| One setting switches OpenAI, Groq or Gemini | `.env` (`MODEL`) | Days 1-2: multi-provider LLM APIs |
| Agents that call tools and decide what to do next | curator, controller | Day 9: AI agents and tools |
| Keyword search over catalog data as a tool | `search_catalog` | Days 5-6: RAG (vector search replaces this) |
| Last agent returns JSON that code parses | `parse_outfit` | Day 10: structured outputs |
| Agents hand work to each other in order | `Process.sequential` | Days 10-11: sequential agents, multi-agent orchestration |
| Web UI | `app.py` | Days 2-3: Gradio |
| Claude Code plans, edits and the human approves | VS Code | Day 9: code-generating agents; Day 12: agent that modifies projects |
| Not shown: cost and tracing | none | Day 10: LangSmith; Day 4: Langfuse |
| Not shown: memory across runs | none | Day 11: agent memory |

---

## If something breaks on stage

| What you see | Do this |
|---|---|
| Red "Error: ..." in the app | Check the key in `.env`, restart `python app.py` |
| Note appears but no outfit cards | The model replied without JSON. Click **Style me** again |
| Run is slow | Set `MODEL` to a smaller model in `.env` and restart |
| Claude Code edit fails or looks wrong | Rewind code, or copy the backup file (see section 7) |
| Everything fails | Play the screen recording of Runs 1 and 2 and move to the code tour |
