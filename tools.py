import json
from pathlib import Path

from crewai.tools import tool

CATALOG_PATH = Path(__file__).parent / "catalog.json"


def load_catalog():
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)["products"]


def get_products(item_ids):
    """Return catalog entries for the given ids, in order, skipping unknown ids."""
    by_id = {p["id"]: p for p in load_catalog()}
    return [by_id[i] for i in item_ids if i in by_id]


def _score(product, words):
    haystack = " ".join(
        [product["name"], product["category"], product["colour"], product["vibe"]]
        + product["occasions"]
    ).lower()
    return sum(1 for w in words if w in haystack)


@tool("search_catalog")
def search_catalog(query: str, category: str = "all", max_price: int = 0) -> str:
    """Search the Fouzia Design Studio catalog.
    query: space-separated keywords such as occasion, colour or vibe (e.g. "mehendi pastel soft").
    category: a category name from list_categories, or "all".
    max_price: maximum price in rupees for a single item; 0 means no limit.
    Returns a JSON list of matching products with id, name, price, category, colour and vibe."""
    words = [w for w in query.lower().replace(",", " ").split() if w]
    results = []
    for p in load_catalog():
        if category != "all" and p["category"] != category.lower():
            continue
        if max_price and p["price"] > max_price:
            continue
        s = _score(p, words) if words else 0
        if words and s == 0:
            continue
        results.append((s, p))
    results.sort(key=lambda t: (-t[0], t[1]["price"]))
    out = [
        {k: p[k] for k in ("id", "name", "price", "category", "colour", "vibe")}
        for _, p in results
    ]
    return json.dumps(out, ensure_ascii=False)


@tool("list_categories")
def list_categories() -> str:
    """List every category in the catalog with how many items it has and a few example item names.
    Use it to understand what the store sells before searching.
    Returns a JSON list of {category, count, examples}."""
    by_category = {}
    for p in load_catalog():
        by_category.setdefault(p["category"], []).append(p["name"])
    out = [
        {"category": c, "count": len(names), "examples": names[:3]}
        for c, names in by_category.items()
    ]
    return json.dumps(out, ensure_ascii=False)


@tool("check_budget")
def check_budget(item_ids: str, budget: int) -> str:
    """Check whether a set of catalog items fits a budget.
    item_ids: comma-separated product ids, for example "P3,P7,P8".
    budget: total budget in rupees.
    Returns JSON with the item names, the exact total, whether it is within budget, and the amount remaining."""
    ids = [i.strip().upper() for i in item_ids.split(",") if i.strip()]
    items = get_products(ids)
    unknown = [i for i in ids if i not in {p["id"] for p in items}]
    total = sum(p["price"] for p in items)
    return json.dumps(
        {
            "items": [{"id": p["id"], "name": p["name"], "price": p["price"]} for p in items],
            "unknown_ids": unknown,
            "total": total,
            "budget": budget,
            "within_budget": total <= budget,
            "remaining": budget - total,
        },
        ensure_ascii=False,
    )
