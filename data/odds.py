def compute_odds(percent: float) -> float:
    probability = percent / 100
    if probability <= 0 or probability >= 1:
        raise ValueError("percent must be between 0 and 100 (exclusive)")
    return probability / (1 - probability)
