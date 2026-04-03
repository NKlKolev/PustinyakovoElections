from statistics import mean


def compute_national_indicators(voters: list) -> dict:
    if not voters:
        return {}

    return {
        "доверие_в_институциите": round(mean(v.regime_trust for v in voters), 3),
        "гняв_в_обществото": round(mean(v.anger for v in voters), 3),
        "икономическо_удовлетворение": round(mean(v.economic_satisfaction for v in voters), 3),
        "сигурност_и_страх": round(mean(v.security_concern for v in voters), 3),
        "интерес_към_кампанията": round(mean(v.campaign_interest for v in voters), 3),
    }


def compute_party_support(voters: list) -> dict:
    counts = {}

    for v in voters:
        party = v.current_preference
        counts[party] = counts.get(party, 0) + 1

    total = sum(counts.values())

    return {
        party: round((count / total) * 100, 2)
        for party, count in counts.items()
    }


def compute_regional_mood(voters: list) -> dict:
    regions = {}

    for v in voters:
        region = v.region
        if region not in regions:
            regions[region] = {
                "anger": [],
                "trust": [],
                "economy": []
            }

        regions[region]["anger"].append(v.anger)
        regions[region]["trust"].append(v.regime_trust)
        regions[region]["economy"].append(v.economic_satisfaction)

    result = {}

    for region, data in regions.items():
        result[region] = {
            "гняв": round(mean(data["anger"]), 3),
            "доверие": round(mean(data["trust"]), 3),
            "икономика": round(mean(data["economy"]), 3),
        }

    return result
