"""
RunStep model: id, run_id, step_id, status, output, error.
"""

from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class RunStep(Base):
    """
    RunStep represents a single step execution within a run.
    - status: "pending", "running", "completed", "failed"
    - output: JSON result of the step
    - error: error message if step failed
    """
    __tablename__ = "run_steps"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("steps.id"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    output = Column(JSON, default={}, nullable=True)
    error = Column(String, nullable=True)

    # Relationship back to Run
    run = relationship("Run", back_populates="run_steps")

    def to_dict(self):
        return {
            "id": self.id,
            "run_id": self.run_id,
            "step_id": self.step_id,
            "status": self.status,
            "output": self.output,
            "error": self.error,
        }
