# ISO 3166-1 alpha-2 country code mapping
COUNTRY_CODE_MAP = {
    "united states": "US",
    "usa": "US",
    "united kingdom": "GB",
    "uk": "GB",
    "germany": "DE",
    "japan": "JP",
    "france": "FR",
    "canada": "CA",
    "australia": "AU",
    "india": "IN",
    "brazil": "BR",
    "mexico": "MX",
    "south korea": "KR",
    "korea": "KR",
    "china": "CN",
    "russia": "RU",
    "spain": "ES",
    "italy": "IT",
    "netherlands": "NL",
    "switzerland": "CH",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "poland": "PL",
    "singapore": "SG",
    "hong kong": "HK",
    "new zealand": "NZ",
    "ireland": "IE",
    "israel": "IL",
    "uae": "AE",
    "united arab emirates": "AE",
    "thailand": "TH",
    "vietnam": "VN",
    "indonesia": "ID",
    "malaysia": "MY",
    "philippines": "PH",
    "pakistan": "PK",
    "bangladesh": "BD",
    "south africa": "ZA",
    "egypt": "EG",
    "turkey": "TR",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
}


def country_name_to_iso_code(country_name: str) -> str:
    """Convert country name to ISO 3166-1 alpha-2 country code.

    Args:
        country_name: The name of the country (case-insensitive)

    Returns:
        ISO 3166-1 alpha-2 country code (e.g., "US", "GB", "DE")

    Raises:
        ValueError: If country name is not found in the mapping

    Example:
        >>> country_name_to_iso_code("United States")
        'US'
        >>> country_name_to_iso_code("Japan")
        'JP'
    """
    normalized_name = country_name.lower().strip()

    if normalized_name in COUNTRY_CODE_MAP:
        return COUNTRY_CODE_MAP[normalized_name]

    raise ValueError(
        f"Country '{country_name}' not found. "
        f"Please use a valid country name or ISO code directly."
    )
