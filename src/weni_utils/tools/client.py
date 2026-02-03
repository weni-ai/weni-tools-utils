"""
VTEXClient - Client for VTEX APIs

This module contains all communication logic with VTEX APIs,
extracted and consolidated from existing agents.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests

@dataclass
class ProductVariation:
    """Represents a product variation (SKU)"""

    sku_id: str
    sku_name: str
    variations: str  # Format: "[Color: White, Size: M]"
    price: Optional[float] = None
    spot_price: Optional[float] = None
    list_price: Optional[float] = None
    pix_price: Optional[float] = None
    credit_card_price: Optional[float] = None
    image_url: str = ""
    seller_id: Optional[str] = None
    available_quantity: int = 0


@dataclass
class Product:
    """Represents a product with its variations"""

    name: str
    description: str
    brand: str
    product_link: str
    image_url: str
    categories: List[str]
    specification_groups: List[Dict]
    variations: List[ProductVariation]


class VTEXClient():
    """
    Client for communication with VTEX APIs.

    Centralizes all API calls for:
    - Intelligent Search (product search)
    - Cart Simulation (stock verification)
    - Regions (regionalization)
    - SKU Details (product details)

    Example:
        client = VTEXClient(
            base_url="https://store.vtexcommercestable.com.br",
            store_url="https://store.com.br"
        )

        products = client.intelligent_search("drill")
    """

    def __init__(
        self,
        base_url: str,
        store_url: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize the VTEX client.

        Args:
            base_url: VTEX API base URL (e.g., https://store.vtexcommercestable.com.br)
            store_url: Store URL (e.g., https://store.com.br)
            vtex_app_key: App Key for authenticated APIs (optional)
            vtex_app_token: App Token for authenticated APIs (optional)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.store_url = store_url.rstrip("/")
        if not self._validate_base_url_and_store_url():
            raise ValueError("Base URL or store URL is invalid")

        self.vtex_app_key = vtex_app_key
        self.vtex_app_token = vtex_app_token
        self.timeout = timeout

    def _get_auth_headers(self) -> Dict[str, str]:
        """Return authentication headers if available"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.vtex_app_key and self.vtex_app_token:
            headers["X-VTEX-API-AppKey"] = self.vtex_app_key
            headers["X-VTEX-API-AppToken"] = self.vtex_app_token

        return headers

    def _validate_base_url_and_store_url(self) -> bool:
        """Validate if the base URL and store URL are valid"""
        if not self.base_url or not self.store_url:
            return False
        
        if not self.base_url.startswith("https://") or not self.store_url.startswith("https://"):
            return False

        if not self.base_url.endswith((".vtexcommercestable.com.br", "myvtex.com")):
            return False
        
        return True

    def intelligent_search(
        self,
        product_name: str,
        brand_name: str = "",
        region_id: Optional[str] = None,
        hide_unavailable: bool = True,
        trade_policy_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
        allow_redirect: bool = False,
    ) -> List[Dict]:
        """
        Search products using VTEX Intelligent Search API.
        
        Returns only raw data from the API, without processing.
        Formatting, filtering, and limiting logic should be done by the agent.

        Args:
            product_name: Product name to search
            brand_name: Product brand (optional)
            region_id: Region ID for regionalization (optional)
            hide_unavailable: Whether to hide unavailable products
            trade_policy_id: Trade policy / sales channel ID (optional)
            cluster_id: Filter by collection ID (optional)
            allow_redirect: Whether to allow redirects (optional)

        Returns:
            List of raw products from VTEX API
        """
        # Build URL with or without regionalization
        query = f"{product_name} {brand_name}".strip()

        # Build path segments
        path_segments = []
        if trade_policy_id:
            path_segments.append(f"trade-policy/{trade_policy_id}")
        if region_id:
            path_segments.append(f"region-id/{region_id}")
        if cluster_id:
            path_segments.append(f"productClusterIds/{cluster_id}")

        path = "/".join(path_segments)
        if path:
            path = f"{path}/"

        search_url = (
            f"{self.base_url}/api/io/_v/api/intelligent-search/product_search/{path}"
            f"?query={query}&simulationBehavior=default"
            f"&hideUnavailableItems={str(hide_unavailable).lower()}"
            f"&allowRedirect={str(allow_redirect).lower()}"
        )

        try:
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Intelligent search error: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON processing error: {e}")
            return []

    def cart_simulation(
        self, items: List[Dict], country: str = "BRA", postal_code: Optional[str] = None
    ) -> Dict:
        """
        Perform cart simulation to check availability.

        Args:
            items: List of items [{id, quantity, seller}]
            country: Country code
            postal_code: Postal code (optional)

        Returns:
            Simulation response
        """
        url = f"{self.base_url}/api/checkout/pub/orderForms/simulation"

        payload = {"items": items, "country": country}

        if postal_code:
            payload["postalCode"] = postal_code

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Cart simulation error: {e}")
            return {"items": []}

    def batch_simulation(
        self,
        sku_id: str,
        quantity: int,
        sellers: List[str],
        postal_code: str,
        max_quantity_per_seller: int = 8000,
        max_total_quantity: int = 24000,
    ) -> Optional[Dict]:
        """
        Simulate a specific SKU with multiple sellers (used for regionalization).

        Args:
            sku_id: SKU ID
            quantity: Desired quantity
            sellers: List of sellers
            postal_code: Postal code
            max_quantity_per_seller: Maximum quantity per seller
            max_total_quantity: Maximum total quantity

        Returns:
            Best simulation result or None
        """
        quantity = int(quantity)

        # Calculate quantity per seller
        if len(sellers) > 1:
            total_quantity = min(quantity * len(sellers), max_total_quantity)
            quantity_per_seller = min(total_quantity // len(sellers), max_quantity_per_seller)
        else:
            quantity_per_seller = min(quantity, max_quantity_per_seller)

        items = [
            {"id": sku_id, "quantity": quantity_per_seller, "seller": seller} for seller in sellers
        ]

        url = f"{self.base_url}/_v/api/simulations-batches?sc=1&RnbBehavior=1"
        payload = {"items": items, "country": "BRA", "postalCode": postal_code}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            simulation_data = response.json()

            data_content = simulation_data.get("data", {})
            if not data_content:
                return None

            sku_simulations = data_content.get(sku_id, [])
            if not sku_simulations:
                return None

            # Return simulation with highest quantity
            return max(sku_simulations, key=lambda x: x.get("quantity", 0))

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Batch simulation error: {e}")
            return None

    def get_region(
        self, postal_code: str, trade_policy: int, country_code: str
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Query the regionalization API to get region and sellers.

        Args:
            postal_code: Postal code

        Returns:
            Tuple (region_id, error_message, sellers)
        """
        region_url = f"{self.base_url}/api/checkout/pub/regions?country={country_code}&postalCode={postal_code}&sc={trade_policy}"

        try:
            response = requests.get(region_url, timeout=self.timeout)
            response.raise_for_status()
            regions_data = response.json()

            if not regions_data:
                return (
                    None,
                    "We don't serve your region. Please visit our stores in person.",
                    [],
                )

            region = regions_data[0]
            sellers = region.get("sellers", [])

            if not sellers:
                return (
                    None,
                    "We don't serve your region. Please visit our stores in person.",
                    [],
                )

            region_id = region.get("id")
            seller_ids = [seller.get("id") for seller in sellers]

            return region_id, None, seller_ids

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Regionalization error: {e}")
            return None, f"Error querying regionalization: {e}", []

    def get_sku_details(self, sku_id: str) -> Dict:
        """
        Get SKU details (dimensions, weight, etc).
        Requires VTEX credentials.

        Args:
            sku_id: SKU ID

        Returns:
            Dictionary with SKU details
        """
        default_response = {
            "PackagedHeight": None,
            "PackagedLength": None,
            "PackagedWidth": None,
            "PackagedWeightKg": None,
            "Height": None,
            "Length": None,
            "Width": None,
            "WeightKg": None,
            "CubicWeight": None,
        }

        if not self.vtex_app_key or not self.vtex_app_token:
            return default_response

        url = f"{self.base_url}/api/catalog/pvt/stockkeepingunit/{sku_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)

            if response.status_code != 200:
                return default_response

            data = response.json()

            return {
                "PackagedHeight": data.get("PackagedHeight"),
                "PackagedLength": data.get("PackagedLength"),
                "PackagedWidth": data.get("PackagedWidth"),
                "PackagedWeightKg": data.get("PackagedWeightKg"),
                "Height": data.get("Height"),
                "Length": data.get("Length"),
                "Width": data.get("Width"),
                "WeightKg": data.get("WeightKg"),
                "CubicWeight": data.get("CubicWeight"),
            }

        except Exception:
            return default_response

    def get_product_by_sku(self, sku_id: str) -> Optional[Dict]:
        """
        Search for a specific product by SKU ID.

        Args:
            sku_id: SKU ID

        Returns:
            Product data or None
        """
        search_url = f"{self.base_url}/api/io/_v/api/intelligent-search/product_search/?query=sku.id:{sku_id}"

        try:
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            products = data.get("products", [])
            if not products:
                return None

            return products[0]

        except Exception as e:
            print(f"ERROR: Error searching SKU {sku_id}: {e}")
            return None

    def get_orders_by_document(self, document: str, incomplete_orders: bool = False) -> Dict:
        """
        Search orders by document.

        Args:
            document: Customer document

        Returns:
            Dictionary with orders list
        """
        if not document:
            return {"list": []}

        # Search complete orders
        url = f"{self.base_url}/api/oms/pvt/orders?q={document}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            orders_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Error searching orders: {e}")
            orders_data = {"list": []}

        # Search incomplete orders
        url_incomplete = f"{self.base_url}/api/oms/pvt/orders?q={document}&incompleteOrders={str(incomplete_orders).lower()}"

        try:
            response_incomplete = requests.get(
                url_incomplete, headers=self._get_auth_headers(), timeout=self.timeout
            )
            response_incomplete.raise_for_status()
            orders_data_incomplete = response_incomplete.json()

            if orders_data_incomplete and "list" in orders_data_incomplete:
                if "list" not in orders_data:
                    orders_data["list"] = []
                orders_data["list"].extend(orders_data_incomplete["list"])

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Error searching incomplete orders: {e}")

        return orders_data

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Search order by ID.

        Args:
            order_id: Order ID

        Returns:
            Dictionary with order data or None
        """
        if not order_id:
            return None

        url = f"{self.base_url}/api/oms/pvt/orders/{order_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Error searching order {order_id}: {e}")
            return None
