"""
Workflow model: id, name, is_enabled, trigger, steps.
"""

from sqlalchemy import Column, String, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Workflow(Base):
    """
    Workflow represents an orchestration logic.
    - name: human-readable name
    - is_enabled: whether the workflow is active
    - trigger: JSON object with trigger config
    - steps: list of Step objects
    """
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    trigger = Column(JSON, nullable=False)
    
    # Relationship to Step objects
    steps = relationship("Step", back_populates="workflow", cascade="all, delete-orphan")

    def to_dict(self, include_steps=True):
        return {
            "id": self.id,
            "name": self.name,
            "is_enabled": self.is_enabled,
            "trigger": self.trigger,
            "steps": [step.to_dict() for step in self.steps] if include_steps else [],
        }
