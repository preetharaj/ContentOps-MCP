"""
Additional QA Agents

Specialized agents for SEO, links, style guide, and duplicate detection.
"""

import re
from typing import List, Dict, Any
from qa.agents.base import BaseQAAgent, QAResult, QAIssue, SeverityLevel, RewriteSuggestion


class LinkValidationAgent(BaseQAAgent):
    """Validate links in content."""
    
    def __init__(self):
        super().__init__("link_validation", weight=0.8)
        self.description = "Validates URLs and link formatting"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for valid links."""
        issues = []
        
        # Find all links
        url_pattern = r'https?://[^\s)\]}\'"<>]+'
        links = re.findall(url_pattern, content)
        
        # Also look for markdown links
        md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        # Check for issues
        for url in links:
            if url.endswith((".exe", ".bat", ".zip")):
                issues.append(
                    self.create_issue(
                        SeverityLevel.HIGH,
                        "suspicious_link",
                        f"Suspicious file type in link: {url}",
                        suggestion="Verify the link is safe and necessary"
                    )
                )
        
        # Check markdown links
        for link_text, url in md_links:
            if len(link_text) < 2:
                issues.append(
                    self.create_issue(
                        SeverityLevel.LOW,
                        "poor_link_text",
                        f"Link text too short: '{link_text}'",
                        suggestion="Use descriptive link text (3+ words recommended)"
                    )
                )
        
        score = 100 - (len(issues) * 10)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
            metadata={
                "total_links": len(links) + len(md_links),
                "suspicious_links": len([i for i in issues if i.type == "suspicious_link"]),
            }
        )


class SEOAgent(BaseQAAgent):
    """Basic SEO checks."""
    
    def __init__(self, focus_keyword: str = None):
        super().__init__("seo", weight=0.9)
        self.description = "Performs basic SEO checks"
        self.focus_keyword = focus_keyword
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check SEO basics."""
        issues = []
        
        # Get title from context
        title = context.get("title", "") if context else ""
        
        # Check 1: Title length (50-60 chars optimal)
        if len(title) < 30:
            issues.append(
                self.create_issue(
                    SeverityLevel.MEDIUM,
                    "seo_title_too_short",
                    f"Title too short ({len(title)} chars, recommended 50-60)",
                    suggestion="Expand title with keywords"
                )
            )
        elif len(title) > 70:
            issues.append(
                self.create_issue(
                    SeverityLevel.LOW,
                    "seo_title_too_long",
                    f"Title too long ({len(title)} chars, recommended 50-60)",
                    suggestion="Shorten title to fit search results"
                )
            )
        
        # Check 2: Meta description length (150-160 chars optimal)
        meta_desc = context.get("meta_description", "") if context else ""
        if meta_desc and len(meta_desc) < 120:
            issues.append(
                self.create_issue(
                    SeverityLevel.LOW,
                    "seo_meta_short",
                    f"Meta description too short ({len(meta_desc)} chars, recommended 150-160)",
                    suggestion="Expand meta description"
                )
            )
        
        # Check 3: Headings structure
        heading_pattern = r'^#+\s'
        headings = re.findall(heading_pattern, content, re.MULTILINE)
        if len(headings) == 0:
            issues.append(
                self.create_issue(
                    SeverityLevel.MEDIUM,
                    "seo_no_headings",
                    "No heading structure detected",
                    suggestion="Add h1, h2, h3 headings for better structure"
                )
            )
        
        # Check 4: Focus keyword usage
        if self.focus_keyword:
            keyword_count = content.lower().count(self.focus_keyword.lower())
            if keyword_count == 0:
                issues.append(
                    self.create_issue(
                        SeverityLevel.MEDIUM,
                        "seo_keyword_missing",
                        f"Focus keyword '{self.focus_keyword}' not found",
                        suggestion=f"Add focus keyword '{self.focus_keyword}' naturally throughout content"
                    )
                )
        
        # Check 5: Content length
        word_count = len(content.split())
        if word_count < 300:
            issues.append(
                self.create_issue(
                    SeverityLevel.LOW,
                    "seo_content_short",
                    f"Content too short ({word_count} words, recommended 300+)",
                    suggestion="Expand content with more detail"
                )
            )
        
        score = 100 - (len(issues) * 8)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) < 2,
            issues=issues,
            metadata={
                "word_count": word_count,
                "heading_count": len(headings),
                "title_length": len(title),
            }
        )


