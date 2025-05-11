from typing import Dict, Optional, Type

from financial_document_processor.adapters.ai.ai_provider import AIProvider
from financial_document_processor.adapters.ai.claude_provider import ClaudeProvider
from financial_document_processor.adapters.ai.gemini_provider import GeminiProvider
from financial_document_processor.adapters.ai.openai_provider import OpenAIProvider


# Factory para criar provedores de IA
def create_ai_provider(
        provider_name: str,
        api_key: str,
        model: Optional[str] = None,
        organization_id: Optional[str] = None,
) -> AIProvider:
    """
    Factory para criar instâncias de AIProvider baseado no nome.

    Args:
        provider_name: Nome do provedor ('openai', 'gemini', 'claude')
        api_key: Chave de API do provedor
        model: Nome do modelo a ser usado (opcional)
        organization_id: ID da organização para OpenAI (opcional)

    Returns:
        Instância de AIProvider

    Raises:
        ValueError: Se o provedor não for suportado
    """
    providers: Dict[str, Type[AIProvider]] = {
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "claude": ClaudeProvider,
    }

    provider_class = providers.get(provider_name.lower())

    if not provider_class:
        raise ValueError(f"Provedor não suportado: {provider_name}. Opções disponíveis: {list(providers.keys())}")

    if provider_name.lower() == "openai":
        return provider_class(api_key=api_key, model=model, organization_id=organization_id)
    else:
        return provider_class(api_key=api_key, model=model)