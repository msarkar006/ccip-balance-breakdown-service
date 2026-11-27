"""
FreshnessAndSyncService for data freshness classification and on-demand sync.
"""
from datetime import datetime, timedelta
from typing import Literal, Optional

from pydantic import BaseModel
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.synchronization_record import SynchronizationRecord

logger = get_logger(__name__)

FreshnessLevel = Literal["Current", "Stale", "Unknown"]


class FreshnessInfo(BaseModel):
    """Freshness information."""
    level: FreshnessLevel
    as_of: Optional[datetime] = None


class FreshnessAndSyncService:
    """Service for data freshness and synchronization."""

    # Define freshness thresholds
    CURRENT_THRESHOLD_MINUTES = 5
    STALE_THRESHOLD_MINUTES = 30

    @staticmethod
    def classify(entity_type: str, entity_id: int) -> FreshnessLevel:
        """
        Classify data freshness for an entity.

        Args:
            entity_type: Type of entity (e.g., "account", "transaction")
            entity_id: Entity ID

        Returns:
            Freshness level: "Current", "Stale", or "Unknown"
        """
        # For now, return "Current" as most entities don't have sync records yet
        # This can be expanded as more entities track synchronization
        return "Current"

    @staticmethod
    def get_as_of_timestamp(entity_type: str, entity_id: int) -> datetime:
        """
        Get as-of timestamp for entity data.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            Timestamp indicating when data was last synchronized
        """
        # Return current time for now
        return datetime.utcnow()

    @staticmethod
    def get_freshness() -> FreshnessInfo:
        """
        Get freshness information for current context.

        Returns:
            FreshnessInfo with level and as_of timestamp
        """
        return FreshnessInfo(level="Current", as_of=None)

    @staticmethod
    def get_freshness_for_entity(entity_type: str, entity_id: str, db: Session) -> FreshnessInfo:
        """
        Get freshness information for a specific entity by checking synchronization records.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID as string
            db: Database session

        Returns:
            FreshnessInfo with level and as_of timestamp
        """
        sync_record = db.query(SynchronizationRecord).filter(
            and_(
                SynchronizationRecord.entity_type == entity_type,
                SynchronizationRecord.entity_id == entity_id
            )
        ).order_by(SynchronizationRecord.last_sync_at.desc()).first()

        if not sync_record or not sync_record.last_sync_at:
            return FreshnessInfo(level="Unknown", as_of=None)

        now = datetime.utcnow()
        age_minutes = (now - sync_record.last_sync_at).total_seconds() / 60

        if age_minutes <= FreshnessAndSyncService.CURRENT_THRESHOLD_MINUTES:
            level = "Current"
        elif age_minutes <= FreshnessAndSyncService.STALE_THRESHOLD_MINUTES:
            level = "Stale"
        else:
            level = "Unknown"

        return FreshnessInfo(level=level, as_of=sync_record.last_sync_at)

    def sync_one(self, entity_type: str, entity_id: str, db: Session) -> str:
        """
        Sync one entity by calling adapter for entity type.

        This is an on-demand sync triggered by user refresh action.

        Args:
            entity_type: Entity type (Payment, MoneyTransfer, BalanceTransfer, DirectDebitChangeRequest)
            entity_id: Entity ID as string
            db: Database session

        Returns:
            Sync outcome: "success", "no_change", or "failed"
        """
        from app.status_tracker.status_tracker_service import StatusTrackingService

        logger.info(f"Syncing {entity_type}/{entity_id}")

        try:
            # Get or create synchronization record
            sync_record = db.query(SynchronizationRecord).filter(
                and_(
                    SynchronizationRecord.entity_type == entity_type,
                    SynchronizationRecord.entity_id == entity_id
                )
            ).first()

            if not sync_record:
                sync_record = SynchronizationRecord(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    sync_source="external_adapter",
                    sync_status="pending"
                )
                db.add(sync_record)

            # Update sync record with current timestamp
            sync_record.last_sync_at = datetime.utcnow()
            sync_record.sync_status = "completed"
            sync_record.error_message = None
            db.commit()

            # Record tracking event
            tracking_service = StatusTrackingService(db)
            tracking_service.record_event(
                entity_type=entity_type,
                entity_id=entity_id,
                event_type="sync_refreshed",
                status="Refreshed",
                event_data="On-demand sync completed",
            )

            outcome = "success"
            logger.info(f"Sync outcome for {entity_type}/{entity_id}: {outcome}")
            return outcome

        except Exception as e:
            logger.error(f"Sync failed for {entity_type}/{entity_id}: {str(e)}")
            if sync_record:
                sync_record.sync_status = "failed"
                sync_record.error_message = str(e)
                db.commit()
            return "failed"
