"""
QA Gate Agent Framework

Base classes and utilities for content quality agents.
Each agent focuses on a specific aspect of content quality.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Literal
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels for QA issues."""
    CRITICAL = "critical"      # Blocks publication
    HIGH = "high"              # Should be fixed
    MEDIUM = "medium"          # Recommended to fix
    LOW = "low"                # Nice to fix
    INFO = "info"              # Informational


@dataclass
class QAIssue:
    """A quality issue found by an agent."""
    agent: str
    severity: SeverityLevel
    type: str  # factual, claim, attribution, duplicate, readability, tone, seo, link, hallucination, style
    location: Optional[str] = None  # Line/section reference
    message: str = ""
    context: str = ""  # Relevant quote or code
    suggestion: str = ""  # How to fix
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RewriteSuggestion:
    """Suggestion for rewriting content."""
    section: str
    original_text: str
    suggested_text: str
    reason: str
    priority: int = 1  # 1=highest


@dataclass
class QAResult:
    """Result from a single QA agent."""
    agent_name: str
    score: float  # 0-100
    passed: bool
    issues: List[QAIssue] = field(default_factory=list)
    suggestions: List[RewriteSuggestion] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "score": self.score,
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "suggestions": [asdict(s) for s in self.suggestions],
            "metadata": self.metadata,
            "execution_time_ms": self.execution_time_ms,
        }


class BaseQAAgent(ABC):
    """Base class for all QA agents."""
    
    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self.description = ""
    
    @abstractmethod
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Analyze content and return QA result."""
        pass
    
    def create_issue(
        self,
        severity: SeverityLevel,
        issue_type: str,
        message: str,
        context: str = "",
        suggestion: str = "",
        location: str = None,
    ) -> QAIssue:
        """Helper to create an issue."""
        return QAIssue(
            agent=self.name,
            severity=severity,
            type=issue_type,
            message=message,
            context=context,
            suggestion=suggestion,
            location=location,
        )


class FactualConsistencyAgent(BaseQAAgent):
    """Check for factual consistency throughout content."""
    
    def __init__(self):
        super().__init__("factual_consistency", weight=1.2)
        self.description = "Detects contradictions and inconsistent facts"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for factual contradictions."""
        issues = []
        suggestions = []
        
        # Track claims made
        claims = self._extract_claims(content)
        
        # Check for contradictions
        for i, claim1 in enumerate(claims):
            for claim2 in claims[i + 1:]:
                if self._is_contradictory(claim1, claim2):
                    issues.append(
                        self.create_issue(
                            SeverityLevel.CRITICAL,
                            "factual_contradiction",
                            f"Contradictory statements found",
                            context=f"'{claim1['text']}' vs '{claim2['text']}'",
                            suggestion="Review and reconcile the contradictory statements"
                        )
                    )
        
        score = 100 - (len(issues) * 15)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
        )
    
    def _extract_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract factual claims from content."""
        # Simple claim extraction (in production, use NLP)
        claims = []
        sentences = content.split(".")
        for i, sent in enumerate(sentences):
            if any(keyword in sent.lower() for keyword in ["is", "are", "was", "were", "found", "showed"]):
                claims.append({"text": sent.strip(), "index": i})
        return claims
    
    def _is_contradictory(self, claim1: Dict, claim2: Dict) -> bool:
        """Check if two claims contradict."""
        # Simplified contradiction detection
        contradictions = [
            ("always", "never"),
            ("all", "none"),
            ("increase", "decrease"),
        ]
        
        text1 = claim1["text"].lower()
        text2 = claim2["text"].lower()
        
        for word1, word2 in contradictions:
            if word1 in text1 and word2 in text2:
                return True
        
        return False


class ClaimValidationAgent(BaseQAAgent):
    """Check for unsupported claims."""
    
    def __init__(self):
        super().__init__("claim_validation", weight=1.1)
        self.description = "Identifies claims that lack supporting evidence"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for unsupported claims."""
        issues = []
        suggestions = []
        
        # Find bold claims without support
        bold_claims = self._find_bold_claims(content)
        
        for claim in bold_claims:
            if not self._has_support(content, claim):
                issues.append(
                    self.create_issue(
                        SeverityLevel.HIGH,
                        "unsupported_claim",
                        f"Claim lacks supporting evidence: '{claim}'",
                        suggestion="Add data, research, or citations to support this claim"
                    )
                )
                suggestions.append(
                    RewriteSuggestion(
                        section=claim,
                        original_text=claim,
                        suggested_text=f"{claim} (needs citation/data)",
                        reason="Bold claims should have supporting evidence"
                    )
                )
        
        score = 100 - (len(issues) * 20)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
        )
    
    def _find_bold_claims(self, content: str) -> List[str]:
        """Find potentially bold/unsupported claims."""
        keywords = [
            "proven", "best", "always", "never", "guaranteed",
            "revolutionary", "unique", "only", "certainly"
        ]
        
        claims = []
        sentences = content.split(".")
        for sent in sentences:
            if any(kw in sent.lower() for kw in keywords):
                claims.append(sent.strip())
        
        return claims
    
    def _has_support(self, content: str, claim: str) -> bool:
        """Check if claim has supporting evidence nearby."""
        # Look for citations, data, research references
        support_indicators = ["according to", "research", "study", "data", "found", "showed", "cite", "source"]
        
        # Simple check: look nearby in content
        index = content.find(claim)
        if index == -1:
            return False
        
        # Check nearby text (200 chars before/after)
        nearby = content[max(0, index-200):min(len(content), index+len(claim)+200)]
        
        return any(indicator in nearby.lower() for indicator in support_indicators)


