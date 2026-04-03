from simulation.polling.indicators import (
    compute_national_indicators,
    compute_party_support,
    compute_regional_mood
)

from simulation.polling.scenarios import (
    apply_polling_scenario,
    apply_polling_noise
)


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

    # 2. Add randomness (VERY important)
    apply_polling_noise(voters, intensity=0.02)

    # 3. Compute outputs
    return {
        "national": compute_national_indicators(voters),
        "party_support": compute_party_support(voters),
        "regions": compute_regional_mood(voters)
    }