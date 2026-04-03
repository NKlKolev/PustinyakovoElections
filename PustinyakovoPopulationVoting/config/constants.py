SIM_POPULATION = 10_000
REAL_ACTIVE_VOTERS = 8_595_000

WEIGHTS = {
    "regional_affinity": 0.10,
    "cultural_fit": 0.16,
    "regime_fit": 0.16,
    "urban_class_fit": 0.12,
    "minority_fit": 0.10,
    "leader_effect": 0.08,
    "change_vs_stability_fit": 0.08,
    "loyalty_effect": 0.08,
    "noise": 0.05,
}
PARTY_ROLES = {
    "ПКП- Ново Начало": "government",
    "ГЕРП": "semi-incumbent",
    "ДПС": "anti-system",
    "Демократично Пустиняково": "opposition",
    "СХДС": "semi-incumbent",
    "Пустиняшка Промяна": "anti-system",
    "Израждане": "anti-system",
}

AGE_GROUPS = ["18-29", "30-44", "45-64", "65+"]
AGE_WEIGHTS = [0.22, 0.28, 0.30, 0.25]