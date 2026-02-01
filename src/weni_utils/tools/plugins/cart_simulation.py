"""
Cart Simulation Plugin - Simulação de Carrinho VTEX

Plugin para realizar simulações de carrinho e verificar disponibilidade de produtos.
Retorna dados brutos da API VTEX.
"""

from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from ..client import VTEXClient


class CartSimulation:
    """
    Plugin para simulação de carrinho VTEX.

    Funcionalidades:
    - Simula carrinho simples
    - Simula carrinho batch (múltiplos sellers)
    - Verifica disponibilidade de estoque
    - Retorna dados brutos da API

    Example:
        from weni_utils.tools.plugins import CartSimulation
        from weni_utils.tools import VTEXClient

        client = VTEXClient(base_url="...", store_url="...")
        cart = CartSimulation(client)

        # Simulação simples
        result = cart.simulate(
            items=[{"id": "61556", "quantity": 1, "seller": "1"}],
            postal_code="01310-100"
        )

        # Simulação batch
        result = cart.simulate_batch(
            sku_id="61556",
            sellers=["store1000", "store1003"],
            postal_code="01310-100",
            quantity=10
        )
    """

    def __init__(self, client: "VTEXClient"):
        """
        Inicializa o plugin de simulação de carrinho.

        Args:
            client: Instância do VTEXClient
        """
        self.client = client

    def simulate(
        self,
        items: List[Dict],
        country: str = "BRA",
        postal_code: Optional[str] = None,
    ) -> Dict:
        """
        Realiza simulação de carrinho para verificar disponibilidade.

        Args:
            items: Lista de itens [{id, quantity, seller}]
            country: Código do país (default: "BRA")
            postal_code: CEP (opcional)

        Returns:
            Resposta bruta da simulação da API VTEX

        Example:
            result = cart.simulate(
                items=[
                    {"id": "61556", "quantity": 1, "seller": "1"},
                    {"id": "82598", "quantity": 2, "seller": "1"}
                ],
                postal_code="01310-100"
            )
        """
        return self.client.cart_simulation(
            items=items, country=country, postal_code=postal_code
        )

    def simulate_batch(
        self,
        sku_id: str,
        sellers: List[str],
        postal_code: str,
        quantity: int = 1,
        max_quantity_per_seller: int = 8000,
        max_total_quantity: int = 24000,
    ) -> Optional[Dict]:
        """
        Simula um SKU específico com múltiplos sellers (usado para regionalização).

        Args:
            sku_id: ID do SKU
            quantity: Quantidade desejada (default: 1)
            sellers: Lista de sellers
            postal_code: CEP
            max_quantity_per_seller: Quantidade máxima por seller (default: 8000)
            max_total_quantity: Quantidade máxima total (default: 24000)

        Returns:
            Melhor resultado da simulação ou None

        Example:
            result = cart.simulate_batch(
                sku_id="61556",
                sellers=["store1000", "store1003"],
                postal_code="01310-100",
                quantity=10
            )
        """
        return self.client.batch_simulation(
            sku_id=sku_id,
            quantity=quantity,
            sellers=sellers,
            postal_code=postal_code,
            max_quantity_per_seller=max_quantity_per_seller,
            max_total_quantity=max_total_quantity,
        )

    def check_stock_availability(
        self,
        sku_ids: List[str],
        seller: str = "1",
        quantity: int = 1,
        country: str = "BRA",
        postal_code: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Verifica disponibilidade de estoque para uma lista de SKUs.

        Args:
            sku_ids: Lista de SKU IDs
            seller: Seller ID (default: "1")
            quantity: Quantidade a verificar (default: 1)
            country: Código do país (default: "BRA")
            postal_code: CEP (opcional)

        Returns:
            Dicionário {sku_id: available}

        Example:
            availability = cart.check_stock_availability(
                sku_ids=["61556", "82598", "40240"],
                quantity=2
            )
            # {"61556": True, "82598": True, "40240": False}
        """
        items = [
            {"id": sku_id, "quantity": quantity, "seller": seller} for sku_id in sku_ids
        ]

        result = self.simulate(items=items, country=country, postal_code=postal_code)

        availability = {}
        for item in result.get("items", []):
            sku_id = item.get("id")
            is_available = item.get("availability", "").lower() == "available"
            availability[sku_id] = is_available

        # SKUs não presentes na resposta estão indisponíveis
        for sku_id in sku_ids:
            if sku_id not in availability:
                availability[sku_id] = False

        return availability

    def get_product_price(
        self,
        sku_id: str,
        seller_id: str = "1",
        quantity: int = 1,
        country: str = "BRA",
    ) -> Dict[str, Optional[float]]:
        """
        Obtém preço de um produto via simulação de carrinho.

        Args:
            sku_id: SKU ID
            seller_id: Seller ID (default: "1")
            quantity: Quantidade (default: 1)
            country: Código do país (default: "BRA")

        Returns:
            Dicionário com price e list_price

        Example:
            price = cart.get_product_price(sku_id="61556")
            # {"price": 198.90, "list_price": 249.90}
        """
        result = self.simulate(
            items=[{"id": sku_id, "quantity": quantity, "seller": seller_id}],
            country=country,
        )

        items = result.get("items", [])
        if not items:
            return {"price": None, "list_price": None}

        item = items[0]
        price = item.get("price")
        list_price = item.get("listPrice")

        # Converte de centavos se necessário
        if price and price > 1000:
            price = price / 100
        if list_price and list_price > 1000:
            list_price = list_price / 100

        return {"price": price, "list_price": list_price}
