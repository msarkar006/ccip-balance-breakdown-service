"""
Audit repository for database operations.
"""
from sqlalchemy.orm import Session

from app.audit.audit_models import AuditLog


class AuditRepository:
    """Repository for audit log operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_audit_log(self, audit_log: AuditLog) -> AuditLog:
        """
        Create a new audit log entry.
        
        Args:
            audit_log: AuditLog instance to persist
            
        Returns:
            Persisted AuditLog
        """
        self.db.add(audit_log)
        self.db.flush()
        return audit_log
