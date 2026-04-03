

import random
from typing import Dict, List

from simulation.utils import clip

EVENT_WINDOW_1_BANK = [
    {
        "title": "Инфлационен шок",
        "description": "Цените на храните, горивата и битовите разходи рязко нарастват в цялата страна.",
        "theme": "economy",
        "window": 1,
        "responses": ["attack_government", "promise_relief", "defend_stability"],
    },
    {
        "title": "Теч на документи за корупция",
        "description": "Изтекли документи подсказват, че политически свързани фирми са получили привилегировано отношение.",
        "theme": "corruption",
        "window": 1,
        "responses": ["demand_resignations", "dismiss_as_smear", "pivot_to_reform"],
    },
    {
        "title": "Вълна от регионални протести",
        "description": "Избухват демонстрации заради неравномерното развитие и занемарената инфраструктура.",
        "theme": "regional_development",
        "window": 1,
        "responses": ["promise_investment", "blame_local_elites", "restore_order"],
    },
    {
        "title": "Срив в публичните услуги",
        "description": "Болници, училища и местната администрация попадат под силен обществен натиск.",
        "theme": "public_services",
        "window": 1,
        "responses": ["promise_reform", "defend_record", "attack_corruption"],
    },
]

EVENT_WINDOW_2_BANK = [
    {
        "title": "Инцидент по границата",
        "description": "Напрегнат инцидент край границата изважда сигурността и лидерството на преден план.",
        "theme": "security",
        "window": 2,
        "responses": ["strong_state_response", "call_for_calm", "attack_incompetence"],
    },
    {
        "title": "Напрежение около идентичността в Банкя",
        "description": "Етнически и религиозен спор в Банкя се изостря и доминира националния разговор.",
        "theme": "minority_relations",
        "window": 2,
        "responses": ["defend_minorities", "stress_order", "deescalate"],
    },
    {
        "title": "Скандал с изборната комисия",
        "description": "Появяват се въпроси около неутралността и компетентността на изборната администрация.",
        "theme": "institutions",
        "window": 2,
        "responses": ["defend_institutions", "call_for_investigation", "claim_system_capture"],
    },
    {
        "title": "Твърдения за външно влияние",
        "description": "Появяват се твърдения, че външни актьори се опитват да повлияят на кампанията и общественото мнение.",
        "theme": "international_alignment",
        "window": 2,
        "responses": ["national_defence_rhetoric", "urge_restraint", "use_as_attack"],
    },
]

EVENT_TONE_EFFECTS = {
    "economy": {
        "economic_satisfaction": -0.08,
        "anger": 0.05,
        "campaign_interest": 0.03,
    },
    "corruption": {
        "anger": 0.06,
        "opposition_sentiment": 0.05,
        "campaign_interest": 0.04,
    },
    "regional_development": {
        "anger": 0.03,
        "local_identity": 0.04,
        "campaign_interest": 0.03,
    },
    "public_services": {
        "anger": 0.04,
        "economic_satisfaction": -0.03,
        "campaign_interest": 0.03,
    },
    "security": {
        "security_concern": 0.08,
        "campaign_interest": 0.03,
    },
    "minority_relations": {
        "local_identity": 0.05,
        "anger": 0.04,
        "campaign_interest": 0.03,
    },
    "institutions": {
        "regime_trust": -0.05,
        "opposition_sentiment": 0.04,
        "campaign_interest": 0.03,
    },
    "international_alignment": {
        "security_concern": 0.04,
        "campaign_interest": 0.03,
    },
}

