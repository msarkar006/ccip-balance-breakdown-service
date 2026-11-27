"""add balance category fields

Revision ID: 20261126_1400
Revises: ac8abdc5e7f1
Create Date: 2026-11-26 14:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '20261126_1400'
down_revision = 'ac8abdc5e7f1'
branch_labels = None
depends_on = None


def upgrade():
    """Add display_rank, promo_rate, promo_end_date, source_balance_transfer_id, source_instalment_plan_id to balance_categories."""
    with op.batch_alter_table('balance_categories', schema=None) as batch_op:
        batch_op.add_column(sa.Column('display_rank', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('promo_rate', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('promo_end_date', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('source_balance_transfer_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('source_instalment_plan_id', sa.Integer(), nullable=True))

        batch_op.create_index(
            batch_op.f('ix_balance_categories_source_balance_transfer_id'),
            ['source_balance_transfer_id'],
            unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_balance_categories_source_instalment_plan_id'),
            ['source_instalment_plan_id'],
            unique=False
        )
        batch_op.create_foreign_key(
            'fk_balance_categories_source_balance_transfer_id',
            'balance_transfers',
            ['source_balance_transfer_id'],
            ['id']
        )
        batch_op.create_foreign_key(
            'fk_balance_categories_source_instalment_plan_id',
            'instalment_plans',
            ['source_instalment_plan_id'],
            ['id']
        )


def downgrade():
    """Remove added fields from balance_categories."""
    with op.batch_alter_table('balance_categories', schema=None) as batch_op:
        batch_op.drop_constraint('fk_balance_categories_source_instalment_plan_id', type_='foreignkey')
        batch_op.drop_constraint('fk_balance_categories_source_balance_transfer_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_balance_categories_source_instalment_plan_id'))
        batch_op.drop_index(batch_op.f('ix_balance_categories_source_balance_transfer_id'))
        batch_op.drop_column('source_instalment_plan_id')
        batch_op.drop_column('source_balance_transfer_id')
        batch_op.drop_column('promo_end_date')
        batch_op.drop_column('promo_rate')
        batch_op.drop_column('display_rank')
