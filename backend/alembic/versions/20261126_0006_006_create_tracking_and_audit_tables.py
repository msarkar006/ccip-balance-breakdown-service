"""Create tracking events, synchronization records, and audit logs

Revision ID: 006
Revises: 005
Create Date: 2026-11-26 00:06:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tracking_events table
    op.create_table(
        'tracking_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('event_data', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tracking_events_entity_type'), 'tracking_events', ['entity_type'], unique=False)
    op.create_index(op.f('ix_tracking_events_entity_id'), 'tracking_events', ['entity_id'], unique=False)
    op.create_index(op.f('ix_tracking_events_status'), 'tracking_events', ['status'], unique=False)
    op.create_index(op.f('ix_tracking_events_correlation_id'), 'tracking_events', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_tracking_events_occurred_at'), 'tracking_events', ['occurred_at'], unique=False)

    # Create synchronization_records table
    op.create_table(
        'synchronization_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=50), nullable=False),
        sa.Column('sync_source', sa.String(length=100), nullable=False),
        sa.Column('sync_status', sa.String(length=20), nullable=False),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('next_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_synchronization_records_entity_type'), 'synchronization_records', ['entity_type'], unique=False)
    op.create_index(op.f('ix_synchronization_records_entity_id'), 'synchronization_records', ['entity_id'], unique=False)
    op.create_index(op.f('ix_synchronization_records_sync_status'), 'synchronization_records', ['sync_status'], unique=False)

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=50), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_entity_id'), 'audit_logs', ['entity_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_severity'), 'audit_logs', ['severity'], unique=False)
    op.create_index(op.f('ix_audit_logs_correlation_id'), 'audit_logs', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_occurred_at'), 'audit_logs', ['occurred_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_audit_logs_occurred_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_correlation_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_severity'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_entity_id'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_synchronization_records_sync_status'), table_name='synchronization_records')
    op.drop_index(op.f('ix_synchronization_records_entity_id'), table_name='synchronization_records')
    op.drop_index(op.f('ix_synchronization_records_entity_type'), table_name='synchronization_records')
    op.drop_table('synchronization_records')
    op.drop_index(op.f('ix_tracking_events_occurred_at'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_correlation_id'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_status'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_entity_id'), table_name='tracking_events')
    op.drop_index(op.f('ix_tracking_events_entity_type'), table_name='tracking_events')
    op.drop_table('tracking_events')
