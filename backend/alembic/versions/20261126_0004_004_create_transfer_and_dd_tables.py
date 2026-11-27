"""Create balance transfer, money transfer, payee, and direct debit tables

Revision ID: 004
Revises: 003
Create Date: 2026-11-26 00:04:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create balance_transfers table
    op.create_table(
        'balance_transfers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('external_transfer_id', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=True),
        sa.Column('transfer_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('promotional_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('promotional_period_months', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_balance_transfers_account_id'), 'balance_transfers', ['account_id'], unique=False)
    op.create_index(op.f('ix_balance_transfers_external_transfer_id'), 'balance_transfers', ['external_transfer_id'], unique=True)
    op.create_index(op.f('ix_balance_transfers_idempotency_key'), 'balance_transfers', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_balance_transfers_status'), 'balance_transfers', ['status'], unique=False)

    # Create payees table
    op.create_table(
        'payees',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('payee_name', sa.String(length=255), nullable=False),
        sa.Column('account_number_masked', sa.String(length=20), nullable=False),
        sa.Column('sort_code_masked', sa.String(length=10), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payees_account_id'), 'payees', ['account_id'], unique=False)

    # Create money_transfers table
    op.create_table(
        'money_transfers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('payee_id', sa.Integer(), nullable=False),
        sa.Column('external_transfer_id', sa.String(length=50), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.ForeignKeyConstraint(['payee_id'], ['payees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_money_transfers_account_id'), 'money_transfers', ['account_id'], unique=False)
    op.create_index(op.f('ix_money_transfers_payee_id'), 'money_transfers', ['payee_id'], unique=False)
    op.create_index(op.f('ix_money_transfers_external_transfer_id'), 'money_transfers', ['external_transfer_id'], unique=True)
    op.create_index(op.f('ix_money_transfers_idempotency_key'), 'money_transfers', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_money_transfers_status'), 'money_transfers', ['status'], unique=False)

    # Create direct_debit_mandates table
    op.create_table(
        'direct_debit_mandates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('mandate_reference', sa.String(length=50), nullable=False),
        sa.Column('mandate_type', sa.String(length=50), nullable=False),
        sa.Column('payment_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_direct_debit_mandates_account_id'), 'direct_debit_mandates', ['account_id'], unique=False)
    op.create_index(op.f('ix_direct_debit_mandates_mandate_reference'), 'direct_debit_mandates', ['mandate_reference'], unique=True)
    op.create_index(op.f('ix_direct_debit_mandates_status'), 'direct_debit_mandates', ['status'], unique=False)

    # Create direct_debit_change_requests table
    op.create_table(
        'direct_debit_change_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('mandate_id', sa.Integer(), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('new_payment_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['mandate_id'], ['direct_debit_mandates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_direct_debit_change_requests_mandate_id'), 'direct_debit_change_requests', ['mandate_id'], unique=False)
    op.create_index(op.f('ix_direct_debit_change_requests_idempotency_key'), 'direct_debit_change_requests', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_direct_debit_change_requests_status'), 'direct_debit_change_requests', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_direct_debit_change_requests_status'), table_name='direct_debit_change_requests')
    op.drop_index(op.f('ix_direct_debit_change_requests_idempotency_key'), table_name='direct_debit_change_requests')
    op.drop_index(op.f('ix_direct_debit_change_requests_mandate_id'), table_name='direct_debit_change_requests')
    op.drop_table('direct_debit_change_requests')
    op.drop_index(op.f('ix_direct_debit_mandates_status'), table_name='direct_debit_mandates')
    op.drop_index(op.f('ix_direct_debit_mandates_mandate_reference'), table_name='direct_debit_mandates')
    op.drop_index(op.f('ix_direct_debit_mandates_account_id'), table_name='direct_debit_mandates')
    op.drop_table('direct_debit_mandates')
    op.drop_index(op.f('ix_money_transfers_status'), table_name='money_transfers')
    op.drop_index(op.f('ix_money_transfers_idempotency_key'), table_name='money_transfers')
    op.drop_index(op.f('ix_money_transfers_external_transfer_id'), table_name='money_transfers')
    op.drop_index(op.f('ix_money_transfers_payee_id'), table_name='money_transfers')
    op.drop_index(op.f('ix_money_transfers_account_id'), table_name='money_transfers')
    op.drop_table('money_transfers')
    op.drop_index(op.f('ix_payees_account_id'), table_name='payees')
    op.drop_table('payees')
    op.drop_index(op.f('ix_balance_transfers_status'), table_name='balance_transfers')
    op.drop_index(op.f('ix_balance_transfers_idempotency_key'), table_name='balance_transfers')
    op.drop_index(op.f('ix_balance_transfers_external_transfer_id'), table_name='balance_transfers')
    op.drop_index(op.f('ix_balance_transfers_account_id'), table_name='balance_transfers')
    op.drop_table('balance_transfers')
