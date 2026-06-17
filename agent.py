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
