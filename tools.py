"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str | dict
    create_fit_card(outfit, new_item)               → str | dict

Error Handling Pattern:
    All tools return structured error dicts on failure: {"error": "message"}
    This allows the agent to handle errors uniformly across all tools.
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────


def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 4: parse_query ───────────────────────────────────────────────────────


def parse_query(user_query: str) -> dict:
    """
    Extract structured search parameters from natural language user input.

    Args:
        user_query: The user's request as a natural language string
                    (e.g., "I'm looking for a vintage graphic tee under $30 in size M")

    Returns:
        On success: A dict with three keys:
            {
                "description": "vintage graphic tee" or None,
                "size": "M" or None,
                "max_price": 30.0 or None
            }
            All three values may be None if not specified in the query.

        On failure: A dict with an "error" key containing an error message string.
            Example: {"error": "Failed to parse query: ..."}
    """
    client = _get_groq_client()

    prompt = (
        "Extract the following information from the user's query:\n"
        '1. description: Short concise sets of single space separated keywords of what item or style are they looking for? (e.g., "vintage graphic tee")\n'
        '2. size: What size if specified? (e.g., "M", "L", "US 8", or None if not mentioned)\n'
        "3. max_price: What's the maximum price if specified? (e.g., 30.0, 50.0, or None if not mentioned)\n"
        "\n"
        f'User query: "{user_query}"\n'
        "\n"
        "Respond with ONLY a JSON object (no markdown, no extra text):\n"
        '{"description": "...", "size": "..." or null, "max_price": ... or null}\n'
        "\n"
        "If the description is not clear, set description to null.\n"
        'Only include numeric values for max_price (no "$" symbols).'
    )

    try:
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )

        response_text = response.choices[0].message.content.strip()
        parsed = json.loads(response_text)

        return {
            "description": parsed.get("description"),
            "size": parsed.get("size"),
            "max_price": parsed.get("max_price"),
        }
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return {
            "error": f"Failed to parse query: {str(e)}. Please clarify: what item are you looking for, what size (if any), and what's your max budget (if any)?"
        }


