"""Create balance breakdown, rewards, offers, and instalment tables

Revision ID: 005
Revises: 004
Create Date: 2026-11-26 00:05:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create balance_breakdowns table
    op.create_table(
        'balance_breakdowns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('total_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_balance_breakdowns_account_id'), 'balance_breakdowns', ['account_id'], unique=False)
    op.create_index(op.f('ix_balance_breakdowns_snapshot_date'), 'balance_breakdowns', ['snapshot_date'], unique=False)

    # Create balance_categories table
    op.create_table(
        'balance_categories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('breakdown_id', sa.Integer(), nullable=False),
        sa.Column('category_name', sa.String(length=100), nullable=False),
        sa.Column('category_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('apr', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['breakdown_id'], ['balance_breakdowns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_balance_categories_breakdown_id'), 'balance_categories', ['breakdown_id'], unique=False)

    # Create rewards_programmes table
    op.create_table(
        'rewards_programmes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('programme_name', sa.String(length=100), nullable=False),
        sa.Column('points_balance', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rewards_programmes_account_id'), 'rewards_programmes', ['account_id'], unique=False)
    op.create_index(op.f('ix_rewards_programmes_status'), 'rewards_programmes', ['status'], unique=False)

    # Create offers table
    op.create_table(
        'offers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('offer_code', sa.String(length=50), nullable=False),
        sa.Column('offer_title', sa.String(length=255), nullable=False),
        sa.Column('offer_description', sa.Text(), nullable=True),
        sa.Column('offer_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_offers_account_id'), 'offers', ['account_id'], unique=False)
    op.create_index(op.f('ix_offers_offer_code'), 'offers', ['offer_code'], unique=True)
    op.create_index(op.f('ix_offers_status'), 'offers', ['status'], unique=False)

    # Create instalment_plans table
    op.create_table(
        'instalment_plans',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('plan_reference', sa.String(length=50), nullable=False),
        sa.Column('original_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('remaining_balance', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('instalment_count', sa.Integer(), nullable=False),
        sa.Column('monthly_payment', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('apr', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['account_id'], ['credit_card_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_instalment_plans_account_id'), 'instalment_plans', ['account_id'], unique=False)
    op.create_index(op.f('ix_instalment_plans_plan_reference'), 'instalment_plans', ['plan_reference'], unique=True)
    op.create_index(op.f('ix_instalment_plans_status'), 'instalment_plans', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_instalment_plans_status'), table_name='instalment_plans')
    op.drop_index(op.f('ix_instalment_plans_plan_reference'), table_name='instalment_plans')
    op.drop_index(op.f('ix_instalment_plans_account_id'), table_name='instalment_plans')
    op.drop_table('instalment_plans')
    op.drop_index(op.f('ix_offers_status'), table_name='offers')
    op.drop_index(op.f('ix_offers_offer_code'), table_name='offers')
    op.drop_index(op.f('ix_offers_account_id'), table_name='offers')
    op.drop_table('offers')
    op.drop_index(op.f('ix_rewards_programmes_status'), table_name='rewards_programmes')
    op.drop_index(op.f('ix_rewards_programmes_account_id'), table_name='rewards_programmes')
    op.drop_table('rewards_programmes')
    op.drop_index(op.f('ix_balance_categories_breakdown_id'), table_name='balance_categories')
    op.drop_table('balance_categories')
    op.drop_index(op.f('ix_balance_breakdowns_snapshot_date'), table_name='balance_breakdowns')
    op.drop_index(op.f('ix_balance_breakdowns_account_id'), table_name='balance_breakdowns')
    op.drop_table('balance_breakdowns')
