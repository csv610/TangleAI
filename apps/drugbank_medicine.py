from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import sys
import os

# Add tangle directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tangle'))

from perplx_client import PerplexityClient
from config import ModelConfig, ModelInput


class DrugType(str, Enum):
    """Types of drugs"""
    SMALL_MOLECULE = "small_molecule"
    BIOTECH = "biotech"
    VACCINE = "vaccine"
    BIOLOGIC = "biologic"
    HERB = "herb"


class DrugGroup(str, Enum):
    """Drug approval groups"""
    APPROVED = "approved"
    EXPERIMENTAL = "experimental"
    INVESTIGATIONAL = "investigational"
    WITHDRAWN = "withdrawn"
    ILLICIT = "illicit"
    NUTRACEUTICAL = "nutraceutical"


class RouteOfAdministration(str, Enum):
    """Routes of drug administration"""
    ORAL = "oral"
    INTRAVENOUS = "intravenous"
    INTRAMUSCULAR = "intramuscular"
    SUBCUTANEOUS = "subcutaneous"
    TOPICAL = "topical"
    INHALATION = "inhalation"
    RECTAL = "rectal"
    TRANSDERMAL = "transdermal"
    OPHTHALMIC = "ophthalmic"
    NASAL = "nasal"
    SUBLINGUAL = "sublingual"
    OTHER = "other"


class ChemicalProperties(BaseModel):
    """Chemical properties of the medicine"""
    molecular_formula: Optional[str] = Field(None, description="Molecular formula")
    molecular_weight: Optional[float] = Field(None, description="Molecular weight in g/mol")
    smiles: Optional[str] = Field(None, description="SMILES notation")
    inchi: Optional[str] = Field(None, description="InChI identifier")
    inchi_key: Optional[str] = Field(None, description="InChI Key")
    iupac_name: Optional[str] = Field(None, description="IUPAC name")
    cas_number: Optional[str] = Field(None, description="CAS Registry Number")
    monoisotopic_weight: Optional[float] = Field(None, description="Monoisotopic weight")
    average_mass: Optional[float] = Field(None, description="Average mass")


class Taxonomy(BaseModel):
    """Drug taxonomy classification"""
    kingdom: Optional[str] = Field(None, description="Kingdom classification")
    superclass: Optional[str] = Field(None, description="Superclass")
    drug_class: Optional[str] = Field(None, description="Class")
    subclass: Optional[str] = Field(None, description="Subclass")
    direct_parent: Optional[str] = Field(None, description="Direct parent")
    alternative_parents: Optional[List[str]] = Field(default_factory=list, description="Alternative parents")


class ExternalIdentifier(BaseModel):
    """External database identifiers"""
    database: str = Field(..., description="Database name (e.g., PubChem, ChEMBL, KEGG)")
    identifier: str = Field(..., description="ID in that database")
    url: Optional[HttpUrl] = Field(None, description="Direct link to resource")


class Patent(BaseModel):
    """Patent information"""
    patent_number: str = Field(..., description="Patent number")
    country: str = Field(..., description="Country code")
    approved: Optional[datetime] = Field(None, description="Approval date")
    expires: Optional[datetime] = Field(None, description="Expiration date")
    pediatric_extension: Optional[bool] = Field(None, description="Has pediatric extension")


class ATCCode(BaseModel):
    """Anatomical Therapeutic Chemical Classification"""
    code: str = Field(..., description="ATC code")
    level: str = Field(..., description="ATC level description")


class Interaction(BaseModel):
    """Drug-drug interaction"""
    drug_name: str = Field(..., description="Interacting drug name")
    drugbank_id: Optional[str] = Field(None, description="DrugBank ID of interacting drug")
    description: str = Field(..., description="Interaction description")
    severity: Optional[str] = Field(None, description="Severity level (major, moderate, minor)")


class FoodInteraction(BaseModel):
    """Drug-food interaction"""
    food: str = Field(..., description="Food or nutrient")
    description: str = Field(..., description="Interaction description")


