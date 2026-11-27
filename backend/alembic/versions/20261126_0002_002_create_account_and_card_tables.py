"""Create account and card tables

Revision ID: 002
Revises: 001
Create Date: 2026-11-26 00:02:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credit_card_accounts table
    op.create_table(
        'credit_card_accounts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('account_number_masked', sa.String(length=20), nullable=False),
        sa.Column('sort_code_masked', sa.String(length=10), nullable=False),
        sa.Column('account_status', sa.String(length=20), nullable=False),
        sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('available_credit', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('current_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('minimum_payment_due', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('payment_due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_card_accounts_customer_id'), 'credit_card_accounts', ['customer_id'], unique=False)
    op.create_index(op.f('ix_credit_card_accounts_account_status'), 'credit_card_accounts', ['account_status'], unique=False)

    # Create credit_cards table
    op.create_table(
        'credit_cards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('card_number_masked', sa.String(length=20), nullable=False),
        sa.Column('card_type', sa.String(length=20), nullable=False),
        sa.Column('card_status', sa.String(length=20), nullable=False),
        sa.Column('expiry_month', sa.Integer(), nullable=False),
        sa.Column('expiry_year', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_credit_cards_account_id'), 'credit_cards', ['account_id'], unique=False)
    op.create_index(op.f('ix_credit_cards_card_status'), 'credit_cards', ['card_status'], unique=False)

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('step_up_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['app_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_user_id'), 'user_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_sessions_token_hash'), 'user_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_user_sessions_expires_at'), 'user_sessions', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_sessions_expires_at'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_token_hash'), table_name='user_sessions')
    op.drop_index(op.f('ix_user_sessions_user_id'), table_name='user_sessions')
    op.drop_table('user_sessions')
    op.drop_index(op.f('ix_credit_cards_card_status'), table_name='credit_cards')
    op.drop_index(op.f('ix_credit_cards_account_id'), table_name='credit_cards')
    op.drop_table('credit_cards')
    op.drop_index(op.f('ix_credit_card_accounts_account_status'), table_name='credit_card_accounts')
    op.drop_index(op.f('ix_credit_card_accounts_customer_id'), table_name='credit_card_accounts')
    op.drop_table('credit_card_accounts')
