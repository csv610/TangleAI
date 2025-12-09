#!/usr/bin/env python3
"""
City Information Q&A Command-Line Application using Perplexity API
Queries city information and displays results in the terminal
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

# Add tangle module to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "tangle"))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput
from logging_utils import setup_logging

logger = setup_logging("city_app.log")


class CityInfo(BaseModel):
    """Information about a single city."""
    city_name: str
    local_name: str
    nickname: str
    old_names: str
    etymology: str
    history: str
    province_and_country: str
    latitude: str
    longitude: str
    area: str
    elevation: str
    geography: str
    climate: str
    demographics: str
    time_zone: str
    telephone_code: str
    country_code: str
    tourist_attractions: str
    how_to_reach: str


class CityResponse(BaseModel):
    """Structured response for city information."""
    cities: list[CityInfo]


class ApiError(Exception):
    """Custom exception for API-related errors."""
    pass


class CityGuide:
    """A guide for querying and displaying comprehensive city information."""

    def __init__(self, model: str = "sonar-pro"):
        """
        Initialize the CityGuide with a Perplexity client.

        Args:
            model: The model to use for queries (default: sonar-pro)
        """
        self.client = PerplexityClient()
        self.model = model
        logger.info(f"CityGuide initialized with model: {model}")

    def correct_name(self, city_name: str) -> str:
        """
        Validate and correct a city name if it's misspelled or incorrect.

        Args:
            city_name: The potentially incorrect city name

        Returns:
            The corrected city name
        """
        correction_prompt = f"""Given the city name: "{city_name}", please verify if this is a correctly spelled, real city name.
