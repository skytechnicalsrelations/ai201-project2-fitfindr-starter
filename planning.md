# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Searches the listings database for items matching the user's description, size, and price constraints. Returns a ranked list of matching listings, or an empty list if no items match.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): The type/style of item the user is looking for (e.g., "vintage graphic tee")
- `size` (str | None): The desired size (e.g., "M", "L") or `None` to search all sizes
- `max_price` (float): Maximum price in dollars; only return items at or below this price

**What it returns:**
A list of listing dictionaries sorted by relevance. Each dict contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`. Returns an empty list `[]` if no listings match the filters.

**What happens if it fails or returns nothing:**
Returns an empty list `[]` (no error key). The planning loop detects this and tells the user no listings matched, suggests adjusting criteria, and stops without calling suggest_outfit or create_fit_card.

---

### Tool 2: suggest_outfit

**What it does:**
Takes a new thrifted item and the user's existing wardrobe, then suggests 1–2 complete outfit combinations by pairing the new item with specific pieces from their wardrobe. If the wardrobe is empty, provides general styling advice for the item. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): A listing dict from `search_listings` with fields like `title`, `style_tags`, `colors`, `brand`, `condition`, `price`
- `wardrobe` (dict): The user's wardrobe dict with an `items` key containing a list of wardrobe item dicts; may be empty

**What it returns:**
A non-empty string with 1–2 outfit suggestions. Each suggestion pairs the new item with specific wardrobe pieces and includes styling tips. If the wardrobe is empty, returns general styling advice (from LLM training) for the item instead of specific wardrobe pairings.

**What happens if it fails or returns nothing:**
The tool is designed to handle empty wardrobe gracefully by returning general styling advice. Always returns a non-empty string. If the LLM call fails or returns empty (unexpected), returns a dict with an `"error"` key: `{"error": "..."}`—the agent loop detects this and informs the user.

---

### Tool 3: create_fit_card

**What it does:**
Generates a short, shareable social media caption (tweet/Instagram post style) for the thrifted item and outfit. The caption mentions the item name, price, and platform naturally while capturing the outfit vibe.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion string from `suggest_outfit` describing how to style the new item
- `new_item` (dict): A listing dict from `search_listings` with fields like `title`, `price`, `platform`, `condition`

**What it returns:**
A 2–4 sentence string usable as a social media caption. Sounds casual and authentic (like a real OOTD post), mentions the item, price, and platform naturally, and captures the outfit vibe in specific terms. Outputs may vary (using higher LLM temperature for creativity).

**What happens if it fails or returns nothing:**
If outfit input is empty or missing, or if the LLM call fails, returns a dict with an `"error"` key: `{"error": "..."}`—not a string. The agent loop detects this error dict and informs the user that the fit card could not be generated.

---

### Tool 4: parse_query

**What it does:**
Uses the LLM to extract structured search parameters from the user's natural language query. Parses the description (item type/style), desired size, and maximum price from free-form text.

**Input parameters:**
- `user_query` (str): The user's full request as a natural language string

**What it returns:**
A dict with three keys:
```python
{
    "description": "vintage graphic tee",
    "size": "M" or None,
    "max_price": 30.0 or None
}
```

**What happens if it fails or returns nothing:**
If the LLM cannot parse the query or returns invalid data, returns a dict with an `"error"` key: `{"error": "Failed to parse query: ... Please clarify: what item are you looking for, what size (if any), and what's your max budget (if any)?"}`. The agent loop detects this error dict, stops, and asks the user to clarify. No further tools are called until the user provides valid input. 

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Tool Error Handling Pattern

**All tools use a consistent error-handling pattern:**
- **On success**: Return the normal output (list, string, or dict with result keys)
- **On failure**: Return a dict with an `"error"` key containing a descriptive error message

This allows the agent loop to check a single condition (`if "error" in result`) to detect all failures, regardless of the tool.

**Example:**
```python
# Success
search_listings("vintage tee") → [{ "id": "lst_001", "title": "...", ... }, ...]
suggest_outfit(item, wardrobe) → "Pair this with your jeans..."
create_fit_card(outfit, item) → "thrifted this for $22..."