class Target(BaseModel):
    """Biological target (protein, enzyme, receptor)"""
    target_id: str = Field(..., description="Target ID")
    name: str = Field(..., description="Target name")
    organism: str = Field(..., description="Organism")
    action: Optional[str] = Field(None, description="Type of action (inhibitor, agonist, etc.)")
    gene_name: Optional[str] = Field(None, description="Gene name")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")
    pharmacological_action: Optional[bool] = Field(None, description="Is pharmacologically active")


class Enzyme(BaseModel):
    """Enzyme involved in drug metabolism"""
    enzyme_id: str = Field(..., description="Enzyme ID")
    name: str = Field(..., description="Enzyme name")
    organism: str = Field(..., description="Organism")
    action: Optional[str] = Field(None, description="Metabolic action")
    gene_name: Optional[str] = Field(None, description="Gene name")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")


class Carrier(BaseModel):
    """Carrier protein"""
    carrier_id: str = Field(..., description="Carrier ID")
    name: str = Field(..., description="Carrier name")
    organism: str = Field(..., description="Organism")
    gene_name: Optional[str] = Field(None, description="Gene name")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")


class Transporter(BaseModel):
    """Transporter protein"""
    transporter_id: str = Field(..., description="Transporter ID")
    name: str = Field(..., description="Transporter name")
    organism: str = Field(..., description="Organism")
    action: Optional[str] = Field(None, description="Transport action")
    gene_name: Optional[str] = Field(None, description="Gene name")
    uniprot_id: Optional[str] = Field(None, description="UniProt ID")


class Pharmacodynamics(BaseModel):
    """Pharmacodynamic properties"""
    mechanism_of_action: Optional[str] = Field(None, description="Detailed mechanism of action")
    pharmacodynamics: Optional[str] = Field(None, description="Pharmacodynamic description")
    onset_of_action: Optional[str] = Field(None, description="Time to onset")
    duration_of_action: Optional[str] = Field(None, description="Duration of effect")
    peak_effect: Optional[str] = Field(None, description="Time to peak effect")


class Pharmacokinetics(BaseModel):
    """Pharmacokinetic properties"""
    absorption: Optional[str] = Field(None, description="Absorption characteristics")
    distribution: Optional[str] = Field(None, description="Distribution characteristics")
    volume_of_distribution: Optional[str] = Field(None, description="Volume of distribution")
    protein_binding: Optional[str] = Field(None, description="Protein binding percentage")
    metabolism: Optional[str] = Field(None, description="Metabolism description")
    route_of_elimination: Optional[str] = Field(None, description="Route of elimination")
    half_life: Optional[str] = Field(None, description="Elimination half-life")
    clearance: Optional[str] = Field(None, description="Clearance rate")
    bioavailability: Optional[str] = Field(None, description="Bioavailability")


class Dosage(BaseModel):
    """Dosage information"""
    form: str = Field(..., description="Dosage form (tablet, capsule, injection, etc.)")
    route: RouteOfAdministration = Field(..., description="Route of administration")
    strength: str = Field(..., description="Strength/concentration")
    dosage_instructions: Optional[str] = Field(None, description="Detailed dosing instructions")


class ClinicalTrial(BaseModel):
    """Clinical trial information"""
    trial_id: str = Field(..., description="Trial ID (e.g., NCT number)")
    title: str = Field(..., description="Trial title")
    phase: Optional[str] = Field(None, description="Trial phase")
    status: Optional[str] = Field(None, description="Trial status")
    url: Optional[HttpUrl] = Field(None, description="Link to trial information")


class Manufacturer(BaseModel):
    """Drug manufacturer information"""
    name: str = Field(..., description="Manufacturer name")
    country: Optional[str] = Field(None, description="Country")
    url: Optional[str] = Field(None, description="Company website")


class Contraindication(BaseModel):
    """Contraindication information"""
    condition: str = Field(..., description="Contraindicated condition")
    severity: Optional[str] = Field(None, description="Severity (absolute, relative)")
    description: Optional[str] = Field(None, description="Detailed description")


