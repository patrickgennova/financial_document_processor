import json
from typing import List, Optional

from financial_document_processor.domain.category import CategoryRegistry
from financial_document_processor.domain.transaction import Transaction


class PromptEngineering:
    """
    Serviço responsável por criar prompts otimizados para diferentes provedores de IA.

    Este serviço implementa técnicas de engenharia de prompts para maximizar a qualidade
    dos resultados enquanto minimiza o uso de tokens (e consequentemente os custos).
    """

    def __init__(self):
        # Mapeamento de modelos para estilos de prompts
        self.provider_styles = {
            "openai": {
                "extraction_template": self._openai_extraction_template,
                "categorization_template": self._openai_categorization_template,
            },
            "gemini": {
                "extraction_template": self._gemini_extraction_template,
                "categorization_template": self._gemini_categorization_template,
            },
            "claude": {
                "extraction_template": self._claude_extraction_template,
                "categorization_template": self._claude_categorization_template,
            },
        }

    def create_extraction_prompt(
            self,
            text_content: str,
            document_type: str,
            predefined_categories: Optional[List[str]] = None,
            provider: str = "openai"
    ) -> str:
        """
        Cria um prompt otimizado para extração de transações.

        Args:
            text_content: Texto do documento a ser processado
            document_type: Tipo do documento (ex: bank_statement)
            predefined_categories: Lista de categorias predefinidas (opcional)
            provider: Nome do provedor de IA ('openai', 'gemini', 'claude')

        Returns:
            String com o prompt formatado
        """
        # Limita o tamanho do texto para evitar exceder limites de tokens
        max_text_length = 15000  # Ajuste conforme necessário
        if len(text_content) > max_text_length:
            text_content = text_content[:max_text_length] + "..."

        categories_str = ""
        if predefined_categories and len(predefined_categories) > 0:
            categories_str = "\n\nCategorias disponíveis para uso: " + ", ".join(predefined_categories)

        template_func = self.provider_styles.get(
            provider, self.provider_styles["openai"]
        )["extraction_template"]

        template = template_func(text_content, document_type, categories_str)

        return template

    def create_categorization_prompt(
            self,
            transactions: List[Transaction],
            predefined_categories: Optional[List[str]] = None,
            provider: str = "openai"
    ) -> str:
        """
        Cria um prompt otimizado para categorização de transações.

        Args:
            transactions: Lista de transações a serem categorizadas
            predefined_categories: Lista de categorias predefinidas (opcional)
            provider: Nome do provedor de IA ('openai', 'gemini', 'claude')

        Returns:
            String com o prompt formatado
        """
        transactions_json = []
        for tx in transactions:
            transactions_json.append({
                "id": str(tx.id),
                "date": tx.date.isoformat(),
                "description": tx.description,
                "amount": str(tx.amount),
                "type": tx.type,
                "method": tx.method,
                "categories": tx.categories if tx.categories else []
            })

        transactions_str = json.dumps(transactions_json, ensure_ascii=False, indent=2)

        categories_instructions = ""
        if predefined_categories and len(predefined_categories) > 0:
            categories_str = ", ".join(predefined_categories)
            categories_instructions = f"""
Você deve usar APENAS as seguintes categorias: {categories_str}.

Se a transação não se encaixar em nenhuma dessas categorias, deixe a lista de categorias vazia.
"""
        else:
            generic_categories = list(CategoryRegistry.get_generic_categories())
            generic_categories_str = ", ".join(f'"{cat}"' for cat in generic_categories)

            categories_instructions = f"""
Atribua categorias específicas e descritivas para cada transação.

Evite categorias genéricas como: {generic_categories_str}.

Se você não conseguir determinar uma categoria específica para a transação, deixe a lista de categorias vazia em vez de usar uma categoria genérica.
"""

        template_func = self.provider_styles.get(
            provider, self.provider_styles["openai"]
        )["categorization_template"]

        return template_func(transactions_str, categories_instructions)

    def _openai_extraction_template(
            self, text_content: str, document_type: str, categories_str: str
    ) -> str:
        """Template de extração para OpenAI."""
        return f"""
# Tarefa: Extração de Transações Financeiras

## Contexto
Você está analisando um extrato bancário do tipo '{document_type}'.
O conteúdo está em formato de texto plano, extraído de um documento original.

## Conteúdo do Documento
```
{text_content}
```

## Instruções
1. Extraia TODAS as transações financeiras encontradas no extrato acima.
2. Para cada transação, identifique:
   - Data da transação (formato ISO 'YYYY-MM-DD')
   - Descrição
   - Valor (número decimal)
   - Tipo (CREDIT para entradas, DEBIT para saídas)
   - Método (PIX, TED, BOLETO, etc. se puder identificar)
   - Categorias (lista de strings)
3. Atribua uma pontuação de confiança (0 a 1) para cada transação extraída.
{categories_str}

## Formato de Saída
Retorne os resultados em formato JSON conforme o exemplo abaixo:

```json
{{
  "transactions": [
    {{
      "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário"],
      "confidence_score": 0.95
    }},
    {{
      "date": "2023-01-20",
      "description": "PAGAMENTO - CONTA DE LUZ",
      "amount": "150.25",
      "type": "DEBIT",
      "method": "BOLETO",
      "categories": ["utilidades", "conta de luz"],
      "confidence_score": 0.92
    }}
  ]
}}
```

## Observações Importantes
- Seja preciso e extraia TODAS as transações, mesmo que pareçam redundantes.
- Foque apenas em transações reais (não extraia saldos, totais ou informações de cabeçalho).
- Se não conseguir identificar algum campo, deixe-o vazio ou null.
- Forneça APENAS o JSON solicitado, sem explicações adicionais.
- Se não houver transações identificáveis, retorne um array vazio.
"""

    def _gemini_extraction_template(
            self, text_content: str, document_type: str, categories_str: str
    ) -> str:
        """Template de extração para Gemini."""
        return f"""
Extraia todas as transações financeiras do seguinte documento do tipo '{document_type}'.

DOCUMENTO:
```
{text_content}
```

INSTRUÇÕES DETALHADAS:
1. Analise o documento acima e extraia todas as transações financeiras individuais.
2. Para cada transação, identifique:
   * Data da transação (formato ISO 'YYYY-MM-DD')
   * Descrição completa da transação
   * Valor exato da transação (número decimal)
   * Tipo da transação: 'credit' para entradas de dinheiro ou 'debit' para saídas
   * Método utilizado, se identificável  ('pix', 'ted', 'doc', 'boleto', 'payment', 'transfer', 'withdrawal', 'deposit', 'loan' ou 'other')
   * Categorias apropriadas para a transação
3. Atribua uma pontuação de confiança (0 a 1) para cada extração
4. Não crie categorias genericas como "transferencia", "recebimento", "pix", etc.
{categories_str}

DIRETRIZES DE PRECISÃO:
- Inclua TODAS as transações visíveis no documento
- Não inclua saldos, totais ou informações de cabeçalho
- Mantenha a precisão nos valores e datas
- Se um campo não puder ser determinado, deixe-o vazio (null)

FORMATO DE RESPOSTA:
Retorne exclusivamente um objeto JSON com a seguinte estrutura:

```json
{{
        "transactions": [
    {{
        "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário"],
      "confidence_score": 0.95
    }}
  ]
}}
```

Se não encontrar transações, retorne um array vazio: {{"transactions": []}}

IMPORTANTE: Responda APENAS com o JSON solicitado, sem texto adicional ou explicações.
"""

    def _claude_extraction_template(
            self, text_content: str, document_type: str, categories_str: str
    ) -> str:
        """Template de extração para Claude."""
        return f"""<documento>
{text_content}
</documento>

Extraia todas as transações financeiras do documento acima, que é um '{document_type}'.

{categories_str}

Siga estas regras rigorosamente:

1. Identifique CADA transação individual presente no documento
2. Para cada transação, extraia:
   - Data (formato YYYY-MM-DD)
   - Descrição completa
   - Valor monetário (como string decimal)
   - Tipo: "credit" para recebimentos ou "debit" para pagamentos
   - Método de pagamento/recebimento quando identificável ('pix', 'ted', 'doc', 'boleto', 'payment', 'transfer', 'withdrawal', 'deposit', 'loan' ou 'other')
   - Categorias relevantes
   - Um valor de confiança entre 0 e 1

3. Não inclua saldos, totais ou informações que não sejam transações
4. Quando não for possível identificar um campo, deixe-o como null
5. Seja extremamente preciso com valores e datas
6. Não crie categorias genericas como "transferencia", "recebimento", "pix", etc.

Retorne os resultados em um JSON estruturado exatamente assim:

```json
{{
        "transactions": [
    {{
        "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário"],
      "confidence_score": 0.95
    }},
    {{
        "date": "2023-01-20",
      "description": "PAGAMENTO - CONTA DE LUZ",
      "amount": "150.25",
      "type": "DEBIT",
      "method": "BOLETO",
      "categories": ["utilidades", "conta de luz"],
      "confidence_score": 0.92
    }}
  ]
}}
```

Responda APENAS com o JSON, sem explicações adicionais.
"""

    def _openai_categorization_template(
            self, transactions_str: str, categories_instructions: str
    ) -> str:
        """Template de categorização para OpenAI."""
        return f"""
# Tarefa: Categorização de Transações Financeiras

## Dados
Abaixo está uma lista de transações financeiras em formato JSON:

```json
{transactions_str}
```

## Instruções
1. Categorize cada transação com base em sua descrição e outros detalhes disponíveis.
2. Adicione ou atualize o campo `categories` para cada transação com uma lista de 1-3 categorias relevantes.
3. Adicione uma pontuação de confiança (`confidence_score`) entre 0 e 1 para cada categorização.

{categories_instructions}

## Formato de Saída
Retorne um objeto JSON contendo a mesma lista de transações, com os campos `categories` e `confidence_score` atualizados:

```json
{{
  "transactions": [
    {{
      "id": "transaction-id-1",
      "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário", "renda fixa"],
      "confidence_score": 0.95
    }},
    {{
      "id": "transaction-id-2",
      "description": "SUPERMERCADO SILVA",
      "date": "2023-01-16",
      "amount": "253.45",
      "type": "DEBIT",
      "method": "CARTÃO DE CRÉDITO",
      "categories": ["alimentação", "supermercado"],
      "confidence_score": 0.92
    }}
  ]
}}
```

## Observações Importantes
- Forneça APENAS o JSON solicitado, sem explicações adicionais.
- Mantenha todos os campos originais das transações.
- Atualize apenas os campos `categories` e `confidence_score`.
"""

    def _gemini_categorization_template(
            self, transactions_str: str, categories_instructions: str
    ) -> str:
        """Template de categorização para Gemini."""
        return f"""
Categorize as seguintes transações financeiras:

```json
{transactions_str}
```

INSTRUÇÕES DETALHADAS:
1. Analise cada transação e atribua categorias adequadas com base na descrição e outros detalhes
2. Para cada transação, atualize apenas:
   * O campo "categories": lista com 1-3 categorias relevantes
   * O campo "confidence_score": valor entre 0 e 1 indicando a confiança da categorização

{categories_instructions}

DIRETRIZES DE CATEGORIZAÇÃO:
- Seja específico e preciso nas categorias atribuídas
- Use categorias que façam sentido para finanças pessoais
- Use entre 1 e 3 categorias por transação
- Mantenha consistência nas categorias entre transações similares

FORMATO DE RESPOSTA:
Retorne um objeto JSON contendo a lista de transações com os campos "categories" e "confidence_score" atualizados:

```json
{{
        "transactions": [
    {{
        "id": "transaction-id-1",
      "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário"],
      "confidence_score": 0.95
    }}
  ]
}}
```

IMPORTANTE: Responda APENAS com o JSON solicitado, sem texto adicional ou explicações.
"""

    def _claude_categorization_template(
            self, transactions_str: str, categories_instructions: str
    ) -> str:
        """Template de categorização para Claude."""
        return f"""<transações>
{transactions_str}
</transações>

Categorize cada transação financeira acima segundo as seguintes instruções:

{categories_instructions}

Diretrizes específicas:
1. Analise cuidadosamente a descrição, valor, tipo e método de cada transação
2. Atribua de 1 a 3 categorias precisas e relevantes para cada transação
3. Adicione uma pontuação de confiança (0-1) para cada categorização
4. Mantenha consistência nas categorias entre transações similares
5. Use categorias específicas e significativas que ajudem na organização financeira

Retorne as transações categorizadas em um JSON estruturado exatamente como este exemplo:

```json
{{
        "transactions": [
    {{
        "id": "transaction-id-1",
      "date": "2023-01-15",
      "description": "TRANSFERÊNCIA RECEBIDA - JOÃO SILVA",
      "amount": "1500.00",
      "type": "CREDIT",
      "method": "TED",
      "categories": ["salário", "renda fixa"],
      "confidence_score": 0.95
    }}
  ]
}}
```

Importante: Mantenha todos os campos originais das transações, atualizando apenas os campos "categories" e "confidence_score".

Responda APENAS com o JSON, sem explicações adicionais.
"""