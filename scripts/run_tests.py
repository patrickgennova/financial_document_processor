#!/usr/bin/env python
"""
Script para executar os testes automatizados.

Uso:
    python scripts/run_tests.py [unit|integration|all] [--coverage]
"""
import os
import subprocess
import sys
from pathlib import Path

# Adiciona o diretório raiz do projeto ao PATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))


def run_tests(test_type="all", coverage=False):
    """
    Executa os testes automatizados.

    Args:
        test_type: Tipo de testes a serem executados (unit, integration, all)
        coverage: Se deve gerar relatório de cobertura
    """
    # Configura o comando base
    command = ["pytest", "-v"]

    # Adiciona parâmetros específicos por tipo de teste
    if test_type == "unit":
        command.append("tests/unit")
    elif test_type == "integration":
        command.append("tests/integration")
    elif test_type == "all":
        command.append("tests")
    else:
        print(f"Tipo de teste inválido: {test_type}")
        print("Tipos válidos: unit, integration, all")
        sys.exit(1)

    # Adiciona cobertura se solicitado
    if coverage:
        command.extend(["--cov=financial_document_processor", "--cov-report=term", "--cov-report=html"])

    # Executa os testes
    print(f"Executando testes: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT_DIR)

    if coverage:
        print("\nRelatório de cobertura gerado em: htmlcov/index.html")

    # Retorna o código de saída
    return result.returncode


def main():
    """Função principal."""
    # Processa argumentos
    test_type = "all"
    coverage = False

    if len(sys.argv) > 1:
        test_type = sys.argv[1]

    if "--coverage" in sys.argv or "-c" in sys.argv:
        coverage = True

    # Executa os testes
    exit_code = run_tests(test_type, coverage)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()