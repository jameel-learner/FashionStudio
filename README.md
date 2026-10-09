# AI Cohort Fashion Studio

A crew of AI agents builds an outfit from a small boutique catalog (Fouzia Design Studio products), checks it against the shopper's budget, and explains the choice. Built with CrewAI and Gradio, demoed in VS Code with Claude Code.

Full demo walkthrough: **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)**

## The crew

| Agent | Job | Tool |
|---|---|---|
| Personal Stylist | Turns the request into a styling brief | none |
| Catalog Curator | Picks real items from the catalog | `search_catalog` |
| Budget Controller | Verifies the total, swaps items if over budget | `check_budget`, `search_catalog` |
| Fashion Copywriter | Writes the note and returns the final item ids as JSON | none |

The total shown on screen is always recomputed in Python from the catalog.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate     # Windows: python -m venv .venv ; .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env                                   # Windows: copy .env.example .env
# put one provider key in .env
python app.py
```

Open the URL it prints (default http://127.0.0.1:7860).

## Files

- `app.py`: Gradio UI with a live agent activity log
- `crew.py`: agents, tasks, crew, output parser
- `tools.py`: catalog search and budget check tools
- `catalog.json`: 8 products. Names and prices come from the storefront; category, colour and occasion tags were added for the demo
- `CLAUDE.md`: project rules that Claude Code reads at the start of every session
- `backup/crew_with_trend_advisor.py`: crew with a fifth agent already added, used as the fallback for the live edit in the demo
- `.env.example`: copy to `.env` and add a key

## Demo prompts

Expected results come from the catalog data and have not been run against a live model yet. Run each once before the session.

| # | Occasion | Budget | What a good answer looks like |
|---|---|---|---|
| 1 | Cousin's mehendi on Saturday evening, soft colours, nothing heavy | 6000 | Blush Wrap Midi Dress + Jhumkas + Potli Bag = 5,600 |
| 2 | Reception tonight, I want something rich and traditional | 5000 | The Maroon Velvet Kurta (5,200) is over budget, so the crew must swap |
| 3 | Brunch with friends, relaxed | 3000 | Floral Co-ord Set (2,400) or Blush Midi Dress (2,800) |
| 4 | Office meeting, polished | 4000 | Black Tailored Jumpsuit (3,600) |
| 5 | Wedding outfit | 1500 | No formal outfit fits; an honest answer, not an invented product |

## Notes

- Product images are not in the catalog because the storefront pages load their data client-side. Add image URLs to `catalog.json` and an `<img>` tag in `render_cards` (in `app.py`) for photos on the cards.
- The agent instructions in `crew.py` are written for clothing and accessories. A different kind of catalog needs those instructions edited.
