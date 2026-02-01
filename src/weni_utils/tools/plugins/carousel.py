"""
Carousel Plugin - Envio de Carousel via WhatsApp

Plugin para clientes que precisam enviar produtos como carousel no WhatsApp.
Formata produtos em XML e envia via API da Weni.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import requests

from .base import PluginBase

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class Carousel(PluginBase):
    """
    Plugin de carousel WhatsApp.

    Funcionalidades:
    - Formata produtos em XML para carousel
    - Envia carousel via API da Weni
    - Limita número de produtos no carousel

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                Carousel(
                    weni_token="seu-token",
                    max_items=10
                )
            ]
        )

        # O carousel é enviado automaticamente após a busca
        result = concierge.search(
            product_name="camiseta",
            contact_info={"urn": "whatsapp:5511999999999"}
        )
    """

    name = "carousel"

    def __init__(
        self,
        weni_token: Optional[str] = None,
        weni_jwt_token: Optional[str] = None,
        weni_api_url: str = "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
        weni_internal_url: str = "https://flows.weni.ai/api/v2/internals/whatsapp_broadcasts",
        max_items: int = 10,
        auto_send: bool = False,
        timeout: int = 30,
    ):
        """
        Inicializa o plugin de carousel.

        Args:
            weni_token: Token de autenticação da Weni
            weni_jwt_token: JWT Token de autenticação da Weni
            weni_api_url: URL da API de broadcast
            max_items: Número máximo de itens no carousel
            auto_send: Se True, envia carousel automaticamente
            timeout: Timeout para requisições
        """
        self.weni_token = weni_token
        self.weni_jwt_token = weni_jwt_token
        self.weni_api_url = weni_api_url
        self.max_items = max_items
        self.auto_send = auto_send
        self.timeout = timeout

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Envia carousel após finalizar resultado (se auto_send=True).
        """
        if not self.auto_send:
            return result

        contact_urn = context.get_contact("urn")
        if not contact_urn:
            return result

        # Obtém token (pode vir do contexto ou da inicialização)
        token = self.weni_token or context.get_credential("WENI_TOKEN")
        if not token:
            return result

        # Prepara dados dos produtos para o carousel
        products_data = self._extract_products_for_carousel(result)

        if products_data:
            success = self.send_carousel(
                products_data=products_data, contact_urn=contact_urn, auth_token=token
            )

            result["carousel_sent"] = success
            result["carousel_items"] = len(products_data)

        return result

    def _extract_products_for_carousel(self, result: Dict[str, Any]) -> List[Dict]:
        """
        Extrai dados de produtos do resultado para formato de carousel.

        Args:
            result: Resultado da busca

        Returns:
            Lista de produtos formatados
        """
        products_data = []

        for key, value in result.items():
            # Ignora chaves que não são produtos
            if key in ["region_message", "carousel_sent", "carousel_items"]:
                continue

            if not isinstance(value, dict):
                continue

            # Verifica se é um produto (tem variations)
            if "variations" not in value:
                continue

            # Extrai primeiro SKU de cada produto
            variations = value.get("variations", [])
            if not variations:
                continue

            first_variation = variations[0]

            product_data = {
                "name": first_variation.get("sku_name", key),
                "sku_id": first_variation.get("sku_id"),
                "image": first_variation.get("imageUrl", value.get("imageUrl", "")),
                "price": first_variation.get("price"),
                "list_price": first_variation.get("listPrice"),
                "product_link": value.get("productLink", ""),
            }

            products_data.append(product_data)

            if len(products_data) >= self.max_items:
                break

        return products_data

    def format_price(self, price: Optional[float], list_price: Optional[float] = None) -> str:
        """
        Formata preço para exibição.

        Args:
            price: Preço atual
            list_price: Preço original (de/por)

        Returns:
            String formatada
        """
        if not price:
            return "Preço não disponível"

        price_str = f"R$ {price:.2f}".replace(".", ",")

        if list_price and list_price > price:
            list_price_str = f"R$ {list_price:.2f}".replace(".", ",")
            return f"{price_str} (de {list_price_str})"

        return price_str

    def create_carousel_xml(self, products_data: List[Dict]) -> str:
        """
        Cria XML do carousel.

        Args:
            products_data: Lista de dados dos produtos

        Returns:
            String XML formatada
        """
        carousel_items = []

        for product in products_data:
            if not product:
                continue

            name = product.get("name", "Produto")
            price_display = self.format_price(product.get("price"), product.get("list_price"))
            image_url = product.get("image", "")
            product_link = product.get("product_link", "")

            # Formata imagem em Markdown
            if image_url:
                alt_text = image_url.split("/")[-1] if "/" in image_url else "produto"
                formatted_image = f"![{alt_text}]({image_url})"
            else:
                formatted_image = ""

            carousel_item = f"""     <carousel-item>
         <name>{name}</name>
         <price>{price_display}</price>
         <description>{name}</description>
         <product_link>{product_link}</product_link>
         <image>{formatted_image}</image>
     </carousel-item>"""

            carousel_items.append(carousel_item)

        xml_content = """<?xml version="1.0" encoding="UTF-8" ?>
""" + "\n".join(
            carousel_items
        )

        return xml_content

    def send_carousel(self, products_data: List[Dict], contact_urn: str, auth_token: str) -> bool:
        """
        Envia carousel via WhatsApp.

        Args:
            products_data: Lista de dados dos produtos
            contact_urn: URN do contato
            auth_token: Token de autenticação

        Returns:
            True se enviado com sucesso
        """
        xml_content = self.create_carousel_xml(products_data)

        headers = {"Authorization": f"Token {auth_token}", "Content-Type": "application/json"}

        payload = {"urns": [contact_urn], "msg": {"text": xml_content}}

        try:
            response = requests.post(
                self.weni_api_url, json=payload, headers=headers, timeout=self.timeout
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"ERROR: Erro ao enviar carousel: {e}")
            return False

    def send_carousel_for_skus(
        self,
        sku_ids: List[str],
        client: "VTEXClient",
        contact_urn: str,
        auth_token: str,
        seller_id: str = "1",
    ) -> bool:
        """
        Envia carousel para uma lista específica de SKUs.

        Útil para enviar carousel manualmente com SKUs selecionados.

        Args:
            sku_ids: Lista de SKU IDs
            client: Cliente VTEX
            contact_urn: URN do contato
            auth_token: Token de autenticação
            seller_id: ID do seller para simulação de preço

        Returns:
            True se enviado com sucesso
        """
        products_data = []

        for sku_id in sku_ids[: self.max_items]:
            product = client.get_product_by_sku(sku_id)
            if not product:
                continue

            # Extrai dados do produto
            product_name = product.get("productName", "")
            product_link = product.get("link", "")

            # Busca item específico
            target_item = None
            for item in product.get("items", []):
                if item.get("itemId") == sku_id:
                    target_item = item
                    break

            if not target_item:
                continue

            # Extrai imagem
            image_url = ""
            images = target_item.get("images", [])
            if images:
                image_url = images[0].get("imageUrl", "")

            # Busca preço via simulação
            simulation = client.cart_simulation(
                items=[{"id": sku_id, "quantity": 1, "seller": seller_id}]
            )

            price = None
            list_price = None
            items = simulation.get("items", [])
            if items:
                item = items[0]
                price = item.get("price", 0) / 100 if item.get("price") else None
                list_price = item.get("listPrice", 0) / 100 if item.get("listPrice") else None

            products_data.append(
                {
                    "name": target_item.get("nameComplete", product_name),
                    "sku_id": sku_id,
                    "image": image_url,
                    "price": price,
                    "list_price": list_price,
                    "product_link": f"{client.store_url}{product_link}?skuId={sku_id}",
                }
            )

        if not products_data:
            return False

        return self.send_carousel(products_data, contact_urn, auth_token)