class AdverseReaction(BaseModel):
    """Adverse drug reaction"""
    reaction: str = Field(..., description="Adverse reaction")
    frequency: Optional[str] = Field(None, description="Frequency (common, rare, etc.)")
    severity: Optional[str] = Field(None, description="Severity level")


class MedicineInfo(BaseModel):
    """
    Comprehensive medicine information model based on DrugBank structure.
    Contains all relevant pharmaceutical, chemical, and clinical data.
    """

    # Basic Information
    drugbank_id: Optional[str] = Field(None, description="DrugBank accession ID")
    name: str = Field(..., description="Primary drug name")
    synonyms: List[str] = Field(default_factory=list, description="Alternative names and brand names")
    description: Optional[str] = Field(None, description="Comprehensive drug description")

    # Classification
    drug_type: Optional[DrugType] = Field(None, description="Type of drug")
    groups: List[DrugGroup] = Field(default_factory=list, description="Drug approval groups")
    categories: List[str] = Field(default_factory=list, description="Therapeutic categories")
    atc_codes: List[ATCCode] = Field(default_factory=list, description="ATC classification codes")
    taxonomy: Optional[Taxonomy] = Field(None, description="Chemical taxonomy")

    # Chemical Properties
    chemical_properties: Optional[ChemicalProperties] = Field(None, description="Chemical properties")

    # Indications and Usage
    indication: Optional[str] = Field(None, description="Approved indications")
    off_label_uses: Optional[List[str]] = Field(default_factory=list, description="Off-label uses")

    # Pharmacology
    pharmacodynamics: Optional[Pharmacodynamics] = Field(None, description="Pharmacodynamic properties")
    pharmacokinetics: Optional[Pharmacokinetics] = Field(None, description="Pharmacokinetic properties")

    # Molecular Interactions
    targets: List[Target] = Field(default_factory=list, description="Biological targets")
    enzymes: List[Enzyme] = Field(default_factory=list, description="Metabolizing enzymes")
    carriers: List[Carrier] = Field(default_factory=list, description="Carrier proteins")
    transporters: List[Transporter] = Field(default_factory=list, description="Transporter proteins")

    # Interactions
    drug_interactions: List[Interaction] = Field(default_factory=list, description="Drug-drug interactions")
    food_interactions: List[FoodInteraction] = Field(default_factory=list, description="Drug-food interactions")

    # Safety Information
    contraindications: List[Contraindication] = Field(default_factory=list, description="Contraindications")
    warnings: Optional[str] = Field(None, description="Warnings and precautions")
    adverse_reactions: List[AdverseReaction] = Field(default_factory=list, description="Adverse reactions")
    black_box_warning: Optional[str] = Field(None, description="FDA black box warning")
    pregnancy_category: Optional[str] = Field(None, description="Pregnancy category")
    lactation: Optional[str] = Field(None, description="Lactation information")

    # Dosage and Administration
    dosages: List[Dosage] = Field(default_factory=list, description="Available dosage forms")
    administration: Optional[str] = Field(None, description="Administration instructions")
    overdose: Optional[str] = Field(None, description="Overdose information")

    # Regulatory and Commercial
    approval_date: Optional[datetime] = Field(None, description="FDA approval date")
    patents: List[Patent] = Field(default_factory=list, description="Patent information")
    manufacturers: List[Manufacturer] = Field(default_factory=list, description="Manufacturers")
    pricing: Optional[Dict[str, str]] = Field(None, description="Pricing information by country")

    # External References
    external_identifiers: List[ExternalIdentifier] = Field(default_factory=list, description="External database IDs")
    clinical_trials: List[ClinicalTrial] = Field(default_factory=list, description="Associated clinical trials")
    literature_references: Optional[List[str]] = Field(default_factory=list, description="PubMed IDs and references")

    # Additional Information
    toxicity: Optional[str] = Field(None, description="Toxicity information")
    affected_organisms: Optional[List[str]] = Field(default_factory=list, description="Affected organisms")
    synthesis_reference: Optional[str] = Field(None, description="Chemical synthesis information")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "drugbank_id": "DB00316",
                "name": "Acetaminophen",
                "synonyms": ["Paracetamol", "Tylenol", "Panadol"],
                "description": "Acetaminophen is a non-opioid, non-salicylate analgesic and antipyretic agent.",
                "drug_type": "small_molecule",
                "groups": ["approved"],
                "categories": ["Analgesics", "Antipyretics"],
                "indication": "For the relief of minor aches and pains and reduction of fever.",
                "pharmacodynamics": {
                    "mechanism_of_action": "Inhibits prostaglandin synthesis in the CNS"
                },
                "chemical_properties": {
                    "molecular_formula": "C8H9NO2",
                    "molecular_weight": 151.163,
                    "cas_number": "103-90-2"
                }
            }
        }
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python drugbank_medicine.py <medicine_name>")
        print("Example: python drugbank_medicine.py Aspirin")
        sys.exit(1)

    medicine_name = " ".join(sys.argv[1:])

    # Configure the model for structured output
    config = ModelConfig(
        model="sonar-pro",
        max_tokens=4096,
        temperature=0.7,
        top_p=0.9,
        stream=False,
        search_mode="web"
    )

    # Create input with the medicine query and response model
    model_input = ModelInput(
        user_prompt=f"Provide comprehensive pharmaceutical information about {medicine_name}. Include drug type, approval status, chemical properties, indications, pharmacodynamics, side effects, dosage forms, and any relevant clinical data.",
        response_model=MedicineInfo
    )

    # Initialize client and generate content
    try:
        client = PerplexityClient()
        response = client.generate_content(model_input, config)

        response_content = response.choices[0].message.content

        # Attempt to fix truncated JSON if needed
        import json as json_module
        import re
        try:
            medicine = MedicineInfo.model_validate_json(response_content)
        except json_module.JSONDecodeError as e:
            # If JSON is truncated, try to fix it by closing incomplete structures
            print("⚠️  Response was truncated, attempting to repair JSON...")

            # Remove incomplete final string and trailing characters
            # Find the last complete quoted string and remove anything after it if truncated
            response_content = response_content.rstrip()

            # If it ends with an incomplete string, remove it
            if '"' in response_content[-10:]:
                # Find the last complete key-value pair
                last_quote = response_content.rfind('":', 0, -5)
                if last_quote > 0:
                    # Find the next quote after the colon
                    next_quote = response_content.find('"', last_quote + 2)
                    if next_quote > 0:
                        # Check if this string is complete
                        try:
                            # Try to find the closing quote
                            close_quote = response_content.find('"', next_quote + 1)
                            if close_quote < 0 or close_quote > len(response_content) - 10:
                                # String is incomplete, truncate before it
                                response_content = response_content[:last_quote + 1]

                        except:
                            response_content = response_content[:last_quote + 1]

            # Clean up trailing comma or bracket
            response_content = response_content.rstrip(',')

            # Ensure proper closing
            if not response_content.endswith('}'):
                # Count braces to balance them
                open_braces = response_content.count('{') - response_content.count('}')
                response_content += '}' * (open_braces + 1)

            try:
                medicine = MedicineInfo.model_validate_json(response_content)
            except Exception:
                # If still failing, use minimal data to at least show something
                print("⚠️  Could not parse response, using fallback...")
                medicine = MedicineInfo(
                    name=medicine_name.title(),
                    indication="Unable to retrieve full information from API"
                )

        print(f"\nMedicine: {medicine.name}")
        print(f"Type: {medicine.drug_type}")
        print(f"Indication: {medicine.indication}")
        print(f"Drug Groups: {', '.join(medicine.groups)}")
    except (ValueError, Exception) as e:
        print(f"Error: {e}")
        sys.exit(1)
