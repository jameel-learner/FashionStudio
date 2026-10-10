import queue
import threading
import time

import gradio as gr

from crew import build_crew, has_main_piece, parse_outfit


def render_cards(outfit):
    if not outfit["items"]:
        return "<p>No items were selected.</p>"
    cards = "".join(
        f"<div style='border:1px solid #ccc;padding:10px;margin:6px;width:200px;display:inline-block;vertical-align:top'>"
        f"<b>{p['name']}</b><br>{p['colour']}<br>{p['category']}<br>Rs {p['price']:,}</div>"
        for p in outfit["items"]
    )
    return f"{cards}<h3>Total: Rs {outfit['total']:,}</h3>"


# Must match the agent roles defined in build_crew, in task execution order.
AGENT_ORDER = ["Personal Stylist", "Catalog Curator", "Budget Controller", "Outfit Auditor", "Fashion Copywriter"]

# Typing effect: characters revealed per update, and seconds between updates.
TYPING_CHUNK = 4
TYPING_DELAY = 0.02


def clip(text, limit=600):
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + " ..."


def run(occasion, budget):
    if not occasion or not occasion.strip():
        yield "", "Please describe the occasion.", "", ""
        return

    events = queue.Queue()
    sections = {role: [] for role in AGENT_ORDER}
    flow = []  # verbose log: what each agent did and what it handed to the next one
    task_index = {"i": 0}  # which agent is currently active, by task order

    def current_role():
        return AGENT_ORDER[min(task_index["i"], len(AGENT_ORDER) - 1)]

    def on_step(step):
        role = current_role()
        tool = getattr(step, "tool", None)
        if tool:
            tool_input = getattr(step, "tool_input", "")
            detail = f"[{role}] used tool {tool}\n  input: {clip(tool_input)}"
            result_text = getattr(step, "result", None)
            if result_text:
                detail += f"\n  result: {clip(result_text)}"
            events.put((role, f"called {tool}({tool_input})", detail))
            return
        text = getattr(step, "text", None)
        if text:
            answer = getattr(step, "output", text)
            events.put((role, clip(text, 160), f"[{role}] final answer\n  {clip(answer)}"))

    def on_task(output):
        role = getattr(output, "agent", current_role())
        i = task_index["i"]
        task_index["i"] += 1
        detail = f"[{role}] finished"
        if i + 1 < len(AGENT_ORDER):
            detail = f">>> {role} hands over to {AGENT_ORDER[i + 1]}\n  {clip(getattr(output, 'raw', ''))}"
        events.put((role, "finished", detail))

    def render():
        blocks = []
        for role in AGENT_ORDER:
            lines = sections[role]
            body = "\n".join(f"  - {line}" for line in lines) if lines else "  ..."
            tool_names = tools_by_role.get(role, [])
            tool_line = f"  tools: {', '.join(tool_names)}" if tool_names else "  tools: none"
            blocks.append(f"{role}:\n{tool_line}\n{body}")
        return "\n\n".join(blocks)

    result = {}
    crew = build_crew(occasion, int(budget), step_callback=on_step, task_callback=on_task)
    tools_by_role = {agent.role: [t.name for t in (agent.tools or [])] for agent in crew.agents}

    def work():
        try:
            result["output"] = crew.kickoff()
        except Exception as e:  # show the error in the UI instead of dying silently
            result["error"] = str(e)
        events.put(None)

    threading.Thread(target=work, daemon=True).start()

    yield "", "", render(), ""
    while True:
        item = events.get()
        if item is None:
            break
        role, line, detail = item
        flow.append(detail)
        lines = sections.setdefault(role, [])
        lines.append("")
        # Reveal the line a few characters at a time so the agent looks like it is typing.
        for end in range(TYPING_CHUNK, len(line) + TYPING_CHUNK, TYPING_CHUNK):
            lines[-1] = line[:end]
            yield "", "", render(), "\n\n".join(flow)
            time.sleep(TYPING_DELAY)

    if "error" in result:
        yield "", f"Error: {result['error']}", render(), "\n\n".join(flow)
        return

    outfit = parse_outfit(result["output"].raw)
    note = outfit["note"]
    if not has_main_piece(result["output"], [p["id"] for p in outfit["items"]]):
        note = "**Warning: this outfit has no main piece, only add-ons. Try again.**\n\n" + note
    yield render_cards(outfit), note, render(), "\n\n".join(flow)


with gr.Blocks(title="AI Cohort Fashion Studio") as demo:
    with gr.Row():
        # Left 75%: the app. Right 25%: verbose agent-to-agent messages.
        with gr.Column(scale=3):
            gr.Markdown("# AI Cohort Fashion Studio\nDescribe an occasion and budget. A crew of AI agents builds an outfit from the catalog.")
            occasion = gr.Textbox(label="Occasion", placeholder="Cousin's mehendi on Saturday evening, soft colours, nothing heavy")
            budget = gr.Number(label="Budget (Rs)", value=6000, precision=0)
            go = gr.Button("Style me")
            cards = gr.HTML(label="Outfit")
            note = gr.Markdown()
            steps = gr.Textbox(label="Agent activity", lines=16)
        with gr.Column(scale=1, min_width=250):
            flow_log = gr.Textbox(label="Agent data flow (verbose)", lines=32, max_lines=32, autoscroll=True)
    go.click(run, [occasion, budget], [cards, note, steps, flow_log])

if __name__ == "__main__":
    demo.launch()
