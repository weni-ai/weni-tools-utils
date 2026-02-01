"""
WeniFlowTrigger Plugin - Disparo de Fluxos Weni

Plugin para disparar fluxos na plataforma Weni durante a busca de produtos.
Útil para tracking, analytics ou ações customizadas.
"""

from typing import TYPE_CHECKING, Any, Dict, Optional

import requests

from .base import PluginBase

if TYPE_CHECKING:
    # from ..client import VTEXClient
    from ..context import SearchContext


class WeniFlowTrigger(PluginBase):
    """
    Plugin para disparar fluxos Weni.

    Funcionalidades:
    - Dispara fluxos após busca de produtos
    - Passa parâmetros customizados para o fluxo
    - Controla execução única por sessão

    Example:
        concierge = ProductConcierge(
            base_url="...",
            store_url="...",
            plugins=[
                WeniFlowTrigger(
                    flow_uuid="uuid-do-fluxo",
                    trigger_once=True
                )
            ]
        )

        result = concierge.search(
            product_name="furadeira",
            credentials={
                "API_TOKEN_WENI": "seu-token"
            },
            contact_info={
                "urn": "whatsapp:5511999999999"
            }
        )
    """

    name = "weni_flow_trigger"

    def __init__(
        self,
        flow_uuid: Optional[str] = None,
        weni_api_url: str = "https://flows.weni.ai/api/v2/flow_starts.json",
        trigger_once: bool = True,
        flow_params: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
    ):
        """
        Inicializa o plugin de fluxo Weni.

        Args:
            flow_uuid: UUID do fluxo a disparar (pode vir das credentials)
            weni_api_url: URL da API de fluxos
            trigger_once: Se True, dispara apenas uma vez por sessão
            flow_params: Parâmetros extras para passar ao fluxo
            timeout: Timeout para requisições
        """
        self.flow_uuid = flow_uuid
        self.weni_api_url = weni_api_url
        self.trigger_once = trigger_once
        self.flow_params = flow_params or {}
        self.timeout = timeout
        self._triggered = False

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Dispara fluxo após finalizar resultado.
        """
        # Verifica se já foi disparado (se trigger_once=True)
        if self.trigger_once and self._triggered:
            return result

        # Obtém credenciais
        api_token = context.get_credential("API_TOKEN_WENI")
        flow_uuid = self.flow_uuid or context.get_credential("EVENT_ID_CONCIERGE")
        contact_urn = context.get_contact("urn")

        if not all([api_token, flow_uuid, contact_urn]):
            return result

        success = self.trigger_flow(
            api_token=api_token,
            flow_uuid=flow_uuid,
            contact_urn=contact_urn,
            params=self.flow_params,
        )

        if success:
            self._triggered = True

        return result

    def trigger_flow(
        self,
        api_token: str,
        flow_uuid: str,
        contact_urn: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Dispara um fluxo Weni.

        Args:
            api_token: Token de autenticação
            flow_uuid: UUID do fluxo
            contact_urn: URN do contato
            params: Parâmetros para o fluxo

        Returns:
            True se disparado com sucesso
        """
        headers = {"Authorization": f"Token {api_token}", "Content-Type": "application/json"}

        payload = {"flow": flow_uuid, "urns": [contact_urn], "params": params or {"executions": 1}}

        try:
            response = requests.post(
                self.weni_api_url, headers=headers, json=payload, timeout=self.timeout
            )

            if response.status_code == 200:
                print(f"WeniFlow: Fluxo {flow_uuid} disparado com sucesso")
                return True
            else:
                print(f"WeniFlow: Falha ao disparar fluxo: {response.status_code}")
                return False

        except Exception as e:
            print(f"WeniFlow: Erro ao disparar fluxo: {e}")
            return False

    def reset(self) -> None:
        """Reseta o estado do plugin para permitir novo disparo."""
        self._triggered = False
