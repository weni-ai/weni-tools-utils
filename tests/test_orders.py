import pytest
from unittest.mock import MagicMock
from weni_utils.tools.client import VTEXClient, ProxyRequest


class TestOrderConcierge:
    """Tests for order-related functionality."""

    def test_convert_cents(self):
        """Test conversion of cents to currency units."""
        # Create a minimal VTEXClient instance for testing
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
        )
        
        data = {
            "items": [
                {"price": 1000, "listPrice": 2000, "name": "Item 1"},
                {"price": 550, "listPrice": None, "name": "Item 2"}
            ],
            "totalValue": 1550,
            "otherField": 123
        }
        
        converted = client._convert_cents(data)
        
        assert converted["items"][0]["price"] == 10.00
        assert converted["items"][0]["listPrice"] == 20.00
        assert converted["items"][1]["price"] == 5.50
        assert converted["totalValue"] == 15.50
        assert converted["otherField"] == 123  # Unchanged


class TestProxyRequest:
    """Tests for proxy request functionality."""

    def test_get_order_by_id(self):
        """Test making a proxy request to get order by ID."""
        # Create a mock context
        mock_context = MagicMock()
        mock_context.project = {"auth_token": "test_token"}
        
        proxy = ProxyRequest(context=mock_context)
        
        # Note: This test requires mocking the actual HTTP request
        # For now, just test the _format_body_proxy_request method
        body = proxy._format_body_proxy_request(
            body=None,
            method="GET",
            path="/api/orders/pvt/document/1543930505162-01"
        )
        
        assert body["method"] == "GET"
        assert body["path"] == "/api/orders/pvt/document/1543930505162-01"