RESPONSE_EFFECTS = {
    "attack_government": {"opposition_sentiment": 0.05, "campaign_interest": 0.03},
    "promise_relief": {"economic_satisfaction": 0.03, "party_loyalty": 0.03},
    "defend_stability": {"party_loyalty": 0.02, "security_concern": 0.02},
    "demand_resignations": {"opposition_sentiment": 0.06, "campaign_interest": 0.03},
    "dismiss_as_smear": {"party_loyalty": 0.02, "anger": 0.01},
    "pivot_to_reform": {"party_loyalty": 0.03, "opposition_sentiment": 0.03},
    "promise_investment": {"party_loyalty": 0.03, "campaign_interest": 0.02},
    "blame_local_elites": {"anger": 0.03, "opposition_sentiment": 0.02},
    "restore_order": {"security_concern": 0.04, "party_loyalty": 0.02},
    "promise_reform": {"party_loyalty": 0.03, "campaign_interest": 0.03},
    "defend_record": {"party_loyalty": 0.02},
    "attack_corruption": {"opposition_sentiment": 0.05, "campaign_interest": 0.03},
    "strong_state_response": {"security_concern": 0.05, "party_loyalty": 0.03},
    "call_for_calm": {"party_loyalty": 0.02, "anger": -0.01},
    "attack_incompetence": {"opposition_sentiment": 0.04, "campaign_interest": 0.03},
    "defend_minorities": {"party_loyalty": 0.03, "local_identity": 0.02},
    "stress_order": {"security_concern": 0.04, "party_loyalty": 0.02},
    "deescalate": {"anger": -0.01, "party_loyalty": 0.02},
    "defend_institutions": {"regime_trust": 0.02, "party_loyalty": 0.02},
    "call_for_investigation": {"opposition_sentiment": 0.04, "campaign_interest": 0.03},
    "claim_system_capture": {"opposition_sentiment": 0.05, "anger": 0.03},
    "national_defence_rhetoric": {"security_concern": 0.04, "party_loyalty": 0.02},
    "urge_restraint": {"party_loyalty": 0.02, "anger": -0.01},
    "use_as_attack": {"opposition_sentiment": 0.04, "campaign_interest": 0.03},
}

PLAYER_PARTY_BONUS = 0.02
AUTO_PARTY_NOISE = 0.10


PARTY_ROLES = {
    "ПКП- Ново Начало": "government",
    "ГЕРП": "semi_incumbent",
    "ДПС": "broker",
    "Демократично Пустиняково": "opposition",
    "СХДС": "opposition",
    "Пустиняшка Промяна": "opposition",
    "Израждане": "anti_system",
}


# Helper to translate event response label
def translate_event_response_label(response: str) -> str:
    mapping = {
        "attack_government": "атака срещу управляващите",
        "promise_relief": "обещание за облекчение",
        "defend_stability": "защита на стабилността",
        "demand_resignations": "искане на оставки",
        "dismiss_as_smear": "отхвърляне като клевета",
        "pivot_to_reform": "завой към реформи",
        "promise_investment": "обещание за инвестиции",
        "blame_local_elites": "обвинение към местните елити",
        "restore_order": "възстановяване на реда",
        "promise_reform": "обещание за реформа",
        "defend_record": "защита на досегашното управление",
        "attack_corruption": "атака срещу корупцията",
        "strong_state_response": "твърд държавнически отговор",
        "call_for_calm": "призив за спокойствие",
        "attack_incompetence": "атака срещу некомпетентността",
        "defend_minorities": "защита на малцинствата",
        "stress_order": "подчертаване на реда",
        "deescalate": "призив за деескалация",
        "defend_institutions": "защита на институциите",
        "call_for_investigation": "призив за разследване",
        "claim_system_capture": "твърдение за овладяна държава",
        "national_defence_rhetoric": "патриотична защитна реторика",
        "urge_restraint": "призив за сдържаност",
        "use_as_attack": "използване на случая за политическа атака",
    }
    return mapping.get(response, response)


def draw_event_card(window: int) -> dict:
    bank = EVENT_WINDOW_1_BANK if window == 1 else EVENT_WINDOW_2_BANK
    return random.choice(bank).copy()


def filter_responses_by_role(event_card: dict, party_name: str) -> list[str]:
    responses = list(event_card["responses"])
    theme = event_card["theme"]
    role = PARTY_ROLES.get(party_name, "opposition")

    if theme == "security":
        if role not in {"government", "semi_incumbent"}:
            responses = [r for r in responses if r != "strong_state_response"]
        if role == "government":
            responses = [r for r in responses if r != "attack_incompetence"]
        if role == "anti_system":
            responses = [r for r in responses if r != "call_for_calm"]

    elif theme == "public_services":
        if role not in {"government", "semi_incumbent"}:
            responses = [r for r in responses if r != "defend_record"]

    elif theme == "institutions":
        if role not in {"government", "semi_incumbent"}:
            responses = [r for r in responses if r != "defend_institutions"]
        if role == "government":
            responses = [r for r in responses if r != "claim_system_capture"]

    elif theme == "economy":
        if role == "government":
            responses = [r for r in responses if r != "attack_government"]
        if role == "anti_system":
            responses = [r for r in responses if r != "defend_stability"]

    elif theme == "corruption":
        if role in {"government", "semi_incumbent", "broker"}:
            responses = [r for r in responses if r != "demand_resignations"]
        if role == "opposition":
            responses = [r for r in responses if r != "dismiss_as_smear"]

    elif theme == "regional_development":
        if role not in {"government", "semi_incumbent"}:
            responses = [r for r in responses if r != "restore_order"]

    elif theme == "international_alignment":
        if role not in {"government", "semi_incumbent"}:
            responses = [r for r in responses if r != "national_defence_rhetoric"]

    return responses if responses else list(event_card["responses"])


