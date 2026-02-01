"""
Exemplo: Agente de Status de Pedido

Este exemplo demonstra como utilizar o OrderConcierge para buscar pedidos
por documento (CPF/CNPJ) ou ID do pedido.

Funcionalidades:
1. Busca por Documento: Retorna lista de pedidos (completos e incompletos)
2. Busca por ID: Retorna detalhes de um pedido específico
"""

from weni import Tool
from weni.context import Context
from weni.responses import TextResponse
from weni_utils.tools import OrderConcierge


class OrderStatusTool(Tool):
    """
    Tool unificada para busca de pedidos.
    
    Aceita 'document' ou 'order_id' como parâmetros.
    """
    
    def execute(self, context: Context) -> TextResponse:
        # Extrai parâmetros
        document = context.parameters.get("document")
        order_id = context.parameters.get("orderID")
        
        # Extrai credenciais
        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        vtex_app_key = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_app_token = context.credentials.get("VTEX_API_APPTOKEN", "")
        
        if not base_url:
            return TextResponse(data={"error": "BASE_URL not configured"})
            
        # Inicializa o concierge
        concierge = OrderConcierge(
            base_url=base_url,
            store_url=store_url,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token
        )
        
        # Busca por ID do pedido
        if order_id:
            result = concierge.get_order_details(order_id)
            return TextResponse(data=result)
            
        # Busca por documento
        if document:
            result = concierge.search_orders(document)
            return TextResponse(data=result)
            
        return TextResponse(data={
            "error": "Either 'document' or 'orderID' parameter is required"
        })
