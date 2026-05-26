"""
QA Scoring and Rules Engine

Combines results from multiple QA agents and produces final scores.
"""

from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from qa.agents.base import QAResult, SeverityLevel


@dataclass
class ScoringWeights:
    """Weights for scoring each dimension."""
    accuracy: float = 0.35
    clarity: float = 0.30
    trust: float = 0.35


@dataclass
class QAGateScores:
    """Final scores for content."""
    accuracy_score: float  # 0-100: factual accuracy
    clarity_score: float   # 0-100: readability and clarity
    trust_score: float     # 0-100: attribution and sourcing
    overall_score: float   # weighted average
    publish_ready: bool
    confidence: float      # 0-1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class QAGateFinalResult:
    """Final result from QA gate."""
    publish_ready: bool
    scores: QAGateScores
    issues: List[Dict[str, Any]] = field(default_factory=list)
    critical_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    agent_results: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "publish_ready": self.publish_ready,
            "scores": self.scores.to_dict(),
            "issues": self.issues,
            "critical_issues": self.critical_issues,
            "suggestions": self.suggestions,
            "agent_results": self.agent_results,
            "metadata": self.metadata,
            "processed_at": self.processed_at.isoformat(),
        }


class QAScoringEngine:
    """Calculates final scores from agent results."""
    
    def __init__(self, weights: ScoringWeights = None):
        self.weights = weights or ScoringWeights()
    
    def score(self, agent_results: List[QAResult]) -> QAGateScores:
        """
        Calculate final scores from agent results.
        
        Accuracy (35%): factual_consistency, claim_validation, hallucination_risk
        Clarity (30%): readability, banned_phrases, style_guide
        Trust (35%): attribution, link_validation, seo
        """
        
        # Group agents by dimension
        accuracy_agents = ["factual_consistency", "claim_validation", "hallucination_risk"]
        clarity_agents = ["readability", "banned_phrases", "style_guide"]
        trust_agents = ["attribution", "link_validation", "seo"]
        
        # Extract scores
        accuracy_score = self._calculate_dimension_score(
            agent_results, accuracy_agents, weight_boosted=True
        )
        clarity_score = self._calculate_dimension_score(
            agent_results, clarity_agents
        )
        trust_score = self._calculate_dimension_score(
            agent_results, trust_agents, weight_boosted=True
        )
        
        # Weighted average
        overall = (
            accuracy_score * self.weights.accuracy +
            clarity_score * self.weights.clarity +
            trust_score * self.weights.trust
        )
        
        # Calculate confidence (consistency of scores)
        scores = [accuracy_score, clarity_score, trust_score]
        variance = sum((s - overall) ** 2 for s in scores) / len(scores)
        confidence = 1.0 - (variance / 10000)
        confidence = max(0.0, min(1.0, confidence))
        
        return QAGateScores(
            accuracy_score=accuracy_score,
            clarity_score=clarity_score,
            trust_score=trust_score,
            overall_score=overall,
            publish_ready=overall >= 75,
            confidence=confidence,
        )
    
    def _calculate_dimension_score(
        self,
        agent_results: List[QAResult],
        agent_names: List[str],
        weight_boosted: bool = False
    ) -> float:
        """Calculate average score for agents in a dimension."""
        
        relevant_results = [
            r for r in agent_results
            if r.agent_name in agent_names
        ]
        
        if not relevant_results:
            return 75.0  # Default if no agents
        
        # Weight by agent weight
        weighted_sum = 0
        weight_sum = 0
        
        for result in relevant_results:
            # Get agent weight (stored in metadata or assume 1.0)
            agent_weight = 1.0
            weighted_sum += result.score * agent_weight
            weight_sum += agent_weight
        
        score = weighted_sum / weight_sum if weight_sum > 0 else 75.0
        
        # Boost weight for critical dimensions
        if weight_boosted:
            score = score * 0.95  # Slightly penalize
        
        return score


