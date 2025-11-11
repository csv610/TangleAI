from perplexity import Perplexity
from typing import List, Optional
from pydantic import BaseModel, Field
import argparse
from pydantic_utils import display_model, get_field_descriptions, build_display_string


class CityInfo(BaseModel):
    """Data model for city information"""
    name: str
    country: str
    population: int = Field(..., json_schema_extra={"formatter": lambda v: f"{v:,}"})
    local_food: List[str]
    area_sq_km: float = Field(..., json_schema_extra={"formatter": lambda v: f"{v} sq km"})
    founded_year: Optional[int] = None
    major_attractions: Optional[List[str]] = None
    average_temperature_celsius: Optional[float] = Field(
        default=None,
        json_schema_extra={"formatter": lambda v: f"{v}°C"}
    )
    night_life: Optional[List[str]] = None


class CityInfoFetcher:
    """Fetches city information from Perplexity API"""

    def __init__(self):
        self.client = Perplexity()

    def fetch(self, city: str, province: Optional[str] = None,
              country: Optional[str] = None) -> CityInfo:
        """
        Fetch city information from Perplexity API

        Args:
            city: City name
            province: Province or state name (optional)
            country: Country name (optional)

        Returns:
            CityInfo with extracted data
        """
        location = build_display_string([city, province, country])
        # Dynamically generate field descriptions from model fields
        field_descriptions = get_field_descriptions(CityInfo, skip_fields=['name', 'country'])
        prompt = f"Get information about {location}. Extract key city information: {field_descriptions}"
        output_format={
                "type": "json_schema",
                "json_schema": {"schema": CityInfo.model_json_schema()}
        }

        completion = self.client.chat.completions.create(
            model="sonar-pro",
            messages=[{"role": "user", "content": prompt}],
            response_format=output_format
        )

        return CityInfo.model_validate_json(completion.choices[0].message.content)

    def display(self, city: CityInfo) -> None:
        """Display city information using utility function"""
        display_model(
            city,
            skip_fields=['name', 'country'],
            title_field=['name', 'country'],
            title_separator=", "
        )


def main():
    parser = argparse.ArgumentParser(
        description="Get city information from Perplexity API",
        epilog="Examples:\n"
               "  python city_info.py Paris\n"
               "  python city_info.py Ajmer --province Rajasthan --country India",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("city", help="City name")
    parser.add_argument("--province", "-p", help="Province/state (optional)")
    parser.add_argument("--country", "-c", help="Country (optional)")

    args = parser.parse_args()

    fetcher = CityInfoFetcher()
    city_info = fetcher.fetch(args.city, args.province, args.country)
    fetcher.display(city_info)


if __name__ == "__main__":
    main()
