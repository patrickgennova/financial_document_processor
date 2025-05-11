import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import asyncpg

from financial_document_processor.adapters.database.repository import Repository
from financial_document_processor.domain.document import Document, DocumentStatus
from financial_document_processor.domain.transaction import Transaction, TransactionMethod, TransactionType
from financial_document_processor.utils.retry import async_retry

logger = logging.getLogger(__name__)


class PostgresRepository(Repository):
    """
    Implementação do repositório de dados usando PostgreSQL.
    """

    def __init__(
            self,
            connection_string: str,
            min_connections: int = 5,
            max_connections: int = 20
    ):
        """
        Inicializa o repositório PostgreSQL.

        Args:
            connection_string: String de conexão com o PostgreSQL
            min_connections: Número mínimo de conexões no pool
            max_connections: Número máximo de conexões no pool
        """
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool = None

    async def connect(self):
        """Estabelece a conexão com o banco de dados."""
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.connection_string,
                min_size=self.min_connections,
                max_size=self.max_connections,
                # Customizações para tipos especiais
                command_timeout=60,
                init=self._init_connection
            )

            logger.info(
                f"Conexão estabelecida com o PostgreSQL. "
                f"Pool criado com {self.min_connections}-{self.max_connections} conexões."
            )

            await self._ensure_schema()

        except Exception as e:
            logger.error(f"Erro ao estabelecer conexão com PostgreSQL: {str(e)}")
            raise

    @staticmethod
    async def _init_connection(conn):
        """
        Inicializa uma conexão no pool.

        Configura funções de conversão para tipos especiais.

        Args:
            conn: Conexão PostgreSQL
        """
        # Conversão de UUID
        await conn.set_type_codec(
            'uuid',
            encoder=lambda u: str(u),
            decoder=lambda u: UUID(u),
            schema='pg_catalog'
        )

        # Registro de JSONB
        await conn.set_type_codec(
            'jsonb',
            encoder=lambda obj: json.dumps(obj),
            decoder=lambda data: json.loads(data),
            schema='pg_catalog',
            format='text'
        )

    async def disconnect(self):
        """Encerra a conexão com o banco de dados."""
        if self.pool:
            await self.pool.close()
            logger.info("Conexão com PostgreSQL encerrada")

    async def _ensure_schema(self):
        """
        Garante que o esquema necessário existe no banco de dados.

        Cria tabelas, índices e outros objetos se não existirem.
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id BIGINT PRIMARY KEY,
                    external_id UUID NOT NULL,
                    user_id BIGINT NOT NULL,
                    document_type VARCHAR(50) NOT NULL,
                    filename VARCHAR(255) NOT NULL,
                    content_type VARCHAR(100) NOT NULL,
                    file_content TEXT NOT NULL,
                    categories JSONB,
                    status VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );

                -- Índices para melhorar a performance
                CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
                CREATE INDEX IF NOT EXISTS idx_documents_external_id ON documents(external_id);
                CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id UUID PRIMARY KEY,
                    document_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    date DATE NOT NULL,
                    description TEXT NOT NULL,
                    amount DECIMAL(15, 2) NOT NULL,
                    type VARCHAR(10) NOT NULL,
                    method VARCHAR(20),
                    categories JSONB,
                    confidence_score FLOAT,
                    created_at TIMESTAMP NOT NULL,

                    CONSTRAINT fk_transactions_document
                        FOREIGN KEY(document_id)
                        REFERENCES documents(id)
                        ON DELETE CASCADE
                );

                -- Índices para melhorar a performance
                CREATE INDEX IF NOT EXISTS idx_transactions_document_id ON transactions(document_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
                CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
            """)

            logger.info("Esquema do banco de dados verificado/criado com sucesso")

    @async_retry(max_retries=3)
    async def save_document(self, document: Document) -> Document:
        """
        Salva um documento no banco de dados.

        Args:
            document: Documento a ser salvo

        Returns:
            Documento salvo com possíveis campos atualizados
        """
        async with self.pool.acquire() as conn:
            try:
                # Verifica se o documento já existe
                existing = await conn.fetchrow(
                    "SELECT id FROM documents WHERE id = $1", document.id
                )

                if existing:
                    # Atualiza o documento existente
                    await conn.execute("""
                        UPDATE documents
                        SET document_type = $1,
                            filename = $2,
                            content_type = $3,
                            file_content = $4,
                            categories = $5,
                            status = $6,
                            updated_at = $7
                        WHERE id = $8
                    """,
                                       document.document_type,
                                       document.filename,
                                       document.content_type,
                                       document.file_content,
                                       json.dumps([c for c in document.categories]) if document.categories else None,
                                       document.status.value,
                                       datetime.now(),
                                       document.id
                                       )
                else:
                    # Insere um novo documento
                    await conn.execute("""
                        INSERT INTO documents(
                            id, external_id, user_id, document_type, filename,
                            content_type, file_content, categories, status,
                            created_at, updated_at
                        )
                        VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                                       document.id,
                                       document.external_id,
                                       document.user_id,
                                       document.document_type,
                                       document.filename,
                                       document.content_type,
                                       document.file_content,
                                       json.dumps([c for c in document.categories]) if document.categories else None,
                                       document.status.value,
                                       document.created_at,
                                       document.updated_at
                                       )

                logger.debug(f"Documento {document.id} salvo com sucesso")
                return document

            except Exception as e:
                logger.error(f"Erro ao salvar documento {document.id}: {str(e)}")
                raise

    @async_retry(max_retries=3)
    async def get_document(self, document_id: int) -> Optional[Document]:
        """
        Obtém um documento pelo ID.

        Args:
            document_id: ID do documento

        Returns:
            Documento encontrado ou None
        """
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM documents WHERE id = $1", document_id
                )

                if not row:
                    return None

                categories = json.loads(row['categories']) if row['categories'] else None

                return Document(
                    id=row['id'],
                    external_id=row['external_id'],
                    user_id=row['user_id'],
                    document_type=row['document_type'],
                    filename=row['filename'],
                    content_type=row['content_type'],
                    file_content=row['file_content'],
                    categories=categories,
                    status=DocumentStatus(row['status']),
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )

            except Exception as e:
                logger.error(f"Erro ao buscar documento {document_id}: {str(e)}")
                raise

    @async_retry(max_retries=3)
    async def update_document_status(
            self, document_id: int, status: DocumentStatus
    ) -> bool:
        """
        Atualiza o status de um documento.

        Args:
            document_id: ID do documento
            status: Novo status

        Returns:
            True se atualizado com sucesso, False caso contrário
        """
        async with self.pool.acquire() as conn:
            try:
                # Atualiza o status do documento
                result = await conn.execute("""
                    UPDATE documents
                    SET status = $1, updated_at = $2
                    WHERE id = $3
                """,
                                            status.value,
                                            datetime.now(),
                                            document_id
                                            )

                success = result and "UPDATE 1" in result

                if success:
                    logger.debug(f"Status do documento {document_id} atualizado para {status.value}")
                else:
                    logger.warning(f"Documento {document_id} não encontrado para atualização de status")

                return success

            except Exception as e:
                logger.error(f"Erro ao atualizar status do documento {document_id}: {str(e)}")
                raise

    @async_retry(max_retries=3)
    async def save_transactions(self, transactions: List[Transaction]) -> List[Transaction]:
        """
        Salva uma lista de transações no banco de dados.

        Args:
            transactions: Lista de transações a ser salva

        Returns:
            Lista de transações salvas com possíveis campos atualizados
        """
        if not transactions:
            return []

        async with self.pool.acquire() as conn:
            # Inicia uma transação no banco
            async with conn.transaction():
                try:
                    saved_transactions = []

                    for tx in transactions:
                        existing = await conn.fetchrow(
                            "SELECT id FROM transactions WHERE id = $1", tx.id
                        )

                        if existing:
                            await conn.execute("""
                                UPDATE transactions
                                SET date = $1,
                                    description = $2,
                                    amount = $3,
                                    type = $4,
                                    method = $5,
                                    categories = $6,
                                    confidence_score = $7
                                WHERE id = $8
                            """,
                                               tx.date,
                                               tx.description,
                                               tx.amount,
                                               tx.type.value,
                                               tx.method.value if tx.method else None,
                                               json.dumps([c for c in tx.categories]) if tx.categories else None,
                                               tx.confidence_score,
                                               tx.id
                                               )
                        else:
                            await conn.execute("""
                                INSERT INTO transactions(
                                    id, document_id, user_id, date, description,
                                    amount, type, method, categories, confidence_score,
                                    created_at
                                )
                                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                            """,
                                               tx.id,
                                               tx.document_id,
                                               tx.user_id,
                                               tx.date,
                                               tx.description,
                                               tx.amount,
                                               tx.type.value,
                                               tx.method.value if tx.method else None,
                                               json.dumps([c for c in tx.categories]) if tx.categories else None,
                                               tx.confidence_score,
                                               tx.created_at
                                               )

                        saved_transactions.append(tx)

                    logger.info(f"Salvas {len(saved_transactions)} transações com sucesso")
                    return saved_transactions

                except Exception as e:
                    logger.error(f"Erro ao salvar transações: {str(e)}")
                    raise

    @async_retry(max_retries=3)
    async def get_transactions_by_document(
            self, document_id: int
    ) -> List[Transaction]:
        """
        Obtém todas as transações associadas a um documento.

        Args:
            document_id: ID do documento

        Returns:
            Lista de transações
        """
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    "SELECT * FROM transactions WHERE document_id = $1 ORDER BY date", document_id
                )

                transactions = []
                for row in rows:
                    categories = json.loads(row['categories']) if row['categories'] else []

                    tx = Transaction(
                        id=row['id'],
                        document_id=row['document_id'],
                        user_id=row['user_id'],
                        date=row['date'],
                        description=row['description'],
                        amount=row['amount'],
                        type=TransactionType(row['type']),
                        method=TransactionMethod(row['method']) if row['method'] else None,
                        categories=categories,
                        confidence_score=row['confidence_score'],
                        created_at=row['created_at']
                    )
                    transactions.append(tx)

                return transactions

            except Exception as e:
                logger.error(f"Erro ao buscar transações do documento {document_id}: {str(e)}")
                raise

    @async_retry(max_retries=3)
    async def get_transactions_by_user(
            self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[Transaction]:
        """
        Obtém transações de um usuário.

        Args:
            user_id: ID do usuário
            limit: Número máximo de transações a retornar
            offset: Offset para paginação

        Returns:
            Lista de transações
        """
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT * FROM transactions 
                    WHERE user_id = $1 
                    ORDER BY date DESC 
                    LIMIT $2 OFFSET $3
                    """,
                    user_id, limit, offset
                )

                transactions = []
                for row in rows:
                    categories = json.loads(row['categories']) if row['categories'] else []

                    tx = Transaction(
                        id=row['id'],
                        document_id=row['document_id'],
                        user_id=row['user_id'],
                        date=row['date'],
                        description=row['description'],
                        amount=row['amount'],
                        type=TransactionType(row['type']),
                        method=TransactionMethod(row['method']) if row['method'] else None,
                        categories=categories,
                        confidence_score=row['confidence_score'],
                        created_at=row['created_at']
                    )
                    transactions.append(tx)

                return transactions

            except Exception as e:
                logger.error(f"Erro ao buscar transações do usuário {user_id}: {str(e)}")
                raise