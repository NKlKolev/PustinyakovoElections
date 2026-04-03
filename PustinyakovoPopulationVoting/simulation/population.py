import random
from typing import Dict, List

from config.constants import AGE_GROUPS, AGE_WEIGHTS
from models.region import RegionProfile
from models.voter import Voter
from simulation.utils import clip, sample_around_mean, weighted_random_choice


def derive_age_adjustments(age_group: str) -> Dict[str, float]:
    if age_group == "18-29":
        return {
            "traditionalism": -0.12,
            "progressive": 0.12,
            "regime_trust": -0.05,
            "opposition": 0.05,
            "volatility": 0.12,
            "turnout": -0.08,
            "campaign_interest": 0.02,
        }

    if age_group == "30-44":
        return {
            "traditionalism": -0.02,
            "progressive": 0.04,
            "regime_trust": -0.02,
            "opposition": 0.03,
            "volatility": 0.05,
            "turnout": 0.00,
            "campaign_interest": 0.03,
        }

    if age_group == "45-64":
        return {
            "traditionalism": 0.05,
            "progressive": -0.04,
            "regime_trust": 0.04,
            "opposition": -0.02,
            "volatility": -0.04,
            "turnout": 0.05,
            "campaign_interest": 0.02,
        }

    return {
        "traditionalism": 0.12,
        "progressive": -0.10,
        "regime_trust": 0.08,
        "opposition": -0.05,
        "volatility": -0.10,
        "turnout": 0.08,
        "campaign_interest": 0.00,
    }


def generate_voter(voter_id: int, region_profile: RegionProfile) -> Voter:
    age_group = weighted_random_choice(AGE_GROUPS, AGE_WEIGHTS)
    age_adjustments = derive_age_adjustments(age_group)

    religious_group = "muslim" if random.random() < region_profile.muslim_share else "majority"

    education = sample_around_mean(region_profile.education_mean)
    income = sample_around_mean(region_profile.income_mean)
    urbanity = sample_around_mean(region_profile.urbanity_mean)

    traditionalism = sample_around_mean(
        region_profile.traditionalism_mean + age_adjustments["traditionalism"]
    )
    progressive_inclination = sample_around_mean(
        region_profile.progressive_mean + age_adjustments["progressive"]
    )
    regime_trust = sample_around_mean(
        region_profile.regime_trust_mean + age_adjustments["regime_trust"]
    )
    opposition_sentiment = sample_around_mean(
        region_profile.opposition_mean + age_adjustments["opposition"]
    )
    volatility = sample_around_mean(
        region_profile.volatility_mean + age_adjustments["volatility"]
    )

    patronage_dependence = sample_around_mean(region_profile.patronage_mean)
    local_identity = sample_around_mean(region_profile.local_identity_mean)

    economic_satisfaction = clip(random.gauss(0.52 + (income - 0.5) * 0.12, 0.10))
    anger = clip(random.gauss(0.32 + (1 - regime_trust) * 0.10, 0.10))
    security_concern = clip(random.gauss(0.45 + traditionalism * 0.10, 0.10))
    campaign_interest = clip(
        random.gauss(0.50 + education * 0.08 + age_adjustments["campaign_interest"], 0.10)
    )

    turnout_baseline = clip(
        region_profile.turnout_mean + age_adjustments["turnout"] + random.gauss(0.0, 0.06)
    )

    return Voter(
        voter_id=voter_id,
        region=region_profile.name,
        age_group=age_group,
        religious_group=religious_group,
        education=education,
        income=income,
        urbanity=urbanity,
        traditionalism=traditionalism,
        progressive_inclination=progressive_inclination,
        regime_trust=regime_trust,
        opposition_sentiment=opposition_sentiment,
        volatility=volatility,
        patronage_dependence=patronage_dependence,
        local_identity=local_identity,
        economic_satisfaction=economic_satisfaction,
        anger=anger,
        security_concern=security_concern,
        campaign_interest=campaign_interest,
        current_preference="",
        previous_preference="",
        party_loyalty=clip(random.gauss(0.45, 0.12)),
        turnout_baseline=turnout_baseline,
        turnout_probability=turnout_baseline,
        did_vote=False,
        final_vote="",
        vote_explanation="",
    )


def generate_population(region_profiles: Dict[str, RegionProfile]) -> List[Voter]:
    voters: List[Voter] = []
    voter_id = 1

    for region_name, region_profile in region_profiles.items():
        for _ in range(region_profile.agents):
            voters.append(generate_voter(voter_id, region_profile))
            voter_id += 1

    return voters