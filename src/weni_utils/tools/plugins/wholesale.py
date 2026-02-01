"""
Wholesale Plugin - Preços de Atacado

Plugin para clientes que trabalham com preços de atacado (quantidade mínima).
Adiciona informações de minQuantity e valueAtacado aos produtos.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import requests

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Wholesale(PluginBase):
    """
    Plugin de preços de atacado.

    Funcionalidades:
    - Busca preço de atacado (valueAtacado) por SKU
    - Busca quantidade mínima (minQuantity) para preço de atacado
    - Adiciona informações aos produtos após verificação de estoque

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                Wholesale(
                    fixed_price_url="https://www.loja.com.br/fixedprices"
                )
            ]
        )
    """

    name = "wholesale"

    def __init__(self, fixed_price_url: Optional[str] = None, timeout: int = 10):
        """
        Inicializa o plugin de atacado.

        Args:
            fixed_price_url: URL base para consulta de preços fixos
                            Se não fornecida, tenta derivar da URL da loja
            timeout: Timeout para requisições
        """
        self.fixed_price_url = fixed_price_url
        self.timeout = timeout
        self._cache: Dict[str, Dict] = {}

    def after_stock_check(
        self, products_with_stock: List[Dict], context: "SearchContext", client: "VTEXClient"
    ) -> List[Dict]:
        """
        Adiciona informações de preço de atacado após verificação de estoque.
        """
        if not products_with_stock:
            return products_with_stock

        # Define URL base se não foi fornecida
        base_url = self.fixed_price_url
        if not base_url:
            # Tenta derivar da store_url do client
            base_url = f"{client.store_url}/fixedprices"

        enriched_products = []

        for product in products_with_stock:
            sku_id = product.get("sku_id")
            seller_id = product.get("sellerId")

            if sku_id and seller_id:
                fixed_price_data = self._get_fixed_price(base_url, seller_id, sku_id)

                product_enriched = product.copy()
                product_enriched.update(
                    {
                        "minQuantity": fixed_price_data.get("minQuantity"),
                        "valueAtacado": fixed_price_data.get("valueAtacado"),
                    }
                )
                enriched_products.append(product_enriched)
            else:
                enriched_products.append(product)

        return enriched_products

    def _get_fixed_price(
        self, base_url: str, seller_id: str, sku_id: str
    ) -> Dict[str, Optional[Any]]:
        """
        Busca preço fixo (atacado) para um SKU.

        Args:
            base_url: URL base para a API de preços fixos
            seller_id: ID do seller
            sku_id: ID do SKU

        Returns:
            Dicionário com minQuantity e valueAtacado
        """
        cache_key = f"{seller_id}:{sku_id}"

        # Verifica cache
        if cache_key in self._cache:
            return self._cache[cache_key]

        url = f"{base_url}/{seller_id}/{sku_id}/1"

        default_response = {"minQuantity": None, "valueAtacado": None}

        try:
            response = requests.get(url, timeout=self.timeout)

            if response.status_code != 200:
                return default_response

            data = response.json()

            result = {
                "minQuantity": data.get("minQuantity") if isinstance(data, dict) else None,
                "valueAtacado": data.get("value") if isinstance(data, dict) else None,
            }

            # Salva no cache
            self._cache[cache_key] = result

            return result

        except Exception as e:
            print(f"ERROR: Erro ao buscar preço de atacado: {e}")
            return default_response

    def clear_cache(self) -> None:
        """Limpa o cache de preços."""
        self._cache.clear()
