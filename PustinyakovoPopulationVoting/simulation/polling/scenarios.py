import random


def apply_polling_scenario(
    voters: list,
    corruption_shock: float = 0.0,
    economic_shock: float = 0.0,
    security_shock: float = 0.0,
    trust_shock: float = 0.0,
    minorities_conflict: float = 0.0,
) -> None:
    for voter in voters:
        voter.anger = min(1.0, max(0.0, voter.anger + corruption_shock))
        voter.economic_satisfaction = min(1.0, max(0.0, voter.economic_satisfaction + economic_shock))
        voter.security_concern = min(1.0, max(0.0, voter.security_concern + security_shock))
        voter.regime_trust = min(1.0, max(0.0, voter.regime_trust + trust_shock))


def apply_polling_noise(voters: list, intensity: float = 0.02) -> None:
    for voter in voters:
        voter.anger = min(1.0, max(0.0, voter.anger + random.uniform(-intensity, intensity)))
        voter.economic_satisfaction = min(1.0, max(0.0, voter.economic_satisfaction + random.uniform(-intensity, intensity)))
        voter.security_concern = min(1.0, max(0.0, voter.security_concern + random.uniform(-intensity, intensity)))
        voter.regime_trust = min(1.0, max(0.0, voter.regime_trust + random.uniform(-intensity, intensity)))
        voter.campaign_interest = min(1.0, max(0.0, voter.campaign_interest + random.uniform(-intensity, intensity)))