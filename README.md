# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

### Tool 1: `parse_query`
**Purpose:** Extract structured search parameters from natural language user input.

**Input:**
- `user_query: str` — The user's request as a natural language string (e.g., "I'm looking for a vintage graphic tee under $30 in size M")

**Return value:**
- **On success:** A dict with three keys: `{"description": str | None, "size": str | None, "max_price": float | None}`
- **On failure:** A dict with an "error" key: `{"error": "message"}`

---

### Tool 2: `search_listings`
**Purpose:** Search the mock listings dataset for items matching the description, optional size, and optional price ceiling.

**Input:**
- `description: str` — Keywords describing what the user is looking for (e.g., "vintage graphic tee")
- `size: str | None = None` — Size string to filter by, or None to skip size filtering (case-insensitive)
- `max_price: float | None = None` — Maximum price (inclusive), or None to skip price filtering

**Return value:**
- **On success:** A list of matching listing dicts, sorted by relevance (best match first). Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`
- **On failure:** A dict with an "error" key: `{"error": "message"}`

---

### Tool 3: `suggest_outfit`
**Purpose:** Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

**Input:**
- `new_item: dict` — A listing dict (the item the user is considering buying)
- `wardrobe: dict` — A wardrobe dict with an 'items' key containing a list of wardrobe item dicts (may be empty)

**Return value:**
- **On success:** A non-empty string with outfit suggestions (includes general styling advice if wardrobe is empty)
- **On failure:** A dict with an "error" key: `{"error": "message"}`

---

### Tool 4: `create_fit_card`
**Purpose:** Generate a short, shareable outfit caption for the thrifted find (2–4 sentences suitable for Instagram/TikTok).

**Input:**
- `outfit: str | dict` — The outfit suggestion string from `suggest_outfit()` (may also be an error dict if that tool failed)
- `new_item: dict` — The listing dict for the thrifted item

**Return value:**
- **On success:** A 2–4 sentence string usable as an Instagram/TikTok caption (mentions item name, price, and platform naturally)
- **On failure:** A dict with an "error" key: `{"error": "message"}`

---

## Planning Loop Explanation

FitFindr uses a **static, fixed-order planning loop** with no branching. The agent executes the following steps in strict sequence:

1. **`parse_query`** — Convert the user's natural language request into structured parameters (description, size, max_price)
2. **`search_listings`** — Use those parameters to find matching thrifted items from the dataset
3. **`suggest_outfit`** — Generate outfit suggestions pairing the best listing with the user's existing wardrobe (or general styling advice if wardrobe is empty)
4. **`create_fit_card`** — Generate a social media caption for the outfit

This linear pipeline is deterministic: each tool's output feeds directly into the next tool's input. If any tool fails (parse_query can't parse, search_listings returns empty results), the agent stops and communicates the error to the user without proceeding further.

---

## State Management Approach

FitFindr maintains a **session object** that encapsulates the user's current interaction state. This session object flows through the entire planning loop, accumulating results as each tool completes:

- **Session initialization:** At the start of `run_agent()`, a session object is created with the user's query and wardrobe.
- **Query parsing:** `parse_query` extracts structured parameters and stores them in the session.
- **Listing search:** `search_listings` populates the session with matching items (the "best" listing is selected for the next step).
- **Outfit suggestion:** `suggest_outfit` takes the selected listing and wardrobe from the session, returns outfit suggestions stored in the session.
- **Caption generation:** `create_fit_card` uses the outfit suggestion and listing (both already in the session) to generate the final caption.

The session object ensures that intermediate results (parsed parameters, search results, outfit suggestions) are available to downstream tools without re-computing them. If an error occurs at any step, the session captures that error state and the agent halts gracefully, communicating the failure to the user.

---

## Interaction Walkthrough

**User query:** "Looking for a vintage graphic tee under $30, size M"

**Step 1 — Tool called: `parse_query`**
- **Input:** `"Looking for a vintage graphic tee under $30, size M"`
- **Why this tool:** Before searching listings, we need to extract structured parameters (what item, size constraint, price limit) from the user's natural language request. This allows flexible queries like "vintage graphic tee" and "size M" to be parsed consistently.
- **Output:** 
  ```json
  {
    "description": "vintage graphic tee",
    "size": "M",
    "max_price": 30.0
  }
  ```

**Step 2 — Tool called: `search_listings`**
- **Input:** 
  - `description="vintage graphic tee"`
  - `size="M"`
  - `max_price=30.0`
- **Why this tool:** Now that we have structured parameters, we search the mock dataset for items matching these criteria. The search ranks results by keyword relevance (title, description, style_tags, colors) and filters by size and price.
- **Output:** List of matching items, with the top match being:
  ```json
  {
    "id": "lst_002",
    "title": "Y2K Baby Tee — Butterfly Print",
    "description": "Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.",
    "category": "tops",
    "style_tags": ["y2k", "vintage", "graphic tee", "cottagecore"],
    "size": "S/M",
    "condition": "excellent",
    "price": 18.00,
    "colors": ["white", "pink", "purple"],
    "brand": null,
    "platform": "depop"
  }
  ```
  (Plus 2-3 other relevant results ranked below this top match.)

**Step 3 — Tool called: `suggest_outfit`**
- **Input:**
  - `new_item`: The Y2K Baby Tee listing (from Step 2's top result)
  - `wardrobe`: User's wardrobe dict (e.g., example wardrobe with 10 items including vintage cardigans, distressed jeans, platform boots)
- **Why this tool:** With a specific item in hand, we ask the stylist to suggest 1–2 complete outfits pairing this tee with pieces from the user's existing wardrobe. This ensures the suggestion is personalized and practical.
- **Output:**
  ```
  Outfit 1: Pair this adorable Y2K baby tee with your black distressed jeans and white platform sneakers for a casual, nostalgic vibe. Layer it under your oversized cream cardigan for cooler days — the soft textures will complement the delicate butterfly print. Add a silver chain necklace and a mini crossbody bag for a subtle Y2K touch.

  Outfit 2: Go full cottage-core by pairing the tee with your sage green midi skirt and ankle boots. The butterfly graphic works beautifully with earthy, romantic aesthetics. Throw on your cropped denim jacket and you've got an effortlessly cute brunch-ready outfit.
  ```

**Step 4 — Tool called: `create_fit_card`**
- **Input:**
  - `outfit`: The outfit suggestion string from Step 3
  - `new_item`: The Y2K Baby Tee listing
- **Why this tool:** Now we generate a snappy, shareable social media caption that brings the outfit to life. The caption mentions the item, price, and platform naturally, and captures the outfit's vibe in a way that would appeal to TikTok or Instagram viewers.
- **Output:**
  ```
  just copped this adorable vintage butterfly baby tee from depop for $18 and i'm obsessed 🦋 the y2k nostalgia is unreal. paired it with my black distressed jeans and cream cardigan for the coziest vibe — it's giving cottagecore meets early 2000s and i'm here for it.
  ```

**Final output to user:**
```
Found: Y2K Baby Tee — Butterfly Print ($18 on Depop)

