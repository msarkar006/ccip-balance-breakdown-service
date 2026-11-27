"""
Audit service for audit event capture.
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.audit.audit_models import AuditLog
from app.audit.audit_repository import AuditRepository


class AuditService:
    """
    Audit service for capturing security and compliance events.
    
    Retention classes:
    - financial_7y: Financial audit events (7 years retention)
    - access_2y: Access control events (2 years retention)
    - tracking_24m: Tracking events (24 months retention)
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditRepository(db)

    def record(
        self,
        user_id: int,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        severity: str = "info",
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        retention_class: str = "tracking_24m"
    ) -> AuditLog:
        """
        Record an audit event.
        
        Args:
            user_id: User ID performing the action
            action: Action type (login, logout, step_up, payment, transfer, mandate_change, etc.)
            entity_type: Entity type (user, payment, transfer, mandate, etc.)
            entity_id: Optional entity ID
            severity: Severity level (info, warning, error)
            correlation_id: Optional correlation ID for request tracing
            details: Optional additional details as JSON
            ip_address: Optional IP address
            retention_class: Retention class (financial_7y, access_2y, tracking_24m)
            
        Returns:
            Created AuditLog
        """
        # Convert retention_class to details if needed for filtering
        if details is None:
            details = {}
        details["retention_class"] = retention_class

        # Serialize details to JSON string
        details_json = json.dumps(details)

        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            severity=severity,
            correlation_id=correlation_id,
            details=details_json,
            ip_address=ip_address,
            occurred_at=datetime.now(timezone.utc)
        )

        return self.repository.create_audit_log(audit_log)