# Failure (all tools)
parse_query("xyz") → {"error": "Failed to parse query: ..."}
suggest_outfit(item, None) → {"error": "LLM call failed: ..."}
create_fit_card("", item) → {"error": "Outfit description is empty."}
```

---

## Planning Loop

**How does your agent decide which tool to call next?**

All tools return either a success value or an error dict (see Tool Error Handling Pattern above). The agent loop checks each result after every tool call.

1. **Call parse_query** — Use the LLM to extract `description`, `size`, and `max_price` from the user's natural language input.
   - **If error** (`if "error" in result`): Return the error message to user and stop.
   - **If success**: Continue to step 2 with parsed values.

2. **Call search_listings** — Pass the parsed parameters to search for matching items.
   - **If error** (`if "error" in result`): Return the error message to user and stop.
   - **If empty list** (`if result == []`): Return "No listings matched your criteria. Try adjusting the price, size, or description." and stop.
   - **If success**: Continue to step 3 with `selected_item = result[0]`.

3. **Call suggest_outfit** — Pass `selected_item` and user's `wardrobe` to get outfit suggestion.
   - **If error** (`if "error" in result`): Return the error message to user and stop.
   - **If success**: Continue to step 4 with outfit string.

4. **Call create_fit_card** — Pass `outfit_suggestion` and `selected_item` to generate the social media caption.
   - **If error** (`if "error" in result`): Return the error message to user and stop.
   - **If success**: Continue to step 5.

5. **Return complete response** — Construct final output combining: item details, outfit suggestion, and fit card caption.

---

## State Management

**How does information from one tool get passed to the next?**

The agent maintains a `session` dict that persists throughout a single user interaction:

```python
session = {
    "query": "I'm looking for...",                 # Original user input
    "wardrobe": {...},                             # User's wardrobe dict (stored for access throughout)
    "parsed": {                                    # Output from parse_query
        "description": "vintage graphic tee",
        "size": "M" or None,
        "max_price": 30.0 or None
    },
    "search_results": [],                          # Output from search_listings (list of dicts)
    "selected_item": {...} or None,                # First result from search_results (used in suggest_outfit and create_fit_card)
    "outfit_suggestion": "Pair this with..." or None,  # Output from suggest_outfit
    "fit_card": "Caption text..." or None,        # Output from create_fit_card
    "error": None or "..."                         # Error message if any step fails
}
```

**Data flow:**
- **parse_query → search_listings:** `parsed` dict (description, size, max_price) becomes the input to search_listings
- **search_listings → suggest_outfit:** `selected_item` (first result from search_results) is passed to suggest_outfit along with `session["wardrobe"]`
- **suggest_outfit → create_fit_card:** `outfit_suggestion` is passed to create_fit_card along with `selected_item`
- **All outputs** are stored in the session dict; the final response is constructed in app.py by combining these fields

**Error handling:** If any step fails, the `error` field is set to a descriptive message and subsequent steps are skipped. The session is returned early without calling remaining tools.



---

## Error Handling

For each tool, describe the specific failure mode and the error dict the tool returns.

The agent loop checks all results with: `if "error" in result` to detect failures uniformly.

| Tool | Failure mode | Return value | Agent response |
|------|-------------|---|----------------|
| parse_query | Cannot parse query or invalid JSON response | `{"error": "Failed to parse query: ..."}` | Display error message; ask user to clarify item, size, price; stop and wait. |
| search_listings | No results match the query | `[]` (empty list, no error key) | Display "No listings matched"; suggest adjusting filters; stop. |
| suggest_outfit | LLM call fails or returns empty | `{"error": "..."}` | Display error message; stop without calling create_fit_card. |
| create_fit_card | Outfit is empty, missing, or LLM fails | `{"error": "..."}` | Display error message; stop. |

---

## Architecture

```
                              User Query
                                  │
                                  ▼
                        ┌─────────────────────┐
                        │  Planning Loop      │
                        │  (agent.py)         │
                        └─────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            ┌──────────────────┐         ┌──────────────────┐
            │  parse_query()   │         │  Session Dict    │
            │  (tools.py)      │         │  ────────────────│
            └──────────────────┘         │ • query          │
                    │                    │ • wardrobe       │
                    │ parsed =           │ • parsed         │
                    │ {desc,size,price}  │ • search_results │
                    │                    │ • selected_item  │
            ┌───────┴──────────┐         │ • outfit_sugges. │
            │                  │         │ • fit_card       │
     [Error]        [Success]           │ • error          │
       │                  │              └──────────────────┘
       │                  ▼                       ▲
       │          search_listings()               │ stores
       │          (tools.py)                      │ results
       │                  │                       │
       │                  ▼                       │
       │          results = [...]                 │
       │                  │                       │
       │         ┌────────┴────────┐              │
       │         │                 │              │
       │    [Empty]          [Items found]        │
       │      │                    │              │
       │      │                    ▼              │
       │      │            selected_item = ──────┼─ results[0]
       │      │                    │              │
       │      │                    ▼              │
       │      │         suggest_outfit() ────────┼─ (selected_item, wardrobe)
       │      │                    │              │
       │      │          ┌─────────┴─────────┐    │
       │      │          │                   │    │
       │      │     [Error]           [Success]   │
       │      │        │                   │      │
       │      │        │                   ▼      │
       │      │        │         outfit_suggestion┤─
       │      │        │                   │      │
       │      │        │                   ▼      │
       │      │        │       create_fit_card()─┼─ (outfit, selected_item)
       │      │        │                   │      │
       │      │        │          ┌────────┴──┐   │
       │      │        │          │           │   │
       │      │        │     [Error]    [Success]│
       │      │        │          │           │   │
       │      │        │          │           ▼   │
       │      │        │          │    fit_card ──┼─
       │      │        │          │           │   │
       └──────┴────────┴──────────┴───────────┤   │
                             │                │   │
                             ▼                ▼   │
                        ┌─────────────────┐       │
                        │ Format Response │◄──────┘
                        │ (error or full  │
                        │ outfit details) │
                        └─────────────────┘
                             │
                             ▼
                        Return to User
                        • Item details (success only)
                        • Outfit suggestion (success only)
                        • Social caption (success only)
                        • Error message (failure only)