class StyleGuideAgent(BaseQAAgent):
    """Check style guide compliance."""
    
    def __init__(self, style_rules: Dict[str, Any] = None):
        super().__init__("style_guide", weight=0.8)
        self.description = "Enforces style guide rules"
        self.style_rules = style_rules or self._default_rules()
    
    def _default_rules(self) -> Dict[str, Any]:
        """Default style guide rules."""
        return {
            "capitalize_headings": True,
            "oxford_comma": True,
            "contractions_allowed": True,
            "active_voice_preferred": True,
            "max_acronyms_per_article": 5,
            "em_dash_style": "spaced",  # spaced or unspaced
        }
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check style guide compliance."""
        issues = []
        
        # Check 1: Contractions
        if not self.style_rules.get("contractions_allowed"):
            contractions = re.findall(r"\b(?:don't|can't|won't|it's|that's)\b", content)
            if contractions:
                issues.append(
                    self.create_issue(
                        SeverityLevel.LOW,
                        "style_contractions",
                        f"Found {len(contractions)} contractions (not allowed)",
                        suggestion="Expand contractions (don't → do not)"
                    )
                )
        
        # Check 2: Oxford comma
        if self.style_rules.get("oxford_comma"):
            oxford_pattern = r'(\w+),\s(\w+)\s(?:and|or)\s(\w+)'
            matches = re.findall(oxford_pattern, content)
            if matches:
                # Check if oxford comma is used
                oxford_used = re.findall(r'(\w+),\s(\w+),\s(?:and|or)\s(\w+)', content)
                if len(matches) > len(oxford_used):
                    issues.append(
                        self.create_issue(
                            SeverityLevel.LOW,
                            "style_oxford_comma",
                            "Missing Oxford comma in list",
                            suggestion="Add comma before 'and' in lists: a, b, and c"
                        )
                    )
        
        # Check 3: Acronyms count
        acronyms = re.findall(r'\b[A-Z]{2,}\b', content)
        if len(acronyms) > self.style_rules.get("max_acronyms_per_article", 5):
            issues.append(
                self.create_issue(
                    SeverityLevel.MEDIUM,
                    "style_too_many_acronyms",
                    f"Too many acronyms ({len(acronyms)})",
                    suggestion=f"Limit acronyms to {self.style_rules.get('max_acronyms_per_article')} per article"
                )
            )
        
        # Check 4: Em dash spacing
        em_dash_style = self.style_rules.get("em_dash_style", "spaced")
        if em_dash_style == "spaced":
            unspaced = re.findall(r'\w—\w', content)  # word—word
            if unspaced:
                issues.append(
                    self.create_issue(
                        SeverityLevel.LOW,
                        "style_em_dash",
                        "Em dashes should have spaces",
                        suggestion="Use: text — text (not text—text)"
                    )
                )
        
        score = 100 - (len(issues) * 8)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) < 2,
            issues=issues,
            metadata={
                "acronyms_found": len(acronyms),
            }
        )


class DuplicateIdeasAgent(BaseQAAgent):
    """Detect duplicate or repeated ideas."""
    
    def __init__(self):
        super().__init__("duplicate_ideas", weight=0.7)
        self.description = "Detects repeated concepts and ideas"
    
    def analyze(self, content: str, context: Dict[str, Any] = None) -> QAResult:
        """Check for duplicate ideas."""
        issues = []
        
        # Split into paragraphs
        paragraphs = content.split("\n\n")
        
        # Extract key phrases from each paragraph
        key_phrases_by_para = []
        for i, para in enumerate(paragraphs):
            if para.strip():
                phrases = self._extract_key_phrases(para)
                key_phrases_by_para.append((i, phrases))
        
        # Check for overlap
        for i in range(len(key_phrases_by_para)):
            for j in range(i + 1, len(key_phrases_by_para)):
                para_i, phrases_i = key_phrases_by_para[i]
                para_j, phrases_j = key_phrases_by_para[j]
                
                overlap = set(phrases_i) & set(phrases_j)
                if len(overlap) >= 2:
                    issues.append(
                        self.create_issue(
                            SeverityLevel.MEDIUM,
                            "duplicate_idea",
                            f"Repeated concept between paragraph {para_i+1} and {para_j+1}",
                            suggestion="Merge or eliminate one instance of the repeated idea"
                        )
                    )
        
        score = 100 - (len(issues) * 15)
        return QAResult(
            agent_name=self.name,
            score=max(0, score),
            passed=len(issues) == 0,
            issues=issues,
        )
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text (simplified)."""
        # Remove common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        
        words = text.lower().split()
        phrases = []
        
        # Find 2-3 word phrases
        for i in range(len(words) - 1):
            phrase = " ".join(words[i:i+2])
            if not any(sw in phrase for sw in stop_words):
                phrases.append(phrase)
        
        return phrases
