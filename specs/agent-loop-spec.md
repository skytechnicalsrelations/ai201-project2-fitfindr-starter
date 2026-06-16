# Spec: Planning Loop and State Management

**File:** `agent.py`
**Status:** Complete all sections before implementing

---

## Purpose

Orchestrate the FitFindr agent — a planning loop that decides which tools to call based on user input and search results. The agent must:
1. Search for listings matching the user's criteria
2. If listings are found, suggest an outfit pairing
3. If the outfit suggestion succeeds, create a social media caption
4. Handle failures gracefully at each step

---

## Input / Output Contract

**Inputs:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_query` | `str` | The user's full request (e.g., "I'm looking for a vintage graphic tee under $30...") |
| `wardrobe` | `dict` | The user's existing wardrobe (from data loader) |

**Output:** `dict` (session state)

```python
{
    "user_query": "...",
    "search_results": [...] or None,
    "selected_item": {...} or None,
    "outfit_suggestion": "..." or None,
    "fit_card": "..." or None,
    "error": "..." or None,
    "final_response": "..."  # what the user sees
}
```

---

## Planning Loop Logic

*Complete the fields below. Describe the exact conditional branches — not just intent, but specific logic.*

---

### Step 1: Parse user input and call search_listings

<!-- What information from the user_query will you extract? Which parameters go to search_listings? -->

```
[your answer here]
```

---

### Step 2: Check search results — first branch point

<!-- What do you check? If empty, what happens? If results exist, what happens next? -->

```
[your answer here]
```

---

### Step 3: Call suggest_outfit (only if search succeeded)

<!-- What data from search_listings goes into suggest_outfit? Exactly which dict/string fields? -->

```
[your answer here]
```

---

### Step 4: Call create_fit_card (only if suggest_outfit succeeded)

<!-- What data from suggest_outfit goes into create_fit_card? -->

```
[your answer here]
```

---

### Step 5: Construct final response

<!-- How do you decide what message to show the user? Different response text for different branches (found/not found, outfit suggested/not suggested, etc.)? -->

```
[your answer here]
```

---

## State Management

**What data is stored in the session dict, and when?**

<!-- For each piece of state (search_results, selected_item, outfit_suggestion, fit_card, error), describe:
     - When it gets set
     - What format it's in
     - How it's passed to the next tool
     - What happens if it's empty/None -->

```
[your answer here]
```

---

## Error Handling

For each tool, describe the specific error condition and what the agent does.

| Tool | Error condition | Agent response | Session state |
|------|-----------------|-----------------|------------------|
| search_listings | Returns empty list `[]` | | |
| suggest_outfit | Wardrobe is empty | | |
| create_fit_card | Outfit input is empty/None | | |

---

## Architecture Diagram

<!-- Draw your agent here using ASCII art or a Mermaid diagram.
     Include:
     - User input
     - Planning loop decision points
     - Each tool call
     - State storage
     - Error branches
     - Final output to user
     
     Example structure:
     User query
       │
       ▼
     Parse & extract params
       │
       ▼
     search_listings(description, size, max_price)
       │
       ├─ results == []
       │   │
       │   └─► [ERROR path] return error message → user
       │
       ├─ results != []
       │   │
       │   ▼ select results[0]
       │ Session: selected_item = results[0]
       │   │
       │   ▼
       ├─► suggest_outfit(selected_item, wardrobe)
       │   │
       │   ▼ outfit_text
       │ Session: outfit_suggestion = outfit_text
       │   │
       │   ▼
       └─► create_fit_card(outfit_text, selected_item)
           │
           ▼ caption
         Session: fit_card = caption
           │
           ▼
         Format final response
           │
           ▼
         Return session to user
 -->

```
[Draw your diagram here]
```

---

## Implementation Notes

*Fill this in after implementing and testing.*

**Trace of a complete interaction (what tools were called and in what order):**

```
Query: [example query]
Tool 1: [tool name, inputs]
Result: [what was returned]
Tool 2: [tool name, inputs]
Result: [what was returned]
Tool 3: [tool name, inputs]
Result: [what was returned]
Final response: [what the user saw]
```

---

**What happens when search_listings returns an empty list?**

```
[Describe what you observed — did the agent skip suggest_outfit? Did it display an error?]
```

---

**What happens when the wardrobe is empty?**

```
[Describe the behavior]
```

---

**What happens when create_fit_card receives an empty outfit string?**

```
[Describe the behavior]
```

---

**One thing about the planning loop that surprised you:**

```
[your answer here]
```