class AttributionAgent(BaseQAAgent):
    """Check for proper attribution and citations."""
    
    def __init__(self):
        super().__init__("attribution", weight=1.1)
        self.description = "Ensures proper citation and attribution"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for missing attributions."""
        issues = []
        
        # Check for quoted material
        quoted_text = self._find_quoted_text(content)
        
        for quote in quoted_text:
            if not self._has_attribution(content, quote):
                issues.append(
                    self.create_issue(
                        SeverityLevel.HIGH,
                        "missing_attribution",
                        f"Quote lacks attribution: '{quote['text']}'",
                        suggestion="Add proper attribution with source and author"
                    )
                )
        
        score = 100 - (len(issues) * 25)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
        )
    
    def _find_quoted_text(self, content: str) -> List[Dict[str, Any]]:
        """Find quoted text in content."""
        quotes = []
        # Look for text in quotes
        import re
        pattern = r'"([^"]+)"'
        for match in re.finditer(pattern, content):
            quotes.append({"text": match.group(1), "position": match.start()})
        return quotes
    
    def _has_attribution(self, content: str, quote: Dict) -> bool:
        """Check if quote has nearby attribution."""
        index = quote["position"]
        # Check nearby text for attribution keywords
        nearby = content[max(0, index-150):min(len(content), index+len(quote["text"])+150)]
        
        attribution_keywords = ["says", "according to", "wrote", "stated", "source:", "from", "via"]
        return any(kw in nearby.lower() for kw in attribution_keywords)


class ReadabilityAgent(BaseQAAgent):
    """Check content readability metrics."""
    
    def __init__(self):
        super().__init__("readability", weight=0.9)
        self.description = "Assesses readability and clarity"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check readability metrics."""
        issues = []
        
        # Calculate readability metrics
        avg_sentence_length = self._avg_sentence_length(content)
        avg_word_length = self._avg_word_length(content)
        
        if avg_sentence_length > 25:
            issues.append(
                self.create_issue(
                    SeverityLevel.MEDIUM,
                    "readability_sentence_length",
                    f"Average sentence length is {avg_sentence_length} words (recommended: < 20)",
                    suggestion="Break up long sentences for better readability"
                )
            )
        
        if avg_word_length > 5:
            issues.append(
                self.create_issue(
                    SeverityLevel.LOW,
                    "readability_word_length",
                    f"Average word length is {avg_word_length} characters",
                    suggestion="Use simpler, shorter words where possible"
                )
            )
        
        score = 100 - (len(issues) * 10)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) < 2,
            issues=issues,
            metadata={
                "avg_sentence_length": avg_sentence_length,
                "avg_word_length": avg_word_length,
            }
        )
    
    def _avg_sentence_length(self, content: str) -> float:
        """Calculate average sentence length."""
        sentences = content.split(".")
        words_per_sentence = [len(s.split()) for s in sentences if s.strip()]
        return sum(words_per_sentence) / len(words_per_sentence) if words_per_sentence else 0
    
    def _avg_word_length(self, content: str) -> float:
        """Calculate average word length."""
        words = content.split()
        if not words:
            return 0
        return sum(len(w) for w in words) / len(words)


