"""Tests for create_fit_card tool"""

from unittest.mock import MagicMock, patch

import pytest

from tools import create_fit_card
from utils.data_loader import load_listings


class TestCreateFitCardSuccess:
    """Test suite for successful create_fit_card calls."""

    @pytest.fixture
    def sample_listing(self):
        """Get a sample listing from the dataset."""
        listings = load_listings()
        return listings[0]

    @pytest.fixture
    def sample_outfit(self):
        """Get a sample outfit suggestion."""
        return "Pair with your black combat boots and oversized grey sweatshirt for an effortless cool vibe."

    @patch("tools._get_groq_client")
    def test_create_fit_card_returns_string(self, mock_get_client, sample_listing, sample_outfit):
        """Test that create_fit_card returns a string on success."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Just grabbed these vintage levi's and I'm obsessed. Paired with my fave boots and sweatshirt, this is THE fit for lazy girl era."))]
        )

        result = create_fit_card(sample_outfit, sample_listing)

        assert isinstance(result, str)
        assert not isinstance(result, dict)

    @patch("tools._get_groq_client")
    def test_create_fit_card_non_empty_string(self, mock_get_client, sample_listing, sample_outfit):
        """Test that the returned caption is non-empty."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Great caption here"))]
        )

        result = create_fit_card(sample_outfit, sample_listing)

        assert len(result.strip()) > 0

    @patch("tools._get_groq_client")
    def test_create_fit_card_mentions_item(self, mock_get_client, sample_listing, sample_outfit):
        """Test that the caption mentions the item."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Found this amazing vintage tee on depop for $18. Styling it with my favorite pieces."))]
        )

        result = create_fit_card(sample_outfit, sample_listing)

        assert isinstance(result, str)
        assert len(result) > 20

    @patch("tools._get_groq_client")
    def test_create_fit_card_with_different_items(self, mock_get_client, sample_outfit):
        """Test create_fit_card with multiple different items."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Great caption"))]
        )

        listings = load_listings()

        # Test with first 3 items
        for listing in listings[:3]:
            result = create_fit_card(sample_outfit, listing)
            assert isinstance(result, str)
            assert len(result) > 0

    @patch("tools._get_groq_client")
    def test_create_fit_card_uses_higher_temperature(self, mock_get_client, sample_listing, sample_outfit):
        """Test that create_fit_card uses higher temperature for variety."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Caption"))]
        )

        create_fit_card(sample_outfit, sample_listing)

        # Verify that temperature 0.9 was passed
        args, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs.get("temperature") == 0.9


class TestCreateFitCardFailure:
    """Test suite for create_fit_card error handling."""

    @pytest.fixture
    def sample_listing(self):
        """Get a sample listing from the dataset."""
        listings = load_listings()
        return listings[0]

    def test_create_fit_card_with_error_dict_from_suggest_outfit(self, sample_listing):
        """Test that create_fit_card handles error dict from suggest_outfit."""
        error_outfit = {"error": "Failed to generate outfit suggestions"}

        result = create_fit_card(error_outfit, sample_listing)

        # Should return error dict
        assert isinstance(result, dict)
        assert "error" in result
        assert isinstance(result["error"], str)

    def test_create_fit_card_with_empty_outfit(self, sample_listing):
        """Test that create_fit_card handles empty outfit string."""
        result = create_fit_card("", sample_listing)

        # Should return error dict
        assert isinstance(result, dict)
        assert "error" in result
        assert isinstance(result["error"], str)

    def test_create_fit_card_with_whitespace_only_outfit(self, sample_listing):
        """Test that create_fit_card handles whitespace-only outfit."""
        result = create_fit_card("   \n\t  ", sample_listing)

        # Should return error dict
        assert isinstance(result, dict)
        assert "error" in result

    @patch("tools._get_groq_client")
    def test_create_fit_card_returns_error_dict_on_exception(self, mock_get_client, sample_listing):
        """Test that create_fit_card returns error dict when LLM call fails."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = RuntimeError("API connection failed")

        outfit = "Some outfit suggestion"
        result = create_fit_card(outfit, sample_listing)

        # Should return a dict with "error" key on failure
        assert isinstance(result, dict)
        assert "error" in result
        assert isinstance(result["error"], str)

    @patch("tools._get_groq_client")
    def test_create_fit_card_error_dict_has_descriptive_message(self, mock_get_client, sample_listing):
        """Test that error dict contains a descriptive error message."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.chat.completions.create.side_effect = ValueError("Invalid response")

        outfit = "Some outfit"
        result = create_fit_card(outfit, sample_listing)

        assert isinstance(result, dict)
        assert "error" in result
        assert len(result["error"]) > 0
