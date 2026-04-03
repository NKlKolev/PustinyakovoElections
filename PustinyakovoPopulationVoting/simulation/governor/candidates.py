import random

from config.parties import PARTY_PROFILES


DEFAULT_GOVERNOR_TUNING = {
    "regional_affinity_weight": 0.30,
    "economy_weight": 0.15,
    "security_weight": 0.15,
    "trust_weight": 0.15,
    "identity_weight": 0.10,
    "minority_weight": 0.05,
    "machine_weight": 0.10,
    "candidate_randomness": 0.12,
    "charisma_bonus": 0.00,
    "competence_bonus": 0.00,
    "machine_bonus": 0.00,
    "anti_system_bonus": 0.00,
    "incumbent_bonus": 0.00,
}



def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def merge_governor_tuning(tuning: dict | None = None) -> dict:
    merged = DEFAULT_GOVERNOR_TUNING.copy()
    if tuning:
        merged.update(tuning)
    return merged



def _get_region_value(region_profile, *possible_names: str, default: float = 0.50) -> float:
    for name in possible_names:
        if hasattr(region_profile, name):
            return _clip(float(getattr(region_profile, name)))
    return default



def build_region_context(region_profile) -> dict:
    """
    Extracts region-level political context from the region profile.
    The helper is intentionally defensive so it works even if the exact
    REGION_PROFILES schema evolves later.
    """
    return {
        "economy": _get_region_value(
            region_profile,
            "economic_satisfaction_base",
            "economy_base",
            "economic_base",
            default=0.50,
        ),
        "security": _get_region_value(
            region_profile,
            "security_concern_base",
            "security_base",
            default=0.50,
        ),
        "trust": _get_region_value(
            region_profile,
            "regime_trust_base",
            "trust_base",
            default=0.50,
        ),
        "identity": _get_region_value(
            region_profile,
            "local_identity_base",
            "identity_base",
            default=0.50,
        ),
        "patronage": _get_region_value(
            region_profile,
            "patronage_dependence_base",
            "patronage_base",
            default=0.50,
        ),
        "minority": _get_region_value(
            region_profile,
            "minority_presence_base",
            "minority_base",
            default=0.30,
        ),
        "anger": _get_region_value(
            region_profile,
            "anger_base",
            default=0.50,
        ),
        "campaign_interest": _get_region_value(
            region_profile,
            "campaign_interest_base",
            default=0.50,
        ),
    }



def compute_party_region_fit(party_name: str, region_name: str, region_profile, tuning: dict | None = None) -> dict:
    profile = PARTY_PROFILES[party_name]
    context = build_region_context(region_profile)
    tuning = merge_governor_tuning(tuning)

    regional_affinity = profile.regional_affinity.get(region_name, 0.50)
    economy_fit = 1.0 - abs(profile.economic_competence - context["economy"])
    security_fit = 1.0 - abs(profile.security_reputation - context["security"])
    trust_fit = 1.0 - abs(profile.change_reputation - (1.0 - context["trust"]))
    identity_fit = 1.0 - abs(profile.progressive_appeal - (1.0 - context["identity"]))
    minority_fit = 1.0 - abs(profile.minority_muslim_appeal - context["minority"])

    machine_fit = 0.50
    if party_name in {"ПКП- Ново Начало", "ГЕРП", "ДПС"}:
        machine_fit = 0.55 + context["patronage"] * 0.40 + tuning["machine_bonus"]
    elif party_name in {"Демократично Пустиняково", "Пустиняшка Промяна"}:
        machine_fit = 0.45 - context["patronage"] * 0.20
    else:
        machine_fit = 0.45 + context["patronage"] * 0.10

    if party_name == "Израждане":
        machine_fit += tuning["anti_system_bonus"]

    if party_name in {"ПКП- Ново Начало", "ГЕРП", "ДПС", "СХДС"}:
        machine_fit += tuning["incumbent_bonus"]

    machine_fit = _clip(machine_fit)

    overall_fit = _clip(
        regional_affinity * tuning["regional_affinity_weight"]
        + economy_fit * tuning["economy_weight"]
        + security_fit * tuning["security_weight"]
        + trust_fit * tuning["trust_weight"]
        + identity_fit * tuning["identity_weight"]
        + minority_fit * tuning["minority_weight"]
        + machine_fit * tuning["machine_weight"],
    )

    return {
        "regional_affinity": round(regional_affinity, 3),
        "economy_fit": round(_clip(economy_fit), 3),
        "security_fit": round(_clip(security_fit), 3),
        "trust_fit": round(_clip(trust_fit), 3),
        "identity_fit": round(_clip(identity_fit), 3),
        "minority_fit": round(_clip(minority_fit), 3),
        "machine_fit": round(_clip(machine_fit), 3),
        "overall_fit": round(overall_fit, 3),
        "region_context": context,
    }



def generate_governor_candidates(region_profiles: dict, tuning: dict | None = None) -> dict:
    candidates = {}
    tuning = merge_governor_tuning(tuning)

    for region_name, region_profile in region_profiles.items():
        candidates[region_name] = []

        for party_name, party_profile in PARTY_PROFILES.items():
            fit = compute_party_region_fit(party_name, region_name, region_profile, tuning=tuning)

            randomness = tuning["candidate_randomness"]

            local_strength = _clip(
                random.uniform(0.35, 0.95) * (0.55 + randomness)
                + fit["overall_fit"] * (0.45 - randomness / 2)
            )
            charisma = _clip(
                random.uniform(0.30, 0.95) * 0.70
                + party_profile.leader_strength * 0.30
                + tuning["charisma_bonus"]
            )
            competence = _clip(
                random.uniform(0.35, 0.95) * 0.40
                + party_profile.economic_competence * 0.30
                + party_profile.security_reputation * 0.15
                + fit["regional_affinity"] * 0.15
                + tuning["competence_bonus"]
            )
            scandal_risk = _clip(
                random.uniform(0.05, 0.60) * (0.65 + randomness / 2)
                + (1.0 - party_profile.change_reputation) * 0.20
                + fit["machine_fit"] * 0.15
            )
            electability = _clip(
                local_strength * 0.30
                + charisma * 0.20
                + competence * 0.20
                + fit["overall_fit"] * 0.25
                + (1.0 - scandal_risk) * 0.05
            )

            candidates[region_name].append(
                {
                    "name": f"{party_name} кандидат",
                    "party": party_name,
                    "region": region_name,
                    "local_strength": round(local_strength, 3),
                    "charisma": round(charisma, 3),
                    "competence": round(competence, 3),
                    "scandal_risk": round(scandal_risk, 3),
                    "party_base": party_name,
                    "regional_affinity": fit["regional_affinity"],
                    "economy_fit": fit["economy_fit"],
                    "security_fit": fit["security_fit"],
                    "trust_fit": fit["trust_fit"],
                    "identity_fit": fit["identity_fit"],
                    "minority_fit": fit["minority_fit"],
                    "machine_fit": fit["machine_fit"],
                    "overall_fit": fit["overall_fit"],
                    "electability": round(electability, 3),
                    "region_context": fit["region_context"],
                    "tuning_snapshot": tuning.copy(),
                }
            )

    return candidates