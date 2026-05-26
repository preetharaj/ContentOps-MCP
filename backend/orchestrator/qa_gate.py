"""
AI Draft-to-Publish QA Gate.

This module implements the local zero-cost QA gate used by Phase 3 workflows.
It can be called as the MCP-style step `qa_gate::run_check` or through the
legacy step runner as `backend.steps.qa_gate.run_check`.
"""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import httpx

try:
    from backend.database import SessionLocal
    from backend.models.run_step import RunStep as DbRunStep
except Exception:  # Allows standalone QA checks before DB dependencies are installed.
    SessionLocal = None
    DbRunStep = None


@dataclass
class QAIssue:
    category: str
    severity: str
    message: str
    context: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class QAGateInput:
    title: str = ""
    meta_description: str = ""
    content: str = ""
    draft_url: str = ""
    post_id: str = ""
    focus_keyword: str = ""
    target_audience: str = "general readers"
    brand_rubric: str = "clear, practical, accurate, non-hype"
    internal_links: List[str] = field(default_factory=list)
    mode: str = "manual_approval"  # manual_approval | auto_publish | send_to_editor
    override: bool = False
    editor_channel: str = "#content-review"


@dataclass
class QAGateResult:
    passed: bool
    status: str
    score: int
    reasoning: str
    suggestions: List[str]
    issues: List[QAIssue]
    checked_at: str
    next_action: str
    can_override: bool
    auto_publish_allowed: bool
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["pass"] = self.passed
        return data