def get_default_response(event_card: dict, party_name: str) -> str:
    responses = filter_responses_by_role(event_card, party_name)
    theme = event_card["theme"]
    role = PARTY_ROLES.get(party_name, "opposition")

    if theme == "security":
        if role in {"government", "semi_incumbent"} and "strong_state_response" in responses:
            return "strong_state_response"
        if role in {"opposition", "anti_system"} and "attack_incompetence" in responses:
            return "attack_incompetence"
        if role in {"broker"} and "call_for_calm" in responses:
            return "call_for_calm"

    elif theme == "corruption":
        if role in {"opposition", "anti_system"} and "demand_resignations" in responses:
            return "demand_resignations"
        if role in {"government", "semi_incumbent", "broker"} and "dismiss_as_smear" in responses:
            return "dismiss_as_smear"
        if "pivot_to_reform" in responses:
            return "pivot_to_reform"

    elif theme == "minority_relations":
        if party_name == "ДПС" and "defend_minorities" in responses:
            return "defend_minorities"
        if party_name in {"ПКП- Ново Начало", "Израждане", "СХДС"} and "stress_order" in responses:
            return "stress_order"
        if "deescalate" in responses:
            return "deescalate"

    elif theme == "economy":
        if party_name in {"ГЕРП", "Демократично Пустиняково"} and "promise_relief" in responses:
            return "promise_relief"
        if party_name == "ПКП- Ново Начало" and role in {"government", "semi_incumbent"} and "defend_stability" in responses:
            return "defend_stability"
        if role in {"opposition", "anti_system"} and "attack_government" in responses:
            return "attack_government"

    elif theme == "public_services":
        if party_name in {"Демократично Пустиняково", "Пустиняшка Промяна"} and "promise_reform" in responses:
            return "promise_reform"
        if party_name in {"ГЕРП", "ПКП- Ново Начало"} and role in {"government", "semi_incumbent"} and "defend_record" in responses:
            return "defend_record"
        if party_name in {"СХДС", "Израждане", "ДПС"} and "attack_corruption" in responses:
            return "attack_corruption"

    elif theme == "institutions":
        if party_name in {"ГЕРП", "ПКП- Ново Начало"} and role in {"government", "semi_incumbent"} and "defend_institutions" in responses:
            return "defend_institutions"
        if party_name in {"Демократично Пустиняково", "СХДС", "Пустиняшка Промяна"} and "call_for_investigation" in responses:
            return "call_for_investigation"
        if party_name in {"ДПС", "Израждане"} and "claim_system_capture" in responses:
            return "claim_system_capture"

    elif theme == "regional_development":
        if party_name in {"Демократично Пустиняково", "Пустиняшка Промяна", "СХДС"} and "promise_investment" in responses:
            return "promise_investment"
        if party_name in {"ГЕРП", "ПКП- Ново Начало"} and role in {"government", "semi_incumbent"} and "restore_order" in responses:
            return "restore_order"
        if party_name in {"ДПС", "Израждане"} and "blame_local_elites" in responses:
            return "blame_local_elites"

    elif theme == "international_alignment":
        if party_name in {"ПКП- Ново Начало", "СХДС", "Израждане"} and role in {"government", "semi_incumbent", "anti_system"} and "national_defence_rhetoric" in responses:
            return "national_defence_rhetoric"
        if party_name in {"Демократично Пустиняково", "ГЕРП"} and "urge_restraint" in responses:
            return "urge_restraint"
        if party_name in {"ДПС", "Пустиняшка Промяна"} and "use_as_attack" in responses:
            return "use_as_attack"

    return responses[0]



def build_event_phase_rows(event_card: dict, parties: dict) -> list[dict]:
    rows = []
    for party_name in parties.keys():
        allowed_responses = filter_responses_by_role(event_card, party_name)
        default_response = get_default_response(event_card, party_name)
        rows.append(
            {
                "Party": party_name,
                "Allowed responses": ", ".join(allowed_responses),
                "Selected response": default_response,
                "Applied response": default_response,
                "Outcome": "Очаква обработка",
            }
        )
    return rows


