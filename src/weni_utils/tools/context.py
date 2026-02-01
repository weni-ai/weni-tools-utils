"""
SearchContext - Contexto compartilhado durante a busca

Este objeto é passado entre o core e os plugins, permitindo que cada
plugin adicione/modifique informações conforme necessário.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchContext:
    """
    Contexto de busca que flui pelo pipeline de plugins.

    Attributes:
        product_name: Nome do produto a buscar
        brand_name: Marca do produto (opcional)
        postal_code: CEP para regionalização (opcional)
        quantity: Quantidade desejada
        country_code: Código do país (default: BRA)

        # Campos que plugins podem preencher
        region_id: ID da região (preenchido por Regionalization plugin)
        sellers: Lista de sellers disponíveis
        region_error: Mensagem de erro de região
        delivery_type: Tipo de entrega (Retirada/Entrega)

        # Campos para resultado
        extra_data: Dados extras que plugins podem adicionar ao resultado
    """

    # Parâmetros de entrada
    product_name: str
    brand_name: str = ""
    postal_code: Optional[str] = None
    quantity: int = 1
    country_code: str = "BRA"
    delivery_type: Optional[str] = None
    trade_policy: Optional[int] = 1

    # Campos preenchidos por plugins
    region_id: Optional[str] = None
    sellers: List[str] = field(default_factory=list)
    seller_rules: Dict[str, List[str]] = field(default_factory=dict)
    region_error: Optional[str] = None

    # Credenciais e configurações extras
    credentials: Dict[str, Any] = field(default_factory=dict)
    contact_info: Dict[str, Any] = field(default_factory=dict)

    # Dados extras para o resultado final
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def add_to_result(self, key: str, value: Any) -> None:
        """Adiciona dados extras que serão incluídos no resultado final"""
        self.extra_data[key] = value

    def get_credential(self, key: str, default: Any = None) -> Any:
        """Obtém uma credencial pelo nome"""
        return self.credentials.get(key, default)

    def get_contact(self, key: str, default: Any = None) -> Any:
        """Obtém informação do contato"""
        return self.contact_info.get(key, default)
