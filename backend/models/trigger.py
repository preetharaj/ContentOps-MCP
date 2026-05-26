"""
Trigger model: app, event, config.
"""

from sqlalchemy import Column, String, JSON, Integer
from backend.database import Base

class Trigger(Base):
    """
    Trigger represents the event that starts a workflow.
    - app: "notion", "slack", etc.
    - event: "page_created", etc.
    - config: JSON metadata (e.g., {"database_id": "..."})
    """
    __tablename__ = "triggers"

    id = Column(Integer, primary_key=True, index=True)
    app = Column(String, nullable=False)
    event = Column(String, nullable=False)
    config = Column(JSON, default={}, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "app": self.app,
            "event": self.event,
            "config": self.config,
        }
