from dataclasses import dataclass
from typing import Dict


@dataclass
class PartyProfile:
    name: str

    economic_position: float
    cultural_position: float
    regime_status: float

    urban_appeal: float
    working_class_appeal: float
    traditionalist_appeal: float
    progressive_appeal: float
    minority_muslim_appeal: float

    machine_power: float
    leader_strength: float

    stability_reputation: float
    change_reputation: float
    security_reputation: float
    economic_competence: float

    regional_affinity: Dict[str, float]