Outfit suggestions:
Outfit 1: Pair this adorable Y2K baby tee with your black distressed jeans and white platform sneakers for a casual, nostalgic vibe. Layer it under your oversized cream cardigan for cooler days — the soft textures will complement the delicate butterfly print. Add a silver chain necklace and a mini crossbody bag for a subtle Y2K touch.

Outfit 2: Go full cottage-core by pairing the tee with your sage green midi skirt and ankle boots. The butterfly graphic works beautifully with earthy, romantic aesthetics. Throw on your cropped denim jacket and you've got an effortlessly cute brunch-ready outfit.

Fit Card Caption:
just copped this adorable vintage butterfly baby tee from depop for $18 and i'm obsessed 🦋 the y2k nostalgia is unreal. paired it with my black distressed jeans and cream cardigan for the coziest vibe — it's giving cottagecore meets early 2000s and i'm here for it.
```


## Error Handling and Fail Points

Every tool is designed to handle its failure mode gracefully—no silent failures or crashes. Instead of raising exceptions, tools return error messages or sensible defaults, and the agent communicates clearly with the user.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `parse_query` | Cannot parse user's natural language request into structured parameters | Agent asks user to clarify: "I couldn't understand your request. Please tell me: what item are you looking for, what size (if any), and what's your max budget (if any)?" Agent stops and waits for clarification—does not proceed to search. |
| `search_listings` | No listings match the user's criteria (returns empty list `[]`) | Agent tells user: "No listings matched your criteria. Try adjusting the price, size, or description." Agent stops without calling suggest_outfit or create_fit_card. |
| `suggest_outfit` | Wardrobe is empty | Tool handles gracefully by returning general styling advice (e.g., "This pairs well with oversized jackets for a relaxed vibe") instead of crashing. Agent proceeds normally with this general advice. |
| `create_fit_card` | Outfit input is missing or empty | Tool returns a descriptive error message string (not a Python exception). Agent detects this and tells user: "Could not generate a fit card. Please try again with a complete outfit suggestion." |

---

## Spec Reflection

**One way planning.md helped during implementation:**

The detailed **Planning Loop** section (steps 1–5) was invaluable during implementation because it provided a clear, sequential checklist for the agent logic. Rather than reasoning about branching conditionals or unclear error propagation, I could follow the exact steps in planning.md: parse → check for error → search → check for empty or error → suggest outfit → check for error → create fit card → check for error → return. This linear structure meant that implementing `run_agent()` was straightforward—each tool call had a predictable outcome and a clear next step. Additionally, the **State Management** section's session dict blueprint ensured that I didn't miss any intermediate result that needed to flow between tools; I could literally copy the field names from planning.md into the session initialization and use them throughout the loop.

**One divergence from your spec, and why:**

The specification initially described three required tools (search_listings, suggest_outfit, create_fit_card), but during planning I added a fourth tool—`parse_query()`—as the first step in the loop. This divergence was necessary because the original specification assumed the agent would receive already-structured input (description, size, max_price), but user experience demanded that the agent accept natural language queries like "Looking for a vintage graphic tee under $30, size M." Rather than ask users to pre-format their requests, `parse_query()` extracts those parameters automatically using the LLM. This divergence improves usability significantly: users can now provide free-form queries, and the agent handles parsing transparently. The trade-off is one additional LLM call per interaction, but the gain in ease of use justifies it.

---

## AI Usage

This section documents specific instances where I used AI tools during the implementation of FitFindr, what input was provided, what was produced, and what modifications were made.

### Instance 1: Tool Function Implementation

**Input provided to AI:**
- The tool specification from the project README (tool names, inputs/outputs, error handling requirements)
- The existing `data_loader.py` to understand the data structure (listings schema, wardrobe format)
- The style of docstrings and error patterns already established in the codebase

**What the AI produced:**
- A complete implementation of all four tools (`parse_query`, `search_listings`, `suggest_outfit`, `create_fit_card`) with proper type hints
- Groq API integration with prompt engineering for query parsing and outfit/caption generation
- Consistent error handling using error dicts across all tools
- LLM calls with appropriate temperature and max_token settings for each use case

**What I changed/overrode:**
- Adjusted the prompt templates in `parse_query` and `suggest_outfit` to better align with project tone and specificity
- Modified the scoring logic in `search_listings` to weight certain fields more heavily (e.g., style_tags vs. title)
- Changed error message wording in several places to be more user-friendly and specific to FitFindr's context

### Instance 2: README Documentation and Planning Loop

**Input provided to AI:**
- The project spec requirements for documenting tools, planning approach, and state management
- The actual function signatures from `tools.py`
- The error handling patterns from the code

**What the AI produced:**
- Complete Tool Inventory section with all four tools, inputs, and return types
- Planning Loop Explanation describing the fixed-order pipeline
- State Management Approach section explaining session object flow
- Error Handling Per Tool section with technical details
- Structured format and organization for the entire README

**What I changed/overrode:**
- Refined the Planning Loop explanation to emphasize "static" and "fixed-order" terminology specific to my implementation
- Customized the State Management section to match my actual session object design (vs. generic explanation)
- Simplified some of the error handling descriptions to be more concise while maintaining clarity
- Added specific examples and tool names where the AI had used generic placeholders

---

## Limitations and Future Enhancements

**Session Scope:** Each call to `run_agent()` creates a fresh, independent session. This means:
- **No multi-turn conversations:** If a user asks "Show me a jacket instead," FitFindr starts with a completely new session and has no memory of the previous "vintage tee" search. Each query is treated as a standalone interaction.
- **No persistent user state:** Wardrobe and search history are not persisted across sessions. Every interaction loads a fresh wardrobe and results.

This is by design for this project (stateless, independent queries), but a production version could add:
- User authentication and session IDs
- Database persistence of wardrobe and search history
- Multi-turn conversation context where follow-up queries reference previous results

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
