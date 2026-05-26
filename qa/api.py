"""
QA Gate API Endpoints

Provides REST API for content quality analysis and publish gate.
"""

from fastapi import APIRouter, HTTPException, Body, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json

from qa.scoring.engine import QAGatePipeline, QAGateFinalResult
from qa.agents.base import (
    FactualConsistencyAgent,
    ClaimValidationAgent,
    AttributionAgent,
    ReadabilityAgent,
    ToneDriftAgent,
    BannedPhrasesAgent,
    HallucinationRiskAgent,
)
from qa.agents.specialized import (
    LinkValidationAgent,
    SEOAgent,
    StyleGuideAgent,
    DuplicateIdeasAgent,
)


# Request/Response Models
class QACheckRequest(BaseModel):
    """Request to perform QA check."""
    content: str
    content_type: str = "article"  # article, newsletter, email, blog
    title: Optional[str] = None
    meta_description: Optional[str] = None
    focus_keyword: Optional[str] = None


class QACheckResponse(BaseModel):
    """QA check response."""
    publish_ready: bool
    scores: Dict[str, Any]
    issues: List[Dict[str, Any]]
    critical_issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    confidence: float
    metadata: Dict[str, Any]


# Initialize pipeline with all agents
def create_qa_pipeline() -> QAGatePipeline:
    """Create QA pipeline with all agents."""
    agents = [
        FactualConsistencyAgent(),
        ClaimValidationAgent(),
        AttributionAgent(),
        ReadabilityAgent(),
        ToneDriftAgent(),
        BannedPhrasesAgent(),
        HallucinationRiskAgent(),
        LinkValidationAgent(),
        SEOAgent(),
        StyleGuideAgent(),
        DuplicateIdeasAgent(),
    ]
    
    return QAGatePipeline(agents=agents)


# Create router
router = APIRouter(prefix="/qa", tags=["qa"])

# Initialize pipeline
qa_pipeline = create_qa_pipeline()


@router.post("/check", response_model=QACheckResponse)
def check_content_quality(request: QACheckRequest) -> QACheckResponse:
    """
    Perform complete QA check on content.
    
    Returns:
    - publish_ready: boolean indicating if ready for publication
    - scores: accuracy, clarity, trust, overall (0-100)
    - issues: detailed issues found
    - critical_issues: blocking issues
    - suggestions: top rewrite suggestions
    - confidence: confidence score (0-1.0)
    """
    
    # Prepare context
    context = {
        "title": request.title or "",
        "meta_description": request.meta_description or "",
        "focus_keyword": request.focus_keyword or "",
    }
    
    # Run QA pipeline
    result = qa_pipeline.process(
        content=request.content,
        content_type=request.content_type,
        context=context,
    )
    
    return QACheckResponse(
        publish_ready=result.publish_ready,
        scores={
            "accuracy": result.scores.accuracy_score,
            "clarity": result.scores.clarity_score,
            "trust": result.scores.trust_score,
            "overall": result.scores.overall_score,
            "publish_ready": result.scores.publish_ready,
        },
        issues=result.issues,
        critical_issues=result.critical_issues,
        suggestions=result.suggestions,
        confidence=result.scores.confidence,
        metadata=result.metadata,
    )


@router.post("/check/full")
def check_with_full_details(request: QACheckRequest) -> Dict[str, Any]:
    """
    Perform QA check with full agent-level details.
    
    Includes detailed results from each agent for advanced analysis.
    """
    
    context = {
        "title": request.title or "",
        "meta_description": request.meta_description or "",
        "focus_keyword": request.focus_keyword or "",
    }
    
    result = qa_pipeline.process(
        content=request.content,
        content_type=request.content_type,
        context=context,
    )
    
    return result.to_dict()


@router.get("/agents")
def list_qa_agents() -> List[Dict[str, str]]:
    """List all available QA agents."""
    agents_info = []
    
    for agent in qa_pipeline.agents:
        agents_info.append({
            "name": agent.name,
            "description": agent.description,
            "weight": agent.weight,
        })
    
    return agents_info