class ToneDriftAgent(BaseQAAgent):
    """Check for tone consistency."""
    
    def __init__(self):
        super().__init__("tone_drift", weight=0.8)
        self.description = "Detects inconsistent tone"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for tone drift."""
        issues = []
        
        # Simple tone analysis - look for shifts in formality
        formal_words = ["moreover", "nevertheless", "therefore", "consequently"]
        casual_words = ["like", "really", "super", "pretty", "basically"]
        
        has_formal = any(word in content.lower() for word in formal_words)
        has_casual = any(word in content.lower() for word in casual_words)
        
        if has_formal and has_casual:
            issues.append(
                self.create_issue(
                    SeverityLevel.MEDIUM,
                    "tone_inconsistency",
                    "Content mixes formal and casual language",
                    suggestion="Maintain consistent tone throughout (formal or casual)"
                )
            )
        
        score = 100 - (len(issues) * 15)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
        )


class BannedPhrasesAgent(BaseQAAgent):
    """Check for banned or problematic phrases."""
    
    def __init__(self, banned_phrases: List[str] = None):
        super().__init__("banned_phrases", weight=0.9)
        self.description = "Detects banned or problematic phrases"
        self.banned_phrases = banned_phrases or [
            "obviously",
            "as everyone knows",
            "clearly",
            "it goes without saying",
        ]
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for banned phrases."""
        issues = []
        
        for phrase in self.banned_phrases:
            if phrase.lower() in content.lower():
                issues.append(
                    self.create_issue(
                        SeverityLevel.MEDIUM,
                        "banned_phrase",
                        f"Contains banned phrase: '{phrase}'",
                        suggestion=f"Remove or rephrase '{phrase}'"
                    )
                )
        
        score = 100 - (len(issues) * 10)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
        )


class HallucinationRiskAgent(BaseQAAgent):
    """Check for potential hallucinations or made-up content."""
    
    def __init__(self):
        super().__init__("hallucination_risk", weight=1.2)
        self.description = "Detects potential hallucinations or fabricated content"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for hallucination risk."""
        issues = []
        
        # Look for red flags
        red_flags = [
            ("specific numbers without source", r"\d{1,}%"),
            ("made-up names/companies", r"[A-Z][a-z]+ (?:Corp|Inc|Ltd)"),
            ("specific dates without reference", r"(?:January|February|March|April|May|June|July|August|September|October|November|December) \d{1,2}, \d{4}"),
        ]
        
        import re
        for flag_name, pattern in red_flags:
            matches = re.findall(pattern, content)
            if matches and not any(indicator in content for indicator in ["according to", "study", "research"]):
                issues.append(
                    self.create_issue(
                        SeverityLevel.CRITICAL,
                        "hallucination_risk",
                        f"Potential hallucination: {flag_name} ({', '.join(matches[:3])})",
                        suggestion="Verify all facts and provide sources for specific claims"
                    )
                )
        
        score = 100 - (len(issues) * 25)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
        )