# Helper function: compute_event_response_fit
def compute_event_response_fit(event_card: dict, party_name: str, response: str) -> float:
    theme = event_card["theme"]

    theme_fit_map = {
        "economy": {
            "ПКП- Ново Начало": 0.55,
            "ГЕРП": 0.75,
            "Демократично Пустиняково": 0.65,
            "ДПС": 0.50,
            "СХДС": 0.55,
            "Пустиняшка Промяна": 0.60,
            "Израждане": 0.45,
        },
        "corruption": {
            "ПКП- Ново Начало": 0.25,
            "ГЕРП": 0.30,
            "Демократично Пустиняково": 0.85,
            "ДПС": 0.35,
            "СХДС": 0.70,
            "Пустиняшка Промяна": 0.80,
            "Израждане": 0.60,
        },
        "regional_development": {
            "ПКП- Ново Начало": 0.60,
            "ГЕРП": 0.65,
            "Демократично Пустиняково": 0.60,
            "ДПС": 0.50,
            "СХДС": 0.55,
            "Пустиняшка Промяна": 0.70,
            "Израждане": 0.45,
        },
        "public_services": {
            "ПКП- Ново Начало": 0.40,
            "ГЕРП": 0.60,
            "Демократично Пустиняково": 0.75,
            "ДПС": 0.45,
            "СХДС": 0.55,
            "Пустиняшка Промяна": 0.70,
            "Израждане": 0.35,
        },
        "security": {
            "ПКП- Ново Начало": 0.90,
            "ГЕРП": 0.60,
            "Демократично Пустиняково": 0.35,
            "ДПС": 0.30,
            "СХДС": 0.75,
            "Пустиняшка Промяна": 0.40,
            "Израждане": 0.80,
        },
        "minority_relations": {
            "ПКП- Ново Начало": 0.25,
            "ГЕРП": 0.45,
            "Демократично Пустиняково": 0.70,
            "ДПС": 0.95,
            "СХДС": 0.35,
            "Пустиняшка Промяна": 0.40,
            "Израждане": 0.20,
        },
        "institutions": {
            "ПКП- Ново Начало": 0.40,
            "ГЕРП": 0.55,
            "Демократично Пустиняково": 0.75,
            "ДПС": 0.35,
            "СХДС": 0.65,
            "Пустиняшка Промяна": 0.70,
            "Израждане": 0.30,
        },
        "international_alignment": {
            "ПКП- Ново Начало": 0.70,
            "ГЕРП": 0.60,
            "Демократично Пустиняково": 0.55,
            "ДПС": 0.45,
            "СХДС": 0.60,
            "Пустиняшка Промяна": 0.50,
            "Израждане": 0.75,
        },
    }

    response_bonus_map = {
        "attack_government": {"Демократично Пустиняково": 0.06, "СХДС": 0.04, "Пустиняшка Промяна": 0.05, "Израждане": 0.03},
        "promise_relief": {"ГЕРП": 0.04, "Демократично Пустиняково": 0.03, "ПКП- Ново Начало": 0.02},
        "defend_stability": {"ПКП- Ново Начало": 0.05, "ГЕРП": 0.03, "СХДС": 0.02},
        "demand_resignations": {"Демократично Пустиняково": 0.07, "СХДС": 0.05, "Пустиняшка Промяна": 0.06},
        "dismiss_as_smear": {"ПКП- Ново Начало": 0.04, "ГЕРП": 0.03, "ДПС": 0.03},
        "pivot_to_reform": {"Демократично Пустиняково": 0.04, "СХДС": 0.03, "Пустиняшка Промяна": 0.05},
        "promise_investment": {"Пустиняшка Промяна": 0.05, "Демократично Пустиняково": 0.03, "СХДС": 0.03},
        "blame_local_elites": {"ДПС": 0.03, "Израждане": 0.03, "ПКП- Ново Начало": 0.02},
        "restore_order": {"ПКП- Ново Начало": 0.04, "ГЕРП": 0.03, "СХДС": 0.04},
        "promise_reform": {"Демократично Пустиняково": 0.05, "Пустиняшка Промяна": 0.05, "СХДС": 0.03},
        "defend_record": {"ГЕРП": 0.04, "ПКП- Ново Начало": 0.03},
        "attack_corruption": {"Демократично Пустиняково": 0.04, "СХДС": 0.04, "Израждане": 0.02},
        "strong_state_response": {"ПКП- Ново Начало": 0.06, "СХДС": 0.05, "Израждане": 0.05},
        "call_for_calm": {"Демократично Пустиняково": 0.04, "ГЕРП": 0.03, "ДПС": 0.02},
        "attack_incompetence": {"Демократично Пустиняково": 0.04, "СХДС": 0.03, "Пустиняшка Промяна": 0.03},
        "defend_minorities": {"ДПС": 0.07, "Демократично Пустиняково": 0.04},
        "stress_order": {"ПКП- Ново Начало": 0.04, "СХДС": 0.04, "Израждане": 0.05},
        "deescalate": {"Демократично Пустиняково": 0.03, "ДПС": 0.03, "ГЕРП": 0.02},
        "defend_institutions": {"ГЕРП": 0.04, "ПКП- Ново Начало": 0.03},
        "call_for_investigation": {"Демократично Пустиняково": 0.05, "СХДС": 0.04, "Пустиняшка Промяна": 0.05},
        "claim_system_capture": {"Израждане": 0.04, "ДПС": 0.03, "ПКП- Ново Начало": 0.02},
        "national_defence_rhetoric": {"ПКП- Ново Начало": 0.05, "Израждане": 0.05, "СХДС": 0.04},
        "urge_restraint": {"Демократично Пустиняково": 0.03, "ГЕРП": 0.03, "ДПС": 0.02},
        "use_as_attack": {"Пустиняшка Промяна": 0.04, "Демократично Пустиняково": 0.03, "ДПС": 0.02},
    }

    base_fit = theme_fit_map.get(theme, {}).get(party_name, 0.50)
    response_bonus = response_bonus_map.get(response, {}).get(party_name, 0.0)
    return base_fit + response_bonus


