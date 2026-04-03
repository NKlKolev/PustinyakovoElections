import random
from collections import Counter

from simulation.governor.candidates import generate_governor_candidates


def _clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def compute_governor_turnout_probability(voter) -> float:
    """
    Governor elections use their own turnout model.
    The result is capped at 60% by design.
    """
    base_turnout = getattr(voter, "turnout_probability", 0.50)
    campaign_interest = getattr(voter, "campaign_interest", 0.50)
    party_loyalty = getattr(voter, "party_loyalty", 0.50)
    anger = getattr(voter, "anger", 0.50)
    regime_trust = getattr(voter, "regime_trust", 0.50)

    turnout = (
        base_turnout * 0.55
        + campaign_interest * 0.15
        + party_loyalty * 0.10
        + anger * 0.08
        + regime_trust * 0.05
        + random.uniform(-0.05, 0.05)
    )

    return _clip(turnout, low=0.05, high=0.60)



def compute_candidate_score_for_voter(voter, candidate: dict) -> float:
    party_match = 1.0 if voter.current_preference == candidate["party"] else 0.0

    regional_affinity = candidate.get("regional_affinity", 0.50)
    electability = candidate.get("electability", 0.50)
    local_strength = candidate.get("local_strength", 0.50)
    charisma = candidate.get("charisma", 0.50)
    competence = candidate.get("competence", 0.50)
    scandal_penalty = candidate.get("scandal_risk", 0.20)

    economy_fit = 1.0 - abs(voter.economic_satisfaction - candidate.get("economy_fit", 0.50))
    security_fit = 1.0 - abs(voter.security_concern - candidate.get("security_fit", 0.50))
    trust_fit = 1.0 - abs(voter.regime_trust - candidate.get("trust_fit", 0.50))
    identity_fit = 1.0 - abs(voter.local_identity - candidate.get("identity_fit", 0.50))

    anger_penalty = voter.anger * scandal_penalty * 0.20

    score = (
        party_match * 0.30
        + electability * 0.18
        + local_strength * 0.12
        + charisma * 0.08
        + competence * 0.08
        + regional_affinity * 0.10
        + economy_fit * 0.05
        + security_fit * 0.04
        + trust_fit * 0.03
        + identity_fit * 0.02
        - anger_penalty
        + random.uniform(-0.05, 0.05)
    )

    return _clip(score, low=-1.0, high=2.0)



def choose_candidate_for_voter(voter, region_candidates: list[dict]) -> dict:
    scored_candidates = []

    for candidate in region_candidates:
        score = compute_candidate_score_for_voter(voter, candidate)
        scored_candidates.append((candidate, score))

    scored_candidates.sort(key=lambda item: item[1], reverse=True)
    top_score = scored_candidates[0][1]

    # Keep all candidates within a tiny margin of the best score,
    # then break ties randomly so results are not static.
    finalists = [
        candidate for candidate, score in scored_candidates
        if score >= top_score - 0.03
    ]

    return random.choice(finalists)



def run_governor_election(voters: list, region_profiles: dict, tuning: dict | None = None) -> dict:
    """
    Runs regional governor elections using candidate-level choice.
    Each region elects one governor.
    """

    candidates = generate_governor_candidates(region_profiles, tuning=tuning)
    regional_results = {}

    for region in region_profiles.keys():
        region_voters = [v for v in voters if v.region == region]
        region_candidates = candidates[region]

        vote_counter = Counter()
        candidate_lookup = {candidate["name"]: candidate for candidate in region_candidates}

        for voter in region_voters:
            turnout_probability = compute_governor_turnout_probability(voter)
            if random.random() > turnout_probability:
                continue

            chosen = choose_candidate_for_voter(voter, region_candidates)
            vote_counter[chosen["name"]] += 1

        if vote_counter:
            winner_name, winner_votes = vote_counter.most_common(1)[0]
            winner_candidate = candidate_lookup[winner_name]
        else:
            winner_name, winner_votes = None, 0
            winner_candidate = None

        total_votes = sum(vote_counter.values())
        vote_shares = {
            candidate_name: round((votes / total_votes) * 100, 2) if total_votes > 0 else 0.0
            for candidate_name, votes in vote_counter.items()
        }

        sorted_results = vote_counter.most_common()
        runner_up_name = sorted_results[1][0] if len(sorted_results) > 1 else None
        runner_up_votes = sorted_results[1][1] if len(sorted_results) > 1 else 0
        margin = winner_votes - runner_up_votes if winner_name is not None else 0

        regional_results[region] = {
            "winner": winner_name,
            "winner_party": winner_candidate["party"] if winner_candidate else None,
            "winner_candidate": winner_candidate,
            "runner_up": runner_up_name,
            "margin_votes": margin,
            "votes": dict(vote_counter),
            "vote_shares": vote_shares,
            "total_votes": total_votes,
        }

    return {
        "regional_results": regional_results,
        "candidates": candidates,
    }