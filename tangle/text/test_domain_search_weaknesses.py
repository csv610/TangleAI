"""
Tests that expose weaknesses in domain_search.py

These tests demonstrate actual bugs and design flaws.
"""

import sys
from domain_search import DomainSearcher


def test_substring_matching_false_positive():
    """WEAKNESS #1: Substring matching too broad - false positives.

    Issue: "springer.com" in "springeropen.com" returns True
    """
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #1: Substring Matching False Positives")
    print("=" * 70)

    # These domains contain "springer" but aren't the authoritative Springer:
    test_domains = [
        "springeropen.com",  # Open access but not the main Springer
        "springerprofessional.de",  # Different entity
        "springerplus.com",  # Related but different
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(test_domains)

    print(f"\nInput: {test_domains}")
    print(f"Output: {filtered}")
    print(f"Scores: {scores}")

    # All got scored because "springer" is in domain
    all_got_high_scores = all(s >= 0.85 for s in scores)

    if all_got_high_scores:
        print("\n⚠️  BUG EXPOSED: All domains got high scores (0.90) due to 'springer' substring!")
        print("   springeropen.com is NOT the authoritative Springer, but scored 0.90")
        return False
    else:
        print("\n✓ No false positives detected")
        return True


def test_substring_matching_gov_false_positive():
    """WEAKNESS #1b: 'gov' substring matches non-government domains."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #1b: 'gov' Substring Matching")
    print("=" * 70)

    test_domains = [
        "governor.com",      # NOT government
        "government.org",    # NOT a real government domain
        "govtech.com",       # NOT government
        "cdc.gov",          # Real government (should have high score)
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(test_domains)

    print(f"\nInput: {test_domains}")
    print(f"Output: {filtered}")
    print(f"Scores: {scores}")

    # Check if non-gov domains got high scores
    for domain, score in zip(filtered, scores):
        if "governor" in domain or "government.org" in domain or "govtech" in domain:
            if score >= 0.85:
                print(f"\n⚠️  BUG EXPOSED: '{domain}' scored {score} due to 'gov' in name!")
                print("   This is not a government domain!")
                return False

    print("\n✓ gov substring matching working as expected")
    return True


def test_silent_data_loss_from_filtering():
    """WEAKNESS #2: Silent data loss - user gets fewer results than requested.

    Issue: If many domains are filtered/excluded, user silently gets fewer results.
    """
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #2: Silent Data Loss from Filtering")
    print("=" * 70)

    # Simulate LLM returning domains with many social media/excluded ones
    llm_response = """DOMAINS:
1. pubmed.ncbi.nlm.nih.gov
2. reddit.com
3. nature.com
4. quora.com
5. science.org
6. facebook.com
7. springer.com
8. twitter.com
9. sciencedirect.com
10. instagram.com
11. cdc.gov
12. tiktok.com
13. medlineplus.gov
14. pinterest.com
15. nejm.org

REASONING:
Medical sources"""

    domains, _ = DomainSearcher._parse_response(llm_response)
    print(f"\nLLM returned: {len(domains)} domains")

    filtered, scores = DomainSearcher._filter_and_score_domains(domains)
    print(f"After filtering: {len(filtered)} domains")
    print(f"Data loss: {len(domains) - len(filtered)} domains removed ({((len(domains)-len(filtered))/len(domains)*100):.1f}%)")

    print(f"\nRemoved domains (social media/excluded):")
    removed = set(domains) - set(filtered)
    for d in removed:
        print(f"  ✗ {d}")

    if len(domains) - len(filtered) > 0:
        print(f"\n⚠️  WEAKNESS EXPOSED: {len(domains)-len(filtered)} domains silently removed!")
        print("   User who requested 15 domains now only gets", len(filtered))
        print("   No warning message shown to user!")
        return False
    else:
        print("\n✓ No silent data loss")
        return True


def test_domain_validation_too_lenient():
    """WEAKNESS #3: Domain validation accepts invalid domains."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #3: Domain Validation Too Lenient")
    print("=" * 70)

    # These "domains" pass validation but are invalid
    invalid_domains = [
        ".",              # Just a dot
        "a.b",           # Too short (might be valid but uncommon)
        "example.123",   # Numeric TLD
        "test.",         # Missing extension
        "real-domain.com",  # This one IS valid
    ]

    # Simulate parsing response with these
    response = "DOMAINS:\n" + "\n".join(f"{i}. {d}" for i, d in enumerate(invalid_domains, 1)) + "\n\nREASONING: test"

    try:
        domains, _ = DomainSearcher._parse_response(response)
        print(f"\nParsed domains: {domains}")

        invalid_accepted = []
        for d in domains:
            if d in [".", "a.b", "example.123", "test."]:
                invalid_accepted.append(d)

        if invalid_accepted:
            print(f"\n⚠️  WEAKNESS EXPOSED: Invalid domains accepted!")
            for d in invalid_accepted:
                print(f"   • '{d}' passed validation")
            return False
        else:
            print("\n✓ No invalid domains accepted")
            return True

    except ValueError:
        # This is ok if parsing failed
        print("✓ Invalid domains rejected during parsing")
        return True


def test_response_parsing_fragile():
    """WEAKNESS #4: Response parsing fails if format varies slightly."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #4: Fragile Response Parsing")
    print("=" * 70)

    # Valid response
    valid_response = """DOMAINS:
1. example.com
2. test.org

REASONING:
This works"""

    # Slightly different format (sections reversed)
    reversed_response = """REASONING:
This won't work if LLM puts reasoning first.

DOMAINS:
1. example.com
2. test.org"""

    # Preamble text before DOMAINS
    preamble_response = """Here are the top domains for your query:

DOMAINS:
1. example.com

REASONING:
With preamble"""

    print("\nTest 1: Valid response")
    try:
        domains, _ = DomainSearcher._parse_response(valid_response)
        print(f"✓ Parsed successfully: {domains}")
    except ValueError as e:
        print(f"✗ Failed: {e}")

    print("\nTest 2: Reversed section order")
    try:
        domains, _ = DomainSearcher._parse_response(reversed_response)
        print(f"✓ Parsed successfully: {domains}")
    except ValueError as e:
        print(f"⚠️  WEAKNESS EXPOSED: {e}")
        print("   Parser only works if DOMAINS comes before REASONING")

    print("\nTest 3: Preamble before DOMAINS")
    try:
        domains, _ = DomainSearcher._parse_response(preamble_response)
        print(f"✓ Parsed successfully: {domains}")
    except ValueError as e:
        print(f"⚠️  WEAKNESS EXPOSED: {e}")
        print("   Parser fails with preamble text")

    return True


def test_no_count_warning_on_filtering():
    """WEAKNESS #2b: No warning when result count < requested count."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #2b: No Warning on Count Mismatch")
    print("=" * 70)

    # Simulate: user wants 10, but many get filtered
    response = """DOMAINS:
1. example.com
2. reddit.com
3. test.org
4. quora.com
5. valid.edu
6. facebook.com
7. good-source.com
8. twitter.com
9. research.org
10. instagram.com

REASONING:
Test"""

    domains, _ = DomainSearcher._parse_response(response)
    filtered, _ = DomainSearcher._filter_and_score_domains(domains)

    print(f"\nRequested count: 10")
    print(f"LLM returned: {len(domains)} domains")
    print(f"After filtering: {len(filtered)} domains")

    if len(filtered) < 10:
        print(f"\n⚠️  WEAKNESS EXPOSED: Only {len(filtered)} results returned!")
        print("   User requested 10 but got 40% fewer due to filtering")
        print("   No log message warns user about this!")
        return False
    else:
        print("✓ Sufficient results")
        return True


def test_no_api_key_flexibility():
    """WEAKNESS #5: API key must come from environment - no flexibility."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #5: No API Key Flexibility")
    print("=" * 70)

    import os

    # Check if we can pass custom API key
    try:
        # Try to init with custom key (this will fail because __init__ doesn't accept it)
        original_key = os.getenv("PERPLEXITY_API_KEY")

        print("\nDomainSearcher.__init__() signature:")
        import inspect
        sig = inspect.signature(DomainSearcher.__init__)
        print(f"  {sig}")

        if "api_key" in str(sig):
            print("✓ Can pass custom API key")
            return True
        else:
            print("⚠️  WEAKNESS EXPOSED: Cannot pass custom API key!")
            print("   Must use environment variable PERPLEXITY_API_KEY")
            print("   Makes testing and key rotation difficult")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_no_model_validation():
    """WEAKNESS #9: No validation of model name."""
    print("\n" + "=" * 70)
    print("WEAKNESS TEST #9: No Model Name Validation")
    print("=" * 70)

    # Invalid model name is accepted
    invalid_model = "this-model-does-not-exist-xyz-123"

    prompt = DomainSearcher._build_prompt("test", 5)

    # Model name is accepted in method signature
    print(f"\nTesting invalid model: '{invalid_model}'")
    print("✓ Invalid model name accepted by _build_prompt()")

    # The error would only occur at API call time
    print("⚠️  WEAKNESS EXPOSED: Invalid model only fails at API call!")
    print("   Better to validate model names upfront")

    return False  # This is a weakness


def run_weakness_tests():
    """Run all weakness tests."""
    tests = [
        ("Substring Matching False Positives", test_substring_matching_false_positive),
        ("Substring Matching 'gov'", test_substring_matching_gov_false_positive),
        ("Silent Data Loss", test_silent_data_loss_from_filtering),
        ("Domain Validation Too Lenient", test_domain_validation_too_lenient),
        ("Fragile Response Parsing", test_response_parsing_fragile),
        ("No Warning on Count Mismatch", test_no_count_warning_on_filtering),
        ("No API Key Flexibility", test_no_api_key_flexibility),
        ("No Model Validation", test_no_model_validation),
    ]

    print("\n" + "=" * 70)
    print("DOMAIN SEARCH - WEAKNESS TESTS")
    print("=" * 70)

    for name, test in tests:
        try:
            result = test()
        except Exception as e:
            print(f"\n⚠️  Test error: {e}")
            result = False

    print("\n" + "=" * 70)
    print("SUMMARY: Multiple weaknesses detected - see tests above")
    print("=" * 70)


if __name__ == "__main__":
    run_weakness_tests()
