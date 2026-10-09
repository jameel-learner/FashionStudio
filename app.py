import queue
import threading

import gradio as gr

from crew import build_crew, parse_outfit


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
AGENT_ORDER = ["Personal Stylist", "Catalog Curator", "Budget Controller", "Fashion Copywriter"]


def run(occasion, budget):
    if not occasion or not occasion.strip():
        yield "", "Please describe the occasion.", ""
        return

    events = queue.Queue()
    sections = {role: [] for role in AGENT_ORDER}
    task_index = {"i": 0}  # which agent is currently active, by task order

    def current_role():
        return AGENT_ORDER[min(task_index["i"], len(AGENT_ORDER) - 1)]

    def on_step(step):
        tool = getattr(step, "tool", None)
        if tool:
            events.put((current_role(), f"called {tool}({getattr(step, 'tool_input', '')})"))
            return
        text = getattr(step, "text", None)
        if text:
            snippet = " ".join(str(text).split())[:160]
            events.put((current_role(), snippet))

    def on_task(output):
        role = getattr(output, "agent", current_role())
        events.put((role, "finished"))
        task_index["i"] += 1

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

    yield "", "", render()
    while True:
        item = events.get()
        if item is None:
            break
        role, line = item
        sections.setdefault(role, []).append(line)
        yield "", "", render()

    if "error" in result:
        yield "", f"Error: {result['error']}", render()
        return

    outfit = parse_outfit(result["output"].raw)
    yield render_cards(outfit), outfit["note"], render()


with gr.Blocks(title="AI Cohort Fashion Studio") as demo:
    gr.Markdown("# AI Cohort Fashion Studio\nDescribe an occasion and budget. A crew of AI agents builds an outfit from the catalog.")
    occasion = gr.Textbox(label="Occasion", placeholder="Cousin's mehendi on Saturday evening, soft colours, nothing heavy")
    budget = gr.Number(label="Budget (Rs)", value=6000, precision=0)
    go = gr.Button("Style me")
    cards = gr.HTML(label="Outfit")
    note = gr.Markdown()
    steps = gr.Textbox(label="Agent activity", lines=16)
    go.click(run, [occasion, budget], [cards, note, steps])

if __name__ == "__main__":
    demo.launch()
