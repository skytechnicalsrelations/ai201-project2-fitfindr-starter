"""
agent.py

The FitFindr planning loop. Orchestrates the four tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json

from tools import create_fit_card, parse_query, search_listings, suggest_outfit

# ── tool definitions ─────────────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "parse_query",
            "description": (
                "Extract structured search parameters (description, size, max_price) "
                "from the user's natural language query using the LLM. "
                "Returns a dict with keys: description (str), size (str or None), max_price (float or None). "
                "On failure, returns {'error': '...'}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "The user's full natural language request (e.g., 'vintage graphic tee under $30, size M')",
                    }
                },
                "required": ["user_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_listings",
            "description": (
                "Search the listings database for items matching the user's criteria. "
                "Filters by description (keyword match), size (exact or None for all), and max_price. "
                "Returns a sorted list of matching listing dicts, or [] if no matches. "
                "Each listing dict contains: id, title, description, category, style_tags, size, condition, price, colors, brand, platform."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "The item type/style to search for (e.g., 'vintage graphic tee')",
                    },
                    "size": {
                        "type": ["string", "null"],
                        "description": "Desired size (e.g., 'M', 'L') or None to search all sizes",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price in dollars; only return items at or below this price",
                    },
                },
                "required": ["description", "size", "max_price"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "suggest_outfit",
            "description": (
                "Generate 1-2 outfit suggestions by pairing a thrifted item with wardrobe pieces. "
                "Takes a new item listing and user's wardrobe dict. "
                "Returns a string with outfit suggestions. If wardrobe is empty, returns general styling advice. "
                "On failure, returns {'error': '...'}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "new_item": {
                        "type": "object",
                        "description": "A listing dict from search_listings with fields: title, style_tags, colors, brand, condition, price, etc.",
                    },
                    "wardrobe": {
                        "type": "object",
                        "description": "User's wardrobe dict with an 'items' key containing a list of wardrobe item dicts",
                    },
                },
                "required": ["new_item", "wardrobe"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_fit_card",
            "description": (
                "Generate a short, casual social media caption (tweet/Instagram post style) for the outfit. "
                "Takes outfit suggestion text and the new item listing. "
                "Returns a 2-4 sentence caption string mentioning item name, price, and platform naturally. "
                "On failure (empty outfit input or LLM failure), returns {'error': '...'}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "outfit": {
                        "type": "string",
                        "description": "The outfit suggestion string from suggest_outfit describing how to style the item",
                    },
                    "new_item": {
                        "type": "object",
                        "description": "A listing dict from search_listings with fields: title, price, platform, condition, etc.",
                    },
                },
                "required": ["outfit", "new_item"],
            },
        },
    },
]

# ── system prompt ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a skilled thrifted fashion advisor and styling expert. "
    "Help users find unique thrifted items and create complete outfit suggestions "
    "by using your available tools to search listings and generate personalized styling advice.\n\n"
    "Always use your tools to search for actual thrifted items and generate outfit suggestions — "
    "don't rely on general fashion knowledge alone. Use parse_query to understand what the user "
    "is looking for, search_listings to find real options, and suggest_outfit to create specific "
    "styling advice based on their wardrobe.\n\n"
    "Keep your advice practical, specific, and grounded in the actual items found. "
    "If no listings match their criteria, suggest adjusting the search filters (price, size, description). "
    "Celebrate thrift finds and help users build creative, sustainable outfits that reflect their personal style."
)

# ── tool dispatch ────────────────────────────────────────────────────────────────


def dispatch_tool(tool_name: str, tool_args: dict) -> str:
    """Route a tool call to the correct function and return the result as a JSON string."""
    # Some models send arguments as JSON "null" for no-argument tools, which
    # json.loads() turns into None — normalize so .get() below is always safe.
    if not isinstance(tool_args, dict):
        tool_args = {}
    print(f"  → Tool call: {tool_name}({tool_args})")

    if tool_name == "parse_query":
        result = parse_query(tool_args["user_query"])
    elif tool_name == "search_listings":
        result = search_listings(
            description=tool_args["description"],
            size=tool_args.get("size"),
            max_price=tool_args["max_price"],
        )
    elif tool_name == "suggest_outfit":
        result = suggest_outfit(
            new_item=tool_args["new_item"],
            wardrobe=tool_args["wardrobe"],
        )
    elif tool_name == "create_fit_card":
        result = create_fit_card(
            outfit=tool_args["outfit"],
            new_item=tool_args["new_item"],
        )
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    print(
        f"  ← Result: {json.dumps(result)[:120]}{'...' if len(json.dumps(result)) > 120 else ''}"
    )
    return json.dumps(result)

# ── session state ─────────────────────────────────────────────────────────────


def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,  # original user query
        "parsed": {},  # extracted description / size / max_price
        "search_results": [],  # list of matching listing dicts
        "selected_item": None,  # top result, passed into suggest_outfit
        "wardrobe": wardrobe,  # user's wardrobe dict
        "outfit_suggestion": None,  # string returned by suggest_outfit
        "fit_card": None,  # string returned by create_fit_card
        "error": None,  # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Call parse_query() to extract description, size, and max_price
                from the user's natural language query.
                Store the result in session["parsed"].
                **ERROR CHECK:** If "error" in session["parsed"], set
                session["error"] and return early.

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                **ERROR CHECK:** If "error" in session["search_results"], set
                session["error"] and return early.
                **EMPTY CHECK:** If session["search_results"] == [], set
                session["error"] to a helpful message ("No listings matched...")
                and return early. Do NOT proceed to suggest_outfit with empty input.

        Step 4: Select the top item from search_results.
                Store it in session["selected_item"] = session["search_results"][0].

        Step 5: Call suggest_outfit() with selected_item and wardrobe.
                Store the result in session["outfit_suggestion"].
                **ERROR CHECK:** If "error" in session["outfit_suggestion"], set
                session["error"] and return early.

        Step 6: Call create_fit_card() with outfit_suggestion and selected_item.
                Store the result in session["fit_card"].
                **ERROR CHECK:** If "error" in session["fit_card"], set
                session["error"] and return early.

        Step 7: Return the session (session["error"] will be None on success).

    Implementation notes:
    - All tools follow the error dict pattern: return {"error": "..."} on failure
    - Check errors uniformly with: if "error" in result
    - Use parse_query() from tools.py (not regex/string splitting)
    - See the error handling table in planning.md for all failure modes
    """
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query to extract description, size, max_price
    session["parsed"] = parse_query(query)
    if "error" in session["parsed"]:
        session["error"] = session["parsed"]["error"]
        return session

    # Step 3: Search listings using parsed parameters
    session["search_results"] = search_listings(
        description=session["parsed"]["description"],
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )
    if (
        isinstance(session["search_results"], dict)
        and "error" in session["search_results"]
    ):
        session["error"] = session["search_results"]["error"]
        return session

    # Check if search returned empty results
    if session["search_results"] == []:
        session["error"] = (
            "No listings matched your criteria. Try adjusting the price, size, or description."
        )
        return session

    # Step 4: Select the top result
    session["selected_item"] = session["search_results"][0]

    # Step 5: Get outfit suggestions
    session["outfit_suggestion"] = suggest_outfit(
        new_item=session["selected_item"],
        wardrobe=session["wardrobe"],
    )
    if (
        isinstance(session["outfit_suggestion"], dict)
        and "error" in session["outfit_suggestion"]
    ):
        session["error"] = session["outfit_suggestion"]["error"]
        return session

    # Step 6: Generate the fit card caption
    session["fit_card"] = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=session["selected_item"],
    )
    if isinstance(session["fit_card"], dict) and "error" in session["fit_card"]:
        session["error"] = session["fit_card"]["error"]
        return session

    # Step 7: Return completed session (error is None on success)
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_empty_wardrobe, get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
