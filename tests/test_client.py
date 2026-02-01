"""
Tests for VTEXClient
"""

import pytest
from unittest.mock import Mock, patch
from weni_utils.tools.client import VTEXClient


class TestVTEXClient:
    """Tests for the VTEXClient class."""
    
    def test_init(self):
        """Test client initialization."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        assert client.base_url == "https://test.vtexcommercestable.com.br"
        assert client.store_url == "https://test.com.br"
        assert client.vtex_app_key is None
        assert client.vtex_app_token is None
    
    def test_init_with_credentials(self):
        """Test client initialization with VTEX credentials."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
            vtex_app_key="my-app-key",
            vtex_app_token="my-app-token"
        )
        
        assert client.vtex_app_key == "my-app-key"
        assert client.vtex_app_token == "my-app-token"
    
    def test_clean_image_url(self):
        """Test image URL cleaning."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        # Test with query parameters
        url = "https://test.com/image.jpg?v=123&size=large"
        assert client._clean_image_url(url) == "https://test.com/image.jpg"
        
        # Test with fragment
        url = "https://test.com/image.png#section"
        assert client._clean_image_url(url) == "https://test.com/image.png"
        
        # Test with both
        url = "https://test.com/image.gif?v=1#top"
        assert client._clean_image_url(url) == "https://test.com/image.gif"
        
        # Test empty
        assert client._clean_image_url("") == ""
        assert client._clean_image_url(None) == ""
    
    def test_format_variations(self):
        """Test variation formatting."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        variations = [
            {"name": "Cor", "values": ["Azul", "Verde"]},
            {"name": "Tamanho", "values": ["M", "G"]}
        ]
        
        result = client._format_variations(variations)
        assert result == "[Cor: Azul, Tamanho: M]"
        
        # Test empty
        assert client._format_variations([]) == "[]"
    
    def test_get_auth_headers_without_credentials(self):
        """Test auth headers without credentials."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        headers = client._get_auth_headers()
        
        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "X-VTEX-API-AppKey" not in headers
        assert "X-VTEX-API-AppToken" not in headers
    
    def test_get_auth_headers_with_credentials(self):
        """Test auth headers with credentials."""
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
            vtex_app_key="my-key",
            vtex_app_token="my-token"
        )
        
        headers = client._get_auth_headers()
        
        assert headers["X-VTEX-API-AppKey"] == "my-key"
        assert headers["X-VTEX-API-AppToken"] == "my-token"


class TestVTEXClientSearch:
    """Tests for VTEXClient search methods."""
    
    @patch('requests.get')
    def test_intelligent_search_success(self, mock_get):
        """Test successful intelligent search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "products": [
                {
                    "productName": "Test Product",
                    "description": "A test product",
                    "brand": "TestBrand",
                    "link": "/test-product",
                    "categories": ["/Category/"],
                    "specificationGroups": [],
                    "items": [
                        {
                            "itemId": "123",
                            "nameComplete": "Test Product - Blue",
                            "variations": [{"name": "Cor", "values": ["Blue"]}],
                            "images": [{"imageUrl": "https://test.com/img.jpg"}],
                            "sellers": [
                                {
                                    "sellerId": "1",
                                    "sellerDefault": True,
                                    "commertialOffer": {
                                        "Price": 99.90,
                                        "AvailableQuantity": 10
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        mock_get.return_value = mock_response
        
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        result = client.intelligent_search("test product")
        
        assert "Test Product" in result
        assert result["Test Product"]["brand"] == "TestBrand"
        assert len(result["Test Product"]["variations"]) == 1
    
    @patch('requests.get')
    def test_intelligent_search_empty(self, mock_get):
        """Test intelligent search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"products": []}
        mock_get.return_value = mock_response
        
        client = VTEXClient(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        result = client.intelligent_search("nonexistent product")
        
        assert result == {}
