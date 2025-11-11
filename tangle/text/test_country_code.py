"""
Unit tests for country_code.py

Tests country name to ISO code conversion.
"""

import unittest
from country_code import country_name_to_iso_code, COUNTRY_CODE_MAP


class TestCountryCodeConversion(unittest.TestCase):
    """Tests for country name to ISO code conversion."""

    def test_usa_variations(self):
        """Test United States name variations."""
        self.assertEqual(country_name_to_iso_code("united states"), "US")
        self.assertEqual(country_name_to_iso_code("USA"), "US")
        self.assertEqual(country_name_to_iso_code("United States"), "US")

    def test_uk_variations(self):
        """Test United Kingdom name variations."""
        self.assertEqual(country_name_to_iso_code("united kingdom"), "GB")
        self.assertEqual(country_name_to_iso_code("UK"), "GB")
        self.assertEqual(country_name_to_iso_code("United Kingdom"), "GB")

    def test_korea_variations(self):
        """Test South Korea name variations."""
        self.assertEqual(country_name_to_iso_code("south korea"), "KR")
        self.assertEqual(country_name_to_iso_code("korea"), "KR")
        self.assertEqual(country_name_to_iso_code("South Korea"), "KR")

    def test_uae_variations(self):
        """Test UAE name variations."""
        self.assertEqual(country_name_to_iso_code("uae"), "AE")
        self.assertEqual(country_name_to_iso_code("united arab emirates"), "AE")
        self.assertEqual(country_name_to_iso_code("UAE"), "AE")

    def test_single_word_countries(self):
        """Test single word country names."""
        test_cases = [
            ("Germany", "DE"),
            ("Japan", "JP"),
            ("France", "FR"),
            ("Canada", "CA"),
            ("Australia", "AU"),
            ("India", "IN"),
            ("Brazil", "BR"),
            ("Mexico", "MX"),
            ("China", "CN"),
            ("Russia", "RU"),
            ("Spain", "ES"),
            ("Italy", "IT"),
            ("Sweden", "SE"),
            ("Norway", "NO"),
            ("Denmark", "DK"),
            ("Finland", "FI"),
            ("Poland", "PL"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_multi_word_countries(self):
        """Test multi-word country names."""
        test_cases = [
            ("south korea", "KR"),
            ("hong kong", "HK"),
            ("new zealand", "NZ"),
            ("south africa", "ZA"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_case_insensitivity(self):
        """Test that conversion is case-insensitive."""
        # All these variations should return the same code
        variants = ["germany", "Germany", "GERMANY", "GeRmAnY"]
        for variant in variants:
            with self.subTest(variant=variant):
                self.assertEqual(country_name_to_iso_code(variant), "DE")

    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is stripped."""
        test_cases = [
            ("  germany  ", "DE"),
            ("  united states  ", "US"),
            ("\tFrance\t", "FR"),
            (" Japan ", "JP"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=repr(country)):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_invalid_country(self):
        """Test error when country not found."""
        with self.assertRaises(ValueError) as context:
            country_name_to_iso_code("Atlantis")
        self.assertIn("Atlantis", str(context.exception))
        self.assertIn("not found", str(context.exception))

    def test_empty_string(self):
        """Test error with empty string."""
        with self.assertRaises(ValueError):
            country_name_to_iso_code("")

    def test_whitespace_only(self):
        """Test error with whitespace only."""
        with self.assertRaises(ValueError):
            country_name_to_iso_code("   ")

    def test_all_mapped_countries(self):
        """Test that all countries in map can be looked up."""
        for country_name, expected_code in COUNTRY_CODE_MAP.items():
            with self.subTest(country=country_name):
                result = country_name_to_iso_code(country_name)
                self.assertEqual(result, expected_code)

    def test_iso_code_format(self):
        """Test that returned codes are 2-character uppercase."""
        test_countries = [
            "United States",
            "United Kingdom",
            "Germany",
            "Japan",
            "France",
        ]
        for country in test_countries:
            with self.subTest(country=country):
                code = country_name_to_iso_code(country)
                self.assertEqual(len(code), 2)
                self.assertTrue(code.isupper())

    def test_similar_names(self):
        """Test countries with similar names."""
        # Ensure exact matches, not substring matches
        self.assertEqual(country_name_to_iso_code("korea"), "KR")
        self.assertEqual(country_name_to_iso_code("south korea"), "KR")

    def test_asian_countries(self):
        """Test Asian countries."""
        test_cases = [
            ("singapore", "SG"),
            ("hong kong", "HK"),
            ("thailand", "TH"),
            ("vietnam", "VN"),
            ("indonesia", "ID"),
            ("malaysia", "MY"),
            ("philippines", "PH"),
            ("pakistan", "PK"),
            ("bangladesh", "BD"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_european_countries(self):
        """Test European countries."""
        test_cases = [
            ("netherlands", "NL"),
            ("switzerland", "CH"),
            ("sweden", "SE"),
            ("norway", "NO"),
            ("denmark", "DK"),
            ("finland", "FI"),
            ("poland", "PL"),
            ("ireland", "IE"),
            ("turkey", "TR"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_americas_countries(self):
        """Test Americas countries."""
        test_cases = [
            ("canada", "CA"),
            ("mexico", "MX"),
            ("argentina", "AR"),
            ("chile", "CL"),
            ("colombia", "CO"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_africa_countries(self):
        """Test African countries."""
        test_cases = [
            ("south africa", "ZA"),
            ("egypt", "EG"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)

    def test_middle_east_countries(self):
        """Test Middle East countries."""
        test_cases = [
            ("israel", "IL"),
            ("uae", "AE"),
            ("united arab emirates", "AE"),
        ]
        for country, expected_code in test_cases:
            with self.subTest(country=country):
                self.assertEqual(country_name_to_iso_code(country), expected_code)


class TestCountryCodeMap(unittest.TestCase):
    """Tests for the country code map."""

    def test_map_not_empty(self):
        """Test that country code map is not empty."""
        self.assertGreater(len(COUNTRY_CODE_MAP), 0)

    def test_all_codes_are_strings(self):
        """Test that all codes in map are strings."""
        for code in COUNTRY_CODE_MAP.values():
            self.assertIsInstance(code, str)

    def test_all_keys_are_lowercase(self):
        """Test that all keys are lowercase."""
        for key in COUNTRY_CODE_MAP.keys():
            self.assertEqual(key, key.lower())

    def test_all_codes_are_uppercase(self):
        """Test that all codes are uppercase."""
        for code in COUNTRY_CODE_MAP.values():
            self.assertTrue(code.isupper())

    def test_no_duplicate_codes_multiple_names(self):
        """Test that same country code can have multiple names."""
        # This is allowed (like "korea" and "south korea" both map to "KR")
        kr_entries = [k for k, v in COUNTRY_CODE_MAP.items() if v == "KR"]
        self.assertGreater(len(kr_entries), 1)

        us_entries = [k for k, v in COUNTRY_CODE_MAP.items() if v == "US"]
        self.assertGreater(len(us_entries), 1)


if __name__ == "__main__":
    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestCountryCodeConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestCountryCodeMap))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print("=" * 70)

    import sys
    sys.exit(0 if result.wasSuccessful() else 1)
