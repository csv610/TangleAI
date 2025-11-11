"""
Unit tests for domain_search.py

Tests parsing, filtering, and scoring logic without API calls.
"""

import sys
from domain_search import DomainSearcher, DomainResult, EXCLUDED_DOMAINS, AUTHORITATIVE_INDICATORS


def test_parse_response_basic():
    """Test basic response parsing."""
    response = """DOMAINS:
1. example.com
2. test.org
3. science.edu

REASONING:
These are example domains for testing."""

    domains, reasoning = DomainSearcher._parse_response(response)
    assert domains == ["example.com", "test.org", "science.edu"], f"Expected 3 domains, got {domains}"
    assert "example" in reasoning.lower(), f"Reasoning should contain 'example', got: {reasoning}"
    print("✓ test_parse_response_basic passed")


def test_parse_response_with_bullets():
    """Test parsing with bullet points."""
    response = """DOMAINS:
- arxiv.org
- nature.com
- springer.com

REASONING:
Top academic sources"""

    domains, reasoning = DomainSearcher._parse_response(response)
    assert domains == ["arxiv.org", "nature.com", "springer.com"], f"Got {domains}"
    print("✓ test_parse_response_with_bullets passed")


def test_parse_response_mixed_formatting():
    """Test parsing with mixed formatting."""
    response = """DOMAINS:
1. arxiv.org
2. nature.com
- science.org
• ieee.org

REASONING:
Mix of formats"""

    domains, reasoning = DomainSearcher._parse_response(response)
    assert "arxiv.org" in domains, f"Missing arxiv.org in {domains}"
    assert "nature.com" in domains, f"Missing nature.com in {domains}"
    assert "science.org" in domains, f"Missing science.org in {domains}"
    assert "ieee.org" in domains, f"Missing ieee.org in {domains}"
    print("✓ test_parse_response_mixed_formatting passed")


def test_filter_and_score_basic():
    """Test domain filtering and scoring."""
    domains = ["arxiv.org", "nature.com", "quora.com", "example.org"]
    filtered, scores = DomainSearcher._filter_and_score_domains(domains)

    # arxiv and nature should be included with high scores
    assert "arxiv.org" in filtered, "arxiv.org should be included"
    assert "nature.com" in filtered, "nature.com should be included"

    # quora should be excluded
    assert "quora.com" not in filtered, "quora.com should be excluded"

    # Scores should match filtered domains
    assert len(filtered) == len(scores), "Mismatch between domains and scores"

    print("✓ test_filter_and_score_basic passed")


def test_filter_and_score_authoritative():
    """Test that authoritative domains get higher scores."""
    domains = ["arxiv.org", "example.org", "unknown-site.com"]
    filtered, scores = DomainSearcher._filter_and_score_domains(domains)

    # Find indices
    arxiv_idx = filtered.index("arxiv.org") if "arxiv.org" in filtered else None

    if arxiv_idx is not None:
        # arxiv.org should have a high score (0.95)
        assert scores[arxiv_idx] >= 0.9, f"arxiv.org score {scores[arxiv_idx]} should be >= 0.9"

    print("✓ test_filter_and_score_authoritative passed")


def test_excluded_domains_filtered():
    """Test that excluded domains are properly filtered."""
    domains = ["reddit.com", "facebook.com", "twitter.com", "example.edu"]
    filtered, scores = DomainSearcher._filter_and_score_domains(domains)

    # All social media should be excluded
    assert "reddit.com" not in filtered, "reddit.com should be excluded"
    assert "facebook.com" not in filtered, "facebook.com should be excluded"
    assert "twitter.com" not in filtered, "twitter.com should be excluded"

    # edu domain should be included
    assert "example.edu" in filtered, "example.edu should be included"

    print("✓ test_excluded_domains_filtered passed")


def test_build_prompt():
    """Test prompt building."""
    prompt = DomainSearcher._build_prompt("quantum computing", 5)

    assert "quantum computing" in prompt, "Query should be in prompt"
    assert "5" in prompt, "Count should be in prompt"
    assert "DOMAINS:" in prompt, "Format hint should be in prompt"
    assert "REASONING:" in prompt, "Format hint should be in prompt"

    print("✓ test_build_prompt passed")


def test_domain_result_dataclass():
    """Test DomainResult dataclass."""
    result = DomainResult(
        query="test query",
        domains=["example.com", "test.org"],
        reasoning="test reasoning",
        quality_scores=[0.8, 0.9]
    )

    assert result.query == "test query"
    assert result.domains == ["example.com", "test.org"]
    assert len(result.quality_scores) == 2

    # Test to_dict
    dict_result = result.to_dict()
    assert dict_result["query"] == "test query"
    assert dict_result["domains"] == ["example.com", "test.org"]

    # Test __str__
    str_result = str(result)
    assert "test query" in str_result
    assert "example.com" in str_result

    print("✓ test_domain_result_dataclass passed")


def test_parse_response_empty_raises():
    """Test that parsing empty domains raises ValueError."""
    response = """DOMAINS:

REASONING:
No domains provided"""

    try:
        DomainSearcher._parse_response(response)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "No domains" in str(e), f"Wrong error message: {e}"
        print("✓ test_parse_response_empty_raises passed")


def test_case_insensitive_parsing():
    """Test that section headers are case-insensitive."""
    response = """domains:
1. example.com

reasoning:
Test"""

    domains, reasoning = DomainSearcher._parse_response(response)
    assert "example.com" in domains, f"Failed to parse lowercase headers: {domains}"
    print("✓ test_case_insensitive_parsing passed")


def test_authoritative_indicators_coverage():
    """Test that authoritative indicators dict has expected entries."""
    assert "arxiv.org" in AUTHORITATIVE_INDICATORS
    assert "nature.com" in AUTHORITATIVE_INDICATORS
    assert AUTHORITATIVE_INDICATORS["arxiv.org"] == 0.95
    print("✓ test_authoritative_indicators_coverage passed")


def test_excluded_domains_coverage():
    """Test that excluded domains include social media."""
    assert "reddit.com" in EXCLUDED_DOMAINS
    assert "quora.com" in EXCLUDED_DOMAINS
    assert "facebook.com" in EXCLUDED_DOMAINS
    print("✓ test_excluded_domains_coverage passed")


def run_all_tests():
    """Run all tests."""
    tests = [
        test_parse_response_basic,
        test_parse_response_with_bullets,
        test_parse_response_mixed_formatting,
        test_filter_and_score_basic,
        test_filter_and_score_authoritative,
        test_excluded_domains_filtered,
        test_build_prompt,
        test_domain_result_dataclass,
        test_parse_response_empty_raises,
        test_case_insensitive_parsing,
        test_authoritative_indicators_coverage,
        test_excluded_domains_coverage,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
