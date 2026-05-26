"""
Run model: id, workflow_id, status, started_at, ended_at.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class Run(Base):
    """
    Run represents a single execution of a workflow.
    - status: "running", "completed", "failed"
    - started_at: timestamp when run started
    - ended_at: timestamp when run ended
    """
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String, default="running", nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)

    # Relationship to RunStep objects
    run_steps = relationship("RunStep", back_populates="run", cascade="all, delete-orphan")

    def to_dict(self, include_steps=True):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "run_steps": [rs.to_dict() for rs in self.run_steps] if include_steps else [],
        }
