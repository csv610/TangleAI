"""
Medical Domain Search - Practical Demo

Demonstrates how to use domain_search for medical/healthcare research.
Includes examples and best practices.
"""

from domain_search import DomainResult, DomainSearcher
import json


def demo_medical_use_cases():
    """Demonstrate realistic medical domain searches."""

    print("=" * 70)
    print("MEDICAL DOMAIN SEARCH - DEMO")
    print("=" * 70)

    # Example 1: Parse a realistic medical response
    print("\n1. PARSING MEDICAL JOURNAL RESPONSE")
    print("-" * 70)

    medical_response = """DOMAINS:
1. pubmed.ncbi.nlm.nih.gov
2. jama.jama.network
3. thelancet.com
4. bmj.com
5. nature.com/nature-medicine
6. nejm.org
7. acpjc.org
8. sciencedirect.com
9. springer.com
10. cochranelibrary.com

REASONING:
These domains represent the most authoritative sources for medical research
including the National Library of Medicine's PubMed (the largest medical
database), high-impact factor journals (JAMA, The Lancet, BMJ, NEJM), and
systematic review databases (Cochrane Library) critical for evidence-based medicine."""

    domains, reasoning = DomainSearcher._parse_response(medical_response)

    print(f"\nQuery: Medical research domains")
    print(f"Domains found: {len(domains)}")
    for i, domain in enumerate(domains, 1):
        print(f"  {i:2}. {domain}")

    print(f"\nReasoning:\n  {reasoning}")

    # Example 2: Domain filtering for medical research
    print("\n\n2. DOMAIN QUALITY FILTERING")
    print("-" * 70)

    test_domains = [
        "pubmed.ncbi.nlm.nih.gov",  # Authoritative - keep
        "healthline.com",            # Consumer health - keep
        "reddit.com",                # Social media - EXCLUDE
        "cdc.gov",                   # Government - keep
        "medlineplus.gov",           # Government - keep
        "quora.com",                 # Q&A - EXCLUDE
        "nature.com",                # Authoritative journal - keep
        "facebook.com",              # Social - EXCLUDE
    ]

    filtered, scores = DomainSearcher._filter_and_score_domains(test_domains)

    print(f"\nInput domains: {len(test_domains)}")
    print(f"Filtered domains: {len(filtered)}")
    print(f"Excluded: {len(test_domains) - len(filtered)}\n")

    print("Remaining domains (sorted by quality score):")
    for domain, score in zip(filtered, scores):
        quality = "★" * int(score * 5)
        print(f"  {domain:35} [{quality:5}] ({score:.2f})")

    # Example 3: Use DomainResult for structured output
    print("\n\n3. STRUCTURED RESULT OUTPUT")
    print("-" * 70)

    result = DomainResult(
        query="diabetes management and treatment",
        domains=[
            "pubmed.ncbi.nlm.nih.gov",
            "medlineplus.gov",
            "diabetes.org",
            "cdc.gov/diabetes",
            "jama.jama.network",
        ],
        reasoning="Authoritative sources including PubMed (medical literature), government health resources (CDC, MedlinePlus), diabetes-specific organizations, and peer-reviewed journals.",
        quality_scores=[0.95, 0.90, 0.85, 0.90, 0.95]
    )

    print(f"\n{result}\n")

    # Example 4: Export to JSON
    print("\n4. JSON EXPORT")
    print("-" * 70)
    result_json = json.dumps(result.to_dict(), indent=2)
    print(result_json)

    # Example 5: Real-world usage comparison
    print("\n\n5. REAL-WORLD USAGE PATTERNS")
    print("-" * 70)

    use_cases = [
        ("COVID-19 vaccine research", 10, "high-quality peer-reviewed studies"),
        ("Mental health treatment options", 8, "evidence-based clinical resources"),
        ("Cardiovascular disease prevention", 12, "latest medical guidelines"),
        ("Pediatric oncology research", 15, "specialized medical databases"),
        ("Drug interactions and side effects", 5, "authoritative pharmaceutical resources"),
    ]

    for query, count, purpose in use_cases:
        print(f"\n✓ Query: '{query}'")
        print(f"  Count: {count} domains")
        print(f"  Purpose: {purpose}")
        print(f"  Expected sources: Medical journals, government agencies, clinical databases")

    # Example 6: Highlight what makes good medical domains
    print("\n\n6. WHAT MAKES A GOOD MEDICAL SOURCE")
    print("-" * 70)

    good_indicators = [
        ("Government health agencies", [".gov", "health.gov", "cdc.gov", "nih.gov"]),
        ("Major universities", [".edu", ".ac.uk", "stanford.edu", "harvard.edu"]),
        ("Peer-reviewed journals", ["nature.com", "science.org", "springer.com"]),
        ("Professional organizations", ["jama.jama.org", "bmj.com", "nejm.org"]),
        ("Medical databases", ["pubmed.ncbi.nlm.nih.gov", "medlineplus.gov"]),
    ]

    for category, examples in good_indicators:
        print(f"\n{category}:")
        for example in examples:
            print(f"  • {example}")

    bad_indicators = [
        ("Social media", "reddit.com, facebook.com, twitter.com"),
        ("General Q&A", "quora.com, stackoverflow.com"),
        ("Blogs/Forums", "medium.com, wordpress.com, blogspot.com"),
    ]

    print("\n\nWHAT TO AVOID")
    print("-" * 40)
    for category, examples in bad_indicators:
        print(f"{category}:")
        print(f"  ✗ {examples}")

    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_medical_use_cases()
