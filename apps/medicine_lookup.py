"""
Medicine Information Lookup System
Fetches comprehensive medicine information using Perplexity AI and returns structured MedicineInfo data
"""

import sys
import os
import json
from typing import Optional
from datetime import datetime

# Add tangle directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tangle'))

from drugbank_medicine import (
    MedicineInfo, ChemicalProperties, Pharmacodynamics, Pharmacokinetics,
    DrugType, DrugGroup, RouteOfAdministration, ATCCode, Target, Enzyme,
    Interaction, FoodInteraction, Dosage, ExternalIdentifier, AdverseReaction,
    Contraindication, Manufacturer, Patent, ClinicalTrial, Taxonomy, Carrier, Transporter
)
from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput


class MedicineLookupService:
    """Service to lookup medicine information using Perplexity AI"""

    def __init__(self, config: Optional[ModelConfig] = None):
        """
        Initialize the medicine lookup service.

        Args:
            config: Optional ModelConfig for API calls. If not provided, uses sensible defaults.

        Raises:
            ValueError: If PERPLEXITY_API_KEY environment variable is not set.
        """
        self.config = config or ModelConfig(
            model="sonar-pro",
            max_tokens=4096,
            temperature=0.7,
            top_p=0.9,
            stream=False,
            search_mode="web"
        )
        self.client = PerplexityClient(self.config)

    def lookup_medicine(self, medicine_name: str) -> MedicineInfo:
        """
        Lookup comprehensive medicine information using Perplexity AI.

        Args:
            medicine_name: Name of the medicine (brand name or generic name)

        Returns:
            MedicineInfo: Comprehensive medicine information

        Raises:
            ValueError: If API key is not set or lookup fails
        """
        print(f"Looking up information for: {medicine_name}")

        # Create model input with structured output
        model_input = ModelInput(
            user_prompt=f"Provide comprehensive pharmaceutical information about {medicine_name}. Include drug type, approval status, chemical properties, indications, pharmacodynamics, side effects, dosage forms, and any relevant clinical data.",
            response_model=MedicineInfo
        )

        try:
            # Call Perplexity API with structured output
            response = self.client.generate_content(model_input, self.config)

            # Validate and parse the response
            medicine_info = MedicineInfo.model_validate_json(
                response.choices[0].message.content
            )

            print(f"  ✓ Successfully retrieved information for: {medicine_info.name}")
            return medicine_info

        except ValueError as e:
            raise ValueError(f"Failed to lookup medicine information: {str(e)}")
        except Exception as e:
            raise Exception(f"Error during medicine lookup: {str(e)}")


def get_medicine_info(medicine_name: str) -> MedicineInfo:
    """
    Main function to get comprehensive medicine information

    Args:
        medicine_name: Name of the medicine (e.g., "Aspirin", "Lisinopril", "Metformin")

    Returns:
        MedicineInfo: Structured medicine information
    """
    service = MedicineLookupService()
    return service.lookup_medicine(medicine_name)


def display_medicine_info(medicine_info: MedicineInfo):
    """Display medicine information in a readable format"""

    print("\n" + "="*80)
    print(f"MEDICINE INFORMATION: {medicine_info.name}")
    print("="*80)

    if medicine_info.synonyms:
        print(f"\nSynonyms: {', '.join(medicine_info.synonyms[:5])}")

    if medicine_info.description:
        print(f"\nDescription:\n{medicine_info.description[:300]}...")

    if medicine_info.indication:
        print(f"\nIndications:\n{medicine_info.indication[:300]}...")

    if medicine_info.chemical_properties:
        print(f"\nChemical Properties:")
        cp = medicine_info.chemical_properties
        if cp.molecular_formula:
            print(f"   - Formula: {cp.molecular_formula}")
        if cp.molecular_weight:
            print(f"   - Molecular Weight: {cp.molecular_weight} g/mol")
        if cp.iupac_name:
            print(f"   - IUPAC Name: {cp.iupac_name[:80]}...")

    if medicine_info.warnings:
        print(f"\nWarnings:\n{medicine_info.warnings[:300]}...")

    if medicine_info.adverse_reactions:
        print(f"\nAdverse Reactions:")
        for reaction in medicine_info.adverse_reactions[:5]:
            print(f"   - {reaction.reaction} ({reaction.frequency})")

    if medicine_info.drug_interactions:
        print(f"\nDrug Interactions ({len(medicine_info.drug_interactions)} found):")
        for interaction in medicine_info.drug_interactions[:3]:
            print(f"   - {interaction.drug_name}: {interaction.description[:100]}...")

    if medicine_info.dosages:
        print(f"\nDosage Information:")
        for dosage in medicine_info.dosages[:2]:
            print(f"   - Route: {dosage.route.value}, Form: {dosage.form}")

    if medicine_info.external_identifiers:
        print(f"\nExternal References:")
        for ext_id in medicine_info.external_identifiers:
            print(f"   - {ext_id.database}: {ext_id.identifier}")

    print("\n" + "="*80)


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        medicine_name = ' '.join(sys.argv[1:])
    else:
        medicine_name = input("Enter medicine name: ")

    try:
        medicine_info = get_medicine_info(medicine_name)
        display_medicine_info(medicine_info)

        # Save to JSON
        output_file = f"{medicine_name.lower().replace(' ', '_')}_info.json"
        with open(output_file, 'w') as f:
            json.dump(medicine_info.model_dump(mode='json'), f, indent=2, default=str)

        print(f"\nFull information saved to: {output_file}")

    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
