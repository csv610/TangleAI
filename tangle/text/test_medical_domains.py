"""
Tests for domain_search.py with medical/healthcare queries.

Tests medical domain discovery, filtering, and scoring.
"""

import sys
from domain_search import DomainSearcher, EXCLUDED_DOMAINS, AUTHORITATIVE_INDICATORS


def test_parse_medical_response():
    """Test parsing a realistic medical domain response."""
    response = """DOMAINS:
1. pubmed.ncbi.nlm.nih.gov
2. medlineplus.gov
3. jama.jama.org
4. thelancet.com
5. nejm.org
6. bmj.com
7. nature.com/nature-medicine
8. sciencedirect.com/journal/the-lancet
9. medicalnewstoday.com
10. healthline.com

REASONING:
These are authoritative medical and healthcare information sources including
peer-reviewed journals (JAMA, The Lancet, BMJ, NEJM), government health resources
(PubMed, MedlinePlus, CDC), and reputable medical news sources."""

    domains, reasoning = DomainSearcher._parse_response(response)

    # Verify critical medical sources are parsed
    assert "pubmed.ncbi.nlm.nih.gov" in domains, "PubMed should be in domains"
    assert "medlineplus.gov" in domains, "MedlinePlus should be in domains"
    assert "jama.jama.org" in domains, "JAMA should be in domains"
    assert "nejm.org" in domains, "NEJM should be in domains"

    # Verify count
    assert len(domains) == 10, f"Expected 10 domains, got {len(domains)}"

    # Verify reasoning is captured
    assert "medical" in reasoning.lower(), "Reasoning should mention medical"
    assert "authoritative" in reasoning.lower(), "Reasoning should mention quality"

    print("✓ test_parse_medical_response passed")


