import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional, Tuple


def validate_decimal(value: Any) -> Tuple[bool, Optional[Decimal]]:
    """
    Valida se um valor pode ser convertido para Decimal.

    Args:
        value: Valor a ser validado

    Returns:
        Tupla (sucesso, valor_decimal)
    """
    if value is None:
        return False, None

    # Se já for um Decimal, retorna-o diretamente
    if isinstance(value, Decimal):
        return True, value

    # Se for string, tenta converter
    if isinstance(value, str):
        # Remove caracteres não numéricos, exceto . e -
        value = re.sub(r'[^\d.-]', '', value)

        # Tenta converter para Decimal
        try:
            decimal_value = Decimal(value)
            return True, decimal_value
        except (InvalidOperation, ValueError):
            return False, None

    # Se for um número, converte para Decimal
    if isinstance(value, (int, float)):
        try:
            return True, Decimal(str(value))
        except (InvalidOperation, ValueError):
            return False, None

    return False, None


def validate_date(value: Any) -> Tuple[bool, Optional[date]]:
    """
    Valida se um valor pode ser convertido para uma data.

    Args:
        value: Valor a ser validado

    Returns:
        Tupla (sucesso, valor_data)
    """
    if value is None:
        return False, None

    # Se já for uma data, retorna diretamente
    if isinstance(value, date):
        return True, value

    # Se for datetime, converte para date
    if isinstance(value, datetime):
        return True, value.date()

    # Se for string, tenta diferentes formatos
    if isinstance(value, str):
        formats = [
            '%d/%m/%Y',  # DD/MM/YYYY
            '%d/%m/%y',  # DD/MM/YY
            '%Y-%m-%d',  # YYYY-MM-DD (ISO)
            '%d-%m-%Y',  # DD-MM-YYYY
            '%d.%m.%Y',  # DD.MM.YYYY
            '%d.%m.%y',  # DD.MM.YY
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(value.strip(), fmt)
                return True, dt.date()
            except ValueError:
                continue

    return False, None


def sanitize_categories(categories: List[str]) -> List[str]:
    """
    Sanitiza uma lista de categorias, removendo duplicatas e valores vazios.

    Args:
        categories: Lista de categorias a ser sanitizada

    Returns:
        Lista sanitizada de categorias
    """
    if not categories:
        return []

    # Remove espaços em branco e converte para minúsculas
    sanitized = [cat.strip().lower() for cat in categories if cat and cat.strip()]

    # Remove duplicatas mantendo a ordem
    seen = set()
    return [cat for cat in sanitized if not (cat in seen or seen.add(cat))]