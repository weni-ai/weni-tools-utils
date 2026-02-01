"""
Exemplo: Agente Reserva Refatorado

Este arquivo mostra como o agente da Reserva fica com a biblioteca.

Plugins utilizados:
- Carousel: Para enviar produtos via WhatsApp carousel
- CAPI: Para enviar eventos de conversão para Meta
"""

from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

# Importa da biblioteca centralizada
from weni_utils.tools import ProductConcierge
from weni_utils.tools.plugins import Carousel, CAPI


class SearchProduct(Tool):
    """
    Tool de busca de produtos para Reserva.
    
    Utiliza plugins de Carousel e CAPI específicos para
    integração com WhatsApp e Meta Conversions API.
    """
    
    def execute(self, context: Context) -> TextResponse:
        # Extrai parâmetros
        product_name = context.parameters.get("product_name", "")
        brand_name = context.parameters.get("brand_name", "")
        
        # Extrai credenciais
        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        weni_token = context.credentials.get("WENI_TOKEN", "")
        
        if not base_url:
            return TextResponse(data={"error": "BASE_URL not configured"})
        
        # Configura os plugins específicos da Reserva
        capi = CAPI(
            event_type="lead",
            auto_send=True,
            only_whatsapp=True
        )
        
        # Carousel com auto_send=False porque a Reserva 
        # tem uma tool separada para enviar carousel
        carousel = Carousel(
            weni_token=weni_token,
            max_items=10,
            auto_send=False  # Será enviado pela tool send_carousel
        )
        
        # Cria o concierge com os plugins
        concierge = ProductConcierge(
            base_url=base_url,
            store_url=store_url,
            plugins=[capi],  # Carousel não incluído aqui pois tem tool separada
            max_products=20,
            max_variations=3,
            utm_source="weni_webchat"
        )
        
        # Executa a busca
        result = concierge.search(
            product_name=product_name,
            brand_name=brand_name,
            credentials={
                "auth_token": context.project.get("auth_token", ""),
            },
            contact_info={
                "urn": context.contact.get("urn", ""),
                "channel_uuid": context.contact.get("channel_uuid", ""),
                "auth_token": context.project.get("auth_token", ""),
            }
        )
        
        return TextResponse(data=result)


class SendCarousel(Tool):
    """
    Tool para enviar carousel de produtos selecionados.
    
    Recebe uma lista de SKU IDs e envia um carousel formatado
    via WhatsApp usando o plugin Carousel.
    """
    
    def execute(self, context: Context) -> TextResponse:
        # Extrai parâmetros
        sku_ids_str = context.parameters.get("sku_ids", "")
        
        # Extrai credenciais
        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        weni_token = context.credentials.get("WENI_TOKEN", "")
        unique_seller = context.credentials.get("UNIQUE_SELLER", "false").lower()
        
        if not base_url:
            return TextResponse(data={"error": "BASE_URL not configured"})
        
        if not sku_ids_str:
            return TextResponse(data={"error": "No SKU IDs provided"})
        
        # Parse SKU IDs
        sku_ids = [sku.strip() for sku in sku_ids_str.split(",") if sku.strip()]
        
        if not sku_ids:
            return TextResponse(data={"error": "No valid SKU IDs provided"})
        
        # Obtém informações do contato
        contact_urn = context.contact.get("urn", "")
        
        if not contact_urn:
            return TextResponse(data={"error": "Contact URN not available"})
        
        # Determina seller
        if unique_seller == "true":
            seller_id = "lojausereservaondemand"
        else:
            seller_id = "1"
        
        # Cria o concierge apenas para usar o client
        concierge = ProductConcierge(
            base_url=base_url,
            store_url=store_url
        )
        
        # Usa o plugin Carousel diretamente
        carousel = Carousel(
            weni_token=weni_token,
            max_items=10
        )
        
        # Envia carousel para os SKUs específicos
        success = carousel.send_carousel_for_skus(
            sku_ids=sku_ids,
            client=concierge.client,
            contact_urn=contact_urn,
            auth_token=weni_token,
            seller_id=seller_id
        )
        
        if success:
            return TextResponse(data={
                "message": f"Carousel sent successfully with {len(sku_ids)} products",
                "products_sent": len(sku_ids),
                "sku_ids_processed": sku_ids
            })
        else:
            return TextResponse(data={"error": "Failed to send WhatsApp broadcast"})


# ============================================================================
# COMPARAÇÃO: ANTES vs DEPOIS
# ============================================================================
#
# ANTES:
# - search_products/main.py: ~400 linhas
# - send_carousel/main.py: ~370 linhas
# - Total: ~770 linhas
#
# DEPOIS:
# - main.py: ~130 linhas (ambas as tools)
#
# A lógica de:
# - intelligentSearch
# - filterProductsWithStock
# - cartSimulation
# - clean_image_url
# - format_price
# - create_carousel_xml
# - send_whatsapp_broadcast
# - get_product_details_by_sku
# - get_product_price
#
# Agora está TODA na biblioteca weni-vtex-concierge
# ============================================================================
