"""
Test suite for agent.py using mocks to test the planning loop logic.

Tests the run_agent() function in isolation, mocking each tool to verify:
- Correct tool call sequence
- Proper state management
- Error handling at each step
- Early termination on failures
"""

import pytest
from unittest.mock import patch, MagicMock

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def example_wardrobe():
    """Return example wardrobe for tests."""
    return get_example_wardrobe()


@pytest.fixture
def empty_wardrobe():
    """Return empty wardrobe for tests."""
    return get_empty_wardrobe()


@pytest.fixture
def mock_listing():
    """Return a mock listing dict."""
    return {
        "id": "lst_001",
        "title": "Vintage Graphic Tee",
        "description": "A cool 90s band tee",
        "category": "tops",
        "style_tags": ["vintage", "grunge"],
        "size": "M",
        "condition": "good",
        "price": 25.0,
        "colors": ["black", "white"],
        "brand": "Nirvana",
        "platform": "depop",
    }


# ── Happy Path Tests ──────────────────────────────────────────────────────────


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_run_agent_happy_path(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, example_wardrobe
):
    """Test complete successful flow through all three tools."""
    # Setup mocks
    mock_parse.return_value = {
        "description": "vintage graphic tee",
        "size": "M",
        "max_price": 30.0,
    }
    mock_search.return_value = [mock_listing]
    mock_outfit.return_value = "Pair with baggy jeans and chunky sneakers"
    mock_card.return_value = "thrifted this tee for $25 and love it!"

    # Run agent
    result = run_agent("vintage graphic tee under $30 size M", example_wardrobe)

    # Verify no error
    assert result["error"] is None

    # Verify state is populated
    assert result["parsed"] == {
        "description": "vintage graphic tee",
        "size": "M",
        "max_price": 30.0,
    }
    assert len(result["search_results"]) == 1
    assert result["selected_item"] == mock_listing
    assert result["outfit_suggestion"] == "Pair with baggy jeans and chunky sneakers"
    assert result["fit_card"] == "thrifted this tee for $25 and love it!"

    # Verify all tools were called in order
    mock_parse.assert_called_once_with("vintage graphic tee under $30 size M")
    mock_search.assert_called_once_with(
        description="vintage graphic tee", size="M", max_price=30.0
    )
    mock_outfit.assert_called_once_with(new_item=mock_listing, wardrobe=example_wardrobe)
    mock_card.assert_called_once()


# ── Error Handling Tests ──────────────────────────────────────────────────────


@patch("agent.parse_query")
def test_parse_query_error(mock_parse, example_wardrobe):
    """Test agent stops if parse_query returns an error dict."""
    mock_parse.return_value = {
        "error": "Could not understand query. Please clarify what item you're looking for."
    }

    result = run_agent("xyz gibberish query", example_wardrobe)

    # Verify error is set and agent returns early
    assert result["error"] == "Could not understand query. Please clarify what item you're looking for."
    assert result["search_results"] == []
    assert result["selected_item"] is None
    assert result["outfit_suggestion"] is None
    assert result["fit_card"] is None
    # Verify no other tools were called
    mock_parse.assert_called_once()


