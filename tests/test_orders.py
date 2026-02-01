import pytest
from unittest.mock import Mock, patch, MagicMock
from weni_utils.tools.orders import OrderConcierge

@pytest.fixture
def mock_client():
        with patch('weni_utils.tools.orders.VTEXClient') as mock:
        yield mock.return_value

@pytest.fixture
def concierge(mock_client):
    return OrderConcierge(
        base_url="https://test.vtex.com",
        store_url="https://test.com",
        vtex_app_key="key",
        vtex_app_token="token"
    )

def test_convert_cents(concierge):
    data = {
        "items": [
            {"price": 1000, "listPrice": 2000, "name": "Item 1"},
            {"price": 550, "listPrice": None, "name": "Item 2"}
        ],
        "totalValue": 1550,
        "otherField": 123
    }
    
    converted = concierge._convert_cents(data)
    
    assert converted["items"][0]["price"] == 10.00
    assert converted["items"][0]["listPrice"] == 20.00
    assert converted["items"][1]["price"] == 5.50
    assert converted["totalValue"] == 15.50
    assert converted["otherField"] == 123  # Unchanged

def test_search_orders(concierge, mock_client):
    mock_client.get_orders_by_document.return_value = {
        "list": [
            {"orderId": "1", "totalValue": 10000}
        ]
    }
    
    result = concierge.search_orders("12345678900")
    
    assert "brazil_time" in result
    assert len(result["orders"]["list"]) == 1
    assert result["orders"]["list"][0]["totalValue"] == 100.00
    mock_client.get_orders_by_document.assert_called_with("12345678900")

def test_get_order_details(concierge, mock_client):
    mock_client.get_order_by_id.return_value = {
        "orderId": "1", 
        "totalValue": 5000
    }
    
    result = concierge.get_order_details("1")
    
    assert "brazil_time" in result
    assert result["order"]["totalValue"] == 50.00
    mock_client.get_order_by_id.assert_called_with("1")

def test_get_order_not_found(concierge, mock_client):
    mock_client.get_order_by_id.return_value = None
    
    result = concierge.get_order_details("999")
    
    assert result["error"] == "Order not found"
    assert result["order"] is None
