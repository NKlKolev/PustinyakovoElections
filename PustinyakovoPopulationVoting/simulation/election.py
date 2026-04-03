import random
from collections import Counter, defaultdict
from typing import Dict, List

from models.party import PartyProfile
from models.voter import Voter
from simulation.scoring import score_party, build_vote_explanation
from simulation.utils import clip, softmax_choice


def compute_turnout_probability(voter: Voter, parties: Dict[str, PartyProfile]) -> float:
    base = voter.turnout_baseline - 0.10

    # keep turnout drivers, but make them weaker so turnout is less inflated
    interest_effect = 0.15 * voter.campaign_interest
    anger_effect = 0.08 * voter.anger
    attachment_effect = 0.12 * voter.party_loyalty

    preferred_party = parties[voter.current_preference]
    machine_effect = 0.10 * preferred_party.machine_power * voter.patronage_dependence

    alienation = 1 - max(voter.regime_trust, voter.opposition_sentiment)
    alienation_effect = -0.25 * alienation

    random_shock = random.gauss(0.0, 0.15)

    turnout_probability = (
            base
            + interest_effect
            + anger_effect
            + attachment_effect
            + machine_effect
            + alienation_effect
            + random_shock
    )

    return clip(turnout_probability, 0.03, 0.75)

def run_baseline_election(voters: List[Voter], parties: Dict[str, PartyProfile]) -> Dict[str, object]:
    national_votes = Counter()
    regional_votes = defaultdict(Counter)
    regional_turnout = Counter()
    regional_eligible = Counter()
    turnout_count = 0

    for voter in voters:
        voter.turnout_probability = compute_turnout_probability(voter, parties)
        regional_eligible[voter.region] += 1
        voter.did_vote = False
        voter.final_vote = ""
        voter.vote_explanation = ""
        if random.random() < voter.turnout_probability:
            turnout_count += 1
            regional_turnout[voter.region] += 1

            scores = {}
            for party_name, party in parties.items():
                scores[party_name] = score_party(voter, party)

            chosen_party, _ = softmax_choice(scores)
            voter.did_vote = True
            voter.final_vote = chosen_party
            voter.vote_explanation = build_vote_explanation(voter, parties[chosen_party])

            national_votes[chosen_party] += 1
            regional_votes[voter.region][chosen_party] += 1

    valid_votes = sum(national_votes.values())
    turnout_rate = turnout_count / len(voters)

    national_percentages = {
        party: (votes / valid_votes * 100) if valid_votes > 0 else 0.0
        for party, votes in national_votes.items()
    }

    regional_results = {}
    for region, vote_counter in regional_votes.items():
        total_region_votes = sum(vote_counter.values())
        regional_results[region] = {
            "turnout": regional_turnout[region] / regional_eligible[region] if regional_eligible[region] else 0.0,
            "winner": vote_counter.most_common(1)[0][0] if total_region_votes else None,
            "vote_shares": {
                party: (votes / total_region_votes * 100) if total_region_votes > 0 else 0.0
                for party, votes in vote_counter.items()
            },
        }

    return {
        "national_votes": national_votes,
        "national_percentages": national_percentages,
        "turnout_rate": turnout_rate,
        "regional_results": regional_results,
        "valid_votes": valid_votes,
    }