class QAGateRulesEngine:
    """Applies rules to determine publish readiness."""
    
    def __init__(self):
        self.rules = self._default_rules()
    
    def _default_rules(self) -> Dict[str, Any]:
        """Default QA gate rules."""
        return {
            "minimum_scores": {
                "accuracy": 70,
                "clarity": 65,
                "trust": 70,
                "overall": 75,
            },
            "critical_issue_blocks_publish": True,
            "max_high_issues": 2,
            "max_medium_issues": 5,
            "require_attribution_for_claims": True,
            "hallucination_risk_blocks": True,
        }
    
    def evaluate(self, scores: QAGateScores, agent_results: List[QAResult]) -> bool:
        """
        Determine if content is ready to publish.
        
        Returns: boolean publish_ready
        """
        
        # Check minimum scores
        if scores.accuracy_score < self.rules["minimum_scores"]["accuracy"]:
            return False
        
        if scores.clarity_score < self.rules["minimum_scores"]["clarity"]:
            return False
        
        if scores.trust_score < self.rules["minimum_scores"]["trust"]:
            return False
        
        if scores.overall_score < self.rules["minimum_scores"]["overall"]:
            return False
        
        # Check for critical issues
        critical_issues = self._get_critical_issues(agent_results)
        if critical_issues and self.rules["critical_issue_blocks_publish"]:
            return False
        
        # Count issues by severity
        high_issues = self._count_issues_by_severity(agent_results, SeverityLevel.HIGH)
        medium_issues = self._count_issues_by_severity(agent_results, SeverityLevel.MEDIUM)
        
        if high_issues > self.rules["max_high_issues"]:
            return False
        
        if medium_issues > self.rules["max_medium_issues"]:
            return False
        
        # Check for hallucination risk
        hallucination_results = [r for r in agent_results if r.agent_name == "hallucination_risk"]
        if hallucination_results:
            if not hallucination_results[0].passed and self.rules["hallucination_risk_blocks"]:
                return False
        
        return True
    
    def _get_critical_issues(self, agent_results: List[QAResult]) -> List[Dict[str, Any]]:
        """Get all critical-level issues."""
        critical = []
        for result in agent_results:
            for issue in result.issues:
                if issue.severity == SeverityLevel.CRITICAL:
                    critical.append(asdict(issue))
        return critical
    
    def _count_issues_by_severity(
        self,
        agent_results: List[QAResult],
        severity: SeverityLevel
    ) -> int:
        """Count issues of a specific severity."""
        count = 0
        for result in agent_results:
            for issue in result.issues:
                if issue.severity == severity:
                    count += 1
        return count


class QAGatePipeline:
    """Orchestrates the full QA pipeline."""
    
    def __init__(self, agents: List = None):
        self.agents = agents or []
        self.scoring_engine = QAScoringEngine()
        self.rules_engine = QAGateRulesEngine()
    
    def process(
        self,
        content: str,
        content_type: str = "article",
        context: Dict[str, Any] = None
    ) -> QAGateFinalResult:
        """
        Process content through full QA pipeline.
        
        Args:
            content: The content to evaluate
            content_type: article, newsletter, email, blog
            context: Additional context (title, meta_description, etc.)
        
        Returns:
            Complete QA gate result
        """
        
        # Run all agents
        agent_results = []
        for agent in self.agents:
            result = agent.analyze(content, context)
            agent_results.append(result)
        
        # Calculate scores
        scores = self.scoring_engine.score(agent_results)
        
        # Evaluate publish readiness
        publish_ready = self.rules_engine.evaluate(scores, agent_results)
        
        # Aggregate issues
        all_issues = []
        critical_issues = []
        all_suggestions = []
        
        for result in agent_results:
            for issue in result.issues:
                issue_dict = asdict(issue)
                all_issues.append(issue_dict)
                if issue.severity == SeverityLevel.CRITICAL:
                    critical_issues.append(issue_dict)
            
            for suggestion in result.suggestions:
                all_suggestions.append(asdict(suggestion))
        
        # Sort by severity
        all_issues.sort(key=lambda x: {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }.get(x["severity"], 5))
        
        # Sort suggestions by priority
        all_suggestions.sort(key=lambda x: x.get("priority", 999))
        
        return QAGateFinalResult(
            publish_ready=publish_ready,
            scores=scores,
            issues=all_issues,
            critical_issues=critical_issues,
            suggestions=all_suggestions[:5],  # Top 5 suggestions
            agent_results=[r.to_dict() for r in agent_results],
            metadata={
                "content_type": content_type,
                "word_count": len(content.split()),
                "agents_run": len(agent_results),
                "total_issues": len(all_issues),
                "critical_issue_count": len(critical_issues),
            },
        )
