"""
PluginBase - Classe base para todos os plugins

Define a interface que todos os plugins devem seguir.
"""

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from ..client import VTEXClient
    from ..context import SearchContext


class PluginBase:
    """
    Classe base abstrata para plugins.

    Plugins são extensões que podem modificar o comportamento do ProductConcierge
    em diferentes pontos do fluxo de busca.

    Hooks disponíveis (em ordem de execução):
    1. before_search - Antes da busca (modificar contexto)
    2. after_search - Após busca (modificar produtos)
    3. after_stock_check - Após verificação de estoque
    4. enrich_products - Enriquecer com dados adicionais
    5. finalize_result - Última modificação antes de retornar

    Example:
        class MyPlugin(PluginBase):
            def before_search(self, context, client):
                # Adiciona region_id ao contexto
                context.region_id = self.get_region(context.postal_code)
                return context
    """

    name: str = "base"

    def before_search(self, context: "SearchContext", client: "VTEXClient") -> "SearchContext":
        """
        Hook executado ANTES da busca inteligente.

        Use este hook para:
        - Modificar parâmetros de busca
        - Obter region_id para regionalização
        - Obter lista de sellers
        - Validar dados de entrada

        Args:
            context: Contexto da busca
            client: Cliente VTEX

        Returns:
            Contexto modificado (ou o mesmo)
        """
        return context

    def after_search(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Hook executado APÓS a busca inteligente.

        Use este hook para:
        - Filtrar produtos por critérios customizados
        - Modificar dados dos produtos
        - Adicionar informações extras

        Args:
            products: Produtos encontrados na busca
            context: Contexto da busca
            client: Cliente VTEX

        Returns:
            Produtos modificados
        """
        return products

    def after_stock_check(
        self, products_with_stock: List[Dict], context: "SearchContext", client: "VTEXClient"
    ) -> List[Dict]:
        """
        Hook executado APÓS verificação de estoque.

        Use este hook para:
        - Adicionar informações de preço especial
        - Modificar dados de estoque
        - Filtrar produtos por disponibilidade customizada

        Args:
            products_with_stock: Lista de produtos com estoque
            context: Contexto da busca
            client: Cliente VTEX

        Returns:
            Lista de produtos modificada
        """
        return products_with_stock

    def enrich_products(
        self, products: Dict[str, Dict], context: "SearchContext", client: "VTEXClient"
    ) -> Dict[str, Dict]:
        """
        Hook para enriquecer produtos com dados adicionais.

        Use este hook para:
        - Adicionar dimensões/peso
        - Adicionar preços especiais
        - Adicionar informações de seller

        Args:
            products: Produtos filtrados
            context: Contexto da busca
            client: Cliente VTEX

        Returns:
            Produtos enriquecidos
        """
        return products

    def finalize_result(self, result: Dict[str, Any], context: "SearchContext") -> Dict[str, Any]:
        """
        Hook para finalizar o resultado antes de retornar.

        Use este hook para:
        - Adicionar mensagens no resultado
        - Enviar eventos (analytics, webhooks)
        - Modificar estrutura final

        Args:
            result: Resultado final
            context: Contexto da busca

        Returns:
            Resultado modificado
        """
        return result
