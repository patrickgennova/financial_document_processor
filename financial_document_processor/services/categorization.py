import logging
import re
from typing import Dict, List, Optional, Tuple

from financial_document_processor.adapters.ai.ai_provider import AIProvider
from financial_document_processor.domain.transaction import Transaction, TransactionType
from financial_document_processor.utils.validators import sanitize_categories

logger = logging.getLogger(__name__)


class CategorizationService:
    """
    Serviço responsável pela categorização de transações financeiras.

    Este serviço implementa a lógica para categorizar transações usando
    regras baseadas em padrões e processamento com IA, buscando otimizar
    o uso dos recursos de IA para reduzir custos.
    """

    def __init__(
            self,
            ai_provider: AIProvider,
            predefined_categories: Optional[List[str]] = None,
            batch_size: int = 10,
            min_confidence_threshold: float = 0.7,
            enable_caching: bool = True
    ):
        """
        Inicializa o serviço de categorização.

        Args:
            ai_provider: Provedor de IA a ser utilizado
            predefined_categories: Lista de categorias predefinidas
            batch_size: Tamanho do lote para processamento em batch
            min_confidence_threshold: Limite mínimo de confiança para aceitação
            enable_caching: Se deve habilitar cache de categorizações
        """
        self.ai_provider = ai_provider
        self.predefined_categories = predefined_categories
        self.batch_size = batch_size
        self.min_confidence_threshold = min_confidence_threshold
        self.enable_caching = enable_caching

        # Cache para evitar chamar a IA para padrões já processados
        self.categorization_cache: Dict[str, Tuple[List[str], float]] = {}

        # Carrega categorias padrão se não forem fornecidas
        if not self.predefined_categories:
            self._load_default_categories()

    def _load_default_categories(self):
        """
        Carrega as categorias padrão para uso quando não há categorias predefinidas.
        """
        self.predefined_categories = [
            # Moradia
            "aluguel", "hipoteca", "condomínio", "iptu", "água", "luz",
            "gás", "internet", "tv", "manutenção", "reforma",

            # Alimentação
            "supermercado", "restaurante", "delivery", "lanche", "café",

            # Transporte
            "combustível", "estacionamento", "transporte público",
            "aplicativo de transporte", "manutenção veículo", "ipva",
            "licenciamento", "seguro auto",

            # Saúde
            "plano de saúde", "medicamentos", "consulta médica", "exames",
            "terapia", "academia", "farmácia",

            # Educação
            "mensalidade escolar", "material escolar", "curso", "livros",

            # Lazer
            "streaming", "cinema", "teatro", "viagem", "hotel", "hobby",

            # Compras
            "vestuário", "calçados", "eletrônicos", "móveis", "presentes",

            # Serviços Financeiros
            "tarifa bancária", "juros", "investimento", "seguro", "empréstimo",

            # Renda
            "salário", "freelance", "bônus", "dividendos", "aluguel recebido",
            "reembolso", "venda",

            # Impostos
            "imposto de renda", "inss", "fgts"
        ]

        logger.info(f"Carregadas {len(self.predefined_categories)} categorias padrão")

    async def categorize_transaction(
            self,
            transaction: Transaction,
            use_ai: bool = True
    ) -> Transaction:
        """
        Categoriza uma única transação.

        Args:
            transaction: Transação a ser categorizada
            use_ai: Se deve usar IA para categorização

        Returns:
            Transação com categorias atualizadas
        """
        # Se já possui categorias, verifica se são válidas
        if transaction.categories and len(transaction.categories) > 0:
            if all(category for category in transaction.categories):
                # Sanitiza as categorias existentes
                transaction.categories = sanitize_categories(transaction.categories)
                return transaction

        # Tenta categorização baseada em regras primeiro
        categories, confidence = self._rule_based_categorization(transaction)

        # Se a confiança for alta o suficiente, usa o resultado
        if confidence >= self.min_confidence_threshold:
            transaction.categories = categories
            transaction.confidence_score = confidence
            return transaction

        # Se o uso de IA estiver habilitado, tenta categorização com IA
        if use_ai:
            # Verifica o cache primeiro
            cache_key = self._generate_cache_key(transaction)

            if self.enable_caching and cache_key in self.categorization_cache:
                cached_categories, cached_confidence = self.categorization_cache[cache_key]
                transaction.categories = cached_categories.copy()
                transaction.confidence_score = cached_confidence
                return transaction

            # Chama a IA para categorizar
            transactions_batch = [transaction]
            categorized_batch = await self.ai_provider.categorize_transactions(
                transactions=transactions_batch,
                predefined_categories=self.predefined_categories
            )

            if categorized_batch and len(categorized_batch) > 0:
                # Atualiza o cache
                if self.enable_caching and categorized_batch[0].confidence_score and categorized_batch[
                    0].confidence_score >= 0.8:
                    self.categorization_cache[cache_key] = (
                        categorized_batch[0].categories,
                        categorized_batch[0].confidence_score or 0.0
                    )

                return categorized_batch[0]

        # Se nada funcionou, usa as categorias baseadas em regras
        transaction.categories = categories
        transaction.confidence_score = confidence
        return transaction

    async def categorize_transactions(
            self,
            transactions: List[Transaction]
    ) -> List[Transaction]:
        """
        Categoriza uma lista de transações.

        Args:
            transactions: Lista de transações a serem categorizadas

        Returns:
            Lista de transações categorizadas
        """
        if not transactions:
            return []

        # Se todas as transações já tiverem categorias, retorna-as diretamente
        if all(
                transaction.categories and len(transaction.categories) > 0 and all(
                    category for category in transaction.categories)
                for transaction in transactions
        ):
            # Apenas sanitiza as categorias existentes
            for tx in transactions:
                tx.categories = sanitize_categories(tx.categories)
            return transactions

        # Aplica categorização baseada em regras para todas as transações
        transactions_requiring_ai = []

        for tx in transactions:
            # Pula transações que já têm categorias válidas
            if tx.categories and len(tx.categories) > 0 and all(category for category in tx.categories):
                tx.categories = sanitize_categories(tx.categories)
                continue

            # Tenta categorização baseada em regras
            categories, confidence = self._rule_based_categorization(tx)

            # Se a confiança for alta, usa o resultado
            if confidence >= self.min_confidence_threshold:
                tx.categories = categories
                tx.confidence_score = confidence
            else:
                # Verifica o cache
                cache_key = self._generate_cache_key(tx)

                if self.enable_caching and cache_key in self.categorization_cache:
                    cached_categories, cached_confidence = self.categorization_cache[cache_key]
                    tx.categories = cached_categories.copy()
                    tx.confidence_score = cached_confidence
                else:
                    # Adiciona à lista para processamento com IA
                    transactions_requiring_ai.append(tx)

        # Processa transações que precisam de IA em lotes
        if transactions_requiring_ai:
            # Divide em lotes para otimizar chamadas de API
            batches = [
                transactions_requiring_ai[i:i + self.batch_size]
                for i in range(0, len(transactions_requiring_ai), self.batch_size)
            ]

            # Processa cada lote
            for batch in batches:
                try:
                    # Chama a IA para categorizar o lote
                    categorized_batch = await self.ai_provider.categorize_transactions(
                        transactions=batch,
                        predefined_categories=self.predefined_categories
                    )

                    # Atualiza o cache com resultados de alta confiança
                    if self.enable_caching:
                        for categorized_tx in categorized_batch:
                            if categorized_tx.confidence_score and categorized_tx.confidence_score >= 0.8:
                                cache_key = self._generate_cache_key(categorized_tx)
                                self.categorization_cache[cache_key] = (
                                    categorized_tx.categories,
                                    categorized_tx.confidence_score
                                )

                except Exception as e:
                    logger.error(f"Erro ao categorizar lote com IA: {str(e)}")
                    # Continua com as próximas transações

        return transactions

    def filter_categories(
            self,
            categories: List[str],
            allowed_categories: Optional[List[str]] = None
    ) -> List[str]:
        """
        Filtra categorias com base em uma lista de categorias permitidas.

        Args:
            categories: Lista de categorias a serem filtradas
            allowed_categories: Lista de categorias permitidas

        Returns:
            Lista filtrada de categorias
        """
        if not allowed_categories:
            allowed_categories = self.predefined_categories

        if not allowed_categories:
            # Se não há lista de permitidas, retorna a lista original sanitizada
            return sanitize_categories(categories)

        allowed_set = {cat.lower() for cat in allowed_categories}
        filtered = [cat for cat in categories if cat.lower() in allowed_set]

        # Retorna a lista sanitizada
        return sanitize_categories(filtered)

    def _rule_based_categorization(
            self,
            transaction: Transaction
    ) -> Tuple[List[str], float]:
        """
        Implementa categorização baseada em regras para transações comuns.

        Args:
            transaction: Transação a ser categorizada

        Returns:
            Tupla (categorias, pontuação de confiança)
        """
        # Normaliza a descrição para matching mais confiável
        description = transaction.description.lower()

        # Patterns para categorias comuns
        patterns = {
            # Moradia
            r'aluguel': ['aluguel', 'moradia'],
            r'condomini|condomín': ['condomínio', 'moradia'],
            r'iptu': ['iptu', 'imposto', 'moradia'],
            r'agua|água|saneamento': ['água', 'utilidades', 'moradia'],
            r'luz|energia|eletric': ['luz', 'energia elétrica', 'utilidades', 'moradia'],
            r'gas|gás': ['gás', 'utilidades', 'moradia'],
            r'internet|fibra|banda larga|net|telecom': ['internet', 'telecomunicação', 'moradia'],

            # Alimentação
            r'supermercado|mercado|mart|super|carrefour|pão de açúcar': ['supermercado', 'alimentação'],
            r'restaurante|rest\.|lanchonete': ['restaurante', 'alimentação'],
            r'ifood|rappi|delivery|entrega': ['delivery', 'alimentação'],

            # Transporte
            r'combustivel|combustível|gasolina|etanol|posto|ipiranga|shell|petrobras': ['combustível', 'transporte'],
            r'estacionamento|parking|valet': ['estacionamento', 'transporte'],
            r'uber|99|taxi|táxi|cabify': ['aplicativo de transporte', 'transporte'],
            r'metro|metrô|trem|onibus|ônibus|brt|bilhete|passagem': ['transporte público', 'transporte'],
            r'ipva': ['ipva', 'imposto', 'transporte'],

            # Saúde
            r'plano de saude|plano de saúde|unimed|amil|sulamerica|bradesco saude': ['plano de saúde', 'saúde'],
            r'farmacia|farmácia|droga|medicamento': ['farmácia', 'medicamentos', 'saúde'],
            r'academia|gym|smart fit': ['academia', 'fitness', 'saúde'],
            r'médico|medico|consulta|clinica|clínica|psicólogo|psicólog': ['consulta médica', 'saúde'],
            r'hospital|emergência|emergencia|pronto': ['hospital', 'emergência médica', 'saúde'],

            # Educação
            r'mensalidade|faculdade|universidade|colégio|colegio|escola': ['mensalidade escolar', 'educação'],
            r'livro|livraria|book': ['livros', 'educação'],
            r'curso|workshop|treinamento': ['curso', 'educação', 'desenvolvimento profissional'],

            # Lazer
            r'netflix|disney|hbo|prime|spotify|streaming': ['streaming', 'assinatura', 'lazer'],
            r'cinema|cinemark|ingresso|movie|filme': ['cinema', 'entretenimento', 'lazer'],
            r'viagem|hotel|airbnb|booking|hospedagem|pousada': ['viagem', 'hospedagem', 'lazer'],

            # Serviços Financeiros
            r'tarifa|anuidade|manutenção conta|manut\. conta': ['tarifa bancária', 'serviços financeiros'],
            r'seguro|porto seguro|seguradora': ['seguro', 'serviços financeiros'],
            r'investimento|aplicação|resgate': ['investimento', 'serviços financeiros'],
            r'empréstimo|emprestimo|financiamento|parcela': ['empréstimo', 'financiamento', 'serviços financeiros'],

            # Renda
            r'salario|salário|pagamento|folha|vencimento': ['salário', 'renda'],
            r'rendimento|dividendo': ['rendimento', 'dividendos', 'renda'],
        }

        # Procura por padrões na descrição
        matched_categories = []
        best_confidence = 0.0

        for pattern, categories in patterns.items():
            if re.search(pattern, description):
                matched_categories.extend(categories)
                # Atribui uma confiança maior para matches mais específicos (padrões mais longos)
                confidence = 0.7 + min(0.2, len(pattern) / 100)
                best_confidence = max(best_confidence, confidence)

        # Remove duplicatas e mantém a ordem
        unique_categories = []
        seen = set()
        for cat in matched_categories:
            if cat not in seen:
                unique_categories.append(cat)
                seen.add(cat)

        # Se não conseguir categorizar, retorna uma lista vazia com baixa confiança
        if not unique_categories:
            # Tenta inferir pelo menos o tipo básico
            if transaction.type == TransactionType.CREDIT:
                return ["renda", "entrada"], 0.6 if transaction.amount and transaction.amount > 1000 else 0.4
            else:
                return ["despesa"], 0.3

        # Limita a 3 categorias por transação
        return unique_categories[:3], best_confidence

    def _generate_cache_key(self, transaction: Transaction) -> str:
        """
        Gera uma chave de cache para uma transação.

        A chave de cache é baseada na descrição normalizada da transação
        e no seu tipo, ignorando valores específicos.

        Args:
            transaction: Transação a ser processada

        Returns:
            String única para uso como chave de cache
        """
        # Normaliza a descrição
        description = transaction.description.lower()
        # Remove números e caracteres especiais para melhor agrupamento
        description = re.sub(r'[0-9,.:\-/]', '', description)
        # Remove espaços extras
        description = re.sub(r'\s+', ' ', description).strip()

        # Constrói a chave de cache com o tipo e descrição processada
        return f"{transaction.type.value}:{description}"