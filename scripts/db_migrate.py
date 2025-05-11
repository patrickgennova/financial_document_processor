#!/usr/bin/env python
"""
Script para executar migrações do banco de dados.

Uso:
    python scripts/db_migrate.py upgrade   # Aplica todas as migrações pendentes
    python scripts/db_migrate.py downgrade # Reverte a última migração
    python scripts/db_migrate.py create "Descrição da migração"  # Cria uma nova migração
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Carrega variáveis de ambiente do arquivo .env
from dotenv import load_dotenv
env_path = ROOT_DIR / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

# Importa as configurações do projeto
from financial_document_processor.config import get_settings


def run_alembic(args):
    """Executa comandos do Alembic."""
    settings = get_settings()

    # Define variáveis de ambiente para o Alembic
    env = os.environ.copy()
    env["DATABASE_URL"] = settings.database.url

    # Constrói o comando do Alembic
    alembic_cmd = ["alembic"] + args

    # Executa o comando
    subprocess.run(alembic_cmd, env=env, cwd=ROOT_DIR)


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(description="Ferramenta de migração de banco de dados")
    parser.add_argument("command", choices=["upgrade", "downgrade", "create"], help="Comando de migração")
    parser.add_argument("arg", nargs="?", help="Argumento adicional para o comando (ex: descrição ou revisão)")

    args = parser.parse_args()

    if args.command == "upgrade":
        run_alembic(["upgrade", "head"])
        print("Migração concluída com sucesso!")

    elif args.command == "downgrade":
        run_alembic(["downgrade", "-1"])
        print("Migração revertida com sucesso!")

    elif args.command == "create":
        if not args.arg:
            print("Erro: A descrição da migração é obrigatória para o comando 'create'")
            sys.exit(1)

        run_alembic(["revision", "--autogenerate", "-m", args.arg])
        print(f"Migração '{args.arg}' criada com sucesso!")


if __name__ == "__main__":
    main()