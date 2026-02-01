"""
CAPI Plugin - Meta Conversions API

Plugin para enviar eventos de conversão para a Meta (Facebook/Instagram).
Integra com a API de conversões da Weni.
"""

from typing import TYPE_CHECKING, Any, Dict

import requests

from .base import PluginBase

if TYPE_CHECKING:
    # from ..client import VTEXClient
    from ..context import SearchContext


class CAPI(PluginBase):
    """
    Plugin de Conversions API (CAPI) do Meta.

    Funcionalidades:
    - Envia eventos de lead após busca de produtos
    - Envia eventos de purchase após compra
    - Integra com a API de conversões da Weni

    Tipos de eventos suportados:
    - lead: Usuário demonstrou interesse (buscou produtos)
    - purchase: Usuário realizou compra

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                CAPI(
                    event_type="lead",
                    auto_send=True
                )
            ]
        )

        result = concierge.search(
            product_name="camiseta",
            contact_info={
                "urn": "whatsapp:5511999999999",
                "channel_uuid": "uuid-do-canal"
            }
        )
    """

    name = "capi"

    VALID_EVENT_TYPES = ["lead", "purchase"]

    def __init__(
        self,
        event_type: str = "lead",
        auto_send: bool = True,
        weni_capi_url: str = "https://flows.weni.ai/conversion/",
        only_whatsapp: bool = True,
        timeout: int = 10,
    ):
        """
        Inicializa o plugin CAPI.

        Args:
            event_type: Tipo de evento a enviar (lead ou purchase)
            auto_send: Se True, envia evento automaticamente após busca
            weni_capi_url: URL da API de conversões da Weni
            only_whatsapp: Se True, só envia para contatos WhatsApp
            timeout: Timeout para requisições
        """
        if event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(f"event_type deve ser um de: {self.VALID_EVENT_TYPES}")

        self.event_type = event_type
        self.auto_send = auto_send
        self.weni_capi_url = weni_capi_url
        self.only_whatsapp = only_whatsapp
        self.timeout = timeout
        self._sent = False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Envia evento CAPI após finalizar resultado (se auto_send=True).
        """
        if not self.auto_send:
            return result

        # Evita enviar duplicado
        if self._sent:
            return result

        contact_urn = context.get_contact("urn")
        channel_uuid = context.get_contact("channel_uuid")
        auth_token = context.credentials.get("auth_token") or context.get_contact("auth_token")

        # Verifica se é WhatsApp (se configurado para só WhatsApp)
        if self.only_whatsapp and contact_urn and "whatsapp" not in contact_urn.lower():
            return result

        success = self.send_event(
            auth_token=auth_token,
            channel_uuid=channel_uuid,
            contact_urn=contact_urn,
            event_type=self.event_type,
        )

        if success:
            self._sent = True
            result["capi_event_sent"] = True
            result["capi_event_type"] = self.event_type

        return result

    def send_event(
        self, auth_token: str, channel_uuid: str, contact_urn: str, event_type: str
    ) -> bool:
        """
        Envia evento de conversão para a Meta.

        Args:
            auth_token: Token de autenticação
            channel_uuid: UUID do canal
            contact_urn: URN do contato
            event_type: Tipo de evento (lead ou purchase)

        Returns:
            True se enviado com sucesso
        """
        if not all([auth_token, channel_uuid, contact_urn]):
            print("CAPI: Faltam parâmetros obrigatórios")
            return False

        if event_type not in self.VALID_EVENT_TYPES:
            print(f"CAPI: Tipo de evento inválido: {event_type}")
            return False

        headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}

        payload = {
            "channel_uuid": channel_uuid,
            "contact_urn": contact_urn,
            "event_type": event_type,
        }

        try:
            response = requests.post(
                self.weni_capi_url, headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                print(f"CAPI: Evento '{event_type}' enviado com sucesso")
                return True
            else:
                print(f"CAPI: Falha ao enviar evento: {response.status_code}")
                return False

        except Exception as e:
            print(f"CAPI: Erro ao enviar evento: {e}")
            return False

    def send_purchase_event(self, context: "SearchContext") -> bool:
        """
        Envia evento de compra manualmente.

        Útil para chamar após confirmação de compra.

        Args:
            context: Contexto com informações do contato

        Returns:
            True se enviado com sucesso
        """
        contact_urn = context.get_contact("urn")
        channel_uuid = context.get_contact("channel_uuid")
        auth_token = context.credentials.get("auth_token")

        return self.send_event(
            auth_token=auth_token,
            channel_uuid=channel_uuid,
            contact_urn=contact_urn,
            event_type="purchase",
        )

    def reset(self) -> None:
        """Reseta o estado do plugin para permitir novo envio."""
        self._sent = False