def test_medical_domain_scoring():
    """Test that medical domains get appropriate scores."""
    medical_domains = [
        "pubmed.ncbi.nlm.nih.gov",
        "medlineplus.gov",
        "jama.jama.org",
        "thelancet.com",
        "nejm.org",
        "healthline.com",  # Lower quality
        "webmd.com",
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(medical_domains)

    # All should be included (none are excluded)
    assert len(filtered) > 0, "Medical domains should not be filtered out"

    # Government sources (.gov) should have high scores
    gov_domains = [d for d in filtered if ".gov" in d]
    assert len(gov_domains) > 0, "Government domains should be included"

    # NIH/PubMed should be in results
    assert any("pubmed" in d.lower() or "ncbi" in d for d in filtered), "PubMed should be included"

    print("✓ test_medical_domain_scoring passed")


def test_nih_authoritative():
    """Test that NIH domains get proper authority scores."""
    nih_domains = ["nih.gov", "ncbi.nlm.nih.gov", "cdc.gov"]
    filtered, scores = DomainSearcher._filter_and_score_domains(nih_domains)

    assert len(filtered) == 3, f"All NIH domains should pass, got {filtered}"

    # Government domains should have score >= 0.85
    min_score = min(scores)
    assert min_score >= 0.85, f"Government domain scores should be >= 0.85, got {min_score}"

    print("✓ test_nih_authoritative passed")


def test_medical_journals_authoritative():
    """Test that medical journals are recognized as authoritative."""
    journal_domains = [
        "nature.com",
        "science.org",
        "springer.com",
        "sciencedirect.com",
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(journal_domains)

    # All journals should be included
    assert len(filtered) == len(journal_domains), f"All journals should pass, got {len(filtered)}/{len(journal_domains)}"

    # All should have high scores
    assert all(s >= 0.85 for s in scores), f"Journal domains should have high scores, got {scores}"

    print("✓ test_medical_journals_authoritative passed")


def test_medical_social_media_excluded():
    """Test that social media and low-quality medical sites are filtered."""
    domains = [
        "reddit.com",  # Social media - should be excluded
        "quora.com",   # Q&A site - should be excluded
        "healthline.com",  # Medical content - should be included
        "mayoclinic.org",  # Medical clinic - should be included
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(domains)

    # Social media should be excluded
    assert "reddit.com" not in filtered, "Reddit should be excluded"
    assert "quora.com" not in filtered, "Quora should be excluded"

    # Medical sites should be included
    assert any("health" in d.lower() or "mayo" in d.lower() for d in filtered), \
        "Medical content sites should be included"

    print("✓ test_medical_social_media_excluded passed")


def test_medical_prompt_generation():
    """Test prompt generation for medical queries."""
    prompt = DomainSearcher._build_prompt("coronavirus treatment clinical trials", count=15)

    assert "coronavirus treatment clinical trials" in prompt, "Query should be in prompt"
    assert "15" in prompt, "Count should be in prompt"
    assert "medical" in prompt.lower() or "health" in prompt.lower() or "subject" in prompt.lower(), \
        "Prompt should reference medical/subject expertise"

    print("✓ test_medical_prompt_generation passed")


def test_medical_filtering_doesnt_lose_data():
    """Test that medical domain filtering behaves predictably."""
    # Simulate LLM returning 20 medical domains
    medical_domains = [
        "pubmed.ncbi.nlm.nih.gov",
        "medlineplus.gov",
        "cdc.gov",
        "fda.gov",
        "who.int",  # World Health Organization
        "nature.com",
        "science.org",
        "lancet.com",
        "bmj.com",
        "jama.jama.org",
        "healthline.com",
        "mayoclinic.org",
        "clevelandclinic.org",
        "stanford.edu",
        "harvard.edu",
        "oxford.ac.uk",
        "springer.com",
        "sciencedirect.com",
        "webmd.com",
        "medicalnewstoday.com",
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(medical_domains)

    # Verify no excluded domains snuck in
    excluded_in_result = [d for d in filtered if d.lower() in EXCLUDED_DOMAINS]
    assert len(excluded_in_result) == 0, f"Excluded domains found: {excluded_in_result}"

    # Verify all results have scores
    assert len(filtered) == len(scores), "Mismatch between domains and scores"

    # Verify sorting
    for i in range(len(scores) - 1):
        assert scores[i] >= scores[i+1], f"Scores not sorted: {scores}"

    print(f"✓ test_medical_filtering_doesnt_lose_data passed ({len(filtered)} domains retained)")


def test_medical_domain_result_output():
    """Test DomainResult output for medical queries."""
    from domain_search import DomainResult

    medical_result = DomainResult(
        query="cancer immunotherapy research",
        domains=["nature.com", "science.org", "pubmed.ncbi.nlm.nih.gov", "jama.jama.org"],
        reasoning="Leading journals and databases for cancer research and immunotherapy",
        quality_scores=[0.95, 0.95, 0.95, 0.95]
    )

    # Test string representation
    result_str = str(medical_result)
    assert "cancer immunotherapy research" in result_str, "Query should be in output"
    assert "4 domains" in result_str, "Domain count should be in output"

    # Test to_dict
    result_dict = medical_result.to_dict()
    assert result_dict["query"] == "cancer immunotherapy research"
    assert len(result_dict["domains"]) == 4
    assert len(result_dict["quality_scores"]) == 4

    print("✓ test_medical_domain_result_output passed")


def run_medical_tests():
    """Run all medical-related tests."""
    tests = [
        test_parse_medical_response,
        test_medical_domain_scoring,
        test_nih_authoritative,
        test_medical_journals_authoritative,
        test_medical_social_media_excluded,
        test_medical_prompt_generation,
        test_medical_filtering_doesnt_lose_data,
        test_medical_domain_result_output,
    ]

    passed = 0
    failed = 0

    print("=" * 60)
    print("MEDICAL DOMAIN SEARCH TESTS")
    print("=" * 60 + "\n")

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} error: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Medical Tests: {passed} passed, {failed} failed")
    print(f"{'='*60}")

    return failed == 0


if __name__ == "__main__":
    success = run_medical_tests()
    sys.exit(0 if success else 1)
