import json
import os
import re

from crewai import LLM, Agent, Crew, Process, Task
from dotenv import load_dotenv

from tools import check_budget, get_products, list_categories, search_catalog

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
        backstory=(
            "You only recommend items that exist in the catalog. You always use the tools and never invent products. "
            "You think of an outfit as one main piece that carries the look, finished with add-ons."
        ),
        tools=[search_catalog, list_categories],
        llm=llm,
        verbose=False,
    )
    controller = Agent(
        role="Budget Controller",
        goal="Make sure the final outfit fits the budget, swapping items if needed",
        backstory=(
            "You never do arithmetic in your head. You always verify the total with the budget tool. "
            "You protect the main piece of an outfit and trim add-ons first."
        ),
        tools=[check_budget, search_catalog],
        llm=llm,
        verbose=False,
    )
    auditor = Agent(
        role="Outfit Auditor",
        goal="Make sure the final outfit has a main piece, and say which items are main pieces and which are add-ons",
        backstory=(
            "You judge items by their catalog category. A main piece is a garment or set that forms the base of "
            "an outfit and could be worn as the look itself. Add-ons only finish or layer onto it. "
            "You decide this yourself from the category names, and you fix outfits that have no main piece."
        ),
        tools=[list_categories, search_catalog, check_budget],
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
            "Using the brief, build a complete outfit from the catalog.\n"
            "1. Call list_categories to see everything the store sells.\n"
            "2. Decide from the category names which categories hold main pieces (a garment or set that forms "
            "the base of the outfit, alone or paired with one partner garment) and which hold add-ons "
            "(things that finish or layer onto the outfit).\n"
            "3. Search for the main piece FIRST, using search_catalog with a main-piece category. "
            "Results are listed cheapest first, so look at the whole list and pick the best fit for the brief, "
            "not just the first row.\n"
            "4. Then search add-on categories and choose up to three add-ons that suit the main piece.\n"
            "Only choose items the search tool returned. The outfit must contain at least one main piece."
        ),
        expected_output=(
            "A list of chosen product ids with name, category, price and a one-line reason each, "
            "marking which one is the main piece."
        ),
        agent=curator,
        context=[brief],
    )
    verify = Task(
        description=(
            f"Check the chosen items against the budget of Rs {budget} with the check_budget tool. "
            "If the total is over budget, cut cost in this order: drop or downgrade add-ons first, "
            "then swap the main piece for a cheaper main piece of the same kind (use search_catalog). "
            "Never remove the main piece without replacing it. Check again after every change "
            "and repeat until within budget."
        ),
        expected_output="The final list of product ids, the verified total, and what was swapped, if anything.",
        agent=controller,
        context=[pick],
    )
    audit = Task(
        description=(
            f"Audit the final outfit from the budget check (budget Rs {budget}). Call list_categories, then judge "
            "each item by its catalog category: is it a main piece (forms the base of the outfit) or an add-on?\n"
            "If the outfit has NO main piece, fix it: use search_catalog to find a main piece that suits the brief, "
            "make room by removing add-ons if needed, and confirm the new total with check_budget.\n"
            "Output ONLY a JSON object, no markdown fences, in this shape: "
            '{"item_ids": ["P3", "P7"], "main_item_ids": ["P3"], "addon_item_ids": ["P7"]}.'
        ),
        expected_output='A JSON object with keys "item_ids", "main_item_ids" and "addon_item_ids".',
        agent=auditor,
        context=[verify],
    )
    write = Task(
        description=(
            "Write a 2-3 sentence styling note for the shopper explaining why this outfit suits "
            "their request. Then output ONLY a JSON object, no markdown fences, in this shape: "
            '{"item_ids": ["P3", "P7"], "note": "..."}. Use the item_ids from the outfit audit.'
        ),
        expected_output='A JSON object with keys "item_ids" and "note".',
        agent=writer,
        context=[audit],
    )

    return Crew(
        agents=[stylist, curator, controller, auditor, writer],
        tasks=[brief, pick, verify, audit, write],
        process=Process.sequential,
        step_callback=step_callback,
        task_callback=task_callback,
        verbose=False,
    )


def _json_object(text):
    """Return the first {...} block in text as a dict, or {} if there is none."""
    match = re.search(r"\{.*\}", str(text), re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {}


def has_main_piece(crew_output, item_ids):
    """True if the Outfit Auditor named at least one main piece that is in the final outfit.
    Which categories count as main is the auditor's judgement, not decided here.
    The audit is the task just before the writer's final task."""
    audit = _json_object(crew_output.tasks_output[-2].raw)
    main_ids = {str(i).strip().upper() for i in audit.get("main_item_ids", [])}
    return bool(main_ids & set(item_ids))


def parse_outfit(raw):
    """Extract {"item_ids": [...], "note": "..."} from the writer's output.
    The total is always recomputed from the catalog, never taken from the model."""
    text = str(raw)
    data = _json_object(text)
    ids = [str(i).strip().upper() for i in data.get("item_ids", [])]
    items = get_products(ids)
    return {
        "items": items,
        "total": sum(p["price"] for p in items),
        "note": data.get("note") or text.strip(),
    }
