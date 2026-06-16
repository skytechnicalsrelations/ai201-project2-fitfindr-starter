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
Returns an empty list `[]`. The planning loop detects this and tells the user no listings matched, suggests adjusting criteria, and stops without calling suggest_outfit or create_fit_card.

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
The tool is designed to handle empty wardrobe gracefully by returning general styling advice. Always returns a non-empty string. If the tool fails or returns empty (unexpected), the agent should treat this as an error and inform the user.

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
If outfit input is empty or missing, returns a descriptive error message string (not a Python exception). The agent detects this error string and informs the user that the fit card could not be generated.

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
If the LLM cannot parse the query or returns invalid data, the agent loop terminates and asks the user to clarify their request. The user must provide: what item they're looking for, desired size (if any), and maximum price (if any). No further tools are called until the user provides valid input. 

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**

1. **Call parse_query** — Use the LLM to extract `description`, `size`, and `max_price` from the user's natural language input. If parsing fails or returns invalid data:
   - Return error message asking user to clarify: "I couldn't understand your request. Please tell me: what item are you looking for, what size (if any), and what's your max budget (if any)?"
   - Stop. Do not call search_listings or any other tools.

2. **Call search_listings** — Pass the parsed parameters to search for matching items.

3. **Check search results** — If `results == []`:
   - Return error message: "No listings matched your criteria. Try adjusting the price, size, or description."
   - Stop. Do not call suggest_outfit or create_fit_card.

4. **Select top result** — If `results` is non-empty, select `selected_item = results[0]` and store in session.

5. **Call suggest_outfit** — Pass `selected_item` and user's `wardrobe` to get outfit suggestion.

6. **Check outfit suggestion** — If `outfit_suggestion` is empty or an error:
   - Return error message to user.
   - Stop. Do not call create_fit_card.

7. **Call create_fit_card** — Pass `outfit_suggestion` and `selected_item` to generate the social media caption.

8. **Return complete response** — Construct final output combining: item details, outfit suggestion, and fit card caption.

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

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| parse_query | Cannot parse query or returns invalid data | Ask user to clarify: what item, size, and max price. Stop and wait for clarification. |
| search_listings | No results match the query | Tell user no listings matched. Suggest adjusting price, size, or description. Stop. |
| suggest_outfit | Wardrobe is empty | Return general styling advice (tool handles this gracefully). |
| create_fit_card | Outfit input is missing or incomplete | Return error message. Tell user fit card could not be generated. |

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
            ┌───────┴─────────┐          │ • outfit_sugges. │
            │                 │          │ • fit_card       │
     [Parse fails]      [Parse OK]       │ • error          │
       │                  │              └──────────────────┘
       │                  │                       ▲
       ▼                  ▼                       │
    Error msg       search_listings()            │
     Return │         (tools.py)                 │ stores
            │              │                     │ results
            │              ▼                     │
            │        results = [...]             │
            │              │                     │
            │         ┌─────┴─────┐              │
            │         │           │              │
            │    [Empty]      [Items found]      │
            │      │               │             │
            │      ▼               ▼             │
            │   Error msg    selected_item = ───┼─ results[0]
            │   Return │         │               │
            │          │         │               │
            │          │         ▼               │
            │          │    suggest_outfit() ────┼─ (selected_item, wardrobe)
            │          │         │               │
            │          │         ▼               │
            │          │    outfit_suggestion ──┼─ (string)
            │          │         │               │
            │          │         ▼               │
            │          │    create_fit_card() ──┼─ (outfit, selected_item)
            │          │         │               │
            │          │         ▼               │
            │          │    fit_card (string) ──┼─ (string)
            │          │         │               │
            └──────────┴─────────┤               │
                        │        │               │
                        ▼        ▼               │
                   ┌─────────────────┐           │
                   │ Format Response │◄──────────┘
                   │ (error or full  │
                   │ outfit details) │
                   └─────────────────┘
                        │
                        ▼
                   Return to User
                   • Item details
                   • Outfit suggestion
                   • Social caption
                   (OR error message)
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

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