def resolve_event_phase(event_card: dict, event_rows: list[dict], player_party: str | None = None) -> list[dict]:
    resolved_rows = []

    for row in event_rows:
        party = row["Party"]
        response = row.get("Selected response", row["Applied response"])
        allowed_responses = filter_responses_by_role(event_card, party)
        if response not in allowed_responses:
            response = get_default_response(event_card, party)
        response_fit = compute_event_response_fit(event_card, party, response)
        response_label = translate_event_response_label(response)

        base_success = 0.38 + (response_fit * 0.34)

        if player_party is not None and party == player_party:
            success_score = base_success + PLAYER_PARTY_BONUS + random.gauss(0, AUTO_PARTY_NOISE)
        else:
            success_score = base_success + random.gauss(0, AUTO_PARTY_NOISE)

        success = success_score >= 0.56

        resolved_rows.append(
            {
                "Party": party,
                "Allowed responses": ", ".join(allowed_responses),
                "Selected response": response,
                "Applied response": response,
                "Success": "Yes" if success else "No",
                "Outcome": (
                    f"{party} овладя политически ситуацията чрез реакцията „{response_label}“ (оценка за съответствие: {response_fit:.2f})."
                    if success
                    else f"Реакцията „{response_label}“ на {party} не успя да натрупа сериозна обществена подкрепа (оценка за съответствие: {response_fit:.2f})."
                ),
            }
        )

    return resolved_rows


def apply_event_shock(voters: list, event_card: dict) -> None:
    theme = event_card["theme"]
    effects = EVENT_TONE_EFFECTS.get(theme, {})

    for voter in voters:
        for field, delta in effects.items():
            current_value = getattr(voter, field)
            setattr(voter, field, clip(current_value + delta))

        if theme == "minority_relations" and voter.religious_group == "muslim":
            voter.local_identity = clip(voter.local_identity + 0.03)
            voter.anger = clip(voter.anger + 0.02)

        if theme == "economy" and voter.income < 0.45:
            voter.economic_satisfaction = clip(voter.economic_satisfaction - 0.03)
            voter.anger = clip(voter.anger + 0.02)


def apply_event_responses(voters: list, event_card: dict, resolved_rows: list[dict]) -> None:
    for row in resolved_rows:
        party = row["Party"]
        response = row["Applied response"]
        success = row["Success"] == "Yes"
        base_effects = RESPONSE_EFFECTS.get(response, {})
        multiplier = 1.0 if success else 0.4

        for voter in voters:
            if voter.current_preference != party:
                continue

            for field, delta in base_effects.items():
                current_value = getattr(voter, field)
                setattr(voter, field, clip(current_value + delta * multiplier))

            if success:
                voter.party_loyalty = clip(voter.party_loyalty + 0.02)
            else:
                voter.party_loyalty = clip(voter.party_loyalty - 0.03)
                voter.campaign_interest = clip(voter.campaign_interest + 0.01)