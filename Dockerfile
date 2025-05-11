# Dockerfile
FROM python:3.10-slim

# Argumentos de build
ARG USER_ID=1000
ARG GROUP_ID=1000

# Instala dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-por \
    imagemagick \
    poppler-utils \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Configura política do ImageMagick para converter PDFs
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' /etc/ImageMagick-6/policy.xml

# Cria um usuário não-root
RUN groupadd -g ${GROUP_ID} appuser && \
    useradd -u ${USER_ID} -g appuser -m appuser

# Define o diretório de trabalho
WORKDIR /app

# Cria diretório para logs com permissões apropriadas
RUN mkdir -p /app/logs && chown -R appuser:appuser /app/logs

# Copia os arquivos do projeto
COPY pyproject.toml setup.py README.md ./
COPY financial_document_processor ./financial_document_processor

# Instala as dependências
RUN pip install --no-cache-dir -e .

# Altera para o usuário não-root
USER appuser

# Define o ponto de entrada
ENTRYPOINT ["python", "-m", "financial_document_processor.main"]