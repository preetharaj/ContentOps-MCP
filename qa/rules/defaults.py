"""QA Rules"""

# Default banned phrases
DEFAULT_BANNED_PHRASES = [
    "obviously",
    "as everyone knows",
    "clearly",
    "it goes without saying",
    "needless to say",
    "of course",
    "as I mentioned",
    "famously",
]

# Default style rules
DEFAULT_STYLE_RULES = {
    "capitalize_headings": True,
    "oxford_comma": True,
    "contractions_allowed": True,
    "active_voice_preferred": True,
    "max_acronyms_per_article": 5,
    "em_dash_style": "spaced",
}

# Default QA gate rules
DEFAULT_QA_RULES = {
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
