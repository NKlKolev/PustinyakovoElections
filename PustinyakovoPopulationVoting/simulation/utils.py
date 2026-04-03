import math
import random
from typing import Dict, List, Tuple


def clip(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def sample_around_mean(mean: float, std_dev: float = 0.12) -> float:
    return clip(random.gauss(mean, std_dev))


def weighted_random_choice(items: List[str], weights: List[float]) -> str:
    return random.choices(items, weights=weights, k=1)[0]


def softmax_choice(scores: Dict[str, float], beta: float = 4.0) -> Tuple[str, Dict[str, float]]:
    exp_scores = {k: math.exp(beta * v) for k, v in scores.items()}
    total = sum(exp_scores.values())
    probabilities = {k: v / total for k, v in exp_scores.items()}

    roll = random.random()
    cumulative = 0.0

    for party, probability in probabilities.items():
        cumulative += probability
        if roll <= cumulative:
            return party, probabilities

    last_party = list(probabilities.keys())[-1]
    return last_party, probabilities