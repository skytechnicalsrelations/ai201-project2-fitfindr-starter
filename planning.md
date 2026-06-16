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

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

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