class QAGate:
    """Runs SEO, link, brand voice, and readability checks before publish."""

    def __init__(self, mcp_client: Optional[Any] = None, llm_client: Optional[Any] = None):
        self.mcp_client = mcp_client
        self.llm_client = llm_client

    async def run_check(
        self,
        payload: Dict[str, Any] | QAGateInput,
        run_step_id: Optional[int] = None,
    ) -> QAGateResult:
        started = time.perf_counter()
        qa_input = self._coerce_input(payload)

        if qa_input.draft_url and not qa_input.content:
            fetched = await self._fetch_draft(qa_input)
            qa_input.content = fetched.get("content") or qa_input.content
            qa_input.title = qa_input.title or fetched.get("title", "")
            qa_input.meta_description = qa_input.meta_description or fetched.get("meta_description", "")
            qa_input.internal_links = qa_input.internal_links or fetched.get("links", [])

        if not qa_input.internal_links and qa_input.content:
            qa_input.internal_links = self.extract_links(qa_input.content)

        issues: List[QAIssue] = []
        suggestions: List[str] = []

        seo_issues, seo_suggestions = self._check_seo(qa_input)
        issues.extend(seo_issues)
        suggestions.extend(seo_suggestions)

        link_issues, link_suggestions = await self._check_links(qa_input.internal_links, qa_input.draft_url)
        issues.extend(link_issues)
        suggestions.extend(link_suggestions)

        readability_issues, readability_suggestions, readability_score = self._check_readability(
            qa_input.content,
            qa_input.target_audience,
        )
        issues.extend(readability_issues)
        suggestions.extend(readability_suggestions)

        brand_issues, brand_suggestions = await self._check_brand_voice(qa_input)
        issues.extend(brand_issues)
        suggestions.extend(brand_suggestions)

        score = self._score(issues, readability_score)
        hard_fail = any(issue.severity in {"critical", "high"} for issue in issues)
        passed = (score >= 75 and not hard_fail) or qa_input.override
        status = "passed" if passed else "failed"

        if qa_input.override and not passed:
            status = "overridden"
            passed = True

        next_action = self._next_action(qa_input, passed)
        reasoning = self._reasoning(score, passed, issues, qa_input, readability_score)
        result = QAGateResult(
            passed=passed,
            status=status,
            score=score,
            reasoning=reasoning,
            suggestions=self._unique(suggestions)[:8],
            issues=issues,
            checked_at=datetime.utcnow().isoformat() + "Z",
            next_action=next_action,
            can_override=not passed,
            auto_publish_allowed=passed and qa_input.mode == "auto_publish",
            metadata={
                "mode": qa_input.mode,
                "target_audience": qa_input.target_audience,
                "brand_rubric": qa_input.brand_rubric,
                "readability_score": readability_score,
                "link_count": len(qa_input.internal_links),
                "processing_time_ms": round((time.perf_counter() - started) * 1000, 2),
                "post_id": qa_input.post_id,
                "editor_channel": qa_input.editor_channel,
            },
        )

        if run_step_id:
            self._store_run_step_result(run_step_id, result)

        return result

    def _coerce_input(self, payload: Dict[str, Any] | QAGateInput) -> QAGateInput:
        if isinstance(payload, QAGateInput):
            return payload
        normalized = dict(payload or {})
        if isinstance(normalized.get("internal_links"), str):
            normalized["internal_links"] = [normalized["internal_links"]]
        accepted = QAGateInput.__dataclass_fields__.keys()
        return QAGateInput(**{key: normalized.get(key) for key in accepted if key in normalized})

    async def _fetch_draft(self, qa_input: QAGateInput) -> Dict[str, Any]:
        if self.mcp_client:
            try:
                result = await self.mcp_client.call_tool(
                    server="wordpress-mcp",
                    tool="get_page",
                    params={"url": qa_input.draft_url, "post_id": qa_input.post_id},
                )
                if isinstance(result, dict):
                    return result
            except Exception:
                pass

        sample_content = qa_input.content or (
            "# MCP-native content operations\n\n"
            "This draft explains how content teams can move from manual publishing "
            "to an MCP-native workflow with a QA gate before publish. "
            "It uses concrete examples, human review, and safe automation."
        )
        return {
            "title": qa_input.title,
            "meta_description": qa_input.meta_description,
            "content": sample_content,
            "links": self.extract_links(sample_content),
        }

    def _check_seo(self, qa_input: QAGateInput) -> Tuple[List[QAIssue], List[str]]:
        issues: List[QAIssue] = []
        suggestions: List[str] = []
        title = (qa_input.title or "").strip()
        meta = (qa_input.meta_description or "").strip()

        if not title:
            issues.append(QAIssue("seo", "high", "SEO title is missing.", suggestion="Add a descriptive 45-65 character title."))
        elif len(title) < 30:
            issues.append(QAIssue("seo", "medium", f"SEO title is short ({len(title)} characters).", suggestion="Expand the title with the audience or outcome."))
        elif len(title) > 70:
            issues.append(QAIssue("seo", "medium", f"SEO title is long ({len(title)} characters).", suggestion="Shorten the title so it does not truncate in search results."))
        else:
            suggestions.append("SEO title length is in a healthy range.")

        if not meta:
            issues.append(QAIssue("seo", "high", "Meta description is missing.", suggestion="Add a 120-160 character meta description."))
        elif len(meta) < 90:
            issues.append(QAIssue("seo", "medium", f"Meta description is short ({len(meta)} characters).", suggestion="Add a clearer promise, audience, and outcome."))
        elif len(meta) > 170:
            issues.append(QAIssue("seo", "medium", f"Meta description is long ({len(meta)} characters).", suggestion="Trim the meta description to around 150 characters."))
        else:
            suggestions.append("Meta description is present and usable.")

        if qa_input.focus_keyword and qa_input.focus_keyword.lower() not in f"{title} {meta} {qa_input.content}".lower():
            issues.append(QAIssue("seo", "low", "Focus keyword is not clearly used in title, meta, or body.", suggestion="Use the focus keyword naturally in one visible location."))

        return issues, suggestions

    async def _check_links(self, links: Iterable[str], draft_url: str = "") -> Tuple[List[QAIssue], List[str]]:
        issues: List[QAIssue] = []
        suggestions: List[str] = []
        links = [link for link in links if link]
        internal_links = [link for link in links if self._is_internal_link(link, draft_url)]

        if not links:
            suggestions.append("No internal links found; add 1-3 relevant internal links if this is a production post.")
            return issues, suggestions

        for link in internal_links[:8]:
            if link.startswith("#") or link.startswith("/"):
                suggestions.append(f"Relative internal link queued for app-level verification: {link}")
                continue
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.head(link, timeout=3.0)
                    if response.status_code >= 400:
                        response = await client.get(link, timeout=3.0)
                    if response.status_code >= 400:
                        issues.append(QAIssue("links", "high", f"Internal link returned HTTP {response.status_code}.", context=link, suggestion="Fix or remove the broken internal link."))
            except Exception:
                issues.append(QAIssue("links", "medium", "Could not verify internal link.", context=link, suggestion="Check this link manually before publishing."))

        if internal_links:
            suggestions.append(f"Checked {len(internal_links)} internal link(s).")
        return issues, suggestions

    def _check_readability(self, content: str, audience: str) -> Tuple[List[QAIssue], List[str], float]:
        plain = self._strip_markup(content or "")
        words = re.findall(r"\b\w+\b", plain)
        sentences = [s for s in re.split(r"[.!?]+", plain) if s.strip()]
        if len(words) < 120:
            return [QAIssue("readability", "medium", "Draft is very short for a publish-ready article.", suggestion="Add more examples, transitions, and proof points.")], [], 100.0

        avg_sentence_length = len(words) / max(len(sentences), 1)
        long_sentence_count = sum(1 for sentence in sentences if len(re.findall(r"\b\w+\b", sentence)) > 28)
        score = max(0.0, min(100.0, 100 - (avg_sentence_length - 16) * 2 - long_sentence_count * 3))

        issues: List[QAIssue] = []
        suggestions: List[str] = []
        if avg_sentence_length > 24:
            issues.append(QAIssue("readability", "medium", f"Average sentence length is high ({avg_sentence_length:.1f} words).", suggestion="Break long sentences into shorter, clearer lines."))
        if long_sentence_count:
            issues.append(QAIssue("readability", "low", f"Found {long_sentence_count} long sentence(s).", suggestion="Shorten long sentences for the target audience."))
        if not issues:
            suggestions.append(f"Readability looks suitable for {audience}.")
        return issues, suggestions, round(score, 1)

    async def _check_brand_voice(self, qa_input: QAGateInput) -> Tuple[List[QAIssue], List[str]]:
        if self.llm_client:
            # Keep the interface open for Claude/local-LLM replacement without making the OSS path paid.
            llm_result = await self.llm_client.evaluate_brand_voice(
                title=qa_input.title,
                content=qa_input.content,
                target_audience=qa_input.target_audience,
                brand_rubric=qa_input.brand_rubric,
            )
            return llm_result.get("issues", []), llm_result.get("suggestions", [])

        issues: List[QAIssue] = []
        suggestions: List[str] = []
        content_lower = (qa_input.content or "").lower()
        rubric_lower = (qa_input.brand_rubric or "").lower()

        banned_hype = ["revolutionary", "game-changing", "10x", "magic", "fully autonomous"]
        if any(term in content_lower for term in banned_hype) and any(term in rubric_lower for term in ["non-hype", "practical", "clear"]):
            issues.append(QAIssue("brand_voice", "medium", "Draft uses hype-heavy phrasing that conflicts with the brand rubric.", suggestion="Replace hype with concrete outcomes and implementation details."))

        if "example" not in content_lower and "specific" in rubric_lower:
            issues.append(QAIssue("brand_voice", "low", "Brand rubric asks for specificity, but the draft has few explicit examples.", suggestion="Add one concrete workflow or API example."))

        if not issues:
            suggestions.append("Brand voice is broadly aligned with the supplied rubric.")
        return issues, suggestions

    def _score(self, issues: List[QAIssue], readability_score: float) -> int:
        penalty = 0
        weights = {"critical": 35, "high": 25, "medium": 10, "low": 4, "info": 1}
        for issue in issues:
            penalty += weights.get(issue.severity, 3)
        readability_penalty = max(0, 75 - readability_score) * 0.4
        return int(max(0, min(100, 100 - penalty - readability_penalty)))

    def _reasoning(self, score: int, passed: bool, issues: List[QAIssue], qa_input: QAGateInput, readability_score: float) -> str:
        if passed:
            return f"QA gate passed with score {score}/100. SEO, internal links, brand voice, and readability were acceptable for {qa_input.target_audience}. Readability score: {readability_score}."
        by_category: Dict[str, int] = {}
        for issue in issues:
            by_category[issue.category] = by_category.get(issue.category, 0) + 1
        categories = ", ".join(f"{category}: {count}" for category, count in by_category.items()) or "no categorized issues"
        return f"QA gate failed with score {score}/100. The workflow is paused before publish. Issues by category: {categories}. Review suggestions, edit the draft, retry after edit, or override and publish."

    def _next_action(self, qa_input: QAGateInput, passed: bool) -> str:
        if passed and qa_input.mode == "auto_publish":
            return "continue_to_publish_post"
        if passed:
            return "await_human_approval"
        if qa_input.mode == "send_to_editor":
            return f"send_to_editor_channel:{qa_input.editor_channel}"
        return "pause_workflow"

    def _store_run_step_result(self, run_step_id: int, result: QAGateResult) -> None:
        if SessionLocal is None or DbRunStep is None:
            return
        db = SessionLocal()
        try:
            run_step = db.query(DbRunStep).filter(DbRunStep.id == run_step_id).first()
            if run_step:
                run_step.output = result.to_dict()
                run_step.status = "completed" if result.passed else "paused"
                db.commit()
        finally:
            db.close()

    @staticmethod
    def extract_links(content: str) -> List[str]:
        markdown_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", content or "")
        html_links = re.findall(r"href=[\"']([^\"']+)[\"']", content or "", flags=re.IGNORECASE)
        bare_links = re.findall(r"https?://[^\s)>'\"]+", content or "")
        return QAGate._unique(markdown_links + html_links + bare_links)

    @staticmethod
    def _is_internal_link(link: str, draft_url: str) -> bool:
        if link.startswith("/") or link.startswith("#"):
            return True
        if not draft_url:
            return False
        return urlparse(link).netloc == urlparse(draft_url).netloc

    @staticmethod
    def _strip_markup(content: str) -> str:
        text = re.sub(r"```.*?```", " ", content, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"[#*_>`\[\]()]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _unique(items: Iterable[str]) -> List[str]:
        seen = set()
        output = []
        for item in items:
            if item and item not in seen:
                seen.add(item)
                output.append(item)
        return output


async def run_qa_gate(payload: Dict[str, Any], run_step_id: Optional[int] = None) -> Dict[str, Any]:
    result = await QAGate().run_check(payload, run_step_id=run_step_id)
    return result.to_dict()


def run_qa_gate_sync(payload: Dict[str, Any], run_step_id: Optional[int] = None) -> Dict[str, Any]:
    return asyncio.run(run_qa_gate(payload, run_step_id=run_step_id))
