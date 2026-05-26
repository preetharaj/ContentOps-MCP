"""
Step model: id, workflow_id, app, action, parameters.
"""

from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class Step(Base):
    """
    Step represents a single action in a workflow.
    - app: "blog", "slack", "email", etc.
    - action: e.g., "create_draft", "notify_team"
    - parameters: JSON config for this step
    """
    __tablename__ = "steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    app = Column(String, nullable=False)
    action = Column(String, nullable=False)
    parameters = Column(JSON, default={}, nullable=False)

    # Relationship back to Workflow
    workflow = relationship("Workflow", back_populates="steps")

    def to_dict(self):
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "app": self.app,
            "action": self.action,
            "parameters": self.parameters,
        }
