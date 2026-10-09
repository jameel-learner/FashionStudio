# AI Cohort Fashion Studio

A small CrewAI app used as a live demo. A crew of agents builds an outfit from a boutique catalog and checks it against the shopper's budget. The UI is Gradio.

## Run

```
python app.py
```

Opens at http://127.0.0.1:7860. Needs a provider key in `.env` (see `.env.example`).

## Layout

- `catalog.json`: the products (id, name, price, category, colour, occasions, vibe)
- `tools.py`: `search_catalog` and `check_budget` tools used by the agents
- `crew.py`: agents, tasks, crew, and `parse_outfit`
- `app.py`: Gradio UI with a live agent activity log

## Rules for changes

- This code is shown on screen to learners. Keep changes small, readable and plainly named.
- Agents live in `build_crew` in `crew.py`. A new agent needs an `Agent`, a `Task`, and an entry in both lists passed to `Crew`.
- Product tools live in `tools.py`. Agents must never invent products; only catalog ids are valid.
- The outfit total is always computed in Python from `catalog.json`. Never trust a total written by a model.
- The final task must keep returning JSON in the shape `{"item_ids": [...], "note": "..."}` because `parse_outfit` depends on it.
- Do not add dependencies without asking.
- Do not create git commits unless asked.