@patch("agent.search_listings")
@patch("agent.parse_query")
def test_search_listings_error(mock_parse, mock_search, example_wardrobe, mock_listing):
    """Test agent stops if search_listings returns an error dict."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = {"error": "Failed to search listings: database connection error"}

    result = run_agent("vintage tee under $50", example_wardrobe)

    # Verify error is set
    assert result["error"] == "Failed to search listings: database connection error"
    assert result["selected_item"] is None
    assert result["outfit_suggestion"] is None
    assert result["fit_card"] is None


@patch("agent.search_listings")
@patch("agent.parse_query")
def test_search_listings_empty(mock_parse, mock_search, example_wardrobe):
    """Test agent stops gracefully if search_listings returns empty list."""
    mock_parse.return_value = {
        "description": "designer ballgown",
        "size": "XXS",
        "max_price": 5.0,
    }
    mock_search.return_value = []  # Empty list, not an error dict

    result = run_agent("designer ballgown size XXS under $5", example_wardrobe)

    # Verify error is set with helpful message
    assert result["error"] == "No listings matched your criteria. Try adjusting the price, size, or description."
    assert result["search_results"] == []
    assert result["selected_item"] is None
    assert result["outfit_suggestion"] is None
    assert result["fit_card"] is None


@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_suggest_outfit_error(
    mock_parse, mock_search, mock_outfit, mock_listing, example_wardrobe
):
    """Test agent stops if suggest_outfit returns an error dict."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = [mock_listing]
    mock_outfit.return_value = {"error": "Failed to generate outfit suggestions: LLM call failed"}

    result = run_agent("vintage tee under $50", example_wardrobe)

    # Verify error is set
    assert result["error"] == "Failed to generate outfit suggestions: LLM call failed"
    assert result["selected_item"] == mock_listing
    assert result["outfit_suggestion"] == {"error": "Failed to generate outfit suggestions: LLM call failed"}
    assert result["fit_card"] is None  # Should not be called


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_create_fit_card_error(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, example_wardrobe
):
    """Test agent stops if create_fit_card returns an error dict."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = [mock_listing]
    mock_outfit.return_value = "Pair with baggy jeans"
    mock_card.return_value = {"error": "Failed to generate caption: outfit is empty"}

    result = run_agent("vintage tee under $50", example_wardrobe)

    # Verify error is set
    assert result["error"] == "Failed to generate caption: outfit is empty"
    assert result["fit_card"] == {"error": "Failed to generate caption: outfit is empty"}


# ── State Management Tests ────────────────────────────────────────────────────


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_state_flows_correctly_through_tools(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, example_wardrobe
):
    """Verify that state from one tool flows correctly to the next."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": "M",
        "max_price": 30.0,
    }
    mock_search.return_value = [mock_listing]
    outfit_text = "Wear with jeans"
    mock_outfit.return_value = outfit_text
    mock_card.return_value = "Instagram caption here"

    result = run_agent("vintage tee under $30 size M", example_wardrobe)

    # Verify suggest_outfit received the correct item
    call_args = mock_outfit.call_args
    assert call_args[1]["new_item"] == mock_listing
    assert call_args[1]["wardrobe"] == example_wardrobe

    # Verify create_fit_card received the correct outfit
    call_args = mock_card.call_args
    assert call_args[1]["outfit"] == outfit_text
    assert call_args[1]["new_item"] == mock_listing


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_empty_wardrobe_passed_to_suggest_outfit(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, empty_wardrobe
):
    """Verify empty wardrobe is correctly passed to suggest_outfit."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = [mock_listing]
    mock_outfit.return_value = "General styling advice for empty wardrobe"
    mock_card.return_value = "Caption"

    result = run_agent("vintage tee", empty_wardrobe)

    # Verify suggest_outfit received the empty wardrobe
    call_args = mock_outfit.call_args
    assert call_args[1]["wardrobe"] == empty_wardrobe
    assert len(call_args[1]["wardrobe"].get("items", [])) == 0


# ── Tool Call Sequence Tests ──────────────────────────────────────────────────


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_tools_not_called_after_parse_error(
    mock_parse, mock_search, mock_outfit, mock_card, example_wardrobe
):
    """Verify search_listings is not called if parse_query fails."""
    mock_parse.return_value = {"error": "Parse error"}

    run_agent("bad query", example_wardrobe)

    # Only parse_query should be called
    mock_parse.assert_called_once()
    mock_search.assert_not_called()
    mock_outfit.assert_not_called()
    mock_card.assert_not_called()


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_tools_not_called_after_search_error(
    mock_parse, mock_search, mock_outfit, mock_card, example_wardrobe
):
    """Verify suggest_outfit is not called if search_listings fails."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = {"error": "Search error"}

    run_agent("vintage tee", example_wardrobe)

    # parse_query and search_listings should be called
    mock_parse.assert_called_once()
    mock_search.assert_called_once()
    # But not the remaining tools
    mock_outfit.assert_not_called()
    mock_card.assert_not_called()


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_create_fit_card_not_called_after_outfit_error(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, example_wardrobe
):
    """Verify create_fit_card is not called if suggest_outfit fails."""
    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = [mock_listing]
    mock_outfit.return_value = {"error": "Outfit generation failed"}

    run_agent("vintage tee", example_wardrobe)

    # parse_query, search_listings, and suggest_outfit should be called
    mock_parse.assert_called_once()
    mock_search.assert_called_once()
    mock_outfit.assert_called_once()
    # But not create_fit_card
    mock_card.assert_not_called()


# ── Multiple Results Test ────────────────────────────────────────────────────


@patch("agent.create_fit_card")
@patch("agent.suggest_outfit")
@patch("agent.search_listings")
@patch("agent.parse_query")
def test_selects_first_result_from_multiple(
    mock_parse, mock_search, mock_outfit, mock_card, mock_listing, example_wardrobe
):
    """Verify agent selects the first (top) result from search_results."""
    second_listing = mock_listing.copy()
    second_listing["id"] = "lst_002"
    second_listing["title"] = "Another Tee"

    mock_parse.return_value = {
        "description": "vintage tee",
        "size": None,
        "max_price": 50.0,
    }
    mock_search.return_value = [mock_listing, second_listing]  # Multiple results
    mock_outfit.return_value = "Outfit"
    mock_card.return_value = "Caption"

    result = run_agent("vintage tee", example_wardrobe)

    # Verify first result is selected
    assert result["selected_item"] == mock_listing
    assert result["selected_item"]["title"] == "Vintage Graphic Tee"

    # Verify suggest_outfit received the first item
    call_args = mock_outfit.call_args
    assert call_args[1]["new_item"] == mock_listing
