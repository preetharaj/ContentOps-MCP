"""
Test Cases and Examples for QA Gate System

Demonstrates the QA Gate with various content scenarios.
"""

# Example 1: Article with hallucination
TEST_ARTICLE_WITH_HALLUCINATION = """
Our latest research shows that 87% of users prefer AI-generated content,
according to a study conducted by a team of experts. The technology has been
proven to increase engagement by 300% in the last quarter.

Additionally, a recent survey from TechCorp revealed that implementing AI
can reduce content production costs by up to 95% within just three months.

These statistics clearly demonstrate the revolutionary impact of AI.
"""

# Example 2: Article with missing attribution
TEST_ARTICLE_MISSING_ATTRIBUTION = """
"Content is king in the digital age," a famous saying that many believe originated
from Bill Gates, though the exact source remains unclear. This principle has become
fundamental to digital marketing strategies.

Many experts agree that quality content drives engagement and builds trust with
audiences. However, few provide concrete evidence for these claims.

The importance of SEO optimization cannot be overstated, as it directly impacts
visibility in search results.
"""

# Example 3: Well-written article
TEST_GOOD_ARTICLE = """
# The Future of Content Marketing

## Introduction

Content marketing has evolved significantly over the past decade. According to
research from HubSpot (2024), 73% of companies plan to increase their content
marketing budgets in the coming year.

## Key Trends

The content landscape continues to shift. A recent study from Content Marketing
Institute shows three major trends emerging:

1. **Personalization** — Dynamic content tailored to user preferences
2. **Multi-format** — Videos, blogs, podcasts complementing traditional text
3. **Data-driven** — Analytics informing content strategy

## Evidence and Examples

Companies implementing these trends have seen measurable results. Substack's
email platform, for instance, has enabled creators to build audiences directly.

## Conclusion

The future of content marketing lies in authenticity, data insights, and
multi-channel distribution. Organizations investing in these areas now will
be well-positioned for success.
"""

# Example 4: Article with style issues
TEST_ARTICLE_STYLE_ISSUES = """
Obviously, we all know that content is really super important for digital marketing.
It's absolutely clear that without good writing, your online presence will suffer.

The stats are compelling—81% of consumers prefer companies that provide
relevant content, and 60% of people have made a purchase decision based on custom content.

Needless to say, this shows the tremendous value of creating high-quality material.
As everyone knows, search engines love fresh content, and Google's algorithms
have been updated many times to reward fresh, unique content.
"""

# Example 5: Newsletter with technical accuracy
TEST_NEWSLETTER = """
# Weekly Tech Digest #47

## Top Stories

### Kubernetes 1.30 Released
The Cloud Native Computing Foundation announced version 1.30 of Kubernetes
this week. According to the official release notes, this version includes
significant performance improvements and API enhancements.

Read the full release notes: https://kubernetes.io/releases/

### Python 3.13 Alpha 5
Python 3.13 alpha 5 is now available for testing. Key features include
improved error messages and new syntax enhancements.

### Latest Research
A study from O'Reilly (2024) found that 65% of organizations are adopting
containerization, up from 42% last year.

## Resources
- https://www.python.org/
- https://kubernetes.io/
- https://www.oreilly.com/
"""

# Test scenarios
TEST_SCENARIOS = {
    "hallucination": {
        "content": TEST_ARTICLE_WITH_HALLUCINATION,
        "title": "The Revolutionary Impact of AI on Content",
        "expected_publish_ready": False,
        "expected_critical_issues": ["hallucination_risk"],
    },
    "missing_attribution": {
        "content": TEST_ARTICLE_MISSING_ATTRIBUTION,
        "title": "The Power of Content Marketing",
        "expected_publish_ready": False,
        "expected_critical_issues": ["missing_attribution"],
    },
    "well_written": {
        "content": TEST_GOOD_ARTICLE,
        "title": "The Future of Content Marketing",
        "expected_publish_ready": True,
        "expected_critical_issues": [],
    },
    "style_issues": {
        "content": TEST_ARTICLE_STYLE_ISSUES,
        "title": "Content Marketing Importance",
        "expected_publish_ready": False,
        "expected_critical_issues": ["banned_phrase"],
    },
    "newsletter": {
        "content": TEST_NEWSLETTER,
        "title": "Weekly Tech Digest #47",
        "content_type": "newsletter",
        "expected_publish_ready": True,
        "expected_critical_issues": [],
    },
}


