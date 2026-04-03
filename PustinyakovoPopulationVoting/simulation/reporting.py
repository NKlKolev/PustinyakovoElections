from collections import Counter
from typing import Dict, List

from models.voter import Voter
from config.constants import REAL_ACTIVE_VOTERS

def print_population_summary(voters: List[Voter]) -> None:
    print("\n=== POPULATION SUMMARY ===")
    by_region = Counter(v.region for v in voters)

    for region, count in by_region.items():
        print(f"{region}: {count}")


def print_preference_summary(voters: List[Voter]) -> None:
    print("\n=== INITIAL PARTY PREFERENCES ===")
    preference_counts = Counter(v.current_preference for v in voters)
    total = len(voters)

    for party, count in preference_counts.most_common():
        print(f"{party}: {count} ({count / total * 100:.2f}%)")


def print_election_results(results: Dict[str, object]) -> None:
    print("\n=== NATIONAL RESULTS ===")
    national_votes = results["national_votes"]
    national_percentages = results["national_percentages"]
    turnout_rate = results["turnout_rate"]
    valid_votes = results["valid_votes"]
    total_bots = sum(national_votes.values())
    scale_factor = REAL_ACTIVE_VOTERS / total_bots if total_bots else 0

    real_valid_votes = int(valid_votes * scale_factor)

    print(f"Turnout: {turnout_rate * 100:.2f}% (~{real_valid_votes:,} voters)")
    print(f"Valid votes (simulated): {valid_votes}")
    print(f"Valid votes (real): {real_valid_votes:,}")
    print()

    for party, votes in national_votes.most_common():
        real_votes = int(votes * scale_factor)
        print(f"{party}: {votes} votes (~{real_votes:,} real votes) ({national_percentages[party]:.2f}%)")

    print("\n=== REGIONAL RESULTS ===")
    regional_results = results["regional_results"]

    for region, result in regional_results.items():
        print(f"\n{region}")
        print(f"  Turnout: {result['turnout'] * 100:.2f}%")
        print(f"  Winner: {result['winner']}")

        for party, share in sorted(
            result["vote_shares"].items(),
            key=lambda item: item[1],
            reverse=True,
        ):
            print(f"    {party}: {share:.2f}%")