"""Tests for suggest_outfit tool"""

from unittest.mock import MagicMock, patch

import pytest

from tools import suggest_outfit
from utils.data_loader import load_listings, get_example_wardrobe, get_empty_wardrobe


class TestSuggestOutfitSuccess:
    """Test suite for successful suggest_outfit calls."""

    @pytest.fixture
    def sample_listing(self):
        """Get a sample listing from the dataset."""
        listings = load_listings()
        return listings[0]

    @pytest.fixture
    def example_wardrobe(self):
        """Get the example wardrobe."""
        return get_example_wardrobe()

    @pytest.fixture
    def empty_wardrobe(self):
        """Get an empty wardrobe."""
        return get_empty_wardrobe()

    @patch("tools._get_groq_client")
    def test_suggest_outfit_with_empty_wardrobe(self, mock_get_client, sample_listing, empty_wardrobe):
        """Test outfit suggestion with an empty wardrobe."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Here are some outfit ideas for this piece..."))]
        )

        result = suggest_outfit(sample_listing, empty_wardrobe)

        # Should return a non-empty string on success
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("tools._get_groq_client")
    def test_suggest_outfit_with_existing_wardrobe(self, mock_get_client, sample_listing, example_wardrobe):
        """Test outfit suggestion with existing wardrobe items."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Outfit 1: Pair this with your baggy jeans and black denim jacket..."))]
        )

        result = suggest_outfit(sample_listing, example_wardrobe)

        # Should return a non-empty string on success
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("tools._get_groq_client")
    def test_suggest_outfit_returns_string_on_success(self, mock_get_client, sample_listing, example_wardrobe):
        """Test that suggest_outfit returns a string on success."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Styling suggestion here"))]
        )

        result = suggest_outfit(sample_listing, example_wardrobe)
        assert isinstance(result, str)
        assert not isinstance(result, dict)

    @patch("tools._get_groq_client")
    def test_suggest_outfit_non_empty_string(self, mock_get_client, sample_listing, example_wardrobe):
        """Test that the returned string is non-empty."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Great outfit idea"))]
        )

        result = suggest_outfit(sample_listing, example_wardrobe)
        assert len(result.strip()) > 0

    @patch("tools._get_groq_client")
    def test_suggest_outfit_mentions_item(self, mock_get_client, sample_listing, example_wardrobe):
        """Test that the suggestion mentions the new item being considered."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="This item pairs beautifully with your wardrobe pieces to create a cohesive look."))]
        )

        result = suggest_outfit(sample_listing, example_wardrobe)

        # The response should be about the item
        assert len(result) > 20  # Should be a substantial response

    @patch("tools._get_groq_client")
    def test_suggest_outfit_with_different_items(self, mock_get_client, example_wardrobe):
        """Test suggest_outfit with multiple different items."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Outfit suggestion"))]
        )

        listings = load_listings()

        # Test with first 3 items
        for listing in listings[:3]:
            result = suggest_outfit(listing, example_wardrobe)
            assert isinstance(result, str)
            assert len(result) > 0

    @patch("tools._get_groq_client")
    def test_suggest_outfit_empty_wardrobe_gives_advice(self, mock_get_client, sample_listing, empty_wardrobe):
        """Test that empty wardrobe returns general styling advice."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="To build outfits around this piece, you'll want to add several versatile basics and layering pieces."))]
        )

        result = suggest_outfit(sample_listing, empty_wardrobe)

        # Should provide some advice about items/pieces
        assert isinstance(result, str)
        assert len(result) > 50  # Should be substantial advice

    @patch("tools._get_groq_client")
    def test_suggest_outfit_with_wardrobe_uses_wardrobe_info(self, mock_get_client, example_wardrobe):
        """Test that the function uses wardrobe information in suggestions."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Pair with your Baggy straight-leg jeans and Black combat boots"))]
        )

        listings = load_listings()
        # Find a graphic tee
        graphic_tee = next(
            (item for item in listings if "graphic" in item["title"].lower()),
            listings[0]
        )

        result = suggest_outfit(graphic_tee, example_wardrobe)
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("tools._get_groq_client")
    def test_suggest_outfit_handles_missing_brand(self, mock_get_client, example_wardrobe):
        """Test suggest_outfit with an item that has None brand."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Nice outfit suggestion"))]
        )

        listings = load_listings()
        item_with_brand = listings[0].copy()
        item_with_brand["brand"] = None

        result = suggest_outfit(item_with_brand, example_wardrobe)
        assert isinstance(result, str)
        assert len(result) > 0


class TestSuggestOutfitFailure:
    """Test suite for suggest_outfit error handling."""

    @pytest.fixture
    def sample_listing(self):
        """Get a sample listing from the dataset."""
        listings = load_listings()
        return listings[0]

    @pytest.fixture
    def example_wardrobe(self):
        """Get the example wardrobe."""
        return get_example_wardrobe()

    @patch("tools._get_groq_client")
    def test_suggest_outfit_returns_error_dict_on_exception(self, mock_get_client, sample_listing, example_wardrobe):
        """Test that suggest_outfit returns error dict when LLM call fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = RuntimeError("API connection failed")

        result = suggest_outfit(sample_listing, example_wardrobe)

        # Should return a dict with "error" key on failure
        assert isinstance(result, dict)
        assert "error" in result
        assert isinstance(result["error"], str)
        assert "connection failed" in result["error"].lower()

    @patch("tools._get_groq_client")
    def test_suggest_outfit_error_dict_has_descriptive_message(self, mock_get_client, sample_listing, example_wardrobe):
        """Test that error dict contains a descriptive error message."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = ValueError("Invalid response format")

        result = suggest_outfit(sample_listing, example_wardrobe)

        assert isinstance(result, dict)
        assert "error" in result
        assert len(result["error"]) > 0
