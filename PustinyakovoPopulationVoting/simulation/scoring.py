import random
from typing import Dict

from config.constants import WEIGHTS
from models.party import PartyProfile
from models.voter import Voter
from simulation.utils import clip, softmax_choice


def get_cultural_fit(voter: Voter, party: PartyProfile) -> float:
    return (
        voter.traditionalism * party.traditionalist_appeal
        + voter.progressive_inclination * party.progressive_appeal
    ) / 2


def get_regime_fit(voter: Voter, party: PartyProfile) -> float:
    return (
        voter.regime_trust * party.regime_status
        + voter.opposition_sentiment * (1 - party.regime_status)
    )


def get_urban_class_fit(voter: Voter, party: PartyProfile) -> float:
    working_class_signal = 1 - voter.income
    return (
        voter.urbanity * party.urban_appeal
        + voter.education * party.urban_appeal
        + working_class_signal * party.working_class_appeal
    ) / 3


def get_minority_fit(voter: Voter, party: PartyProfile) -> float:
    if voter.religious_group == "muslim":
        return clip(party.minority_muslim_appeal * (0.70 + 0.30 * voter.local_identity))
    return 0.0


def get_leader_effect(voter: Voter, party: PartyProfile) -> float:
    return party.leader_strength * voter.campaign_interest


def get_change_vs_stability_fit(voter: Voter, party: PartyProfile) -> float:
    change_demand = (voter.anger + (1 - voter.economic_satisfaction)) / 2
    return (
        change_demand * party.change_reputation
        + (1 - change_demand) * party.stability_reputation
    )


def get_loyalty_effect(voter: Voter, party: PartyProfile) -> float:
    if voter.current_preference == party.name:
        return voter.party_loyalty
    return 0.0


def score_party(voter: Voter, party: PartyProfile) -> float:
    regional_affinity = party.regional_affinity[voter.region]
    cultural_fit = get_cultural_fit(voter, party)
    regime_fit = get_regime_fit(voter, party)
    urban_class_fit = get_urban_class_fit(voter, party)
    minority_fit = get_minority_fit(voter, party)
    leader_effect = get_leader_effect(voter, party)
    change_vs_stability_fit = get_change_vs_stability_fit(voter, party)
    loyalty_effect = get_loyalty_effect(voter, party)
    noise = random.uniform(-0.10, 0.10)

    score = (
        WEIGHTS["regional_affinity"] * regional_affinity
        + WEIGHTS["cultural_fit"] * cultural_fit
        + WEIGHTS["regime_fit"] * regime_fit
        + WEIGHTS["urban_class_fit"] * urban_class_fit
        + WEIGHTS["minority_fit"] * minority_fit
        + WEIGHTS["leader_effect"] * leader_effect
        + WEIGHTS["change_vs_stability_fit"] * change_vs_stability_fit
        + WEIGHTS["loyalty_effect"] * loyalty_effect
        + WEIGHTS["noise"] * noise
    )

    return score


def assign_initial_preference(voter: Voter, parties: Dict[str, PartyProfile]) -> None:
    scores = {}

    for party_name, party in parties.items():
        scores[party_name] = score_party(voter, party)

    chosen_party, _ = softmax_choice(scores)
    voter.current_preference = chosen_party
    voter.previous_preference = chosen_party
def update_preferences_after_campaign(voters: list[Voter], parties: Dict[str, PartyProfile]) -> None:
    for voter in voters:
        scores = {}

        for party_name, party in parties.items():
            scores[party_name] = score_party(voter, party)

        current_party = voter.current_preference
        best_party = max(scores, key=scores.get)
        current_score = scores[current_party]
        best_score = scores[best_party]

        switch_threshold = 0.05 + 0.10 * voter.party_loyalty

        if best_party != current_party and (best_score - current_score) > switch_threshold:
            if random.random() < voter.volatility:
                voter.previous_preference = voter.current_preference
                voter.current_preference = best_party
                voter.party_loyalty = clip(voter.party_loyalty - 0.12)
        else:
            voter.party_loyalty = clip(voter.party_loyalty + 0.02)
def build_vote_explanation(voter: Voter, party: PartyProfile) -> str:
    reasons = []

    # Regional strength
    regional_strength = party.regional_affinity[voter.region]
    if regional_strength >= 0.75:
        reasons.append(f"strong regional support for {party.name}")

    # Cultural fit
    if voter.traditionalism > 0.65 and party.traditionalist_appeal > 0.70:
        reasons.append("traditionalist values")
    elif voter.progressive_inclination > 0.65 and party.progressive_appeal > 0.70:
        reasons.append("progressive values")

    # Regime / opposition logic
    if voter.regime_trust > 0.65 and party.regime_status > 0.70:
        reasons.append("trust in the ruling order")
    elif voter.opposition_sentiment > 0.65 and party.regime_status < 0.30:
        reasons.append("opposition sentiment")

    # Social profile
    if voter.urbanity > 0.70 and voter.education > 0.70 and party.urban_appeal > 0.70:
        reasons.append("urban and educated profile")

    if voter.income < 0.40 and party.working_class_appeal > 0.65:
        reasons.append("working-class appeal")

    # Minority identity
    if voter.religious_group == "muslim" and party.minority_muslim_appeal > 0.70:
        reasons.append("Muslim identity and minority representation")

    # Leader effect
    if voter.campaign_interest > 0.70 and party.leader_strength > 0.80:
        reasons.append("strong leader appeal")

    # Change vs stability
    change_demand = (voter.anger + (1 - voter.economic_satisfaction)) / 2
    if change_demand > 0.65 and party.change_reputation > 0.70:
        reasons.append("desire for change")
    elif change_demand < 0.40 and party.stability_reputation > 0.70:
        reasons.append("preference for stability")

    # Fallback
    if not reasons:
        reasons.append("general party fit")

    return ", ".join(reasons[:3])