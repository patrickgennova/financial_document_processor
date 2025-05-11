from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field


class Category(BaseModel):
    """
    Modelo que representa uma categoria de transação financeira.
    """
    name: str = Field(description="Nome da categoria")
    description: Optional[str] = Field(default=None, description="Descrição da categoria")
    parent: Optional[str] = Field(default=None, description="Categoria pai (para hierarquia)")
    keywords: List[str] = None

    class Config:
        """Configurações do modelo Pydantic."""
        frozen = True


class CategoryRegistry:
    """
    Registro de categorias disponíveis para categorização.
    """
    _categories: Dict[str, Category] = {}
    _generic_categories: Set[str] = {
        "outros", "pix", "pagamento", "transferência", "diversos", "geral",
        "others", "payment", "transfer", "general", "miscellaneous"
    }

    @classmethod
    def register(cls, category: Category) -> None:
        """Registra uma nova categoria."""
        cls._categories[category.name.lower()] = category

    @classmethod
    def get(cls, name: str) -> Optional[Category]:
        """Obtém uma categoria pelo nome."""
        return cls._categories.get(name.lower())

    @classmethod
    def get_all(cls) -> List[Category]:
        """Retorna todas as categorias registradas."""
        return list(cls._categories.values())

    @classmethod
    def is_generic(cls, category_name: str) -> bool:
        """Verifica se uma categoria é considerada genérica (deve ser evitada)."""
        return category_name.lower() in cls._generic_categories

    @classmethod
    def add_generic_category(cls, category_name: str) -> None:
        """Adiciona uma categoria à lista de categorias genéricas."""
        cls._generic_categories.add(category_name.lower())

    @classmethod
    def get_generic_categories(cls) -> Set[str]:
        """Retorna todas as categorias genéricas."""
        return cls._generic_categories.copy()