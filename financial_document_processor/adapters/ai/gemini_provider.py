import json
import logging
from typing import List, Optional

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from financial_document_processor.adapters.ai.ai_provider import AIProvider, AIRequest, AIResponse
from financial_document_processor.domain.transaction import Transaction
from financial_document_processor.services.prompt_engineering import PromptEngineering

logger = logging.getLogger(__name__)


class GeminiProvider(AIProvider):
    """
    Implementação do provedor de IA para Google Gemini.
    """

    def __init__(
            self,
            api_key: str,
            model: str = "gemini-1.5-pro",
            max_retries: int = 3
    ):
        """
        Inicializa o provedor Gemini.

        Args:
            api_key: Chave de API da Google
            model: Modelo a ser utilizado (default: gemini-1.5-pro)
            max_retries: Número máximo de tentativas para chamadas de API
        """
        genai.configure(api_key=api_key)
        self.model = model
        self.max_retries = max_retries
        self.prompt_engineering = PromptEngineering()

        # Mapeamento de modelos para custos (USD por 1000 tokens)
        # Valores aproximados
        self._costs = {
            "gemini-1.5-pro": 0.007,  # $0.007 por 1K tokens
            "gemini-1.5-flash": 0.0035,  # $0.0035 por 1K tokens
            "gemini-1.0-pro": 0.005  # $0.005 por 1K tokens
        }

    @property
    def name(self) -> str:
        return "Gemini"

    def get_cost_per_1k_tokens(self) -> float:
        return self._costs.get(self.model, 0.007)  # Default se o modelo não estiver no dict

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_completion(self, request: AIRequest) -> AIResponse:
        """
        Gera uma completion usando a API do Gemini.

        Args:
            request: Objeto com os parâmetros da requisição

        Returns:
            Objeto AIResponse com a resposta
        """
        try:
            model = genai.GenerativeModel(
                model_name=request.model or self.model,
                generation_config={
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "stop_sequences": request.stop_sequences or [],
                },
                system_instruction=request.system_message or request.prompt
            )

            chat = model.start_chat()

            if request.system_message:
                response = chat.send_message(request.prompt)
            else:
                response = list(chat.history)[-1].parts[0].text

            # Gemini não fornece contagem de tokens diretamente
            # Estimativa aproximada: 4 caracteres = 1 token
            char_count = len(request.prompt) + (len(request.system_message or ""))
            response_chars = len(response.text if hasattr(response, "text") else response)
            total_chars = char_count + response_chars
            estimated_tokens = total_chars // 4

            # Calcula o custo aproximado
            cost = (estimated_tokens / 1000) * self.get_cost_per_1k_tokens()

            return AIResponse(
                content=response.text if hasattr(response, "text") else response,
                model=self.model,
                tokens_used=estimated_tokens,
                cost=cost
            )

        except Exception as e:
            logger.error(f"Erro na chamada para Gemini: {str(e)}")
            raise

    async def extract_transactions(
            self,
            text_content: str,
            document_type: str,
            predefined_categories: Optional[List[str]] = None,
            document_id: int = 0,
            user_id: int = 0,
    ) -> List[Transaction]:
        """
        Extrai transações de um documento utilizando o Gemini.

        Args:
            text_content: Texto extraído do documento
            document_type: Tipo do documento
            predefined_categories: Lista de categorias predefinidas (opcional)
            document_id: ID do documento
            user_id: ID do usuario

        Returns:
            Lista de objetos Transaction
        """
        prompt = self.prompt_engineering.create_extraction_prompt(
            text_content=text_content,
            document_type=document_type,
            predefined_categories=predefined_categories,
            provider="gemini"
        )

        request = AIRequest(
            prompt=prompt,
            system_message="Você é um assistente especializado em extrair transações financeiras de documentos bancários. Forneça apenas o JSON solicitado sem explicações adicionais.",
            temperature=0.0,  # Determinístico
        )

        response = await self.generate_completion(request)

        try:
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_data = response_text[json_start:json_end]
                parsed_data = json.loads(json_data)

                transactions = []
                for item in parsed_data.get("transactions", []):
                    try:
                        item["user_id"] = user_id
                        item["document_id"] = document_id
                        transaction = Transaction(**item)
                        transactions.append(transaction)
                    except Exception as e:
                        logger.error(f"Erro ao converter item para Transaction: {str(e)}")

                return transactions
            else:
                logger.error("Não foi possível encontrar JSON na resposta")
                return []

        except Exception as e:
            logger.error(f"Erro ao processar resposta do Gemini: {str(e)}")
            return []

    async def categorize_transactions(
            self,
            transactions: List[Transaction],
            predefined_categories: Optional[List[str]] = None
    ) -> List[Transaction]:
        """
        Categoriza uma lista de transações utilizando o Gemini.

        Args:
            transactions: Lista de transações a serem categorizadas
            predefined_categories: Lista de categorias predefinidas (opcional)

        Returns:
            Lista de transações com categorias atualizadas
        """
        if not transactions:
            return transactions

        if all(
                len(transaction.categories) > 0 and not ("" in transaction.categories)
                for transaction in transactions
        ):
            return transactions

        MAX_BATCH_SIZE = 10
        batches = [
            transactions[i:i + MAX_BATCH_SIZE]
            for i in range(0, len(transactions), MAX_BATCH_SIZE)
        ]

        categorized_transactions = []

        for batch in batches:
            prompt = self.prompt_engineering.create_categorization_prompt(
                transactions=batch,
                predefined_categories=predefined_categories,
                provider="gemini"
            )

            request = AIRequest(
                prompt=prompt,
                system_message="Você é um assistente especializado em categorizar transações financeiras. Forneça apenas o JSON solicitado sem explicações adicionais.",
                temperature=0.0,  # Determinístico
            )

            response = await self.generate_completion(request)

            try:
                response_text = response.content
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_data = response_text[json_start:json_end]
                    parsed_data = json.loads(json_data)

                    for i, item in enumerate(parsed_data.get("transactions", [])):
                        if i < len(batch):
                            batch[i].categories = item.get("categories", [])
                            batch[i].confidence_score = item.get("confidence_score", None)

                    categorized_transactions.extend(batch)
                else:
                    logger.error("Não foi possível encontrar JSON na resposta de categorização")
                    categorized_transactions.extend(batch)
            except Exception as e:
                logger.error(f"Erro ao processar resposta de categorização: {str(e)}")
                categorized_transactions.extend(batch)

        return categorized_transactions
