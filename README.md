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

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**

**Step 1 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 2 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Step 3 — Tool called:**
- Tool:
- Input:
- Why this tool:
- Output:

**Final output to user:**

---

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

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**

**One divergence from your spec, and why:**

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
