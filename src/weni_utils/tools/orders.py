"""
OrderConcierge - Classe principal para busca de pedidos

Esta classe orquestra a busca de pedidos e tratamento de dados.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import pytz

from .client import VTEXClient


class OrderConcierge:
    """
    Classe principal para busca de pedidos VTEX.

    Example:
        concierge = OrderConcierge(
            base_url="https://loja.vtexcommercestable.com.br",
            store_url="https://loja.com.br"
        )

        orders = concierge.search_orders("12345678900")
        order_details = concierge.get_order_details("123456")
    """

    def __init__(
        self,
        base_url: str,
        store_url: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
    ):
        """
        Inicializa o OrderConcierge.

        Args:
            base_url: URL base da API VTEX
            store_url: URL da loja
            vtex_app_key: App Key VTEX (opcional)
            vtex_app_token: App Token VTEX (opcional)
        """
        self.client = VTEXClient(
            base_url=base_url,
            store_url=store_url,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
        )

    def _convert_cents(self, data: Any) -> Any:
        """
        Converte valores em centavos para reais.

        Args:
            data: Dados a converter

        Returns:
            Dados convertidos
        """
        currency_fields = [
            "totalValue",
            "value",
            "totals",
            "itemPrice",
            "sellingPrice",
            "price",
            "listPrice",
            "costPrice",
            "basePrice",
            "fixedPrice",
            "shippingEstimate",
            "tax",
            "discount",
            "total",
            "subtotal",
            "freight",
            "marketingData",
            "paymentData",
        ]

        if isinstance(data, dict):
            converted_data = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    converted_data[key] = self._convert_cents(value)
                elif isinstance(value, (int, float)) and any(
                    field in key.lower() for field in currency_fields
                ):
                    converted_data[key] = round(value / 100, 2) if value is not None else value
                else:
                    converted_data[key] = value
            return converted_data
        elif isinstance(data, list):
            return [self._convert_cents(item) for item in data]
        else:
            return data

    def search_orders(self, document: str) -> Dict[str, Any]:
        """
        Busca pedidos por documento.

        Args:
            document: Documento do cliente

        Returns:
            Dicionário com pedidos e data atual
        """
        orders_data = self.client.get_orders_by_document(document)
        converted_orders = self._convert_cents(orders_data)

        return {
            "orders": converted_orders,
            "brazil_time": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        }

    def get_order_details(self, order_id: str) -> Dict[str, Any]:
        """
        Busca detalhes de um pedido.

        Args:
            order_id: ID do pedido

        Returns:
            Dicionário com detalhes do pedido e data atual
        """
        order_data = self.client.get_order_by_id(order_id)

        if not order_data:
            return {"error": "Order not found", "order": None}

        converted_order = self._convert_cents(order_data)

        return {
            "order": converted_order,
            "brazil_time": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime(
                "%d/%m/%Y %H:%M:%S"
            ),
        }
