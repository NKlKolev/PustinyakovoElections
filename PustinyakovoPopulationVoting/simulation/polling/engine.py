import random

from simulation.polling.indicators import (
    compute_national_indicators,
    compute_party_support,
    compute_regional_mood,
)

from simulation.polling.scenarios import (
    apply_polling_scenario,
    apply_polling_noise,
)



def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))



def build_governor_inputs_from_polling(voters) -> dict:
    """
    Builds region-level governor-election inputs from the current polling electorate.
    The values are different on every run, but remain anchored in the regional
    characteristics of the simulated voters.
    """
    regional_groups = {}

    for voter in voters:
        regional_groups.setdefault(voter.region, []).append(voter)

    governor_inputs = {}

    for region_name, region_voters in regional_groups.items():
        count = len(region_voters)
        if count == 0:
            continue

        avg_anger = sum(v.anger for v in region_voters) / count
        avg_economy = sum(v.economic_satisfaction for v in region_voters) / count
        avg_trust = sum(v.regime_trust for v in region_voters) / count
        avg_security = sum(v.security_concern for v in region_voters) / count
        avg_identity = sum(v.local_identity for v in region_voters) / count
        avg_patronage = sum(v.patronage_dependence for v in region_voters) / count
        avg_campaign_interest = sum(v.campaign_interest for v in region_voters) / count

        corruption_shock = _clip(
            avg_anger * 0.32
            + (1.0 - avg_trust) * 0.18
            + random.uniform(-0.05, 0.05),
            0.00,
            0.45,
        )

        economic_shock = _clip(
            (0.50 - avg_economy) * 0.35
            + random.uniform(-0.06, 0.06),
            -0.20,
            0.20,
        )

        trust_shock = _clip(
            (avg_trust - 0.50) * 0.40
            + random.uniform(-0.06, 0.06),
            -0.30,
            0.15,
        )

        security_shock = _clip(
            avg_security * 0.18
            + random.uniform(-0.04, 0.04),
            0.00,
            0.20,
        )

        identity_weight = _clip(
            avg_identity * 0.18
            + random.uniform(-0.03, 0.03),
            0.00,
            0.20,
        )

        machine_weight = _clip(
            avg_patronage * 0.16
            + random.uniform(-0.03, 0.03),
            0.00,
            0.20,
        )

        charisma_bonus = _clip(
            (avg_campaign_interest - 0.50) * 0.12
            + random.uniform(-0.03, 0.03),
            -0.05,
            0.10,
        )

        competence_bonus = _clip(
            avg_economy * 0.10
            + avg_trust * 0.06
            - 0.08
            + random.uniform(-0.03, 0.03),
            -0.05,
            0.15,
        )

        anti_system_bonus = _clip(
            avg_anger * 0.14
            + (1.0 - avg_trust) * 0.10
            + random.uniform(-0.03, 0.03),
            0.00,
            0.20,
        )

        incumbent_bonus = _clip(
            avg_trust * 0.18
            - avg_anger * 0.16
            + random.uniform(-0.04, 0.04),
            -0.15,
            0.15,
        )

        governor_inputs[region_name] = {
            "corruption_shock": round(corruption_shock, 3),
            "economic_shock": round(economic_shock, 3),
            "trust_shock": round(trust_shock, 3),
            "security_shock": round(security_shock, 3),
            "identity_weight": round(identity_weight, 3),
            "machine_weight": round(machine_weight, 3),
            "charisma_bonus": round(charisma_bonus, 3),
            "competence_bonus": round(competence_bonus, 3),
            "anti_system_bonus": round(anti_system_bonus, 3),
            "incumbent_bonus": round(incumbent_bonus, 3),
        }

    return governor_inputs



def run_polling(
    voters,
    corruption_shock=0.0,
    economic_shock=0.0,
    security_shock=0.0,
    trust_shock=0.0,
):
    # 1. Apply scenario shocks
    apply_polling_scenario(
        voters,
        corruption_shock=corruption_shock,
        economic_shock=economic_shock,
        security_shock=security_shock,
        trust_shock=trust_shock,
    )

    # 2. Add randomness
    apply_polling_noise(voters, intensity=0.02)

    # 3. Compute outputs
    return {
        "national": compute_national_indicators(voters),
        "party_support": compute_party_support(voters),
        "regions": compute_regional_mood(voters),
        "governor_inputs": build_governor_inputs_from_polling(voters),
    }
