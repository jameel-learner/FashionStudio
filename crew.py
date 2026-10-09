import json
import os
import re

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

from tools import check_budget, get_products, search_catalog

load_dotenv()  # reads keys and MODEL from a local .env file if present

# Pick any provider CrewAI supports by setting MODEL, e.g.
#   openai/gpt-4o-mini            (needs OPENAI_API_KEY)
#   groq/llama-3.3-70b-versatile  (needs GROQ_API_KEY, free tier available)
#   gemini/gemini-2.0-flash       (needs GEMINI_API_KEY)
DEFAULT_MODEL = "openai/gpt-4o-mini"


def make_llm():
    return LLM(model=os.getenv("MODEL", DEFAULT_MODEL), temperature=0.3)


def build_crew(occasion, budget, llm=None, step_callback=None, task_callback=None):
    llm = llm or make_llm()

    stylist = Agent(
        role="Personal Stylist",
        goal="Turn a shopper's request into a clear styling brief",
        backstory="You are a Bengaluru stylist who knows Indian and western wear and how to match outfits to occasions.",
        llm=llm,
        verbose=False,
    )
    curator = Agent(
        role="Catalog Curator",
        goal="Pick real items from the store catalog that fit the brief",
        backstory="You only recommend items that exist in the catalog. You always use the search tool and never invent products.",
        tools=[search_catalog],
        llm=llm,
        verbose=False,
    )
    controller = Agent(
        role="Budget Controller",
        goal="Make sure the final outfit fits the budget, swapping items if needed",
        backstory="You never do arithmetic in your head. You always verify the total with the budget tool.",
        tools=[check_budget, search_catalog],
        llm=llm,
        verbose=False,
    )
    writer = Agent(
        role="Fashion Copywriter",
        goal="Explain the final outfit warmly in a few sentences and output it as JSON",
        backstory="You write short, friendly styling notes for a boutique.",
        llm=llm,
        verbose=False,
    )

    brief = Task(
        description=(
            f"Shopper request: {occasion!r}. Total budget: Rs {budget}.\n"
            "Write a short styling brief: occasion, formality, colour palette, what to avoid, "
            "and a rough budget split between the main outfit and accessories."
        ),
        expected_output="A brief of at most 6 lines.",
        agent=stylist,
    )
    pick = Task(
        description=(
            "Using the brief, search the catalog and choose a complete outfit: one main piece "
            "(kurta, kurti, dress, jumpsuit or co-ord set), optionally one outerwear piece, "
            "and up to two accessories. Use the search_catalog tool; only choose items it returns."
        ),
        expected_output="A list of chosen product ids with name, price and a one-line reason each.",
        agent=curator,
        context=[brief],
    )
    verify = Task(
        description=(
            f"Check the chosen items against the budget of Rs {budget} with the check_budget tool. "
            "If the total is over budget, swap the most expensive item for a cheaper catalog item "
            "(use search_catalog) and check again. Repeat until within budget. "
            "If nothing can fit, drop the least important item."
        ),
        expected_output="The final list of product ids, the verified total, and what was swapped, if anything.",
        agent=controller,
        context=[pick],
    )
    write = Task(
        description=(
            "Write a 2-3 sentence styling note for the shopper explaining why this outfit suits "
            "their request. Then output ONLY a JSON object, no markdown fences, in this shape: "
            '{"item_ids": ["P3", "P7"], "note": "..."}. Use the final item ids from the budget check.'
        ),
        expected_output='A JSON object with keys "item_ids" and "note".',
        agent=writer,
        context=[verify],
    )

    return Crew(
        agents=[stylist, curator, controller, writer],
        tasks=[brief, pick, verify, write],
        process=Process.sequential,
        step_callback=step_callback,
        task_callback=task_callback,
        verbose=False,
    )


def parse_outfit(raw):
    """Extract {"item_ids": [...], "note": "..."} from the writer's output.
    The total is always recomputed from the catalog, never taken from the model."""
    text = str(raw)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    data = {}
    if match:
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError:
            data = {}
    ids = [str(i).strip().upper() for i in data.get("item_ids", [])]
    items = get_products(ids)
    return {
        "items": items,
        "total": sum(p["price"] for p in items),
        "note": data.get("note") or text.strip(),
    }