# ── Tool 1: search_listings ───────────────────────────────────────────────────


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict] | dict:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        On success: A list of matching listing dicts, sorted by relevance (best match first).
            Returns an empty list if nothing matches — does NOT raise an exception.
            Each listing dict has the following fields:
                id, title, description, category, style_tags (list), size,
                condition, price (float), colors (list), brand, platform

        On failure: A dict with an "error" key containing an error message string.
            Example: {"error": "Failed to load listings: ..."}
    """
    try:
        # Step 1: Load all listings
        listings = load_listings()

        # Step 2: Filter by max_price (if provided)
        if max_price is not None:
            listings = [item for item in listings if item["price"] <= max_price]

        # Step 3: Filter by size (if provided, case-insensitive)
        if size is not None:
            size_lower = size.lower()
            listings = [item for item in listings if size_lower in item["size"].lower()]

        # Step 4: Score listings by keyword overlap with description
        keywords = description.lower().split()

        scored_listings = []
        for item in listings:
            score = 0

            # Search text: title, description, style_tags, colors, brand, category
            search_text = (
                f"{item['title']} {item['description']} "
                f"{' '.join(item['style_tags'])} "
                f"{' '.join(item['colors'])} "
                f"{item.get('brand', '')} {item['category']}"
            ).lower()

            # Count keyword matches
            for keyword in keywords:
                if keyword in search_text:
                    score += 1

            # Step 5: Drop listings with score 0
            if score > 0:
                scored_listings.append((score, item))

        # Step 6: Sort by score (highest first) and return listing dicts
        scored_listings.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_listings]
    except Exception as e:
        return {"error": f"Failed to search listings: {str(e)}"}


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────


def suggest_outfit(new_item: dict, wardrobe: dict) -> str | dict:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        On success: A non-empty string with outfit suggestions.
            If the wardrobe is empty, returns general styling advice for the item
            rather than raising an exception or returning an empty string.

        On failure: A dict with an "error" key containing an error message string.
            Example: {"error": "Failed to generate suggestions: ..."}
    """
    client = _get_groq_client()

    is_empty = len(wardrobe.get("items", [])) == 0

    if is_empty:
        prompt = (
            "You are a friendly fashion stylist. A user is considering buying a thrifted item but has an empty wardrobe.\n"
            "\n"
            "Item details:\n"
            f"- Title: {new_item['title']}\n"
            f"- Description: {new_item['description']}\n"
            f"- Style tags: {', '.join(new_item['style_tags'])}\n"
            f"- Colors: {', '.join(new_item['colors'])}\n"
            f"- Condition: {new_item['condition']}\n"
            f"- Category: {new_item['category']}\n"
            "\n"
            "Suggest 1-2 complete outfits they could build around this item. For each outfit:\n"
            "1. List the key pieces needed (what categories, colors, styles would work well)\n"
            "2. Describe the overall vibe or occasion\n"
            "3. Give specific styling tips\n"
            "\n"
            "Be specific and actionable. Sound like you're talking to a friend, not a product description."
        )

    else:
        wardrobe_text = "Current wardrobe items:\n"
        for item in wardrobe["items"]:
            wardrobe_text += (
                f"- {item['name']} "
                f"(Category: {item['category']}, Colors: {', '.join(item['colors'])}, "
                f"Style: {', '.join(item['style_tags'])})\n"
            )

        prompt = (
            "You are a friendly fashion stylist. A user is considering buying a thrifted item and wants outfit suggestions using their existing wardrobe.\n"
            "\n"
            "New item they're considering:\n"
            f"- Title: {new_item['title']}\n"
            f"- Description: {new_item['description']}\n"
            f"- Style tags: {', '.join(new_item['style_tags'])}\n"
            f"- Colors: {', '.join(new_item['colors'])}\n"
            f"- Condition: {new_item['condition']}\n"
            f"- Category: {new_item['category']}\n"
            "\n"
            f"{wardrobe_text}"
            "\n"
            "Suggest 1-2 specific complete outfits that pair the new item with pieces from their wardrobe. For each outfit:\n"
            "1. List all pieces by name (use the exact names from their wardrobe)\n"
            "2. Explain how they work together\n"
            "3. Describe the vibe or occasion\n"
            "4. Give specific styling tips\n"
            "\n"
            "Be specific, actionable, and enthusiastic. Sound like you're talking to a friend."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return {"error": f"Failed to generate outfit suggestions: {str(e)}"}


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────


def create_fit_card(outfit: str | dict, new_item: dict) -> str | dict:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit(). May also be
                  an error dict if suggest_outfit() failed.
        new_item: The listing dict for the thrifted item.

    Returns:
        On success: A 2–4 sentence string usable as an Instagram/TikTok caption.
            The caption will:
            - Feel casual and authentic (like a real OOTD post, not a product description)
            - Mention the item name, price, and platform naturally (once each)
            - Capture the outfit vibe in specific terms
            - Sound different each time for different inputs (uses higher LLM temperature)

        On failure: A dict with an "error" key containing an error message string.
            Example: {"error": "Failed to generate caption: ..."}
            This happens if outfit is invalid/empty or the LLM call fails.
    """
    # Guard against error dict or empty outfit from suggest_outfit
    if isinstance(outfit, dict):
        return {
            "error": f"Cannot create caption: suggest_outfit failed with error: {outfit.get('error', 'Unknown error')}"
        }

    if not outfit or not outfit.strip():
        return {"error": "Cannot create caption: outfit suggestion is empty or missing"}

    client = _get_groq_client()

    prompt = (
        "You are a fashion influencer writing a casual Instagram/TikTok caption for an OOTD (Outfit Of The Day) post.\n"
        "\n"
        "Item being featured:\n"
        f"- Name: {new_item['title']}\n"
        f"- Price: ${new_item['price']}\n"
        f"- Platform: {new_item['platform']}\n"
        f"- Description: {new_item['description']}\n"
        "\n"
        f"Outfit suggestion:\n{outfit}\n"
        "\n"
        "Write a 2-4 sentence caption that:\n"
        "1. Feels casual and authentic (like a real friend talking, not a product description)\n"
        "2. Mentions the item name, price, and platform naturally (once each)\n"
        "3. Captures the outfit vibe in specific terms\n"
        "4. Sounds authentic and unique\n"
        "\n"
        "Do NOT use hashtags. Just write the caption text."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return {"error": f"Failed to generate caption: {str(e)}"}
