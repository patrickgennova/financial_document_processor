"""
Setup script for the financial_document_processor package.
"""
from setuptools import setup, find_packages

setup(
    name="financial-document-processor",
    version="0.1.0",
    description="Microserviço para processamento de documentos financeiros com IA",
    author="Seu Nome",
    author_email="seu.email@exemplo.com",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "aiokafka>=0.8.0",
        "pydantic>=2.0.0",
        "loguru>=0.7.0",
        "httpx>=0.24.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.5",
        "asyncpg>=0.27.0",
        "openai>=1.0.0",
        "google-generativeai>=0.3.0",
        "anthropic>=0.5.0",
        "pypdf>=3.15.1",
        "pytesseract>=0.3.10",
        "tenacity>=8.2.0",
        "prometheus-client>=0.17.0",
        "alembic>=1.10.0",
        "python-dotenv>=1.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "pytest-asyncio>=0.20.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
            "ruff>=0.0.260",
            "greenlet>=3.2.2"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Financial",
    ],
)