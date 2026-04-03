from dataclasses import dataclass


@dataclass
class Voter:
    voter_id: int

    # basic identity
    region: str
    age_group: str
    religious_group: str

    # socio-economic
    education: float
    income: float
    urbanity: float

    # political predispositions
    traditionalism: float
    progressive_inclination: float
    regime_trust: float
    opposition_sentiment: float
    volatility: float
    patronage_dependence: float
    local_identity: float

    # dynamic state (will change later)
    economic_satisfaction: float
    anger: float
    security_concern: float
    campaign_interest: float

    # electoral state
    current_preference: str
    previous_preference: str
    party_loyalty: float

    turnout_baseline: float
    turnout_probability: float
    did_vote: bool
    final_vote: str
    vote_explanation: str