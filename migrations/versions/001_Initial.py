"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2023-05-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Verifica se os enums já existem antes de criá-los
    inspector = sa.inspect(connection)
    existing_enums = set()

    # Essa consulta pega todos os tipos enum já existentes no banco
    for enum in connection.execute(
        text("SELECT typname FROM pg_type JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid GROUP BY typname")
    ).fetchall():
        existing_enums.add(enum[0])

    # Criação dos enums, se não existirem
    if 'documentstatusenum' not in existing_enums:
        status_enum = postgresql.ENUM(
            'pending', 'processing', 'processed', 'failed',
            name='documentstatusenum'
        )
        status_enum.create(connection)

    if 'transactiontypeenum' not in existing_enums:
        type_enum = postgresql.ENUM(
            'credit', 'debit',
            name='transactiontypeenum'
        )
        type_enum.create(connection)

    if 'transactionmethodenum' not in existing_enums:
        method_enum = postgresql.ENUM(
            'pix', 'ted', 'doc', 'boleto', 'payment', 'transfer',
            'withdrawal', 'deposit', 'loan', 'other',
            name='transactionmethodenum'
        )
        method_enum.create(connection)

    # Verifica se as tabelas já existem
    existing_tables = inspector.get_table_names()

    # Criação da tabela de documentos se não existir
    if 'documents' not in existing_tables:
        op.create_table(
            'documents',
            sa.Column('id', sa.BigInteger(), primary_key=True),
            sa.Column('external_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', sa.BigInteger(), nullable=False),
            sa.Column('document_type', sa.String(50), nullable=False),
            sa.Column('filename', sa.String(255), nullable=False),
            sa.Column('content_type', sa.String(100), nullable=False),
            sa.Column('file_content', sa.Text(), nullable=False),
            sa.Column('categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('status', postgresql.ENUM('pending', 'processing', 'processed', 'failed', name='documentstatusenum', create_type=False),
                     nullable=False, server_default='pending'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id', name='pk_documents')
        )

        # Criação de índices para a tabela documents
        op.create_index('idx_documents_user_id', 'documents', ['user_id'])
        op.create_index('idx_documents_external_id', 'documents', ['external_id'])
        op.create_index('idx_documents_status', 'documents', ['status'])

    # Criação da tabela de transações se não existir
    if 'transactions' not in existing_tables:
        op.create_table(
            'transactions',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('document_id', sa.BigInteger(), nullable=False),
            sa.Column('user_id', sa.BigInteger(), nullable=False),
            sa.Column('date', sa.DateTime(), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('amount', sa.Numeric(15, 2), nullable=False),
            sa.Column('type', postgresql.ENUM('credit', 'debit', name='transactiontypeenum', create_type=False), nullable=False),
            sa.Column('method', postgresql.ENUM('pix', 'ted', 'doc', 'boleto', 'payment', 'transfer',
                                          'withdrawal', 'deposit', 'loan', 'other', name='transactionmethodenum', create_type=False),
                      nullable=True),
            sa.Column('categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('confidence_score', sa.Numeric(3, 2), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['document_id'], ['documents.id'], name='fk_transactions_document_id_documents', ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id', name='pk_transactions')
        )

        # Criação de índices para a tabela transactions
        op.create_index('idx_transactions_document_id', 'transactions', ['document_id'])
        op.create_index('idx_transactions_user_id', 'transactions', ['user_id'])
        op.create_index('idx_transactions_date', 'transactions', ['date'])
        op.create_index('idx_transactions_type', 'transactions', ['type'])


def downgrade():
    # Verifica se as tabelas existem antes de removê-las
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    # Remoção da tabela de transações e seus índices, se existir
    if 'transactions' in existing_tables:
        op.drop_table('transactions')

    # Remoção da tabela de documentos e seus índices, se existir
    if 'documents' in existing_tables:
        op.drop_table('documents')

    # Verifica se os enums existem antes de removê-los
    existing_enums = set()
    for enum in connection.execute(
        text("SELECT typname FROM pg_type JOIN pg_enum ON pg_enum.enumtypid = pg_type.oid GROUP BY typname")
    ).fetchall():
        existing_enums.add(enum[0])

    # Remoção dos tipos enumerados, se existirem
    if 'transactionmethodenum' in existing_enums:
        op.execute(text('DROP TYPE IF EXISTS transactionmethodenum'))

    if 'transactiontypeenum' in existing_enums:
        op.execute(text('DROP TYPE IF EXISTS transactiontypeenum'))

    if 'documentstatusenum' in existing_enums:
        op.execute(text('DROP TYPE IF EXISTS documentstatusenum'))