```

**Data flow:**
- **User query** → Planning loop parses it with `parse_query()`
- **Parsed parameters** → `search_listings()` uses them to find matches
- **Search results** → Top item selected and stored in session
- **Selected item + wardrobe** → `suggest_outfit()` creates styling advice
- **Outfit suggestion + item** → `create_fit_card()` generates caption
- **All session data** → Formatted into final response to user

**Error branches:**
- If `parse_query` fails → return clarification request, stop
- If `search_listings` returns empty → return "no matches" message, stop
- If any tool produces error → return error message, skip remaining tools

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

For each tool, I will use Claude to generate the function implementation:

1. **search_listings**: Give Claude the Tool 1 spec block (what it does, inputs, return value, failure handling). Ask it to implement using `load_listings()` from `utils/data_loader.py`. Verify by checking: (a) filters by all three parameters (description, size, max_price), (b) handles empty results by returning `[]` not raising exception, (c) scores and sorts by relevance. Test with 3 queries: one that matches many items, one that matches few, one that matches none.

2. **suggest_outfit**: Give Claude the Tool 2 spec, the Groq API setup pattern (client initialization, model name), and instruction to use `_get_groq_client()` from tools.py. Verify: (a) LLM call succeeds, (b) returns non-empty string, (c) handles empty wardrobe gracefully (returns general advice, not crash), (d) output is specific to the new_item and wardrobe contents. Test with both example and empty wardrobe.

3. **create_fit_card**: Give Claude the Tool 3 spec and note that temperature should be higher for variability. Verify: (a) guards against empty outfit input, (b) returns error message string (not exception), (c) outputs vary across multiple calls, (d) caption sounds casual and mentions item/price/platform. Test by running 3 times on same input and confirming variation.

**Milestone 4 — Planning loop and state management:**

I will use Claude to implement `run_agent()` in agent.py:

1. **Input**: Give Claude the Planning Loop section (all 8 steps), the State Management section (session dict structure and data flow), and the Architecture diagram. Also provide the error handling table.

2. **Expected output**: A complete implementation of `run_agent()` that: (a) calls each tool in sequence according to the planning loop, (b) stores results in session dict, (c) checks for empty/error results after each step, (d) terminates early and sets `session["error"]` on failures, (d) returns the session dict at the end.

3. **Verification**: (a) Test the happy path with the example query in the file — confirm all three tools are called and final session has all fields populated. (b) Test the no-results path (already in __main__) — confirm agent stops after search_listings and returns error message. (c) Verify state passing by printing session after each step and confirming selected_item flows into suggest_outfit unchanged, outfit_suggestion flows into create_fit_card unchanged.

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1: Parse Query**
- **Tool called:** `parse_query()`
- **Input:** User's full query string
- **Why this tool:** Extract structured search parameters (description, size, max_price) from natural language
- **Output:** 
```python
{
    "description": "vintage graphic tee",
    "size": None,  # user didn't specify size
    "max_price": 30.0
}
```
- **Session update:** `session["parsed"]` = the dict above

**Step 2: Search Listings**
- **Tool called:** `search_listings()`
- **Input:** `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- **Why this tool:** Find all listings matching the user's criteria
- **Output:** List of 3 matching listings (e.g., "Faded Band Tee — $22, Depop, Good condition", "Vintage Nirvana Tee — $28, Thrift+, Fair condition", "Distressed Tour Tee — $19.99, Poshmark, Good condition"), sorted by relevance
- **Session update:** `session["search_results"]` = list of 3 dicts; `session["selected_item"]` = first result (the band tee at $22)