def run_test_scenario(scenario_name: str, verbose: bool = True):
    """Run a test scenario and report results."""
    from qa.scoring.engine import QAGatePipeline
    from qa.agents import (
        FactualConsistencyAgent,
        ClaimValidationAgent,
        AttributionAgent,
        ReadabilityAgent,
        ToneDriftAgent,
        BannedPhrasesAgent,
        HallucinationRiskAgent,
        LinkValidationAgent,
        SEOAgent,
    )
    from qa.agents.specialized import (
        StyleGuideAgent,
        DuplicateIdeasAgent,
    )
    
    if scenario_name not in TEST_SCENARIOS:
        print(f"Unknown scenario: {scenario_name}")
        return False
    
    scenario = TEST_SCENARIOS[scenario_name]
    
    # Create pipeline
    agents = [
        FactualConsistencyAgent(),
        ClaimValidationAgent(),
        AttributionAgent(),
        ReadabilityAgent(),
        ToneDriftAgent(),
        BannedPhrasesAgent(),
        HallucinationRiskAgent(),
        LinkValidationAgent(),
        SEOAgent(focus_keyword="content"),
        StyleGuideAgent(),
        DuplicateIdeasAgent(),
    ]
    
    pipeline = QAGatePipeline(agents=agents)
    
    # Process content
    result = pipeline.process(
        content=scenario["content"],
        content_type=scenario.get("content_type", "article"),
        context={"title": scenario["title"]},
    )
    
    # Report results
    print(f"\n{'='*60}")
    print(f"Test Scenario: {scenario_name.upper()}")
    print(f"{'='*60}")
    
    print(f"\nContent: {scenario['title']}")
    print(f"Type: {scenario.get('content_type', 'article')}")
    print(f"Word count: {result.metadata['word_count']}")
    
    print(f"\nSCORES:")
    print(f"  Accuracy:  {result.scores.accuracy_score:.1f}/100")
    print(f"  Clarity:   {result.scores.clarity_score:.1f}/100")
    print(f"  Trust:     {result.scores.trust_score:.1f}/100")
    print(f"  Overall:   {result.scores.overall_score:.1f}/100")
    
    print(f"\nPUBLISH DECISION:")
    print(f"  Ready: {result.publish_ready}")
    print(f"  Confidence: {result.scores.confidence:.2f}")
    
    if result.critical_issues:
        print(f"\nCRITICAL ISSUES ({len(result.critical_issues)}):")
        for issue in result.critical_issues:
            print(f"  [{issue['agent']}] {issue['message']}")
            if issue.get('suggestion'):
                print(f"    → {issue['suggestion']}")
    else:
        print(f"\nCRITICAL ISSUES: None")
    
    if result.issues:
        print(f"\nALL ISSUES ({len(result.issues)}):")
        by_severity = {}
        for issue in result.issues:
            severity = issue['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        for severity, count in sorted(by_severity.items()):
            print(f"  {severity.upper()}: {count}")
    
    if result.suggestions:
        print(f"\nTOP SUGGESTIONS:")
        for i, suggestion in enumerate(result.suggestions[:3], 1):
            print(f"  {i}. {suggestion['reason']}")
            print(f"     Priority: {suggestion.get('priority', 'N/A')}")
    
    # Validate expectations
    success = True
    
    if scenario.get("expected_publish_ready") != result.publish_ready:
        print(f"\n⚠️  FAILED: Expected publish_ready={scenario.get('expected_publish_ready')}")
        print(f"   Got: {result.publish_ready}")
        success = False
    
    # Check for expected critical issues
    expected_critical = scenario.get("expected_critical_issues", [])
    found_critical_types = {issue['type'] for issue in result.critical_issues}
    
    for expected_type in expected_critical:
        if expected_type not in found_critical_types:
            print(f"\n⚠️  FAILED: Expected critical issue type: {expected_type}")
            success = False
    
    if success:
        print(f"\n✅ PASSED")
    
    return success


def run_all_tests():
    """Run all test scenarios."""
    print("\n" + "="*60)
    print("QA GATE TEST SUITE")
    print("="*60)
    
    results = {}
    for scenario_name in TEST_SCENARIOS.keys():
        passed = run_test_scenario(scenario_name, verbose=True)
        results[scenario_name] = passed
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)
    
    for scenario, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {scenario}")
    
    print(f"\nTotal: {passed_count}/{total_count} passed")
    
    return passed_count == total_count


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run specific scenario
        scenario = sys.argv[1]
        run_test_scenario(scenario)
    else:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
