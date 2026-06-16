# Spec: Tool Functions

**File:** `tools.py`
**Status:** Complete all sections before implementing.

---

## Purpose

These three functions are the tools the agent can call. They search for clothing listings, generate outfit suggestions, and create social media captions. Each tool returns structured data to the agent loop, which uses it to inform the next step.

---

## Function 1: `search_listings()`

### Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `description` | `str` | The type/style of item the user is looking for |
| `size` | `str \| None` | The size (e.g., "M", "L", "S") or `None` to include all sizes |
| `max_price` | `float` | Maximum price in dollars; only return items at or below this price |

**Output:** `list`

When listings are **found**, return:
```python
[
  {"id": "...", "title": "...", "price": 22.0, ...},
  {"id": "...", "title": "...", "price": 19.50, ...},
  ...
]
```

When **no listings** match the filters, return:
```python
[]
```

---

### Design Decisions

*Complete the blank fields below before implementing.*

---

#### Search strategy

<!-- How will you filter the listings? Which fields will you check? In what order? -->

```
[your answer here]
```

---

#### Field matching approach

<!-- How will you handle case sensitivity for size? Should "M" match "medium"? Should you normalize the description input before searching? -->

```
[your answer here]
```

---

#### Result ordering

<!-- If multiple listings match, how will you sort them (by price, relevance, condition)? -->

```
[your answer here]
```

---

#### Implementation Notes

*Fill this in after implementing and testing.*

**Test: does `search_listings("vintage graphic tee", size=None, max_price=50)` return results?**
```
[yes / no — if no, describe what happened]
```

**Test: does `search_listings("jacket", size="M", max_price=20)` correctly filter by size AND price?**
```
[yes / no — if no, describe what happened]
```

**One edge case you discovered while implementing:**
```
[your answer here]
```

---

## Function 2: `suggest_outfit()`

### Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `new_item` | `dict` | A listing dict (from `search_listings`) containing at least `title`, `style_tags`, `colors`, `brand`, `condition` |
| `wardrobe` | `dict` | The user's wardrobe dict (from `get_example_wardrobe()` or `get_empty_wardrobe()`) with an `items` list |

**Output:** `str`

A text suggestion describing how to style the new item with the user's existing wardrobe. Must be at least 1–2 sentences, specific to the wardrobe contents.

When the wardrobe is **empty**, still return useful styling advice (general advice that doesn't depend on specific items).

---

### Design Decisions

*Complete the blank fields below before implementing.*

---

#### LLM call approach

<!-- What model will you use (e.g., Groq's llama-3.3-70b-versatile)? What environment variable holds the API key? -->

```
[your answer here]
```

---

#### Prompt construction

<!-- What information from new_item and wardrobe will you include in the prompt to the LLM? How will you format the wardrobe data for the LLM to read? -->

```
[your answer here]
```

---

#### Empty wardrobe handling

<!-- How will the LLM know the wardrobe is empty? What instruction will you give it to still produce useful output? -->

```
[your answer here]
```

---

#### Implementation Notes

*Fill this in after implementing and testing.*

**Test: does `suggest_outfit(listing, wardrobe)` return a non-empty string?**
```
[yes / no — if no, describe what happened]
```

**Test: does `suggest_outfit(listing, get_empty_wardrobe())` return useful styling advice even with an empty wardrobe?**
```
[yes / no — what was returned?]
```

**One edge case you discovered while implementing:**
```
[your answer here]
```

---

## Function 3: `create_fit_card()`

### Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `outfit` | `str` | The outfit suggestion text (from `suggest_outfit`) |
| `new_item` | `dict` | The listing dict with fields like `title`, `platform`, `price`, `condition` |

**Output:** `str`

A social media caption (tweet/Instagram post style) that references the new item and styling advice. Must be creative, concise, and include relevant details (price, platform, vibe).

When `outfit` is **empty or None**, return an error message string (not a Python exception).

---

### Design Decisions

*Complete the blank fields below before implementing.*

---

#### LLM call approach

<!-- Same LLM and key as suggest_outfit? -->

```
[your answer here]
```

---

#### Prompt construction

<!-- What tone/style should the caption have? Should it mention the platform (Depop, Thrift, etc.)? Should it include budget-friendly language? -->

```
[your answer here]
```

---

#### Empty outfit handling

<!-- What error message will you return if outfit is empty? Make it useful to the agent (so the agent knows what went wrong). -->

```
[your answer here]
```

---

#### Variability

<!-- Should the LLM outputs vary each time, or be deterministic? If varied, what temperature will you use? -->

```
[your answer here]
```

---

#### Implementation Notes

*Fill this in after implementing and testing.*

**Test: does `create_fit_card(outfit, item)` return a non-empty string?**
```
[yes / no]
```

**Test: running `create_fit_card(outfit, item)` three times on the same input — do the outputs vary?**
```
[yes / no — show one example of variation, or explain why they should be identical]
```

**Test: does `create_fit_card("", item)` return an error message string (not raise an exception)?**
```
[yes / no — what was returned?]
```

**One edge case you discovered while implementing:**
```
[your answer here]
```