**Step 3: Suggest Outfit**
- **Tool called:** `suggest_outfit()`
- **Input:** `new_item` = the band tee listing dict, `wardrobe` = user's wardrobe (from data_loader with items like jeans, sneakers, etc.)
- **Why this tool:** Generate styling suggestions pairing the new item with existing wardrobe pieces
- **Output:** 
```
"Pair this faded band tee with your wide-leg baggy jeans and chunky platform sneakers 
for an authentic 90s grunge look. Roll the sleeves once and tuck the front corner 
slightly for shape. The oversized fit + cropped silhouette works perfectly with your style."
```
- **Session update:** `session["outfit_suggestion"]` = the string above

**Step 4: Create Fit Card**
- **Tool called:** `create_fit_card()`
- **Input:** `outfit` = the outfit suggestion string from Step 3, `new_item` = the band tee listing dict
- **Why this tool:** Generate a casual, shareable social media caption for the complete look
- **Output:**
```
"thrifted this faded band tee off depop for $22 and honestly it was made for my 
wide-legs 🖤 rolled the sleeves and it's perfect grunge energy. full look in my stories"
```
- **Session update:** `session["fit_card"]` = the string above; `session["error"]` = None (no errors)

**Final output to user:**
The agent presents three panels:
1. **Item found:** "Faded Band Tee — $22, Depop, Good condition"
2. **Outfit suggestion:** "Pair this faded band tee with your wide-leg baggy jeans and chunky platform sneakers for an authentic 90s grunge look..."
3. **Fit card (social caption):** "thrifted this faded band tee off depop for $22 and honestly it was made for my wide-legs 🖤..."

User sees a complete outfit recommendation with styling advice and a ready-to-post caption.
