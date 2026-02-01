"""
Regionalization Plugin - Regionalização por CEP

Plugin para clientes que precisam de regionalização baseada em CEP.
Determina a região e sellers disponíveis antes da busca.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Regionalization(PluginBase):
    """
    Plugin de regionalização por CEP.

    Funcionalidades:
    - Obtém region_id baseado no CEP
    - Obtém lista de sellers disponíveis para a região
    - Aplica regras específicas de sellers (ex: regras da Mooca)
    - Adiciona mensagem de erro se região não é atendida

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[Regionalization()]
        )

        # Com regras específicas de sellers
        concierge = ProductConcierge(
            plugins=[
                Regionalization(
                    seller_rules={
                        "mooca_sellers": ["loja1000", "loja1003", "loja1500"],
                        "retirada_sellers": ["loja1000", "loja1003"],
                        "entrega_sellers": ["loja1000", "loja1500"],
                    },
                    priority_categories=[
                        "/Categoria/Subcategoria/",
                    ]
                )
            ]
        )
    """

    name = "regionalization"

    def __init__(
        self,
        seller_rules: Optional[Dict[str, List[str]]] = None,
        priority_categories: Optional[List[str]] = None,
        require_delivery_type_for_priority: bool = False,
        default_seller: str = "1",
    ):
        """
        Inicializa o plugin de regionalização.

        Args:
            seller_rules: Regras customizadas de sellers por região/tipo
            priority_categories: Categorias que requerem lógica especial
            require_delivery_type_for_priority: Se True, exige delivery_type para categorias prioritárias
            default_seller: Seller padrão quando não há regionalização
        """
        self.seller_rules = seller_rules or {}
        self.priority_categories = priority_categories or []
        self.require_delivery_type_for_priority = require_delivery_type_for_priority
        self.default_seller = default_seller

    def before_search(self, context: "SearchContext", client: "VTEXClient") -> "SearchContext":
        """
        Obtém região e sellers antes da busca.
        """
        if not context.postal_code:
            # Sem CEP, usa seller padrão
            context.sellers = [self.default_seller]
            return context

        # Consulta API de regionalização
        region_id, error, sellers = client.get_region(
            context.postal_code, context.trade_policy, context.country_code
        )

        context.region_id = region_id
        context.region_error = error

        if error:
            # Usa seller padrão em caso de erro
            context.sellers = [self.default_seller]
        else:
            context.sellers = sellers

        # Aplica regras customizadas de sellers
        context.sellers = self._apply_seller_rules(
            context.sellers, context.delivery_type, context.seller_rules
        )

        return context

    def _apply_seller_rules(
        self, sellers: List[str], delivery_type: Optional[str], seller_rules: Dict[str, List[str]]
    ) -> List[str]:
        """
        Aplica regras customizadas de sellers.

        Args:
            sellers: Lista de sellers da região
            delivery_type: Tipo de entrega (Retirada/Entrega)

        Returns:
            Lista de sellers filtrada
        """
        if not seller_rules:
            return sellers

        if seller_rules and all(seller in seller_rules for seller in sellers):
            if delivery_type == "Retirada":
                return seller_rules.get("retirada_sellers", sellers)
            elif delivery_type == "Entrega":
                return seller_rules.get("entrega_sellers", sellers)

        return sellers

    def after_search(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Verifica se precisa de delivery_type para categorias prioritárias.
        """
        if not self.require_delivery_type_for_priority:
            return products

        if not products:
            return products

        # Verifica se algum produto é de categoria prioritária
        has_priority = False
        for product_name, product_data in products.items():
            categories = product_data.get("categories", [])
            if self._is_priority_category(categories):
                has_priority = True
                break

        # Se tem categoria prioritária e não tem delivery_type, adiciona erro
        if has_priority and not context.delivery_type:
            mooca_sellers = self.seller_rules.get("mooca_sellers", [])
            if mooca_sellers and all(s in mooca_sellers for s in context.sellers):
                context.add_to_result(
                    "delivery_type_required",
                    "Para produtos de pisos e revestimentos na sua região, "
                    "é necessário informar o tipo de entrega (Retirada ou Entrega).",
                )

        return products

    def _is_priority_category(self, categories: List[str]) -> bool:
        """Verifica se produto pertence a categoria prioritária."""
        if not categories or not self.priority_categories:
            return False

        for category in categories:
            if category in self.priority_categories:
                return True

        return False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Adiciona mensagem de região ao resultado se necessário.
        """
        # A mensagem de região já é adicionada pelo ProductConcierge
        # Este hook pode ser usado para adicionar informações extras
        return result
