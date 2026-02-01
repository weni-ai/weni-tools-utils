"""
StockManager - Gerenciamento de estoque e disponibilidade

Este módulo contém a lógica para verificar disponibilidade de produtos
e filtrar resultados com base em estoque.
"""

from typing import Any, Dict, List, Optional, Set

from .context import SearchContext


class StockManager:
    """
    Gerenciador de estoque e disponibilidade de produtos.

    Responsável por:
    - Verificar disponibilidade via simulação de carrinho
    - Filtrar produtos sem estoque
    - Enriquecer produtos com informações de estoque

    Example:
        manager = StockManager()
        products_with_stock = manager.check_availability(
            client, products, context
        )
    """

    def __init__(self):
        """Inicializa o gerenciador de estoque"""
        pass

    def _flatten_products_to_skus(self, products: Dict[str, Dict]) -> List[Dict]:
        """
        Converte estrutura de produtos para lista de SKUs para simulação.

        Args:
            products: Dicionário de produtos estruturados

        Returns:
            Lista de SKUs com informações necessárias para simulação
        """
        sku_list = []

        for product_name, product_data in products.items():
            for variation in product_data.get("variations", []):
                sku_list.append(
                    {
                        "sku_id": variation.get("sku_id"),
                        "sku_name": variation.get("sku_name"),
                        "variations": variation.get("variations"),
                        "seller": variation.get("sellerId"),
                        "description": product_data.get("description"),
                        "brand": product_data.get("brand"),
                        "specification_groups": product_data.get("specification_groups"),
                        "categories": product_data.get("categories", []),
                        "imageUrl": variation.get("imageUrl"),
                        "price": variation.get("price"),
                        "spotPrice": variation.get("spotPrice"),
                        "pixPrice": variation.get("pixPrice"),
                        "creditCardPrice": variation.get("creditCardPrice"),
                    }
                )

        return sku_list

    def _select_available_products(
        self, simulation_result: Dict, products_details: List[Dict]
    ) -> List[Dict]:
        """
        Seleciona produtos disponíveis baseado na simulação de carrinho.

        Args:
            simulation_result: Resultado da simulação
            products_details: Lista de detalhes dos produtos

        Returns:
            Lista de produtos disponíveis
        """
        available_ids: Set[str] = set()

        for item in simulation_result.get("items", []):
            if item.get("availability", "").lower() == "available":
                original_id = item.get("id")
                if original_id:
                    available_ids.add(original_id)

        return [p for p in products_details if p.get("sku_id") in available_ids]

    def check_availability_simple(
        self, client: Any, products: Dict[str, Dict], context: SearchContext  # VTEXClient
    ) -> List[Dict]:
        """
        Verifica disponibilidade usando simulação simples de carrinho.

        Usado quando não há regionalização ou sellers específicos.

        Args:
            client: Instância do VTEXClient
            products: Dicionário de produtos estruturados
            context: Contexto da busca

        Returns:
            Lista de produtos com estoque disponível
        """
        if not products:
            return []

        # Converte para lista de SKUs
        products_details = self._flatten_products_to_skus(products)

        if not products_details:
            return []

        # Monta itens para simulação
        items = []
        for product in products_details:
            sku_id = product.get("sku_id")
            seller = product.get("seller", "1")
            items.append({"id": sku_id, "quantity": context.quantity, "seller": seller})

        # Executa simulação
        simulation_result = client.cart_simulation(items=items, country=context.country_code)

        # Filtra produtos disponíveis
        return self._select_available_products(simulation_result, products_details)

    def check_availability_with_sellers(
        self,
        client: Any,  # VTEXClient
        products: Dict[str, Dict],
        context: SearchContext,
        priority_categories: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Verifica disponibilidade usando simulação batch com sellers específicos.

        Usado quando há regionalização e lista de sellers.

        Args:
            client: Instância do VTEXClient
            products: Dicionário de produtos estruturados
            context: Contexto da busca (deve ter sellers preenchido)
            priority_categories: Categorias que requerem lógica especial de estoque

        Returns:
            Lista de produtos com estoque disponível e informações do seller
        """
        if not products or not context.sellers:
            return self.check_availability_simple(client, products, context)

        products_details = self._flatten_products_to_skus(products)

        if not products_details:
            return []

        priority_categories = priority_categories or []
        products_with_stock = []

        for product in products_details:
            sku_id = product.get("sku_id")
            categories = product.get("categories", [])

            # Verifica se é categoria prioritária
            is_priority = self._is_priority_category(categories, priority_categories)

            # Define quantidade para simulação
            if is_priority:
                simulation_quantity = max(context.quantity, 1000)
            else:
                simulation_quantity = context.quantity

            # Executa simulação batch
            simulation_result = client.batch_simulation(
                sku_id=sku_id,
                quantity=simulation_quantity,
                sellers=context.sellers,
                postal_code=context.postal_code,
            )

            if simulation_result and simulation_result.get("quantity", 0) > 0:
                # Enriquece produto com informações da simulação
                product_with_stock = product.copy()
                product_with_stock.update(
                    {
                        "measurementUnit": simulation_result.get("measurementUnit", ""),
                        "unitMultiplier": simulation_result.get("unitMultiplier", 1),
                        "deliveryType": simulation_result.get("deliveryType", ""),
                        "sellerId": simulation_result.get("sellerId", ""),
                        "available_quantity": simulation_result.get("quantity", 0),
                    }
                )
                products_with_stock.append(product_with_stock)

        return products_with_stock

    def _is_priority_category(self, categories: List[str], priority_categories: List[str]) -> bool:
        """
        Verifica se produto pertence a uma categoria prioritária.

        Args:
            categories: Categorias do produto
            priority_categories: Lista de categorias prioritárias

        Returns:
            True se pertence a categoria prioritária
        """
        if not categories or not priority_categories:
            return False

        for category in categories:
            if category in priority_categories:
                return True

        return False

    def filter_products_with_stock(
        self, products_structured: Dict[str, Dict], products_with_stock: List[Dict]
    ) -> Dict[str, Dict]:
        """
        Filtra a estrutura original de produtos mantendo apenas os com estoque.

        Args:
            products_structured: Estrutura original de produtos
            products_with_stock: Lista de SKUs que têm estoque

        Returns:
            Estrutura de produtos filtrada
        """
        if not products_with_stock:
            return {}

        # Cria mapa de informações de estoque por SKU
        stock_info = {}
        for product in products_with_stock:
            sku_id = product.get("sku_id")
            stock_info[sku_id] = {
                "measurementUnit": product.get("measurementUnit", ""),
                "unitMultiplier": product.get("unitMultiplier", 1),
                "deliveryType": product.get("deliveryType", ""),
                "sellerId": product.get("sellerId", ""),
                "available_quantity": product.get("available_quantity", 0),
                "minQuantity": product.get("minQuantity"),
                "valueAtacado": product.get("valueAtacado"),
            }

        # Filtra produtos
        filtered_products = {}

        for product_name, product_data in products_structured.items():
            filtered_variations = []

            for variation in product_data.get("variations", []):
                sku_id = variation.get("sku_id")
                if sku_id in stock_info:
                    # Adiciona informações de estoque à variação
                    variation_with_stock = variation.copy()
                    variation_with_stock.update(stock_info[sku_id])
                    filtered_variations.append(variation_with_stock)

            if filtered_variations:
                filtered_product = product_data.copy()
                filtered_product["variations"] = filtered_variations
                filtered_products[product_name] = filtered_product

        return filtered_products

    def limit_payload_size(
        self, products: Dict[str, Dict], max_size_kb: int = 20
    ) -> Dict[str, Dict]:
        """
        Limita o tamanho do payload para garantir que não ultrapasse o limite.

        Args:
            products: Dicionário de produtos
            max_size_kb: Tamanho máximo em KB

        Returns:
            Dicionário de produtos limitado
        """
        import json

        product_list = [
            {"product_name": name, "product_data": data} for name, data in products.items()
        ]

        json_data = json.dumps(product_list)
        size_kb = len(json_data.encode("utf-8")) / 1024

        while size_kb > max_size_kb and product_list:
            product_list.pop()
            json_data = json.dumps(product_list)
            size_kb = len(json_data.encode("utf-8")) / 1024

        return {item["product_name"]: item["product_data"] for item in product_list}
