#!/usr/bin/env python
"""
Script para resetar completamente o banco de dados.

ATENÇÃO: Este script é destrutivo e deve ser usado apenas em ambiente de desenvolvimento.
Ele remove todas as tabelas e tipos personalizados do banco de dados configurado.

Uso:
    python scripts/db_reset.py [-f]  # Use -f para forçar a exclusão sem confirmação
"""
import argparse
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Adiciona o diretório raiz do projeto ao PATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Importa as configurações do projeto
from financial_document_processor.config import get_settings


def reset_database(force: bool = False):
    """Reseta completamente o banco de dados."""
    settings = get_settings()
    db_url = settings.database.url

    if not force:
        print(f"ATENÇÃO: Você está prestes a resetar o banco de dados: {db_url}")
        confirm = input("Digite 'sim' para confirmar: ")

        if confirm.lower() != 'sim':
            print("Operação cancelada.")
            return

    engine = create_engine(db_url)

    with engine.connect() as conn:
        # Inicia uma transação
        with conn.begin():
            # Encontra todas as tabelas no esquema público
            tables = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname='public'")
            ).fetchall()
            table_names = [table[0] for table in tables]

            # Drop cascaded para remover todas as tabelas
            if table_names:
                print(f"Removendo tabelas: {', '.join(table_names)}")
                for table in table_names:
                    conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))

            # Remove todos os tipos enum personalizados
            enums = conn.execute(
                text("SELECT typname FROM pg_type JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid GROUP BY typname")
            ).fetchall()
            enum_names = [enum[0] for enum in enums]

            if enum_names:
                print(f"Removendo tipos enum: {', '.join(enum_names)}")
                for enum in enum_names:
                    conn.execute(text(f'DROP TYPE IF EXISTS "{enum}" CASCADE'))

            # Limpa a tabela de migrações do Alembic
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))

    print("Banco de dados resetado com sucesso!")
    print("Execute 'python scripts/db_migrate.py upgrade' para recriar as tabelas.")


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Ferramenta para resetar o banco de dados")
    parser.add_argument("-f", "--force", action="store_true", help="Força o reset sem confirmação")

    args = parser.parse_args()
    reset_database(args.force)


if __name__ == "__main__":
    main()