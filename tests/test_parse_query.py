"""
Tests for the parse_query tool.

Tests cover:
- Happy path: full query with description, size, and max_price
- Partial queries: only some fields specified
- Edge cases: empty, whitespace-only, ambiguous queries
- Error handling: LLM failures and invalid responses
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from tools import parse_query


class TestParseQueryHappyPath:
    """Test successful parsing of well-formed queries."""

    @patch("tools._get_groq_client")
    def test_full_query_with_all_fields(self, mock_get_client):
        """Test parsing a query with description, size, and price."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "vintage graphic tee",
            "size": "M",
            "max_price": 30.0,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("I'm looking for a vintage graphic tee in size M under $30")

        assert result["description"] == "vintage graphic tee"
        assert result["size"] == "M"
        assert result["max_price"] == 30.0

    @patch("tools._get_groq_client")
    def test_query_without_size(self, mock_get_client):
        """Test parsing a query with no size specified."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "denim jacket",
            "size": None,
            "max_price": 75.0,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("I want a denim jacket for under 75 dollars")

        assert result["description"] == "denim jacket"
        assert result["size"] is None
        assert result["max_price"] == 75.0

    @patch("tools._get_groq_client")
    def test_query_without_price(self, mock_get_client):
        """Test parsing a query with no max_price specified."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "black sneakers",
            "size": "US 10",
            "max_price": None,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("Looking for black sneakers in US size 10")

        assert result["description"] == "black sneakers"
        assert result["size"] == "US 10"
        assert result["max_price"] is None

    @patch("tools._get_groq_client")
    def test_query_description_only(self, mock_get_client):
        """Test parsing a query with only description."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "vintage band tee",
            "size": None,
            "max_price": None,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("Show me vintage band tees")

        assert result["description"] == "vintage band tee"
        assert result["size"] is None
        assert result["max_price"] is None


class TestParseQueryEdgeCases:
    """Test edge cases and ambiguous queries."""

    @patch("tools._get_groq_client")
    def test_query_with_all_none(self, mock_get_client):
        """Test parsing an ambiguous query where nothing can be extracted."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": None,
            "size": None,
            "max_price": None,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("xyz meaningless text")

        assert result["description"] is None
        assert result["size"] is None
        assert result["max_price"] is None
        assert "error" not in result

    @patch("tools._get_groq_client")
    def test_query_with_whitespace_around_response(self, mock_get_client):
        """Test that JSON response is parsed correctly even with extra whitespace."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Response with leading/trailing whitespace
        response_text = """
        {
            "description": "vintage leather jacket",
            "size": "L",
            "max_price": 100.0
        }
        """
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=response_text))]
        )

        result = parse_query("vintage leather jacket, large, under 100")

        assert result["description"] == "vintage leather jacket"
        assert result["size"] == "L"
        assert result["max_price"] == 100.0


class TestParseQueryErrors:
    """Test error handling and failure modes."""

    @patch("tools._get_groq_client")
    def test_invalid_json_response(self, mock_get_client):
        """Test handling of invalid JSON from LLM."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Return invalid JSON
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="not valid json"))]
        )

        result = parse_query("some query")

        assert "error" in result
        assert "Failed to parse query" in result["error"]

    @patch("tools._get_groq_client")
    def test_missing_required_keys_in_response(self, mock_get_client):
        """Test handling when LLM response is missing expected keys."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Return JSON without required keys
        response_dict = {"unexpected_key": "value"}
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("some query")

        # Should gracefully handle missing keys using .get()
        assert result["description"] is None
        assert result["size"] is None
        assert result["max_price"] is None
        assert "error" not in result

    @patch("tools._get_groq_client")
    def test_empty_response_content(self, mock_get_client):
        """Test handling of empty response content."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Return response with empty choices list
        mock_client.chat.completions.create.return_value = MagicMock(choices=[])

        result = parse_query("some query")

        assert "error" in result

    @patch("tools._get_groq_client")
    def test_api_key_missing(self, mock_get_client):
        """Test handling when API key is not available."""
        mock_get_client.side_effect = ValueError("GROQ_API_KEY not set")

        with pytest.raises(ValueError, match="GROQ_API_KEY not set"):
            parse_query("some query")


class TestParseQueryIntegration:
    """Integration tests that verify realistic query patterns."""

    @patch("tools._get_groq_client")
    def test_realistic_query_with_price_symbol(self, mock_get_client):
        """Test that LLM correctly extracts price even with $ symbol."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "oversized hoodie",
            "size": "XL",
            "max_price": 50.0,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query("Looking for an oversized hoodie XL under $50")

        assert result["description"] == "oversized hoodie"
        assert result["size"] == "XL"
        assert result["max_price"] == 50.0

    @patch("tools._get_groq_client")
    def test_realistic_query_with_complex_description(self, mock_get_client):
        """Test extraction from a complex multi-part query."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        response_dict = {
            "description": "y2k cargo pants",
            "size": "W30",
            "max_price": 45.0,
        }
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
        )

        result = parse_query(
            "I'm looking for some vintage y2k cargo pants in waist 30, "
            "nothing over $45 please"
        )

        assert result["description"] == "y2k cargo pants"
        assert result["size"] == "W30"
        assert result["max_price"] == 45.0

    @patch("tools._get_groq_client")
    def test_realistic_query_size_variations(self, mock_get_client):
        """Test that various size formats are handled."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        test_cases = [
            ("M", "a medium shirt"),
            ("US 8", "shoes size US 8"),
            ("W26 L34", "jeans W26 L34"),
            ("One Size", "a one-size beanie"),
        ]

        for size, query in test_cases:
            response_dict = {
                "description": "test item",
                "size": size,
                "max_price": None,
            }
            mock_client.chat.completions.create.return_value = MagicMock(
                choices=[MagicMock(message=MagicMock(content=json.dumps(response_dict)))]
            )

            result = parse_query(query)
            assert result["size"] == size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
