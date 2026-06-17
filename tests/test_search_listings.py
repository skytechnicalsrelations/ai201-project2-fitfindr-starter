"""Tests for search_listings tool"""

from unittest.mock import patch

import pytest

from tools import search_listings


class TestSearchListings:
    """Test suite for the search_listings function."""

    def test_basic_search(self):
        """Test basic search without filters."""
        results = search_listings("vintage graphic tee")
        assert len(results) > 0
        assert all(isinstance(item, dict) for item in results)

    def test_search_with_price_filter(self):
        """Test search with price filter."""
        results = search_listings("vintage graphic tee", max_price=30)
        assert len(results) > 0
        assert all(item["price"] <= 30 for item in results)

    def test_search_with_size_filter(self):
        """Test search with size filter."""
        results = search_listings("vintage graphic tee", size="M")
        assert len(results) > 0
        assert all("m" in item["size"].lower() for item in results)

    def test_search_with_both_filters(self):
        """Test search with both price and size filters."""
        results = search_listings("vintage graphic tee", size="L", max_price=40)
        assert len(results) > 0
        assert all(item["price"] <= 40 for item in results)
        assert all("l" in item["size"].lower() for item in results)

    def test_no_matches(self):
        """Test search with no matching results."""
        results = search_listings("flying unicorn xyz abc")
        assert results == []

    def test_relevance_sorting(self):
        """Test that results are sorted by relevance."""
        results = search_listings("blue denim")
        assert len(results) > 0

        # Higher scoring items should come first
        # The first result should have both keywords in its fields
        first_item = results[0]
        search_text = (
            f"{first_item['title']} {first_item['description']} "
            f"{' '.join(first_item['style_tags'])} "
            f"{' '.join(first_item['colors'])} "
            f"{first_item.get('brand', '')} {first_item['category']}"
        ).lower()
        assert "blue" in search_text and "denim" in search_text

    def test_returns_listing_dict_structure(self):
        """Test that returned items have all required fields."""
        results = search_listings("vintage tee")
        assert len(results) > 0

        required_fields = [
            "id", "title", "description", "category", "style_tags",
            "size", "condition", "price", "colors", "brand", "platform"
        ]
        for item in results[:3]:  # Check first 3 results
            for field in required_fields:
                assert field in item, f"Missing field: {field}"

    def test_case_insensitive_size_matching(self):
        """Test that size matching is case-insensitive."""
        results_lower = search_listings("shirt", size="m")
        results_upper = search_listings("shirt", size="M")
        results_mixed = search_listings("shirt", size="M")

        # All should find items with 'm' in the size
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_size_substring_matching(self):
        """Test that size matching uses substring (e.g., 'M' matches 'S/M')."""
        results = search_listings("shirt", size="M")
        # Should match both "M" and "S/M" and "L/M" etc.
        assert len(results) > 0
        for item in results:
            assert "m" in item["size"].lower()

    def test_price_inclusive_boundary(self):
        """Test that price filter is inclusive at boundary."""
        # Find an item with a specific price
        all_results = search_listings("vintage")
        if all_results:
            exact_price = all_results[0]["price"]
            results = search_listings("vintage", max_price=exact_price)
            # Should include items at exactly the max price
            assert any(item["price"] == exact_price for item in results)

    def test_empty_description(self):
        """Test search with empty description."""
        results = search_listings("")
        # Empty description should match nothing (no keywords)
        assert results == []

    def test_single_keyword(self):
        """Test search with single keyword."""
        results = search_listings("denim")
        assert len(results) > 0
        # All results should contain 'denim' somewhere
        for item in results:
            search_text = (
                f"{item['title']} {item['description']} "
                f"{' '.join(item['style_tags'])} "
                f"{' '.join(item['colors'])} "
                f"{item.get('brand', '')} {item['category']}"
            ).lower()
            assert "denim" in search_text


class TestSearchListingsFailure:
    """Test suite for search_listings error handling."""

    @patch("tools.load_listings")
    def test_search_listings_returns_error_dict_on_exception(self, mock_load):
        """Test that search_listings returns error dict when loading fails."""
        mock_load.side_effect = RuntimeError("Failed to load listings file")

        result = search_listings("vintage tee")

        # Should return a dict with "error" key on failure
        assert isinstance(result, dict)
        assert "error" in result
        assert isinstance(result["error"], str)
        assert "Failed to search listings" in result["error"]

    @patch("tools.load_listings")
    def test_search_listings_error_dict_has_descriptive_message(self, mock_load):
        """Test that error dict contains a descriptive error message."""
        mock_load.side_effect = FileNotFoundError("Listings file not found")

        result = search_listings("shirt")

        assert isinstance(result, dict)
        assert "error" in result
        assert len(result["error"]) > 0
