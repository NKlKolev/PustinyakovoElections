from dataclasses import dataclass


@dataclass
class RegionProfile:
    name: str
    population: int
    agents: int

    education_mean: float
    income_mean: float
    urbanity_mean: float

    turnout_mean: float
    volatility_mean: float

    traditionalism_mean: float
    progressive_mean: float

    regime_trust_mean: float
    opposition_mean: float

    patronage_mean: float
    local_identity_mean: float

    muslim_share: float