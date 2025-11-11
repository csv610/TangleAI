"""
Medicine Information Lookup System
Fetches comprehensive medicine information from various sources and returns structured MedicineInfo data
"""

from medicine_info_model import (
    MedicineInfo, ChemicalProperties, Pharmacodynamics, Pharmacokinetics,
    DrugType, DrugGroup, RouteOfAdministration, ATCCode, Target, Enzyme,
    Interaction, FoodInteraction, Dosage, ExternalIdentifier, AdverseReaction,
    Contraindication, Manufacturer, Patent, ClinicalTrial, Taxonomy, Carrier, Transporter
)
from typing import Optional, Dict, Any, List
import requests
import json
from datetime import datetime


class MedicineLookupService:
    """Service to lookup medicine information from multiple sources"""
    
    def __init__(self):
        self.sources = {
            'openfda': 'https://api.fda.gov/drug/',
            'rxnav': 'https://rxnav.nlm.nih.gov/REST/',
            'pubchem': 'https://pubchem.ncbi.nlm.nih.gov/rest/pug/',
            'drugbank': 'https://go.drugbank.com/drugs/'  # Note: Requires API key for full access
        }
    
    def lookup_medicine(self, medicine_name: str) -> MedicineInfo:
        """
        Main method to lookup medicine information by name
        
        Args:
            medicine_name: Name of the medicine (brand name or generic name)
            
        Returns:
            MedicineInfo: Comprehensive medicine information
        """
        print(f"Looking up information for: {medicine_name}")
        
        # Initialize data containers
        basic_info = self._fetch_basic_info(medicine_name)
        chemical_info = self._fetch_chemical_info(medicine_name)
        pharmacology_info = self._fetch_pharmacology_info(medicine_name)
        safety_info = self._fetch_safety_info(medicine_name)
        interaction_info = self._fetch_interaction_info(medicine_name)
        clinical_info = self._fetch_clinical_info(medicine_name)
        
        # Build MedicineInfo object
        medicine_info = self._build_medicine_info(
            medicine_name,
            basic_info,
            chemical_info,
            pharmacology_info,
            safety_info,
            interaction_info,
            clinical_info
        )
        
        return medicine_info
    
    def _fetch_basic_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch basic drug information"""
        print(f"  → Fetching basic information...")
        
        # Try RxNorm API for basic info
        try:
            url = f"{self.sources['rxnav']}drugs.json?name={medicine_name}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'found': True,
                    'data': data,
                    'source': 'rxnav'
                }
        except Exception as e:
            print(f"    Warning: RxNorm lookup failed - {str(e)}")
        
        return {'found': False, 'data': {}, 'source': None}
    
    def _fetch_chemical_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch chemical properties from PubChem"""
        print(f"  → Fetching chemical properties...")
        
        try:
            # Search PubChem by name
            search_url = f"{self.sources['pubchem']}compound/name/{medicine_name}/property/MolecularFormula,MolecularWeight,IUPACName,InChI,InChIKey,CanonicalSMILES/JSON"
            response = requests.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'found': True,
                    'data': data,
                    'source': 'pubchem'
                }
        except Exception as e:
            print(f"    Warning: PubChem lookup failed - {str(e)}")
        
        return {'found': False, 'data': {}, 'source': None}
    
    def _fetch_pharmacology_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch pharmacology information"""
        print(f"  → Fetching pharmacology information...")
        
        # This would typically call DrugBank API or similar
        # For demo purposes, returning placeholder structure
        return {
            'found': False,
            'data': {},
            'source': None,
            'note': 'Requires DrugBank API access'
        }
    
    def _fetch_safety_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch safety and adverse event information from OpenFDA"""
        print(f"  → Fetching safety information...")
        
        try:
            # Query OpenFDA adverse events
            url = f"{self.sources['openfda']}label.json?search=openfda.brand_name:\"{medicine_name}\"+openfda.generic_name:\"{medicine_name}\"&limit=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'found': True,
                    'data': data,
                    'source': 'openfda'
                }
        except Exception as e:
            print(f"    Warning: OpenFDA lookup failed - {str(e)}")
        
        return {'found': False, 'data': {}, 'source': None}
    
    def _fetch_interaction_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch drug interaction information"""
        print(f"  → Fetching interaction information...")
        
        try:
            # Try RxNorm interaction API
            # First get RxCUI
            url = f"{self.sources['rxnav']}rxcui.json?name={medicine_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'idGroup' in data and 'rxnormId' in data['idGroup']:
                    rxcui = data['idGroup']['rxnormId'][0]
                    
                    # Get interactions
                    interaction_url = f"{self.sources['rxnav']}interaction/interaction.json?rxcui={rxcui}"
                    interaction_response = requests.get(interaction_url, timeout=10)
                    
                    if interaction_response.status_code == 200:
                        return {
                            'found': True,
                            'data': interaction_response.json(),
                            'source': 'rxnav'
                        }
        except Exception as e:
            print(f"    Warning: Interaction lookup failed - {str(e)}")
        
        return {'found': False, 'data': {}, 'source': None}
    
    def _fetch_clinical_info(self, medicine_name: str) -> Dict[str, Any]:
        """Fetch clinical trial and usage information"""
        print(f"  → Fetching clinical information...")
        
        # This would typically call ClinicalTrials.gov API
        return {
            'found': False,
            'data': {},
            'source': None,
            'note': 'Requires ClinicalTrials.gov API integration'
        }
    
    def _build_medicine_info(
        self,
        medicine_name: str,
        basic_info: Dict,
        chemical_info: Dict,
        pharmacology_info: Dict,
        safety_info: Dict,
        interaction_info: Dict,
        clinical_info: Dict
    ) -> MedicineInfo:
        """Build MedicineInfo object from collected data"""
        
        print(f"  → Building MedicineInfo object...")
        
        # Extract chemical properties
        chemical_properties = None
        if chemical_info['found'] and 'PropertyTable' in chemical_info['data']:
            props = chemical_info['data']['PropertyTable']['Properties'][0]
            chemical_properties = ChemicalProperties(
                molecular_formula=props.get('MolecularFormula'),
                molecular_weight=props.get('MolecularWeight'),
                smiles=props.get('CanonicalSMILES'),
                inchi=props.get('InChI'),
                inchi_key=props.get('InChIKey'),
                iupac_name=props.get('IUPACName')
            )
        
        # Extract external identifiers
        external_identifiers = []
        if chemical_info['found'] and 'PropertyTable' in chemical_info['data']:
            cid = chemical_info['data']['PropertyTable']['Properties'][0].get('CID')
            if cid:
                external_identifiers.append(
                    ExternalIdentifier(
                        database="PubChem",
                        identifier=str(cid),
                        url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
                    )
                )
        
        # Extract synonyms and description from FDA data
        synonyms = []
        description = None
        indication = None
        warnings = None
        adverse_reactions_list = []
        contraindications_list = []
        dosages_list = []
        drug_interactions_list = []
        
        if safety_info['found'] and 'results' in safety_info['data']:
            result = safety_info['data']['results'][0]
            
            # Get brand and generic names
            if 'openfda' in result:
                openfda = result['openfda']
                if 'brand_name' in openfda:
                    synonyms.extend(openfda['brand_name'])
                if 'generic_name' in openfda:
                    synonyms.extend(openfda['generic_name'])
            
            # Get description and indications
            if 'description' in result:
                description = ' '.join(result['description']) if isinstance(result['description'], list) else result['description']
            
            if 'indications_and_usage' in result:
                indication = ' '.join(result['indications_and_usage']) if isinstance(result['indications_and_usage'], list) else result['indications_and_usage']
            
            # Get warnings
            if 'warnings' in result:
                warnings = ' '.join(result['warnings']) if isinstance(result['warnings'], list) else result['warnings']
            
            # Get adverse reactions
            if 'adverse_reactions' in result:
                adverse_text = ' '.join(result['adverse_reactions']) if isinstance(result['adverse_reactions'], list) else result['adverse_reactions']
                # Parse common adverse reactions (simplified)
                for reaction in ['nausea', 'headache', 'dizziness', 'fatigue', 'diarrhea']:
                    if reaction.lower() in adverse_text.lower():
                        adverse_reactions_list.append(
                            AdverseReaction(
                                reaction=reaction.capitalize(),
                                frequency="Common"
                            )
                        )
            
            # Get contraindications
            if 'contraindications' in result:
                contra_text = ' '.join(result['contraindications']) if isinstance(result['contraindications'], list) else result['contraindications']
                contraindications_list.append(
                    Contraindication(
                        condition="As listed in prescribing information",
                        description=contra_text[:500]  # Truncate for brevity
                    )
                )
            
            # Get dosage information
            if 'dosage_and_administration' in result:
                dosage_text = ' '.join(result['dosage_and_administration']) if isinstance(result['dosage_and_administration'], list) else result['dosage_and_administration']
                # Try to parse route
                route = RouteOfAdministration.ORAL  # Default
                if 'intravenous' in dosage_text.lower():
                    route = RouteOfAdministration.INTRAVENOUS
                elif 'topical' in dosage_text.lower():
                    route = RouteOfAdministration.TOPICAL
                
                dosages_list.append(
                    Dosage(
                        form="As prescribed",
                        route=route,
                        strength="See prescribing information",
                        dosage_instructions=dosage_text[:500]
                    )
                )
        
        # Extract drug interactions
        if interaction_info['found']:
            if 'interactionTypeGroup' in interaction_info['data']:
                for group in interaction_info['data']['interactionTypeGroup']:
                    if 'interactionType' in group:
                        for interaction_pair in group['interactionType']:
                            if 'interactionPair' in interaction_pair:
                                for pair in interaction_pair['interactionPair']:
                                    drug_interactions_list.append(
                                        Interaction(
                                            drug_name=pair.get('interactionConcept', [{}])[0].get('minConceptItem', {}).get('name', 'Unknown'),
                                            description=pair.get('description', 'No description available'),
                                            severity=pair.get('severity', 'Unknown')
                                        )
                                    )
        
        # Build final MedicineInfo object
        medicine_info = MedicineInfo(
            name=medicine_name.title(),
            synonyms=list(set(synonyms)),  # Remove duplicates
            description=description,
            drug_type=DrugType.SMALL_MOLECULE,  # Default assumption
            groups=[DrugGroup.APPROVED] if safety_info['found'] else [],
            indication=indication,
            chemical_properties=chemical_properties,
            external_identifiers=external_identifiers,
            warnings=warnings,
            adverse_reactions=adverse_reactions_list,
            contraindications=contraindications_list,
            dosages=dosages_list,
            drug_interactions=drug_interactions_list
        )
        
        return medicine_info


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
        print(f"\n📋 Synonyms: {', '.join(medicine_info.synonyms[:5])}")
    
    if medicine_info.description:
        print(f"\n📝 Description:\n{medicine_info.description[:300]}...")
    
    if medicine_info.indication:
        print(f"\n💊 Indications:\n{medicine_info.indication[:300]}...")
    
    if medicine_info.chemical_properties:
        print(f"\n🧪 Chemical Properties:")
        cp = medicine_info.chemical_properties
        if cp.molecular_formula:
            print(f"   - Formula: {cp.molecular_formula}")
        if cp.molecular_weight:
            print(f"   - Molecular Weight: {cp.molecular_weight} g/mol")
        if cp.iupac_name:
            print(f"   - IUPAC Name: {cp.iupac_name[:80]}...")
    
    if medicine_info.warnings:
        print(f"\n⚠️  Warnings:\n{medicine_info.warnings[:300]}...")
    
    if medicine_info.adverse_reactions:
        print(f"\n🔴 Adverse Reactions:")
        for reaction in medicine_info.adverse_reactions[:5]:
            print(f"   - {reaction.reaction} ({reaction.frequency})")
    
    if medicine_info.drug_interactions:
        print(f"\n🔄 Drug Interactions ({len(medicine_info.drug_interactions)} found):")
        for interaction in medicine_info.drug_interactions[:3]:
            print(f"   - {interaction.drug_name}: {interaction.description[:100]}...")
    
    if medicine_info.dosages:
        print(f"\n💉 Dosage Information:")
        for dosage in medicine_info.dosages[:2]:
            print(f"   - Route: {dosage.route.value}, Form: {dosage.form}")
    
    if medicine_info.external_identifiers:
        print(f"\n🔗 External References:")
        for ext_id in medicine_info.external_identifiers:
            print(f"   - {ext_id.database}: {ext_id.identifier}")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    # Example usage
    import sys
    
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
        
        print(f"\n✅ Full information saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