If it is correct, respond with just the city name.
If it is misspelled or doesn't exist, suggest the correct city name that the user most likely meant.
Respond with ONLY the corrected city name, nothing else."""

        try:
            logger.info(f"Validating city name: '{city_name}'")

            model_input = ModelInput(
                user_prompt=correction_prompt,
                system_prompt="You are a geography expert. Correct misspelled city names and suggest the most likely city the user meant."
            )

            config = ModelConfig(model=self.model)
            response = self.client.generate_content(model_input, config)

            if response.text:
                corrected_name = response.text.strip()
                if corrected_name.lower() != city_name.lower():
                    logger.info(f"City name corrected from '{city_name}' to '{corrected_name}'")
                    print(f"\n✓ Corrected city name: '{city_name}' → '{corrected_name}'")
                return corrected_name
            return city_name

        except Exception as e:
            logger.warning(f"Could not validate city name: {str(e)}")
            return city_name


    def get_info(self, city_name: str, province: Optional[str] = None, country: Optional[str] = None, length: str = "detail") -> Optional[Dict[str, Any]]:
        """
        Get information about a city from Perplexity API.

        Args:
            city_name: The name of the city
            province: Optional province or state to search for a specific city
            country: Optional country to search for a specific city
            length: Information length - "short" for brief info or "detail" for comprehensive info

        Returns:
            Dictionary with city information including old names, location, climate, attractions, and citations or None if an error occurs
        """
        if length == "short":
            system_prompt = """You are a concise geography and travel assistant. Provide brief, essential structured information about cities. For each city, include only:
    - City name (English name)
    - Local name (name in the local language)
    - Nickname (common nicknames)
    - Province and country
    - Latitude and longitude coordinates
    - Climate (brief)
    - Population (brief)
    - Time zone
    - Telephone code
    - Country code
    - Key tourist attractions (3-4 main ones)
    - How to reach (brief)"""
        else:  # detail
            system_prompt = """You are a comprehensive geography and travel assistant. Provide detailed structured information about cities. For each city, include:
    - City name (English name)
    - Local name (name in the local language)
    - Nickname (common nicknames or what it's known as, e.g., "The City of Love" for Paris)
    - Old names (historical names)
    - Etymology (origin and meaning of the name)
    - History (brief historical overview)
    - Province and country
    - Latitude and longitude coordinates
    - Area (in square kilometers)
    - Elevation (in meters above sea level)
    - Geography (geographic features and location characteristics)
    - Climate (weather patterns and seasons)
    - Demographics (population, ethnic composition)
    - Time zone (UTC offset or IANA timezone)
    - Telephone code (phone dialing code)
    - Country code (ISO 3166-1 alpha-2)
    - Tourist attractions (popular landmarks and sites)
    - How to reach (transportation methods and directions)"""

        # Build user prompt based on whether province/country are provided
        if province and country:
            user_prompt = f"Provide detailed information about the city {city_name} in {province}, {country}."
        elif country:
            user_prompt = f"Provide detailed information about the city {city_name} in {country}."
        elif province:
            user_prompt = f"Provide detailed information about the city {city_name} in {province}."
        else:
            user_prompt = f"Provide detailed information about the city: {city_name}. If there are multiple cities with this name, include information about all of them."
            system_prompt += "\n\nIf there are multiple cities with the same name worldwide, list all of them."

        try:
            logger.info(f"Sending request to Perplexity API for city: '{city_name}'")

            model_input = ModelInput(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=CityResponse
            )

            config = ModelConfig(model=self.model)

            response = self.client.generate_content(model_input, config)

            # Extract the response content
            logger.info("Successfully received response from API")

            # Structured output was requested, so response.json should contain the parsed model
            if response.json:
                logger.info("Successfully parsed structured JSON response")
                return response.json.model_dump()

            logger.error("No structured output received in the response.")
            return None

        except Exception as e:
            logger.error(f"Error querying API: {str(e)}")
            raise ApiError(f"Error querying Perplexity API: {str(e)}")

    def save_results_to_json(self, city_name: str, data: Dict[str, Any], province: Optional[str] = None, country: Optional[str] = None) -> str:
        """
        Save the city information results to a JSON file.

        Args:
            city_name: The city name
            data: The parsed response data from the API
            province: Optional province/state
            country: Optional country

        Returns:
            The filename where the data was saved
        """
        # Build filename
        filename_parts = [city_name]
        if province:
            filename_parts.append(province)
        if country:
            filename_parts.append(country)

        filename = "_".join(filename_parts) + ".json"

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to {filename}")
            print(f"\n✅ Results saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"Error saving results to JSON: {str(e)}")
            print(f"\n❌ Error saving results to JSON: {str(e)}")
            return None

    def display_results(self, city_name: str, data: Optional[Dict[str, Any]]) -> None:
        """
        Display the city information results in a formatted terminal output.

        Args:
            city_name: The original city name searched
            data: The parsed response data from the API
        """
        if not data:
            print("\n❌ No data received from API")
            return

        print("\n" + "=" * 70)
        print(f"City Search: {city_name}")
        print("=" * 70)

        cities = data.get("cities", [])

        if not cities:
            print("\n❌ No cities found")
            return

        def is_empty(value):
            """Check if a value is empty or 'N/A'."""
            return value is None or value == "" or value == "N/A"

        # Display information for each city
        for idx, city in enumerate(cities, 1):
            if len(cities) > 1:
                print(f"\n{'─' * 70}")
                print(f"City {idx}: {city.get('city_name', 'N/A')}")
                print(f"{'─' * 70}")

            # Display Local Name
            if not is_empty(city.get("local_name")):
                print("\n🗣️  Local Name:")
                print(city.get("local_name"))

            # Display Nickname
            if not is_empty(city.get("nickname")):
                print("\n🏷️  Nickname:")
                print(city.get("nickname"))

            # Display Old Names
            if not is_empty(city.get("old_names")):
                print("\n📜 Old Names:")
                print(city.get("old_names"))

            # Display Etymology
            if not is_empty(city.get("etymology")):
                print("\n📖 Etymology:")
                print(city.get("etymology"))

            # Display History
            if not is_empty(city.get("history")):
                print("\n📚 History:")
                print(city.get("history"))

            # Display Province and Country
            if not is_empty(city.get("province_and_country")):
                print("\n🗺️  Province & Country:")
                print(city.get("province_and_country"))

            # Display Coordinates
            latitude = city.get("latitude")
            longitude = city.get("longitude")
            if not is_empty(latitude) or not is_empty(longitude):
                print("\n📍 Coordinates:")
                if not is_empty(latitude):
                    print(f"  Latitude:  {latitude}")
                if not is_empty(longitude):
                    print(f"  Longitude: {longitude}")

            # Display Area
            if not is_empty(city.get("area")):
                print("\n📐 Area:")
                print(city.get("area"))

            # Display Elevation
            if not is_empty(city.get("elevation")):
                print("\n⛰️  Elevation:")
                print(city.get("elevation"))

            # Display Geography
            if not is_empty(city.get("geography")):
                print("\n🏔️  Geography:")
                print(city.get("geography"))

            # Display Climate
            if not is_empty(city.get("climate")):
                print("\n🌤️  Climate:")
                print(city.get("climate"))

            # Display Demographics
            if not is_empty(city.get("demographics")):
                print("\n👥 Demographics:")
                print(city.get("demographics"))

            # Display Time Zone
            if not is_empty(city.get("time_zone")):
                print("\n🕐 Time Zone:")
                print(city.get("time_zone"))

            # Display Telephone Code
            if not is_empty(city.get("telephone_code")):
                print("\n☎️  Telephone Code:")
                print(city.get("telephone_code"))

            # Display Country Code
            if not is_empty(city.get("country_code")):
                print("\n🏳️  Country Code:")
                print(city.get("country_code"))

            # Display Tourist Attractions
            if not is_empty(city.get("tourist_attractions")):
                print("\n🎭 Tourist Attractions:")
                print(city.get("tourist_attractions"))

            # Display How to Reach
            if not is_empty(city.get("how_to_reach")):
                print("\n🚗 How to Reach:")
                print(city.get("how_to_reach"))


def main():
    """Main entry point for the command-line application."""
    parser = argparse.ArgumentParser(
        description="City Information Application - Get information about cities using Perplexity API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python city_info.py Paris                                    # Shows all Paris cities worldwide (detailed)
  python city_info.py Paris -c France                         # Shows Paris, France only (detailed)
  python city_info.py Paris -c France -l short                # Shows Paris, France with short info
  python city_info.py Springfield -c USA -p Illinois          # Shows Springfield, Illinois, USA (detailed)
  python city_info.py Tokyo -m sonar -l short                 # Shows Tokyo with short info using sonar model
  python city_info.py Rome --country Italy -l detail          # Shows Rome, Italy with detailed info
        """
    )

    parser.add_argument(
        "city_name",
        help="The name of the city to search"
    )

    parser.add_argument(
        "-p", "--province",
        default=None,
        help="Province or state (optional - use to search for a specific city)"
    )

    parser.add_argument(
        "-c", "--country",
        default=None,
        help="Country (optional - use to search for a specific city)"
    )

    parser.add_argument(
        "-m", "--model",
        default="sonar",
        help="Model to use for the query (default: sonar)"
    )

    parser.add_argument(
        "-l", "--length",
        choices=["short", "detail"],
        default="detail",
        help="Information length: 'short' for brief info or 'detail' for comprehensive info (default: detail)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    try:
        # Initialize the CityGuide
        guide = CityGuide(model=args.model)
        logger.info("CityGuide initialized successfully")

        # Validate and correct city name if needed
        print(f"\n🔍 Validating city name: '{args.city_name}'")
        corrected_city_name = guide.correct_name(args.city_name)

        # Query the API
        print(f"\n🔄 Querying Perplexity API for: '{corrected_city_name}'")
        print("Please wait...\n")

        result = guide.get_info(corrected_city_name, province=args.province, country=args.country, length=args.length)

        # Display results
        if result:
            guide.display_results(corrected_city_name, result)

            # Save results to JSON
            guide.save_results_to_json(corrected_city_name, result, province=args.province, country=args.country)
        else:
            print("\n❌ Failed to get a valid response from the API")
            sys.exit(1)

    except ApiError as e:
        logger.error(f"API Error: {str(e)}")
        print(f"\n❌ API Error: {str(e)}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