@router.post("/agents/{agent_name}/check")
def check_with_specific_agent(
    agent_name: str,
    content: str = Body(...),
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """Run a specific QA agent on content."""
    
    # Find agent
    agent = next((a for a in qa_pipeline.agents if a.name == agent_name), None)
    
    if not agent:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_name}' not found"
        )
    
    context = {"title": title or ""} if title else None
    result = agent.analyze(content, context)
    
    return result.to_dict()


@router.get("/rules")
def get_qa_rules() -> Dict[str, Any]:
    """Get current QA gate rules."""
    return qa_pipeline.rules_engine.rules


@router.post("/rules/update")
def update_qa_rules(new_rules: Dict[str, Any]) -> Dict[str, str]:
    """Update QA gate rules."""
    try:
        # Update rules
        for key, value in new_rules.items():
            if key in qa_pipeline.rules_engine.rules:
                qa_pipeline.rules_engine.rules[key] = value
        
        return {"status": "success", "message": "QA rules updated"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update rules: {str(e)}"
        )


@router.get("/scores/weights")
def get_scoring_weights() -> Dict[str, float]:
    """Get current scoring weights."""
    return {
        "accuracy": qa_pipeline.scoring_engine.weights.accuracy,
        "clarity": qa_pipeline.scoring_engine.weights.clarity,
        "trust": qa_pipeline.scoring_engine.weights.trust,
    }


@router.post("/scores/weights/update")
def update_scoring_weights(weights: Dict[str, float]) -> Dict[str, str]:
    """Update scoring weights."""
    try:
        if "accuracy" in weights:
            qa_pipeline.scoring_engine.weights.accuracy = weights["accuracy"]
        if "clarity" in weights:
            qa_pipeline.scoring_engine.weights.clarity = weights["clarity"]
        if "trust" in weights:
            qa_pipeline.scoring_engine.weights.trust = weights["trust"]
        
        return {"status": "success", "message": "Scoring weights updated"}
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update weights: {str(e)}"
        )


@router.post("/batch/check")
def batch_check_content(
    contents: List[QACheckRequest]
) -> List[Dict[str, Any]]:
    """
    Perform QA check on multiple content items.
    
    Useful for batch processing newsletters or articles.
    """
    results = []
    
    for request in contents:
        context = {
            "title": request.title or "",
            "meta_description": request.meta_description or "",
            "focus_keyword": request.focus_keyword or "",
        }
        
        result = qa_pipeline.process(
            content=request.content,
            content_type=request.content_type,
            context=context,
        )
        
        results.append({
            "content_id": hash(request.content) % 1000000,
            "publish_ready": result.publish_ready,
            "scores": {
                "accuracy": result.scores.accuracy_score,
                "clarity": result.scores.clarity_score,
                "trust": result.scores.trust_score,
                "overall": result.scores.overall_score,
            },
            "issue_count": len(result.issues),
            "critical_issue_count": len(result.critical_issues),
        })
    
    return results


@router.get("/summary")
def get_qa_system_summary() -> Dict[str, Any]:
    """Get summary of QA system capabilities."""
    return {
        "system": "AI Draft-to-Publish QA Gate",
        "agents": len(qa_pipeline.agents),
        "agent_list": [
            {"name": a.name, "weight": a.weight}
            for a in qa_pipeline.agents
        ],
        "scoring_dimensions": ["accuracy", "clarity", "trust"],
        "severity_levels": ["critical", "high", "medium", "low", "info"],
        "capabilities": [
            "Factual consistency checking",
            "Unsupported claim detection",
            "Missing attribution detection",
            "Duplicate idea detection",
            "Readability analysis",
            "Tone drift detection",
            "Banned phrase detection",
            "SEO basics checking",
            "Link validation",
            "Hallucination risk detection",
            "Style guide compliance",
        ],
    }
