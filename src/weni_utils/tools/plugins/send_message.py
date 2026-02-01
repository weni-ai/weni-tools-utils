"""
Send Message Plugin - Envio de Mensagens via WhatsApp Broadcast

Plugin para envio de mensagens através da API do WhatsApp Broadcast da Weni.
Suporta envio de mensagens de texto, templates, anexos, quick replies e footers.
"""

from typing import Any, Dict, List, Optional, Union

import requests
import json

from .base import PluginBase


class SendMessage(PluginBase):
    """
    Plugin de envio de mensagem usando a API do WhatsApp Broadcast da Weni.

    Este plugin permite enviar mensagens através da API de broadcast da Weni,
    suportando diferentes tipos de conteúdo e formatações.

    Funcionalidades:
        - Envio de mensagens de texto simples
        - Envio de templates com variáveis dinâmicas
        - Anexos (imagens, PDFs, documentos)
        - Quick replies (botões de resposta rápida)
        - Footers personalizados
        - Autenticação flexível (Token ou JWT)

    Args:
        weni_token: Token de autenticação da Weni para API externa
        weni_jwt_token: JWT Token de autenticação para API interna
        weni_api_url_external: URL da API externa de broadcast
        weni_api_url_internal: URL da API interna de broadcast
        timeout: Timeout em segundos para requisições HTTP (padrão: 30)
        channel_uuid: UUID do canal WhatsApp para envio das mensagens

    """

    name = "send_message"

    def __init__(
        self,
        weni_token: Optional[str] = None,
        weni_jwt_token: Optional[str] = None,
        weni_api_url_external: str = "https://flows.weni.ai/api/v2/whatsapp_broadcasts.json",
        weni_api_url_internal: str = "https://flows.weni.ai/api/v2/internals/whatsapp_broadcasts",
        timeout: int = 30,
        channel_uuid: Optional[str] = "",
    ):
        """
        Inicializa o plugin de envio de mensagens.

        Args:
            weni_token: Token de autenticação da Weni para API externa.
                       Se fornecido, será usado para autenticação na API externa.
            weni_jwt_token: JWT Token de autenticação para API interna.
                           Se fornecido junto com weni_token=None, será usado na API interna.
            weni_api_url_external: URL da API externa de broadcast da Weni.
            weni_api_url_internal: URL da API interna de broadcast da Weni.
            timeout: Timeout em segundos para requisições HTTP (padrão: 30).
            channel_uuid: UUID do canal WhatsApp onde as mensagens serão enviadas.
                         Deve ser fornecido para que as mensagens sejam enviadas corretamente.

        Note:
            É necessário fornecer pelo menos um dos tokens (weni_token ou weni_jwt_token).
            O channel_uuid é obrigatório para o envio de mensagens.
        """
        if not weni_token and not weni_jwt_token:
            raise ValueError(
                "É necessário fornecer pelo menos um token de autenticação "
                "(weni_token ou weni_jwt_token)"
            )

        self.weni_token = weni_token
        self.weni_jwt_token = weni_jwt_token
        self.weni_api_url_external = weni_api_url_external
        self.weni_api_url_internal = weni_api_url_internal
        self.channel_uuid = channel_uuid or ""
        self.timeout = timeout

    def send_message(
        self,
        message: str,
        contact_urn: str,
        variables: List[str],
        attachments: Optional[List[Union[str, Dict[str, Any]]]] = None,
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template_uuid: Optional[str] = None,
        locale: str = "pt_BR",
    ) -> Dict[str, Any]:
        """
        Envia uma mensagem via WhatsApp Broadcast.

        Método principal para envio de mensagens. Suporta diferentes tipos de conteúdo:
        mensagens de texto, templates, anexos, quick replies e footers.

        Args:
            message: Texto da mensagem a ser enviada. Pode ser vazio se usar template.
            contact_urn: URN do contato no formato "whatsapp:5511999999999".
            variables: Lista de variáveis para substituição em templates.
                      Exemplo: ["João", "R$ 100,00"] para template "Olá {{1}}, seu pedido {{2}}".
            attachments: Lista opcional de anexos. Pode ser lista de URLs (str) ou
                        lista de dicionários com informações do anexo.
            footer: Texto opcional para rodapé da mensagem.
            quick_replies: Lista opcional de quick replies (botões de resposta rápida).
                          Pode ser lista de strings ou lista de dicionários.
            template_uuid: UUID opcional do template a ser usado. Se fornecido,
                          a mensagem será enviada como template.
            locale: Locale do template (padrão: "pt_BR").

        Returns:
            Dict contendo a resposta da API com os seguintes campos possíveis:
                - success: bool indicando sucesso (quando há erro)
                - error: str com mensagem de erro (quando há erro)
                - status_code: int com código HTTP (quando há erro HTTP)
                - response: str com resposta da API (quando há erro HTTP)
                - url: str com URL da requisição (quando há erro)
                - Dados da resposta JSON da API (quando bem-sucedido)

        Raises:
            ValueError: Se contact_urn estiver vazio ou channel_uuid não estiver configurado.
        """
        if not contact_urn:
            raise ValueError("contact_urn não pode estar vazio")

        if not self.channel_uuid:
            raise ValueError("channel_uuid deve ser configurado no __init__ para enviar mensagens")

        return self.send_broadcast_external(
            message,
            contact_urn,
            variables,
            attachments,
            footer,
            quick_replies,
            template_uuid,
            locale,
        )

    def send_broadcast_external(
        self,
        message: str,
        contact_urn: str,
        variables: List[str],
        attachments: Optional[List[Union[str, Dict[str, Any]]]] = None,
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template_uuid: Optional[str] = None,
        locale: str = "pt_BR",
    ) -> Dict[str, Any]:
        """
        Envia mensagem usando a API do WhatsApp Broadcast (método interno).

        Este método realiza o processamento e formatação dos dados antes de enviar
        para a API da Weni.

        Args:
            message: Texto da mensagem.
            contact_urn: URN do contato.
            variables: Lista de variáveis para templates.
            attachments: Lista opcional de anexos.
            footer: Texto opcional para rodapé.
            quick_replies: Lista opcional de quick replies.
            template_uuid: UUID opcional do template.
            locale: Locale do template.

        Returns:
            Dict com a resposta da API ou informações de erro.
        """
        # Formata anexos se fornecidos
        formatted_attachments = []
        if attachments:
            formatted_attachments = self.format_attachments(attachments)

        # Formata template se fornecido
        template = None
        if template_uuid:
            template = self.format_template(template_uuid, variables, locale)

        # Formata payload completo
        payload = self.format_payload(
            message=message,
            template=template,
            attachments=formatted_attachments,
            contact_urn=contact_urn,
            footer=footer,
            quick_replies=quick_replies,
        )

        # Envia requisição e retorna resposta
        response = self.request_broadcast(payload)
        return response

    def format_payload(
        self,
        message: Optional[str] = "",
        attachments: Optional[List[str]] = None,
        contact_urn: Optional[str] = "",
        footer: Optional[str] = None,
        quick_replies: Optional[List[Union[str, Dict[str, Any]]]] = None,
        template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Formata o payload para o envio da mensagem.

        Cria a estrutura de dados no formato esperado pela API do WhatsApp Broadcast.

        Args:
            message: Texto da mensagem.
            attachments: Lista de anexos formatados.
            contact_urn: URN do contato.
            footer: Texto do rodapé.
            quick_replies: Lista de quick replies.
            template: Dicionário com informações do template.

        Returns:
            Dict com o payload formatado no formato esperado pela API.

        Note:
            O payload retornado é um dicionário Python, não uma string JSON.
            A serialização para JSON é feita no método request_broadcast.
        """
        if attachments is None:
            attachments = []

        payload = {
            "urns": [contact_urn],
            "channel": self.channel_uuid,
            "msg": {
                "text": message or "",
                "attachments": attachments,
            },
        }

        # Adiciona campos opcionais apenas se fornecidos
        if template:
            payload["msg"]["template"] = template

        if footer:
            payload["msg"]["footer"] = footer

        if quick_replies:
            payload["msg"]["quick_replies"] = quick_replies

        return payload

    def format_template(
        self, template_uuid: str, variables: List[str], locale: str = "pt_BR"
    ) -> Dict[str, Any]:
        """
        Formata o template para o envio da mensagem.

        Cria a estrutura de dados do template no formato esperado pela API.

        Args:
            template_uuid: UUID do template cadastrado na Weni.
            variables: Lista de variáveis para substituição no template.
                      A ordem das variáveis deve corresponder à ordem no template.
            locale: Locale do template (padrão: "pt_BR").
                   Exemplos: "pt_BR", "en_US", "es_ES".

        Returns:
            Dict com a estrutura do template formatada:
                {
                    "uuid": str,
                    "variables": List[str],
                    "locale": str
                }

        """
        return {"uuid": template_uuid, "variables": variables, "locale": locale}

    def format_attachments(self, attachments: List[Union[str, Dict[str, Any]]]) -> List[str]:
        """
        Formata os anexos para o envio da mensagem.

        Converte URLs ou dicionários de anexos para o formato esperado pela API:
        "mime/type:url". Detecta automaticamente o tipo MIME baseado na extensão
        do arquivo ou usa o tipo fornecido no dicionário.

        Args:
            attachments: Lista de anexos. Pode conter:
                       - Strings com URLs dos arquivos
                       - Dicionários com formato {"url": str, "mime_type": str, ...}

        Returns:
            Lista de strings no formato "mime/type:url" para cada anexo válido.

        Supported MIME Types:
            - Imagens: image/png, image/jpg, image/jpeg, image/gif
            - Documentos: application/pdf, application/doc, application/docx
            - Planilhas: application/xls, application/xlsx
        """
        formatted_attachments = []

        # Mapeamento de extensões para tipos MIME
        mime_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        for attachment in attachments:
            # Se for dicionário, extrai URL e tipo MIME
            if isinstance(attachment, dict):
                url = attachment.get("url", "")
                mime_type = attachment.get("mime_type", "")
                if not url:
                    continue
                if mime_type:
                    formatted_attachments.append(f"{mime_type}:{url}")
                    continue
                # Se não tiver mime_type, tenta detectar pela extensão
                attachment = url

            # Converte para string e normaliza
            url = str(attachment).strip()
            if not url:
                continue

            # Detecta tipo MIME pela extensão (case-insensitive)
            url_lower = url.lower()
            mime_type = None

            for ext, mime in mime_types.items():
                if url_lower.endswith(ext):
                    mime_type = mime
                    break

            if mime_type:
                formatted_attachments.append(f"{mime_type}:{url}")
            else:
                # Se não conseguir detectar, usa como link genérico
                # ou pode lançar um aviso (comentado para manter compatibilidade)
                formatted_attachments.append(f"application/octet-stream:{url}")

        return formatted_attachments

    def request_broadcast(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envia a requisição para a API do WhatsApp Broadcast com tratamento de erros.

        Realiza a requisição HTTP POST para a API da Weni e trata diferentes tipos
        de erros que podem ocorrer durante a comunicação.

        Args:
            payload: Dicionário com o payload formatado para envio.
                   Será serializado para JSON automaticamente pelo requests.

        Returns:
            Dict com a resposta da API. Em caso de sucesso, retorna o JSON da resposta.
            Em caso de erro, retorna um dict com:
                - success: False
                - error: str com mensagem de erro
                - status_code: int (apenas para erros HTTP)
                - response: str (apenas para erros HTTP, contém resposta da API)
                - url: str com a URL da requisição

        """
        # Determina URL e headers baseado no token disponível
        if self.weni_token:
            url = self.weni_api_url_external
            headers = {
                "Authorization": f"Token {self.weni_token}",
                "Content-Type": "application/json",
            }
        elif self.weni_jwt_token:
            url = self.weni_api_url_internal
            headers = {
                "Authorization": f"Bearer {self.weni_jwt_token}",
                "Content-Type": "application/json",
            }
        else:
            # Este caso não deveria acontecer devido à validação no __init__
            return {
                "success": False,
                "error": "Nenhum token de autenticação configurado",
                "url": "",
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": f"Timeout ao tentar se conectar à API após {self.timeout}s",
                "url": url,
            }

        except requests.exceptions.HTTPError as http_err:
            status_code = None
            response_text = None

            if hasattr(http_err, "response") and http_err.response is not None:
                status_code = http_err.response.status_code
                try:
                    response_text = http_err.response.text
                except Exception:
                    response_text = "Não foi possível ler a resposta"

            return {
                "success": False,
                "error": f"Erro HTTP {status_code}: {str(http_err)}",
                "status_code": status_code,
                "response": response_text,
                "url": url,
            }

        except requests.exceptions.RequestException as err:
            return {
                "success": False,
                "error": f"Erro de requisição: {str(err)}",
                "url": url,
            }

        except json.JSONDecodeError as json_err:
            return {
                "success": False,
                "error": f"Erro ao decodificar resposta JSON: {str(json_err)}",
                "url": url,
            }

        except Exception as ex:
            return {
                "success": False,
                "error": f"Erro inesperado: {str(ex)}",
                "url": url,
            }
