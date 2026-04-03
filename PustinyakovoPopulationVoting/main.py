import random
from collections import Counter
from statistics import mean
import time
from simulation.governor.engine import run_governor_election
import os
import copy
def get_logo_path(party_name: str) -> str:
    base_path = os.path.dirname(__file__)
    logo_path = os.path.join(base_path, "logos", f"{party_name}.png")

    if os.path.exists(logo_path):
        return logo_path
    return None

import base64

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def build_logo_html(party_name: str, max_width: int = 160, max_height: int = 160) -> str:
    logo_path = get_logo_path(party_name)
    if not logo_path:
        return ""

    encoded = encode_image_to_base64(logo_path)
    if not encoded:
        return ""

    return f'<img src="data:image/png;base64,{encoded}" style="max-width:{max_width}px; max-height:{max_height}px; object-fit:contain;" />'

from config.constants import REAL_ACTIVE_VOTERS, SIM_POPULATION
from config.parties import PARTY_PROFILES
from config.regions import REGION_PROFILES
from simulation.election import run_baseline_election
from simulation.population import generate_population
from simulation.reporting import (
    print_election_results,
    print_population_summary,
    print_preference_summary,
)
from simulation.scoring import assign_initial_preference, update_preferences_after_campaign
from simulation.strategy import (
    apply_resolved_actions_to_voters,
    build_action_log_rows,
    choose_party_actions,
    resolve_party_action,
)
from simulation.events import (
    apply_event_responses,
    apply_event_shock,
    build_event_phase_rows,
    draw_event_card,
    resolve_event_phase,
)
from simulation.polling.engine import run_polling

try:
    import streamlit as st
except ImportError:
    st = None

DEBATE_QUESTION_BANK = [
    {
         "въпрос": "Как бихте подобрили икономиката?",
        "theme": "economy",
        "party_fit": {
            "ПКП- Ново Начало": 0.45,
            "ГЕРП": 0.75,
            "Демократично Пустиняково": 0.60,
            "ДПС": 0.55,
            "СХДС": 0.50,
            "Пустиняшка Промяна": 0.45,
            "Израждане": 0.20,
        },
    },
    {
         "въпрос": "Как бихте се справили с корупцията?",   #How will you deal with corruption?
        "theme": "corruption",
        "party_fit": {
            "ПКП- Ново Начало": 0.30,
            "ГЕРП": 0.40,
            "Демократично Пустиняково": 0.85,
            "ДПС": 0.45,
            "СХДС": 0.70,
            "Пустиняшка Промяна": 0.50,
            "Израждане": 0.50,
        },
    },
    {
         "въпрос": "Как бихте могли да опазите националната сигурност?+",  #How will you protect national security?+
        "theme": "security",
        "party_fit": {
            "ПКП- Ново Начало": 0.90,
            "ГЕРП": 0.65,
            "Демократично Пустиняково": 0.40,
            "ДПС": 0.35,
            "СХДС": 0.75,
            "Пустиняшка Промяна": 0.40,
            "Израждане": 0.60,
        },
    },
    {
         "въпрос": "Как вашата партия би се справила с отношенията между малцинствата?",    #How will you handle minority relations?
        "theme": "minority_relations",
        "party_fit": {
            "ПКП- Ново Начало": 0.25,
            "ГЕРП": 0.50,
            "Демократично Пустиняково": 0.70,
            "ДПС": 0.95,
            "СХДС": 0.35,
            "Пустиняшка Промяна": 0.30,
            "Израждане": 0.20,
        },
    },
    {
         "въпрос": "Как бихте подобрили стандарта на живот на Пустиняците?+",   #How will you improve living standards?+
        "theme": "living_standards",
        "party_fit": {
            "ПКП- Ново Начало": 0.55,
            "ГЕРП": 0.70,
            "Демократично Пустиняково": 0.60,
            "ДПС": 0.55,
            "СХДС": 0.50,
            "Пустиняшка Промяна": 0.30,
            "Израждане": 0.10,
        },
    },
    {
         "въпрос": "Какви промени бихте направили в публичния сектор?",      #How will you reform public services?
        "theme": "public_services",
        "party_fit": {
            "ПКП- Ново Начало": 0.40,
            "ГЕРП": 0.65,
            "Демократично Пустиняково": 0.75,
            "ДПС": 0.50,
            "СХДС": 0.55,
            "Пустиняшка Промяна": 0.30,
            "Израждане": 0.15,
        },
    },
    {
         "въпрос": "След години на политически разочерования, защо трябва избирателите да ви се доверят?",    #Why should voters trust you after years of political disappointment?
        "theme": "trust",
        "party_fit": {
            "ПКП- Ново Начало": 0.55,
            "ГЕРП": 0.45,
            "Демократично Пустиняково": 0.65,
            "ДПС": 0.40,
            "СХДС": 0.60,
            "Пустиняшка Промяна": 0.75,
            "Израждане": 0.55,
        },
    },
    {
         "въпрос": "Защо според вас корупцията е толкова дълбоко вкоренена под управлението на политическия елит?",     #Why has corruption persisted under the political elite?
        "theme": "corruption",
        "party_fit": {
            "ПКП- Ново Начало": 0.20,
            "ГЕРП": 0.30,
            "Демократично Пустиняково": 0.85,
            "ДПС": 0.35,
            "СХДС": 0.70,
            "Пустиняшка Промяна": 0.80,
            "Израждане": 0.65,
        },
    },
    {
         "въпрос": "Кой според вас е отговорен за вискоите разходи и ниските заплати в страната?",   #Who is really responsible for low wages and rising prices?
        "theme": "living_standards",
        "party_fit": {
            "ПКП- Ново Начало": 0.55,
            "ГЕРП": 0.60,
            "Демократично Пустиняково": 0.45,
            "ДПС": 0.40,
            "СХДС": 0.55,
            "Пустиняшка Промяна": 0.60,
            "Израждане": 0.70,
        },
    },
    {
         "въпрос": "Можете ли да докажете на избирателите, че защитавате тяхните интереси, а не само собствените?",  #Are you protecting ordinary people or just your own networks?
        "theme": "trust",
        "party_fit": {
            "ПКП- Ново Начало": 0.30,
            "ГЕРП": 0.35,
            "Демократично Пустиняково": 0.70,
            "ДПС": 0.30,
            "СХДС": 0.60,
            "Пустиняшка Промяна": 0.75,
            "Израждане": 0.65,
        },
    },
    {
         "въпрос": "Как бихте ограничили купуването на гласове и натискът върху регионите?",   #How would you stop vote buying and political pressure in the regions?
        "theme": "corruption",
        "party_fit": {
            "ПКП- Ново Начало": 0.15,
            "ГЕРП": 0.25,
            "Демократично Пустиняково": 0.80,
            "ДПС": 0.20,
            "СХДС": 0.65,
            "Пустиняшка Промяна": 0.70,
            "Израждане": 0.45,
        },
    },
    {
         "въпрос": "Трябва ли правителството да приеме по-тежки мерки за справяне със сепаратистите и анти-правителствените терористични организации?+",   #Should the state be tougher against separatist and anti-state forces?+
        "theme": "security",
        "party_fit": {
            "ПКП- Ново Начало": 0.90,
            "ГЕРП": 0.65,
            "Демократично Пустиняково": 0.30,
            "ДПС": 0.20,
            "СХДС": 0.75,
            "Пустиняшка Промяна": 0.35,
            "Израждане": 0.80,
        },
    },
    {
         "въпрос": "Мултикултурните реформи в страната засилиха ли позицията на страната ни или я намалиха?",   #Has multiculturalism strengthened the country or слаб отговорened it?
        "theme": "minority_relations",
        "party_fit": {
            "ПКП- Ново Начало": 0.25,
            "ГЕРП": 0.45,
            "Демократично Пустиняково": 0.70,
            "ДПС": 0.95,
            "СХДС": 0.30,
            "Пустиняшка Промяна": 0.35,
            "Израждане": 0.15,
        },
    },
    {
         "въпрос": "Бихте ли избрали стабилността, дори да означава ограничена гражданска свобода?+",    #Would you choose stability even if it means fewer freedoms?+
        "theme": "security",
        "party_fit": {
            "ПКП- Ново Начало": 0.85,
            "ГЕРП": 0.60,
            "Демократично Пустиняково": 0.25,
            "ДПС": 0.35,
            "СХДС": 0.70,
            "Пустиняшка Промяна": 0.40,
            "Израждане": 0.75,
        },
    },
    {
         "въпрос": "Защо трябва младите да останат в страната, а не отидат в чужбина?",     #Why should young people stay in the country instead of leaving?
        "theme": "public_services",
        "party_fit": {
            "ПКП- Ново Начало": 0.35,
            "ГЕРП": 0.55,
            "Демократично Пустиняково": 0.75,
            "ДПС": 0.45,
            "СХДС": 0.50,
            "Пустиняшка Промяна": 0.70,
            "Израждане": 0.40,
        },
    },
    {
         "въпрос": "Кой според вас тук, е най-компрометиран от олигархично влияние?",    #Who in this debate is most compromised by oligarchic influence?
        "theme": "corruption",
        "party_fit": {
            "ПКП- Ново Начало": 0.20,
            "ГЕРП": 0.25,
            "Демократично Пустиняково": 0.75,
            "ДПС": 0.20,
            "СХДС": 0.60,
            "Пустиняшка Промяна": 0.80,
            "Израждане": 0.55,
        },
    },
    {
         "въпрос": "Трябва ли религията и традиционните ценности да имат по-голямо влияние в обществото?+",    #Should religion and traditional values have a bigger role in public life?+
        "theme": "minority_relations",
        "party_fit": {
            "ПКП- Ново Начало": 0.80,
            "ГЕРП": 0.55,
            "Демократично Пустиняково": 0.20,
            "ДПС": 0.50,
            "СХДС": 1,
            "Пустиняшка Промяна": 0.30,
            "Израждане": 0.85,
        },
    },
    {
         "въпрос": "Ако спечелите изборите, кои са първите олигархически мрежи, които бихте прекратили?",  #If you win, which elite groups will lose power first?
        "theme": "trust",
        "party_fit": {
            "ПКП- Ново Начало": 0.35,
            "ГЕРП": 0.30,
            "Демократично Пустиняково": 0.65,
            "ДПС": 0.25,
            "СХДС": 0.60,
            "Пустиняшка Промяна": 0.85,
            "Израждане": 0.75,
        },
    },
]

DEBATE_TONES = [
    "спокоен тон",
    "агресивен тон ",
    "технически обяснения",
    "тежък популизъм",
]

DEBATE_TONE_EFFECTS = {
    "спокоен тон": {
        "leader_weight": 0.20,
        "issue_weight": 0.60,
        "randomness": 0.20,
    },
    "агресивен тон ": {
        "leader_weight": 0.45,
        "issue_weight": 0.30,
        "randomness": 0.25,
    },
    "технически обяснения": {
        "leader_weight": 0.15,
        "issue_weight": 0.70,
        "randomness": 0.15,
    },
    "тежък популизъм": {
        "leader_weight": 0.35,
        "issue_weight": 0.35,
        "randomness": 0.30,
    },
}
DEBATE_QUESTIONS = [item[ "въпрос"] for item in DEBATE_QUESTION_BANK]
DEBATE_ANSWER_STYLES = ["силен отговор", "избягване на въпроса", "слаб отговор"]

VOTE_BUYING_ATTEMPT = {
    "ПКП- Ново Начало": 0.95,
    "ГЕРП": 0.80,
    "ДПС": 0.90,
    "Демократично Пустиняково": 0.25,
    "СХДС": 0.35,
    "Пустиняшка Промяна": 0.15,
    "Израждане": 0.30,
}

VOTE_BUYING_SUCCESS = {
    "ПКП- Ново Начало": 0.90,
    "ГЕРП": 0.50,
    "ДПС": 0.50,
    "Демократично Пустиняково": 0.15,
    "СХДС": 0.40,
    "Пустиняшка Промяна": 0.15,
    "Израждане": 0.15,
}
VOTE_BUYING_EFFECTS = {
    "ПКП- Ново Начало": {
        "loyalty_gain": 0.10,
        "turnout_gain": 0.09,
        "campaign_gain": 0.03,
        "failure_anger": 0.02,
        "failure_loyalty_loss": 0.02,
        "reputation_cost": 0.01,
        "anti_machine_anger": 0.01,
    },
    "ГЕРП": {
        "loyalty_gain": 0.07,
        "turnout_gain": 0.06,
        "campaign_gain": 0.02,
        "failure_anger": 0.03,
        "failure_loyalty_loss": 0.04,
        "reputation_cost": 0.02,
        "anti_machine_anger": 0.02,
    },
    "ДПС": {
        "loyalty_gain": 0.09,
        "turnout_gain": 0.08,
        "campaign_gain": 0.03,
        "failure_anger": 0.02,
        "failure_loyalty_loss": 0.03,
        "reputation_cost": 0.01,
        "anti_machine_anger": 0.01,
    },
    "Демократично Пустиняково": {
        "loyalty_gain": 0.04,
        "turnout_gain": 0.03,
        "campaign_gain": 0.01,
        "failure_anger": 0.04,
        "failure_loyalty_loss": 0.06,
        "reputation_cost": 0.04,
        "anti_machine_anger": 0.03,
    },
    "СХДС": {
        "loyalty_gain": 0.05,
        "turnout_gain": 0.04,
        "campaign_gain": 0.01,
        "failure_anger": 0.04,
        "failure_loyalty_loss": 0.05,
        "reputation_cost": 0.03,
        "anti_machine_anger": 0.02,
    },
    "Пустиняшка Промяна": {
        "loyalty_gain": 0.03,
        "turnout_gain": 0.02,
        "campaign_gain": 0.01,
        "failure_anger": 0.05,
        "failure_loyalty_loss": 0.07,
        "reputation_cost": 0.05,
        "anti_machine_anger": 0.03,
    },
    "Израждане": {
        "loyalty_gain": 0.04,
        "turnout_gain": 0.03,
        "campaign_gain": 0.01,
        "failure_anger": 0.04,
        "failure_loyalty_loss": 0.05,
        "reputation_cost": 0.03,
        "anti_machine_anger": 0.02,
    },
}
def extract_primary_actions(party_actions: dict) -> dict:
    primary_actions = {}

    for party_name, actions in party_actions.items():
        primary_actions[party_name] = {
            "Първа цел на кампанията": actions["primary_action"],
            "Какво е направила партията": actions["primary_variant"],
            "Кого атакува партията": actions["primary_target"],
        }

    return primary_actions

def render_polling_mode() -> None:
    st.title("📈 Социологически проучвания")
    st.caption("Този модул показва моментна снимка на обществените нагласи, партийната подкрепа и регионалните различия.")

    if st.button("🔄 Генерирай нова извадка"):
        st.session_state.pop("polling_base_voters", None)
        st.rerun()

    if st.button("🔙 Назад към менюто"):
        st.session_state.app_mode = None
        st.rerun()

    if "polling_base_voters" not in st.session_state:
        st.session_state.polling_base_voters = generate_population(REGION_PROFILES)
        for voter in st.session_state.polling_base_voters:
            assign_initial_preference(voter, PARTY_PROFILES)

    voters = copy.deepcopy(st.session_state.polling_base_voters)
    st.write("### Настройка на политическата среда")

    corruption_shock = st.slider(
        "Корупционен натиск",
        min_value=-1.0,
        max_value=1.0,
        value=0.00,
        step=0.01,
    )

    economic_shock = st.slider(
        "Икономически натиск",
        min_value=-1.0,
        max_value=1.0,
        value=0.00,
        step=0.01,
    )

    security_shock = st.slider(
        "Натиск по линия на сигурността",
        min_value=-1.0,
        max_value=1.0,
        value=0.00,
        step=0.01,
    )

    trust_shock = st.slider(
        "Промяна в доверието към институциите",
        min_value=-1.0,
        max_value=1.0,
        value=0.00,
        step=0.01,
    )
    minorities_conflict = st.slider(
        "Напрежение с малцинствата",
        min_value=-1.0,
        max_value=1.0,
        value=0.00,
        step=0.01,

    )
    if st.button("📊 Покажи резултатите"):
        results = run_polling(
            voters,
            corruption_shock=corruption_shock,
            economic_shock=economic_shock,
            security_shock=security_shock,
            trust_shock=trust_shock,
        )

        st.write("### Национални индикатори")
        national_rows = [
            {"Индикатор": "Доверие в институциите", "Стойност": results["national"]["доверие_в_институциите"]},
            {"Индикатор": "Гняв в обществото", "Стойност": results["national"]["гняв_в_обществото"]},
            {"Индикатор": "Икономическо удовлетворение", "Стойност": results["national"]["икономическо_удовлетворение"]},
            {"Индикатор": "Сигурност и страх", "Стойност": results["national"]["сигурност_и_страх"]},
            {"Индикатор": "Интерес към кампанията", "Стойност": results["national"]["интерес_към_кампанията"]},
        ]
        st.dataframe(national_rows, use_container_width=True)

        st.write("### Партийна подкрепа")
        party_rows = [
            {"Партия": party, "Подкрепа (%)": support}
            for party, support in results["party_support"].items()
        ]
        st.dataframe(party_rows, use_container_width=True)
        st.bar_chart({row["Партия"]: row["Подкрепа (%)"] for row in party_rows})

        st.write("### Регионални нагласи")
        region_rows = [
            {
                "Регион": region,
                "Гняв": values["гняв"],
                "Доверие": values["доверие"],
                "Икономика": values["икономика"],
            }
            for region, values in results["regions"].items()
        ]
        st.dataframe(region_rows, use_container_width=True)

def build_governor_region_tuning(region_name: str) -> dict:
    with st.expander(f"⚙️ Настройки за {region_name}", expanded=False):
        regional_affinity_weight = st.slider(
            "Тежест на регионалната близост",
            min_value=0.00,
            max_value=0.60,
            value=0.30,
            step=0.01,
            key=f"{region_name}_regional_affinity_weight",
        )

        economy_weight = st.slider(
            "Тежест на икономическия профил",
            min_value=0.00,
            max_value=0.40,
            value=0.15,
            step=0.01,
            key=f"{region_name}_economy_weight",
        )

        security_weight = st.slider(
            "Тежест на сигурността",
            min_value=0.00,
            max_value=0.40,
            value=0.15,
            step=0.01,
            key=f"{region_name}_security_weight",
        )

        trust_weight = st.slider(
            "Тежест на доверието / антистатукво нагласата",
            min_value=0.00,
            max_value=0.40,
            value=0.15,
            step=0.01,
            key=f"{region_name}_trust_weight",
        )

        identity_weight = st.slider(
            "Тежест на идентичността / локалната култура",
            min_value=0.00,
            max_value=0.30,
            value=0.10,
            step=0.01,
            key=f"{region_name}_identity_weight",
        )

        minority_weight = st.slider(
            "Тежест на малцинствения фактор",
            min_value=0.00,
            max_value=0.20,
            value=0.05,
            step=0.01,
            key=f"{region_name}_minority_weight",
        )

        machine_weight = st.slider(
            "Тежест на машинния / клиентелисткия вот",
            min_value=0.00,
            max_value=0.30,
            value=0.10,
            step=0.01,
            key=f"{region_name}_machine_weight",
        )

        candidate_randomness = st.slider(
            "Случайност при качествата на кандидатите",
            min_value=0.00,
            max_value=0.30,
            value=0.12,
            step=0.01,
            key=f"{region_name}_candidate_randomness",
        )

        charisma_bonus = st.slider(
            "Общ бонус за харизма",
            min_value=-0.20,
            max_value=0.20,
            value=0.00,
            step=0.01,
            key=f"{region_name}_charisma_bonus",
        )

        competence_bonus = st.slider(
            "Общ бонус за компетентност",
            min_value=-0.20,
            max_value=0.20,
            value=0.00,
            step=0.01,
            key=f"{region_name}_competence_bonus",
        )

        machine_bonus = st.slider(
            "Допълнителен бонус за системни партии с мрежи",
            min_value=-0.20,
            max_value=0.20,
            value=0.00,
            step=0.01,
            key=f"{region_name}_machine_bonus",
        )

        anti_system_bonus = st.slider(
            "Бонус за антисистемни партии",
            min_value=-0.20,
            max_value=0.20,
            value=0.00,
            step=0.01,
            key=f"{region_name}_anti_system_bonus",
        )

        incumbent_bonus = st.slider(
            "Бонус за партии на статуквото / полу-статуквото",
            min_value=-0.20,
            max_value=0.20,
            value=0.00,
            step=0.01,
            key=f"{region_name}_incumbent_bonus",
        )

    return {
        "regional_affinity_weight": regional_affinity_weight,
        "economy_weight": economy_weight,
        "security_weight": security_weight,
        "trust_weight": trust_weight,
        "identity_weight": identity_weight,
        "minority_weight": minority_weight,
        "machine_weight": machine_weight,
        "candidate_randomness": candidate_randomness,
        "charisma_bonus": charisma_bonus,
        "competence_bonus": competence_bonus,
        "machine_bonus": machine_bonus,
        "anti_system_bonus": anti_system_bonus,
        "incumbent_bonus": incumbent_bonus,
    }



def build_governor_win_explanation(region_name: str, region_result: dict) -> str:
    winner_candidate = region_result.get("winner_candidate") or {}
    winner_party = region_result.get("winner_party", "Неизвестна партия")
    margin_votes = region_result.get("margin_votes", 0)

    reasons = []

    if winner_candidate.get("regional_affinity", 0) >= 0.65:
        reasons.append("силна регионална близост")
    if winner_candidate.get("electability", 0) >= 0.65:
        reasons.append("висока обща избираемост")
    if winner_candidate.get("local_strength", 0) >= 0.65:
        reasons.append("добра локална позиция")
    if winner_candidate.get("charisma", 0) >= 0.65:
        reasons.append("силна лична харизма")
    if winner_candidate.get("competence", 0) >= 0.65:
        reasons.append("убедителен управленски профил")
    if winner_candidate.get("machine_fit", 0) >= 0.65:
        reasons.append("силна организационна и мрежова подкрепа")
    if winner_candidate.get("trust_fit", 0) >= 0.65:
        reasons.append("добро попадение в нагласите за доверие / антистатукво")
    if winner_candidate.get("economy_fit", 0) >= 0.65:
        reasons.append("добро съответствие с икономическите нагласи в региона")
    if winner_candidate.get("security_fit", 0) >= 0.65:
        reasons.append("силно съответствие с темата за сигурността")

    if not reasons:
        reasons.append("по-добър общ баланс между партиен профил, регионален контекст и качествата на кандидата")

    if margin_votes >= 150:
        race_text = "Победата е убедителна."
    elif margin_votes >= 50:
        race_text = "Победата е относително стабилна."
    else:
        race_text = "Надпреварата е била много оспорвана."

    return f"{winner_party} печели в {region_name} заради {', '.join(reasons[:3])}. {race_text}"



def render_governor_mode() -> None:
    st.title("🗺️ Губернаторски избори")
    st.caption("Всеки регион избира свой губернатор на базата на локална политическа динамика.")

    if st.button("🔙 Назад към менюто"):
        st.session_state.app_mode = None
        st.session_state.campaign_state = None
        st.rerun()

    if "governor_voters" not in st.session_state:
        st.session_state.governor_voters = generate_population(REGION_PROFILES)
        for voter in st.session_state.governor_voters:
            assign_initial_preference(voter, PARTY_PROFILES)

    voters = st.session_state.governor_voters

    st.write("### Настройка по региони")
    st.caption("За всеки регион можете да зададете различни тежести и бонуси, които да влияят върху губернаторските избори.")
    st.info(
        "Как работят настройките: тези плъзгачи не променят директно самите избиратели, а променят това как моделът оценява кандидатите във всеки регион. "
        "След това всеки избирател сравнява кандидатите според собствените си нагласи — икономика, сигурност, доверие, локална идентичност, гняв и партийно предпочитание. "
        "Колкото по-висока е дадена тежест, толкова по-силно този фактор влияе върху крайния избор на избирателя."
    )

    current_tuning_signature = []

    region_tuning_map = {}
    for region_name in REGION_PROFILES.keys():
        region_tuning_map[region_name] = build_governor_region_tuning(region_name)
        region_signature = tuple(sorted(region_tuning_map[region_name].items()))
        current_tuning_signature.append((region_name, region_signature))

    current_tuning_signature = tuple(current_tuning_signature)

    if st.session_state.get("governor_results_signature") != current_tuning_signature:
        st.session_state.pop("governor_results", None)

    if st.button("📊 Проведи губернаторските избори и покажи обобщението"):
        status_box = st.empty()
        progress_bar = st.progress(0)

        status_box.info("🗳️ Губернаторският изборен ден започна.")
        progress_bar.progress(10)
        time.sleep(2.2)

        status_box.warning("⚠️ Има известно напрежение около някои изборни секции.")
        progress_bar.progress(25)
        time.sleep(2.2)

        status_box.info("🕓 Изборният ден върви към своя край.")
        progress_bar.progress(40)
        time.sleep(2.2)

        status_box.success("✅ Изборният ден приключи.")
        progress_bar.progress(55)
        time.sleep(2.2)

        status_box.info("📦 Регионалните избирателни комисии обработват протоколите.")
        progress_bar.progress(70)
        time.sleep(2.2)

        status_box.info("📊 Резултатите почти са готови.")
        progress_bar.progress(85)
        time.sleep(2.2)

        status_box.success("🏛️ Централната избирателна комисия е готова да обяви резултатите.")
        progress_bar.progress(95)
        time.sleep(2.2)

        aggregated_results = {}
        aggregated_candidates = {}

        for region_name, region_profile in REGION_PROFILES.items():
            region_voters = [v for v in voters if v.region == region_name]
            region_result_bundle = run_governor_election(
                region_voters,
                {region_name: region_profile},
                tuning=region_tuning_map[region_name],
            )
            aggregated_results[region_name] = region_result_bundle["regional_results"][region_name]
            aggregated_candidates[region_name] = region_result_bundle["candidates"][region_name]

        st.session_state.governor_results = {
            "regional_results": aggregated_results,
            "candidates": aggregated_candidates,
            "region_tuning": region_tuning_map,
        }
        st.session_state.governor_results_signature = current_tuning_signature

        progress_bar.progress(100)
        time.sleep(0.6)

    if "governor_results" in st.session_state:
        results = st.session_state.governor_results

        st.write("### 🗺️ Обобщени резултати по региони")

        rows = []
        scale_factor = REAL_ACTIVE_VOTERS / SIM_POPULATION

        for region_name, data in results["regional_results"].items():
            winner_name = data.get("winner")
            vote_shares = data.get("vote_shares", {})
            winner_share = vote_shares.get(winner_name, 0.0) if winner_name else 0.0
            simulated_votes = data.get("total_votes", 0)
            estimated_real_votes = int(simulated_votes * scale_factor)
            simulated_margin = data.get("margin_votes", 0)
            estimated_real_margin = int(simulated_margin * scale_factor)

            rows.append({
                "Регион": region_name,
                "Победител": data.get("winner_party", data.get("winner", "Няма данни")),
                "Кандидат": data.get("winner", "Няма данни"),
                "Процент за победителя": round(winner_share, 2),
                "Симулирани гласове": simulated_votes,
                "Прогнозни реални гласове": estimated_real_votes,
                "Разлика (симулирани гласове)": simulated_margin,
                "Разлика (прогнозни реални гласове)": estimated_real_margin,
                "Обяснение": build_governor_win_explanation(region_name, data),
            })

        st.dataframe(rows, use_container_width=True)


def run_poll(voters, party_profiles, sample_size=2000):
    sample = random.sample(voters, min(sample_size, len(voters)))

    counts = {party: 0 for party in party_profiles.keys()}

    for voter in sample:
        counts[voter.current_preference] += 1

    total = sum(counts.values())

    poll_results = []
    for party, count in counts.items():
        share = (count / total) * 100 if total > 0 else 0
        noise = random.gauss(0, 1.2)
        share_noisy = max(0, share + noise)

        poll_results.append({
            "Политическа Партия": party,
            "Резултати от Проучването %": round(share_noisy, 2)  # ✅ FIXED KEY
        })

    poll_results.sort(key=lambda x: x["Резултати от Проучването %"], reverse=True)

    return poll_results

def extract_secondary_actions(party_actions: dict) -> dict:
    secondary_actions = {}

    for party_name, actions in party_actions.items():
        secondary_actions[party_name] = {
            "Втора цел на кампанията": actions["secondary_action"],
            "Какво е направила партията във втория цикъл на кампанията": actions["secondary_variant"],
            "Кого атакува кампанията": actions["secondary_target"],
        }

    return secondary_actions

def resolve_primary_window(primary_actions: dict) -> list[dict]:
    resolved_actions = []

    for party_name, actions in primary_actions.items():
        resolved_actions.append(
            resolve_party_action(
                party_name=party_name,
                action_type=actions["Първа цел на кампанията"],
                variant=actions["Какво е направила партията"],
                target_party=actions["Кого атакува партията"],
                action_slot="primary",
            )
        )

    return resolved_actions

def resolve_secondary_window(secondary_actions: dict) -> list[dict]:
    resolved_actions = []

    for party_name, actions in secondary_actions.items():
        resolved_actions.append(
            resolve_party_action(
                party_name=party_name,
                action_type=actions["Втора цел на кампанията"],
                variant=actions["Какво е направила партията във втория цикъл на кампанията"],
                target_party=actions["Кого атакува кампанията"],
                action_slot="secondary",
            )
        )

    return resolved_actions

def run_leader_debate(parties: dict, num_questions: int = 4) -> list[dict]:
    selected_items = random.sample(DEBATE_QUESTION_BANK, k=min(num_questions, len(DEBATE_QUESTION_BANK)))
    debate_rows = []

    for slot_index, item in enumerate(selected_items, start=1):
        for party_name in parties.keys():
            debate_rows.append(
                {
                    "Слот": slot_index,
                     "Въпрос": item[ "въпрос"],
                    "Тема на дебата": item["theme"],
                    "Тон на дебата": "спокоен тон",
                    "Политическа Партия": party_name,
                    "Как е отговорила партията": "избягване на въпроса",
                }
            )

    return debate_rows

def apply_debate_effects(voters: list, debate_rows: list[dict]) -> None:
    for row in debate_rows:
        party = row["Политическа Партия"]
        answer_style = row["Как е отговорила партията"]
        question = row[ "Въпрос"]

        for voter in voters:
            if voter.current_preference != party:
                continue

            if answer_style == "силен отговор":
                voter.party_loyalty = min(1.0, voter.party_loyalty + 0.04)
                voter.campaign_interest = min(1.0, voter.campaign_interest + 0.03)
            elif answer_style == "слаб отговор":
                voter.party_loyalty = max(0.0, voter.party_loyalty - 0.04)
                voter.campaign_interest = min(1.0, voter.campaign_interest + 0.01)

            if "economy" in question.lower() or "living standards" in question.lower():
                if answer_style == "силен отговор":
                    voter.economic_satisfaction = min(1.0, voter.economic_satisfaction + 0.01)
                elif answer_style == "слаб отговор":
                    voter.anger = min(1.0, voter.anger + 0.01)

            if "security" in question.lower():
                if answer_style == "силен отговор":
                    voter.security_concern = min(1.0, voter.security_concern + 0.01)

def run_single_simulation():
    voters = generate_population(REGION_PROFILES)

    for voter in voters:
        assign_initial_preference(voter, PARTY_PROFILES)

    party_actions = choose_party_actions(PARTY_PROFILES)

    # Campaign Window 1
    primary_actions = extract_primary_actions(party_actions)
    resolved_window_1 = resolve_primary_window(primary_actions)
    apply_resolved_actions_to_voters(voters, resolved_window_1)
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    # Leader Debate
    debate_rows = run_leader_debate(PARTY_PROFILES)
    apply_debate_effects(voters, debate_rows)
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    # Campaign Window 2
    secondary_actions = extract_secondary_actions(party_actions)
    resolved_window_2 = resolve_secondary_window(secondary_actions)
    apply_resolved_actions_to_voters(voters, resolved_window_2)
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    results = run_baseline_election(voters, PARTY_PROFILES)

    return voters, results, resolved_window_1, debate_rows, resolved_window_2


def run_multiple_simulations(num_runs: int = 200):
    all_results = []
    win_counter = Counter()
    turnout_values = []

    for _ in range(num_runs):
        _, results, _, _, _ = run_single_simulation()
        all_results.append(results)
        turnout_values.append(results["turnout_rate"])

        national_votes = results["national_votes"]
        winner = national_votes.most_common(1)[0][0]
        win_counter[winner] += 1

    average_vote_share = {}
    min_vote_share = {}
    max_vote_share = {}

    for party in PARTY_PROFILES.keys():
        shares = [result["national_percentages"].get(party, 0.0) for result in all_results]
        average_vote_share[party] = mean(shares)
        min_vote_share[party] = min(shares)
        max_vote_share[party] = max(shares)

    most_likely_ranking = sorted(
        average_vote_share.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return {
        "num_runs": num_runs,
        "average_vote_share": average_vote_share,
        "min_vote_share": min_vote_share,
        "max_vote_share": max_vote_share,
        "win_counter": win_counter,
        "average_turnout": mean(turnout_values),
        "most_likely_ranking": most_likely_ranking,
    }


def print_monte_carlo_summary(summary: dict) -> None:
    print("\n=== MOST LIKELY OUTCOME (MONTE CARLO) ===")
    print(f"Simulations: {summary['num_runs']}")
    print(f"Average turnout: {summary['average_turnout'] * 100:.2f}%\n")

    print("Average national vote share:")
    for party, avg_share in summary["most_likely_ranking"]:
        min_share = summary["min_vote_share"][party]
        max_share = summary["max_vote_share"][party]
        wins = summary["win_counter"][party]
        win_rate = wins / summary["num_runs"] * 100
        print(
            f"{party}: {avg_share:.2f}% "
            f"(range {min_share:.2f}% - {max_share:.2f}%, wins {wins}/{summary['num_runs']} = {win_rate:.2f}%)"
        )

    print("\nMost likely ranking:")
    for index, (party, avg_share) in enumerate(summary["most_likely_ranking"], start=1):
        print(f"{index}. {party} - {avg_share:.2f}%")


def build_single_run_rows(results: dict) -> list[dict]:
    national_votes = results["national_votes"]
    national_percentages = results["national_percentages"]
    scale_factor = REAL_ACTIVE_VOTERS / SIM_POPULATION

    rows = []
    for party, votes in national_votes.most_common():
        rows.append(
            {
                "Политическа Партия": party,
                "Simulated votes": votes,
                "Estimated real votes": int(votes * scale_factor),
                "Vote share %": round(national_percentages[party], 2),
            }
        )
    return rows


def build_regional_rows(results: dict) -> list[dict]:
    rows = []
    regional_results = results["regional_results"]

    for region, result in regional_results.items():
        rows.append(
            {
                "Region": region,
                "Turnout %": round(result["turnout"] * 100, 2),
                "Winner": result["winner"],
            }
        )
    return rows


def build_regional_explanation_rows(results: dict) -> list[dict]:
    rows = []
    regional_results = results["regional_results"]

    for region, result in regional_results.items():
        vote_shares = result["vote_shares"]
        if not vote_shares:
            continue

        sorted_parties = sorted(vote_shares.items(), key=lambda item: item[1], reverse=True)
        winner, winner_share = sorted_parties[0]
        runner_up, runner_up_share = sorted_parties[1] if len(sorted_parties) > 1 else (None, 0.0)
        margin = winner_share - runner_up_share

        reasons = []

        if winner == "Демократично Пустиняково":
            reasons.append("urban and educated electorate")
            reasons.append("progressive values")
            reasons.append("opposition sentiment")
        elif winner == "ПКП- Ново Начало":
            reasons.append("traditionalist electorate")
            reasons.append("regime trust")
            reasons.append("machine and patronage influence")
        elif winner == "СХДС":
            reasons.append("traditionalist but opposition-leaning voters")
            reasons.append("силен отговор regional development appeal")
            reasons.append("силен отговор leader effect")
        elif winner == "ДПС":
            reasons.append("Muslim and minority representation")
            reasons.append("силен отговор local identity")
            reasons.append("regional concentration of support")
        elif winner == "ГЕРП":
            reasons.append("moderate and pragmatic electorate")
            reasons.append("urban-economic appeal")
            reasons.append("stability-oriented voters")
        else:
            reasons.append("broad local fit")

        if margin >= 10:
            contest = "clear regional lead"
        elif margin >= 5:
            contest = "solid but competitive lead"
        else:
            contest = "very close regional race"

        rows.append(
            {
                "Region": region,
                "Winning party": winner,
                "Winner %": round(winner_share, 2),
                "Runner-up": runner_up,
                "Margin": round(margin, 2),
                "Regional explanation": f"{winner} wins because of {', '.join(reasons[:3])}; this is a {contest}.",
            }
        )

    return rows

def build_debate_rows(debate_rows: list[dict]) -> list[dict]:
    return debate_rows
def translate_debate_tone(tone: str) -> str:
    mapping = {
        "спокоен тон": "Спокоен тон",
        "агресивен тон ": "Агресивен тон",
        "агресивен тон": "Агресивен тон",
        "технически обяснения": "Технически обяснения",
        "тежък популизъм": "Тежък популизъм",
    }
    return mapping.get(tone, tone)


def get_debate_result_badge(answer_style: str) -> tuple[str, str, str]:
    if answer_style == "силен отговор":
        return ("Силен отговор", "#1f9d55", "#e9f7ef")
    if answer_style == "слаб отговор":
        return ("Слаб отговор", "#c0392b", "#fdecea")
    return ("Избягване на въпроса", "#b9770e", "#fff4e5")


def get_debate_result_comment(answer_style: str) -> str:
    if answer_style == "силен отговор":
        return "Убедително представяне с добра видимост за зрителите."
    if answer_style == "слаб отговор":
        return "Колебливо включване, което едва ли ще помогне на партията."
    return "Представяне без сериозен пробив, но и без тежък провал."


def render_debate_tv_view(debate_rows: list[dict], debate_title: str, channel_name: str) -> None:
    if not debate_rows:
        st.info("Няма налични данни за дебата.")
        return

    grouped_rows = {}
    for row in debate_rows:
        slot = row["Слот"]
        grouped_rows.setdefault(slot, []).append(row)

    st.markdown(
        f"""
        <div style="padding:18px; border-radius:16px; background:linear-gradient(90deg, rgba(20,20,20,0.96), rgba(40,40,40,0.92)); color:white; margin-bottom:18px; border:1px solid rgba(255,255,255,0.08);">
            <div style="display:flex; justify-content:space-between; align-items:center; gap:18px; flex-wrap:wrap;">
                <div>
                    <div style="font-size:1.2rem; font-weight:800; margin-bottom:6px;">📺 {debate_title}</div>
                    <div style="opacity:0.82;">Специално студио на {channel_name} — въпроси, сблъсък на позиции и моментни оценки.</div>
                </div>
                <div style="background:#c62828; color:white; padding:6px 12px; border-radius:999px; font-weight:800; letter-spacing:0.04em;">НА ЖИВО</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for slot in sorted(grouped_rows.keys()):
        slot_rows = grouped_rows[slot]
        first_row = slot_rows[0]
        question = first_row["Въпрос"]
        tone = translate_debate_tone(first_row.get("Тон на дебата", "спокоен тон"))

        st.markdown(
            f"""
            <div style="padding:14px 16px; border-radius:14px; background:rgba(25,25,25,0.92); color:white; margin:14px 0 12px 0; border-left:6px solid #d32f2f;">
                <div style="font-size:0.9rem; opacity:0.82; margin-bottom:6px;">Въпрос {slot} · {tone}</div>
                <div style="font-size:1.05rem; font-weight:700;">{question}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        columns = st.columns(2)
        for index, row in enumerate(slot_rows):
            party_name = row["Политическа Партия"]
            answer_style = row["Как е отговорила партията"]
            badge_text, badge_color, badge_bg = get_debate_result_badge(answer_style)
            comment_text = get_debate_result_comment(answer_style)
            logo_html = build_logo_html(party_name, max_width=90, max_height=90)

            with columns[index % 2]:
                st.markdown(
                    f"""
                    <div style="padding:16px; border-radius:14px; border:1px solid rgba(0,0,0,0.10); background:rgba(255,255,255,0.68); margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; gap:18px; min-height:150px;">
                        <div style="flex:1;">
                            <div style="font-size:1.02rem; font-weight:800; margin-bottom:10px;">{party_name}</div>
                            <div style="display:inline-block; padding:6px 10px; border-radius:999px; background:{badge_bg}; color:{badge_color}; font-weight:800; margin-bottom:10px;">
                                {badge_text}
                            </div>
                            <div style="font-size:0.95rem; opacity:0.92;">{comment_text}</div>
                        </div>
                        <div style="width:100px; min-width:100px; display:flex; justify-content:center; align-items:center;">
                            {logo_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
def translate_action_slot(slot: str) -> str:
    mapping = {
        "primary": "Първи етап",
        "secondary": "Втори етап",
    }
    return mapping.get(slot, slot)


def translate_action_type(action_type: str) -> str:
    mapping = {
        "boost_campaign": "Подсилване на кампанията",
        "attack_opponent": "Атака срещу опонент",
        "fabricate_scandal": "Скандална атака",
    }
    return mapping.get(action_type, action_type)


def translate_action_variant(variant: str) -> str:
    mapping = {
        "social_media_outreach": "кампания в социалните мрежи",
        "national_tour": "национална обиколка",
        "tv_interview": "телевизионно интервю",
        "policy_announcement": "политическо обещание / програма",
        "corruption_accusation": "обвинение в корупция",
        "policy_attack": "атака по политики",
        "leader_attack": "персонална атака срещу лидера",
        "negative_ads": "негативна рекламна кампания",
        "fake_corruption_scandal": "изфабрикуван корупционен скандал",
        "leaked_documents": "изтекли документи",
        "identity_based_scandal": "идентичностен скандал",
        "foreign_influence_accusation": "обвинение за чуждо влияние",
    }
    return mapping.get(variant, variant)


def translate_success(success_value) -> str:
    if success_value in {True, "Yes", "yes", "Да"}:
        return "Да"
    if success_value in {False, "No", "no", "Не"}:
        return "Не"
    return str(success_value)


def build_campaign_stage_display_rows(resolved_actions: list[dict]) -> list[dict]:
    rows = []

    for action in resolved_actions:
        party = action.get("party", action.get("Party", "Неизвестна партия"))
        slot = action.get("action_slot", action.get("Action slot", ""))
        action_type = action.get("action_type", action.get("Action", ""))
        variant = action.get("variant", action.get("Variant", ""))
        target = action.get("target_party", action.get("Target", None))
        success = action.get("success", action.get("Success", ""))
        success_chance = action.get("success_chance", action.get("Success chance", 0))
        if isinstance(success_chance, float):
            success_chance = int(success_chance * 100)
        multiplier = action.get("multiplier", action.get("Effect strength", 0))

        rows.append(
            {
                "Партия": party,
                "Етап": translate_action_slot(slot),
                "Тип ход": translate_action_type(action_type),
                "Конкретен ход": translate_action_variant(variant),
                "Цел": target if target not in {None, "None", "—", ""} else "Няма пряка цел",
                "Успех": translate_success(success),
                "Шанс за успех (%)": success_chance,
                "Сила на ефекта": round(multiplier, 2) if isinstance(multiplier, (int, float)) else multiplier,
            }
        )

    return rows


def render_campaign_stage_cards(resolved_actions: list[dict]) -> None:
    display_rows = build_campaign_stage_display_rows(resolved_actions)
    columns = st.columns(2)

    for index, row in enumerate(display_rows):
        target_text = row["Цел"]
        success_text = row["Успех"]
        success_color = "#1f9d55" if success_text == "Да" else "#c0392b"

        with columns[index % 2]:
            logo_path = get_logo_path(row["Партия"])

            logo_html = ""
            if logo_path:
                logo_html = f'<img src="data:image/png;base64,{encode_image_to_base64(logo_path)}" style="max-width:160px; max-height:160px; object-fit:contain;" />'

            st.markdown(
                f"""
                <div style="padding:16px; border-radius:14px; border:1px solid rgba(0,0,0,0.10); background:rgba(255,255,255,0.65); margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; gap:24px; min-height:220px;">
                    <div style="flex:1;">
                        <div style="font-size:1.08rem; font-weight:700; margin-bottom:8px;">{row['Партия']}</div>
                        <div style="margin-bottom:6px;"><strong>Етап:</strong> {row['Етап']}</div>
                        <div style="margin-bottom:6px;"><strong>Тип ход:</strong> {row['Тип ход']}</div>
                        <div style="margin-bottom:6px;"><strong>Конкретен ход:</strong> {row['Конкретен ход']}</div>
                        <div style="margin-bottom:6px;"><strong>Цел:</strong> {target_text}</div>
                        <div style="margin-bottom:6px;"><strong>Шанс за успех:</strong> {row['Шанс за успех (%)']}%</div>
                        <div style="margin-bottom:6px;"><strong>Сила на ефекта:</strong> {row['Сила на ефекта']}</div>
                        <div style="font-weight:700; color:{success_color};"><strong>Успех:</strong> {success_text}</div>
                    </div>
                    <div style="width:180px; min-width:180px; display:flex; justify-content:center; align-items:center;">
                        {logo_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
def render_interactive_debate_inputs(debate_key: str, debate_rows: list[dict]) -> None:
    question_options = [item[ "въпрос"] for item in DEBATE_QUESTION_BANK]
    slots = sorted({row["Слот"] for row in debate_rows})

    for slot in slots:
        slot_rows = [row for row in debate_rows if row["Слот"] == slot]
        first_row = slot_rows[0]

        question_key = f"{debate_key}_slot_{slot}_question"
        tone_key = f"{debate_key}_slot_{slot}_tone"

        default_question_index = question_options.index(first_row[ "Въпрос"]) if first_row[ "Въпрос"] in question_options else 0
        default_tone_index = DEBATE_TONES.index(first_row.get("Тон на дебата", "спокоен тон")) if first_row.get("Тон на дебата", "спокоен тон") in DEBATE_TONES else 0

        st.markdown(f"**Question Slot {slot}**")
        st.selectbox(
            f"Choose question for slot {slot}",
            question_options,
            index=default_question_index,
            key=question_key,
        )
        st.selectbox(
            f"Choose debate tone for slot {slot}",
            DEBATE_TONES,
            index=default_tone_index,
            key=tone_key,
        )

def build_event_rows(event_rows: list[dict]) -> list[dict]:
    return event_rows
def translate_event_response(response: str) -> str:
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


def build_event_display_rows(event_rows: list[dict]) -> list[dict]:
    rows = []

    for row in event_rows:
        party = row.get("Party", row.get("Политическа Партия", "Неизвестна партия"))
        selected_response = row.get("Selected response", row.get("Избрана реакция", ""))
        applied_response = row.get("Applied response", row.get("Приложена реакция", ""))
        success = row.get("Success", row.get("Успех", ""))
        outcome = row.get("Outcome", row.get("Ефект", ""))
        allowed_responses = row.get("Allowed responses", row.get("Разрешени реакции", ""))

        rows.append(
            {
                "Партия": party,
                "Избрана реакция": translate_event_response(selected_response),
                "Приложена реакция": translate_event_response(applied_response),
                "Успех": translate_success(success),
                "Ефект": outcome,
                "Разрешени реакции": ", ".join(
                    translate_event_response(item.strip())
                    for item in allowed_responses.split(",")
                    if item.strip()
                ) if isinstance(allowed_responses, str) and allowed_responses else "",
            }
        )

    return rows


def render_event_reaction_cards(event_rows: list[dict]) -> None:
    display_rows = build_event_display_rows(event_rows)
    columns = st.columns(2)

    for index, row in enumerate(display_rows):
        success_text = row["Успех"]
        success_color = "#1f9d55" if success_text == "Да" else "#c0392b"
        allowed_block = ""
        if row["Разрешени реакции"]:
            allowed_block = (
                f"<div style='margin-top:8px; font-size:0.93rem; opacity:0.85;'>"
                f"<strong>Възможни реакции:</strong> {row['Разрешени реакции']}</div>"
            )

        with columns[index % 2]:
            st.markdown(
                f"<div style=\"padding:16px; border-radius:14px; border:1px solid rgba(0,0,0,0.10); background:rgba(255,255,255,0.65); margin-bottom:14px;\">"
                f"<div style=\"font-size:1.08rem; font-weight:700; margin-bottom:8px;\">{row['Партия']}</div>"
                f"<div style=\"margin-bottom:6px;\"><strong>Избрана реакция:</strong> {row['Избрана реакция']}</div>"
                f"<div style=\"margin-bottom:6px;\"><strong>Приложена реакция:</strong> {row['Приложена реакция']}</div>"
                f"<div style=\"margin-bottom:6px; font-weight:700; color:{success_color};\"><strong>Успех:</strong> {success_text}</div>"
                f"<div style=\"margin-top:8px;\"><strong>Политически ефект:</strong> {row['Ефект']}</div>"
                f"{allowed_block}"
                f"</div>",
                unsafe_allow_html=True,
            )

def build_poll_rows(poll_results: list[dict]) -> list[dict]:
    return poll_results


def build_poll_summary(poll_results: list[dict]) -> str:
    if not poll_results:
        return "Няма налично социологическо обобщение."

    ranked = sorted(poll_results, key=lambda row: row["Резултати от Проучването %"], reverse=True)
    top = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None
    bottom = ranked[-1]

    if second is None:
        return f"{top['Политическа Партия']} е единствената партия в това проучване."

    gap = top["Резултати от Проучването %"] - second["Резултати от Проучването %"]

    if gap >= 5:
        race_text = f"{top['Политическа Партия']} има ясна преднина пред {second['Политическа Партия']}."
    elif gap >= 2:
        race_text = f"{top['Политическа Партия']} води, но {second['Политическа Партия']} остава в рамките на конкурентна дистанция."
    else:
        race_text = f"Надпреварата е много оспорвана, като {top['Политическа Партия']} е само с минимална преднина пред {second['Политическа Партия']}."

    return f"{race_text} {bottom['Политическа Партия']} засега има най-слаба подкрепа в това междинно социологическо проучване."

def render_event_card(event_card: dict) -> None:
    st.write(f"### {event_card['title']}")
    st.caption(event_card["description"])

def collect_interactive_debate_rows(debate_key: str, debate_rows: list[dict]) -> list[dict]:
    updated_rows = []
    slots = sorted({row["Слот"] for row in debate_rows})

    for slot in slots:
        slot_rows = [row for row in debate_rows if row["Слот"] == slot]

        selected_question = st.session_state.get(
            f"{debate_key}_slot_{slot}_question",
            slot_rows[0][ "Въпрос"],
        )
        selected_tone = st.session_state.get(
            f"{debate_key}_slot_{slot}_tone",
            slot_rows[0].get("Тон на дебата", "спокоен тон"),
        )

        matching_item = next(
            item for item in DEBATE_QUESTION_BANK
            if item[ "въпрос"] == selected_question
        )

        for row in slot_rows:
            updated_rows.append(
                {
                    "Слот": slot,
                     "Въпрос": selected_question,
                    "Тема на дебата": matching_item["theme"],
                    "Тон на дебата": selected_tone,
                    "Политическа Партия": row["Политическа Партия"],
                    "Как е отговорила партията": row.get("Как е отговорила партията", "избягване на въпроса"),
                }
            )

    return updated_rows

def auto_resolve_debate_rows(debate_rows: list[dict]) -> list[dict]:
    resolved_rows = []

    for row in debate_rows:
        question_item = next(
            (item for item in DEBATE_QUESTION_BANK if item["въпрос"] == row["Въпрос"]),
            None
        )

        if question_item is None:
            continue

        party = row["Политическа Партия"]
        theme = row["Тема на дебата"]
        tone = row.get("Тон на дебата", "спокоен тон")
        tone_effect = DEBATE_TONE_EFFECTS.get(tone, DEBATE_TONE_EFFECTS["спокоен тон"])
        profile = PARTY_PROFILES[party]

        issue_fit = question_item["party_fit"].get(party, 0.50)
        leader_strength = profile.leader_strength

        if theme in {"economy", "living_standards", "public_services"}:
            topic_strength = profile.economic_competence
        elif theme == "corruption":
            topic_strength = profile.change_reputation
        elif theme == "trust":
            topic_strength = max(profile.change_reputation, profile.leader_strength * 0.6)
        elif theme == "security":
            topic_strength = profile.security_reputation
        elif theme == "minority_relations":
            topic_strength = max(profile.minority_muslim_appeal, profile.progressive_appeal * 0.5)
        else:
            topic_strength = 0.50

        score = (
            issue_fit * tone_effect["issue_weight"]
            + leader_strength * tone_effect["leader_weight"]
            + topic_strength * 0.20
            + random.gauss(0, tone_effect["randomness"] * 0.19)
        )

        if score >= 0.68:
            answer_style = "силен отговор"
        elif score <= 0.48:
            answer_style = "слаб отговор"
        else:
            answer_style = "избягване на въпроса"

        resolved_rows.append(
            {
                "Слот": row["Слот"],
                 "Въпрос": row[ "Въпрос"],
                "Тема на дебата": row["Тема на дебата"],
                "Тон на дебата": tone,
                "Политическа Партия": party,
                "Как е отговорила партията": answer_style,
            }
        )

    return resolved_rows

def build_vote_buying_target_regions(party_name: str, count: int = 2) -> list[str]:
    affinities = PARTY_PROFILES[party_name].regional_affinity
    return [
        region for region, _ in sorted(
            affinities.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:count]
    ]


def run_vote_buying_phase() -> list[dict]:
    rows = []

    for party_name in PARTY_PROFILES.keys():
        attempt_chance = VOTE_BUYING_ATTEMPT.get(party_name, 0.0)
        success_chance = VOTE_BUYING_SUCCESS.get(party_name, 0.0)
        attempted = random.random() < attempt_chance

        if attempted:
            target_regions = build_vote_buying_target_regions(party_name)
            success = random.random() < success_chance
            rows.append(
                {
                    "Политическа Партия": party_name,
                    "Attempted": "Yes",
                    "Target regions": ", ".join(target_regions),
                    "Success": "Yes" if success else "No",
                    "Attempt chance": int(attempt_chance * 100),
                    "Success chance": int(success_chance * 100),
                    "Outcome": (
                        "Machine networks and clientelist pressure increased turnout and loyalty, but the tactic also carried a reputational cost."
                        if success
                        else "The effort was inefficient, increased resentment among affected voters, and damaged the party's image."
                    ),
                }
            )
        else:
            rows.append(
                {
                    "Политическа Партия": party_name,
                    "Attempted": "No",
                    "Target regions": "—",
                    "Success": "—",
                    "Attempt chance": int(attempt_chance * 100),
                    "Success chance": int(success_chance * 100),
                    "Outcome": "The party chose not to engage in vote buying during this phase.",
                }
            )

    return rows


def apply_vote_buying_effects(voters: list, vote_buying_rows: list[dict]) -> None:
    for row in vote_buying_rows:
        if row["Attempted"] != "Yes":
            continue

        party = row["Политическа Партия"]
        target_regions = row["Target regions"].split(", ")
        success = row["Success"] == "Yes"
        effects = VOTE_BUYING_EFFECTS.get(
            party,
            {
                "loyalty_gain": 0.05,
                "turnout_gain": 0.04,
                "campaign_gain": 0.01,
                "failure_anger": 0.03,
                "failure_loyalty_loss": 0.04,
                "reputation_cost": 0.02,
                "anti_machine_anger": 0.02,
            },
        )

        for voter in voters:
            if voter.region not in target_regions:
                continue

            # Automatic reputational cost for merely engaging in vote buying.
            if voter.current_preference == party and voter.patronage_dependence < 0.45:
                voter.party_loyalty = max(0.0, voter.party_loyalty - effects["reputation_cost"])

            # Anti-machine voters react negatively to the tactic even if it works.
            if voter.current_preference != party and voter.patronage_dependence < 0.30:
                voter.anger = min(1.0, voter.anger + effects["anti_machine_anger"])

            if voter.current_preference == party or voter.patronage_dependence > 0.65:
                if success:
                    voter.party_loyalty = min(1.0, voter.party_loyalty + effects["loyalty_gain"])
                    voter.turnout_probability = min(1.0, voter.turnout_probability + effects["turnout_gain"])
                    voter.campaign_interest = min(1.0, voter.campaign_interest + effects["campaign_gain"])
                else:
                    voter.anger = min(1.0, voter.anger + effects["failure_anger"])
                    voter.party_loyalty = max(0.0, voter.party_loyalty - effects["failure_loyalty_loss"])


def build_vote_buying_rows(vote_buying_rows: list[dict]) -> list[dict]:
    return vote_buying_rows

def get_stage_label(stage: int) -> str:
    labels = {
        0: "С откриването на предизборната кампания, можете да се запознаете с партийте",
        1: "Кампаниите на Политическите Партии са официално открити! Ето и първите дейности на партиите!",
        2: "Извънредни Новини! Как ще реагират партиите?",
        3: "Първият Лидерски Дебат е на живо по pTV",
        4: "Ето и първото социологическо проучване! На кого имат най-голямо доверие гражданите на Пустиняково?",
        5: "Партиите продължават своите кампании, ето и какво напраиха те:",
        6: "Извънредни Новини! Как ще реагират партиите?",
        7: "Вторият Лидерски Дебат е на живо по NovaTV",
        8: "Финална Мобилизация",
        9: "Изборният ден е официално закрит!",
    }
    return labels.get(stage, "В момента тече политическа кампания")


def render_stage_banner(stage: int) -> None:
    stage_titles = {
        0: ("🧭 Преди началото на кампанията","Партиите влизат в предизборния период с различни ресурси, образи и политически стратегии."),
        1: ("🟦 Откриване на Кампаниите", "Кои са първите цели на кампаниите си, които партиите поставиха?"),
        2: ("⚡ Извънредни Новини!", "Как ще реагират партийте! Всички са под обществено наблюдение, и най-малката грешка в реакцията може да им коства!"),
        3: ("🎤 Първият Лидерски Дебат по pTV", "В първият политически дебат, политическите лидери имат възможността да представят своите позиции по различни теми и да спечелят гласа на хората!"),
        4: ("📊 Първо Социологическо проучване", "В средата на кампанията отправяме поглед към социологическото проучване на PalfaReserach. Кой има преднина?"),
        5: ("🟧 Как партиите продължават кампанните си?", "Кампанията продължата, но изборите наближават, сега е времето за добри стратегически решения!"),
        6: ("⚡ Извънредни Новини!", "Пореден обществен шок по важна тема! Какви са реакциите на законодателите?"),
        7: ("🎤 Вторият Лидерски Дебат по NovaTV", "Във вторият лидерски дебат, лидерите имат възможност да си оправят бакиите от предния дебат!"),
        8: ("🟥 Финална Мобилизация", "Ще успеят ли партиите да организират сигурния си вот?"),
        9: ("🗳️ Изборите Приключиха! Кои са победителите?", "Централната Избирателна Комисия е обработила резултатите! Ето кои са новите 120!"),
    }

    title, subtitle = stage_titles.get(stage, ("Campaign", "Political competition is underway."))

    st.markdown(
        f"""
        <div style="padding: 16px 18px; border-radius: 14px; background: linear-gradient(90deg, rgba(31,119,180,0.12), rgba(255,255,255,0.02)); border: 1px solid rgba(255,255,255,0.10); margin: 8px 0 18px 0;">
            <div style="font-size: 1.15rem; font-weight: 700; margin-bottom: 6px;">{title}</div>
            <div style="opacity: 0.85;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def initialize_campaign_state() -> dict:
    voters = generate_population(REGION_PROFILES)

    for voter in voters:
        assign_initial_preference(voter, PARTY_PROFILES)

    party_actions = choose_party_actions(PARTY_PROFILES)

    primary_actions = extract_primary_actions(party_actions)
    resolved_window_1 = resolve_primary_window(primary_actions)

    event_card_1 = draw_event_card(window=1)
    event_rows_1 = build_event_phase_rows(event_card_1, PARTY_PROFILES)

    debate_rows_1 = run_leader_debate(PARTY_PROFILES)


    secondary_actions = extract_secondary_actions(party_actions)
    resolved_window_2 = resolve_secondary_window(secondary_actions)

    event_card_2 = draw_event_card(window=2)
    event_rows_2 = build_event_phase_rows(event_card_2, PARTY_PROFILES)

    debate_rows_2 = run_leader_debate(PARTY_PROFILES)
    vote_buying_rows = run_vote_buying_phase()

    return {
        "stage": 0,
        "voters": voters,
        "resolved_window_1": resolved_window_1,
        "event_card_1": event_card_1,
        "event_rows_1": event_rows_1,
        "debate_rows_1": debate_rows_1,
        "early_poll_results": None,
        "poll_released": False,
        "resolved_window_2": resolved_window_2,
        "event_card_2": event_card_2,
        "event_rows_2": event_rows_2,
        "debate_rows_2": debate_rows_2,
        "vote_buying_rows": vote_buying_rows,
        "event_1_resolved": False,
        "debate_1_resolved": False,
        "event_2_resolved": False,
        "debate_2_resolved": False,
        "results": None,
    }

def get_party_intro_text(party_name: str) -> dict:
    descriptions = {
        "ПКП- Ново Начало": {
            "profile": "Управляваща, властово-консервативна партия",
            "summary": "ПКП- Ново Начало залага на стабилност, силна държава, контрол и добре изградени местни мрежи.",
            "strengths": "Сигурност, властови ресурс, патронажни мрежи",
        },
        "Демократично Пустиняково": {
            "profile": "Градска реформаторска опозиция",
            "summary": "Демократично Пустиняково се позиционира като антикорупционна, проевропейска и модернизаторска алтернатива.",
            "strengths": "Антикорупция, институции, публични услуги",
        },
        "ГЕРП": {
            "profile": "Прагматична системна партия",
            "summary": "ГЕРП се стреми да изглежда като умерена и управленски компетентна сила, която може да внесе ред и предвидимост.",
            "strengths": "Икономика, управленски опит, стабилност",
        },
        "СХДС": {
            "profile": "Консервативна християн-демократическа партия",
            "summary": "СХДС съчетава традиционализъм, вяра, единство и фокус върху реда, сигурността и регионалните проблеми.",
            "strengths": "Сигурност, ред, регионално развитие, традиционни норми",
        },
        "ДПС": {
            "profile": "Партия с регионално и малцинствено ядро",
            "summary": "ДПС разчита на силна локална концентрация, представителство на малцинствени общности и дисциплиниран електорат.",
            "strengths": "Местна идентичност, малцинствено представителство, мобилизация",
        },
        "Израждане": {
            "profile": "Популистка националистическа опозиция",
            "summary": "Израждане използва антиелитна, антизападна и силно конфронтационна реторика, насочена към протестен вот.",
            "strengths": "Популизъм, протестен електорат, националистическа мобилизация",
        },
        "Пустиняшка Промяна": {
            "profile": "Нова протестна партия",
            "summary": "Пустиняшка Промяна се опитва да събере недоволните от стария елит и да се представи като свежа алтернатива.",
            "strengths": "Протестен вот, антисистемен импулс, реформистки образ",
        },
    }
    return descriptions.get(
        party_name,
        {
            "profile": "Политическа партия",
            "summary": "Няма налично кратко описание.",
            "strengths": "Няма налични данни.",
        },
    )

def render_zero_window() -> None:
    st.write("### Политическа обстановка преди началото на кампанията")
    st.caption("Преди официалния старт на кампанията избирателите и медиите оценяват основните политически сили, техните профили и шансове.")

    st.markdown(
        """
        <div style="padding:16px; border-radius:14px; border:1px solid rgba(0,0,0,0.10); background:rgba(255,255,255,0.65); margin-bottom:18px;">
            <div style="font-size:1.05rem; font-weight:700; margin-bottom:8px;">Общ контекст</div>
            <div style="margin-bottom:6px;">Страната навлиза в нов предизборен период на фона на натрупано недоверие, силна поляризация и борба между статукво и промяна.</div>
            <div style="margin-bottom:6px;">Основните теми в общественото пространство са корупцията, сигурността, стандартът на живот, регионалните неравенства и стабилността на институциите.</div>
            <div>Изходът от изборите ще зависи не само от твърдите ядра, но и от способността на партиите да овладеят дневния ред още в първите дни на кампанията.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("### Основни политически сили")

    parties = list(PARTY_PROFILES.keys())
    columns = st.columns(2)

    for index, party_name in enumerate(parties):
        party_info = get_party_intro_text(party_name)
        logo_html = build_logo_html(party_name, max_width=120, max_height=120)

        with columns[index % 2]:
            st.markdown(
                f"""
                <div style="padding:16px; border-radius:14px; border:1px solid rgba(0,0,0,0.10); background:rgba(255,255,255,0.65); margin-bottom:14px; display:flex; justify-content:space-between; align-items:center; gap:20px; min-height:200px;">
                    <div style="flex:1;">
                        <div style="font-size:1.08rem; font-weight:700; margin-bottom:8px;">{party_name}</div>
                        <div style="margin-bottom:8px;"><strong>Профил:</strong> {party_info['profile']}</div>
                        <div style="margin-bottom:8px;"><strong>Кратко описание:</strong> {party_info['summary']}</div>
                        <div><strong>Силни страни:</strong> {party_info['strengths']}</div>
                    </div>
                    <div style="width:140px; min-width:140px; display:flex; justify-content:center; align-items:center;">
                        {logo_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

def run_cli_campaign() -> tuple[list, dict]:
    campaign_state = initialize_campaign_state()
    voters = campaign_state["voters"]

    apply_resolved_actions_to_voters(voters, campaign_state["resolved_window_1"])
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    apply_debate_effects(voters, campaign_state["debate_rows_1"])
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    apply_resolved_actions_to_voters(voters, campaign_state["resolved_window_2"])
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    apply_debate_effects(voters, campaign_state["debate_rows_2"])
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    apply_vote_buying_effects(voters, campaign_state["vote_buying_rows"])
    update_preferences_after_campaign(voters, PARTY_PROFILES)

    results = run_baseline_election(voters, PARTY_PROFILES)
    return voters, results

def build_monte_carlo_rows(summary: dict) -> list[dict]:
    rows = []

    for party, avg_share in summary["most_likely_ranking"]:
        min_share = summary["min_vote_share"][party]
        max_share = summary["max_vote_share"][party]
        wins = summary["win_counter"][party]
        win_rate = wins / summary["num_runs"] * 100
        rows.append(
            {
                "Политическа Партия": party,
                "Average vote share %": round(avg_share, 2),
                "Min %": round(min_share, 2),
                "Max %": round(max_share, 2),
                "Wins": wins,
                "Win rate %": round(win_rate, 2),
            }
        )

    return rows


def build_voter_explanation_rows(voters: list, limit: int = 20) -> list[dict]:
    rows = []

    explained_voters = [
        voter for voter in voters
        if voter.did_vote and voter.final_vote and voter.vote_explanation
    ]

    for voter in explained_voters[:limit]:
        rows.append(
            {
                "Voter ID": voter.voter_id,
                "Region": voter.region,
                "Age group": voter.age_group,
                "Religious group": voter.religious_group,
                "Final vote": voter.final_vote,
                "Explanation": voter.vote_explanation,
            }
        )

    return rows


def run_streamlit_app() -> None:
    st.set_page_config(page_title="Избори в Пустиняково", layout="wide")

    if "app_mode" not in st.session_state:
        st.session_state.app_mode = None

    if "campaign_state" not in st.session_state:
        st.session_state.campaign_state = None

    if st.session_state.app_mode is None:
        st.title("🙋🏻‍♂️Система за гласуване на Република Пустиняково 🇧🇬")
        st.markdown("### ↘️Изберете тип избори")

        col1, col2 = st.columns(2)

        if col1.button("🗳️Избори за Върховен Конгрес на Република Пустиняково", use_container_width=True):
            st.session_state.app_mode = "general"
            st.rerun()

        if col2.button("🗺️ Национални Губернаторски Избори 🗳️", use_container_width=True):
            st.session_state.app_mode = "governor"
            st.rerun()

        # --- NEW SECTION ---
        st.markdown("---")
        st.markdown("### 📊 Референдуми и Социологически проучвания")

        col3, col4 = st.columns(2)

        if col3.button("🗳️ Референдум", use_container_width=True):
            st.session_state.app_mode = "referendum"
            st.rerun()

        if col4.button("📈 Социологически проучвания", use_container_width=True):
            st.session_state.app_mode = "polls"
            st.rerun()

        st.markdown("---")
        st.markdown("### 🏛️ Конгрес на Република Пустиняково 🇧🇬")

        st.link_button(
            "🏛️ Система за гласуване на Върховния Конгрес на Република Пустиняково 🇧🇬",
            "https://rational-vote-choice-simulation-yynnne6kpfqjgqtkddahsq.streamlit.app/",
            use_container_width=True,
        )

        return

    if st.session_state.app_mode == "governor":
        render_governor_mode()
        return


    if st.session_state.app_mode == "referendum":
        st.title("🗳️ Референдум")
        st.warning("Режимът за референдуми все още не е имплементиран.")

        if st.button("🔙 Назад към менюто"):
            st.session_state.app_mode = None
            st.rerun()

        return

    if st.session_state.app_mode == "polls":
        render_polling_mode()
        return

    if st.session_state.app_mode == "general":
        st.title("🗳️Избори за Върховен Конгрес на Република Пустиняково")
        st.write("Отворете кампанията и преминете стъпка по стъпка през етапите, дебатите и изборния ден.")

        if st.button("🔙 Назад към менюто"):
            st.session_state.app_mode = None
            st.session_state.campaign_state = None  # important reset
            st.rerun()

    top_col_1, top_col_2 = st.columns(2)
    if top_col_1.button("Отвори кампанията", type="primary"):
        launch_status = st.empty()
        launch_progress = st.progress(0)

        launch_status.write("Партиите се подготвят! 🤼‍♂️Гражданите започват да се запознават с партиите - кандидати за новият Върховен Конгрес! 📊Кампаниите сега са по-важни от всякога...")
        launch_progress.progress(20)

        with st.spinner("️️⚙️Периодът на Политически Кампании официално се открива..."):
            st.session_state.campaign_state = initialize_campaign_state()
            time.sleep(5.5)

        launch_status.write("Първите дейности в кампаниите на партиите са ясни...")
        launch_progress.progress(100)
        st.rerun()

    if top_col_2.button("Рестартирай кампанията"):
        st.session_state.campaign_state = None
        st.rerun()

    campaign_state = st.session_state.get("campaign_state", None)
    if campaign_state is None:
        return

    voters = campaign_state["voters"]
    stage = campaign_state["stage"]

    st.info(get_stage_label(stage))
    render_stage_banner(stage)

    if stage >= 0:
        render_zero_window()

        if stage == 0 and st.button("Влез в първия етап на кампанията"):
            with st.spinner(
                    "Партиите официално откриват кампаниите си, а медиите насочват вниманието си към първите им ходове..."):
                time.sleep(2)
                campaign_state["stage"] = 1
            st.rerun()

    if stage >= 1:
        st.write("### Първи етап на кампаниите")
        st.caption("✅ Периодът на политическите кампании официално е открит. Ето какви са първите ходове на партиите.")
        render_campaign_stage_cards(campaign_state["resolved_window_1"])

        if stage == 1 and st.button("Продължи напред"):
            with st.spinner("Гражданите се запознават в кампаниите на партиите и започват да сформират избора си..."):
                apply_resolved_actions_to_voters(voters, campaign_state["resolved_window_1"])
                update_preferences_after_campaign(voters, PARTY_PROFILES)
                time.sleep(5)
                campaign_state["stage"] = 2
            st.rerun()

    if stage >= 2:
        st.write("### Извънредни Новини!")
        st.markdown(f"**{campaign_state['event_card_1']['description']}**")
        if stage == 2 and not campaign_state["event_1_resolved"]:
            if st.button("Как регират партиите?"):
                with st.spinner("Партиите сформират позициите си по темата..."):
                    apply_event_shock(voters, campaign_state["event_card_1"])
                    campaign_state["event_rows_1"] = resolve_event_phase(
                        campaign_state["event_card_1"],
                        campaign_state["event_rows_1"],
                    )
                    campaign_state["event_1_resolved"] = True
                    time.sleep(2)
                st.rerun()
        else:
            render_event_reaction_cards(campaign_state["event_rows_1"])
            if stage == 2 and campaign_state["event_1_resolved"]:
                if st.button("Първи Лидерски Дебат (pTV)"):
                    with st.spinner("📺Представителите на партиите се подготвят за лидерския дебат по pTV"):
                        apply_event_responses(
                            voters,
                            campaign_state["event_card_1"],
                            campaign_state["event_rows_1"],
                        )
                        update_preferences_after_campaign(voters, PARTY_PROFILES)
                        time.sleep(2)
                        campaign_state["stage"] = 3
                    st.rerun()

    if stage >= 3:
        st.write("### 📺1️⃣Първи Лидерски Дебат по pTV")
        if stage == 3 and not campaign_state["debate_1_resolved"]:
            st.caption(
                "Редакцията на pTV е подбрала въпросите, на които представителите на партиите ще отговарят на живо в ефир. Справиха ли се участниците?"
            )
            render_interactive_debate_inputs("debate1", campaign_state["debate_rows_1"])

            if st.button("📈Ето и как се справиха участниците в дебата"):
                with st.spinner("Resolving Debate 1 performances..."):
                    campaign_state["debate_rows_1"] = collect_interactive_debate_rows(
                        "debate1",
                        campaign_state["debate_rows_1"],
                    )
                    campaign_state["debate_rows_1"] = auto_resolve_debate_rows(campaign_state["debate_rows_1"])
                    campaign_state["debate_1_resolved"] = True
                    time.sleep(2)
                st.rerun()
        else:
            render_debate_tv_view(campaign_state["debate_rows_1"], "Първи лидерски дебат", "pTV")
            st.info(build_debate_summary(campaign_state["debate_rows_1"]))

            if stage == 3 and campaign_state["debate_1_resolved"]:
                if st.button("🏢Кампаниите продължават!"):
                    with st.spinner("📰Гражданите четат сутрешния вестник и се запознават с резултата от дебата..."):
                        apply_debate_effects(voters, campaign_state["debate_rows_1"])
                        update_preferences_after_campaign(voters, PARTY_PROFILES)
                        time.sleep(5)
                        campaign_state["stage"] = 4
                    st.rerun()

    if stage >= 4:
        st.write("### Социологическо Проучване на Електорални Нагласи на PalfaResearch")
        st.caption("Какво показва социологическото проучване на PalfaResearch? Кои са фаворитите?")

        if stage == 4 and not campaign_state["poll_released"]:
            if st.button("📊Покажи Социологическо проучване"):
                with st.spinner("PalfaResearch провежда проучването..."):
                    campaign_state["early_poll_results"] = run_poll(voters, PARTY_PROFILES)
                    campaign_state["poll_released"] = True
                    time.sleep(3)
                st.rerun()
        else:
            st.dataframe(build_poll_rows(campaign_state["early_poll_results"]), use_container_width=True)
            st.bar_chart({row["Политическа Партия"]: row["Резултати от Проучването %"] for row in build_poll_rows(campaign_state["early_poll_results"])})
            st.info(build_poll_summary(campaign_state["early_poll_results"]))

            if stage == 4 and campaign_state["poll_released"]:
                if st.button("Още от кампаниите ➡️"):
                    campaign_state["stage"] = 5
                    st.rerun()

    if stage >= 5:
        st.write("### Кампаниите продължават с пълна сила!")
        render_campaign_stage_cards(campaign_state["resolved_window_2"])
        if stage == 5 and st.button("Какво следва➡️"):
            with st.spinner("Динамиката в страната се подрежда..."):
                apply_resolved_actions_to_voters(voters, campaign_state["resolved_window_2"])
                update_preferences_after_campaign(voters, PARTY_PROFILES)
                time.sleep(5)
                campaign_state["stage"] = 6
            st.rerun()
    if stage >= 6:
        st.write("### Опаа.. Пак Извънредни Новини!")
        st.markdown(f"**{campaign_state['event_card_2']['description']}**")
        if stage == 6 and not campaign_state["event_2_resolved"]:
            if st.button("‼️Как реагираха партиите?"):
                with st.spinner("😥Партиите подготвят позициите си..."):
                    apply_event_shock(voters, campaign_state["event_card_2"])
                    campaign_state["event_rows_2"] = resolve_event_phase(
                        campaign_state["event_card_2"],
                        campaign_state["event_rows_2"],
                    )
                    campaign_state["event_2_resolved"] = True
                    time.sleep(2)
                st.rerun()
        else:
            render_event_reaction_cards(campaign_state["event_rows_2"])
            if stage == 6 and campaign_state["event_2_resolved"]:
                if st.button("Продължи към Втори Лидерски Политически Дебат (NovaTV)"):
                    with st.spinner("📰Народа чете вестници..."):
                        apply_event_responses(
                            voters,
                            campaign_state["event_card_2"],
                            campaign_state["event_rows_2"],
                        )
                        update_preferences_after_campaign(voters, PARTY_PROFILES)
                        time.sleep(2)
                        campaign_state["stage"] = 7
                    st.rerun()

    if stage >= 7:
        st.write("### 📺2️⃣ Втори Лидерски Дебат (NovaTV)")
        if stage == 7 and not campaign_state["debate_2_resolved"]:
            st.caption(
                "NovaTV подбира въпросите към представителите на политическите партии."
            )
            render_interactive_debate_inputs("debate2", campaign_state["debate_rows_2"])

            if st.button("Покажи Резултатите от Втория Политически Дебат"):
                with st.spinner("Обработка на резултатите от предизборния дебат..."):
                    campaign_state["debate_rows_2"] = collect_interactive_debate_rows(
                        "debate2",
                        campaign_state["debate_rows_2"],
                    )
                    campaign_state["debate_rows_2"] = auto_resolve_debate_rows(campaign_state["debate_rows_2"])
                    campaign_state["debate_2_resolved"] = True
                    time.sleep(2)
                st.rerun()
        else:
            render_debate_tv_view(campaign_state["debate_rows_2"], "Втори лидерски дебат", "NovaTV")
            st.info(build_debate_summary(campaign_state["debate_rows_2"]))

            if stage == 7 and campaign_state["debate_2_resolved"]:
                if st.button("Продължи към следващата стъпка на кампанията"):
                    with st.spinner("📰Гражданите се запознават с резултата от Вторият Политически Дебат..."):
                        apply_debate_effects(voters, campaign_state["debate_rows_2"])
                        update_preferences_after_campaign(voters, PARTY_PROFILES)
                        time.sleep(5)
                        campaign_state["stage"] = 8
                    st.rerun()

    if stage >= 8:
        st.write("### Мобилизация на вота")
        st.dataframe(build_vote_buying_rows(campaign_state["vote_buying_rows"]), use_container_width=True)

        if stage == 8 and st.button("🗳️Открий Изборния Ден"):
            progress_text = st.empty()
            progress_bar = st.progress(0)

            progress_text.write("🫳🗳️Гражданите на Пустиняково гласуват...")
            progress_bar.progress(20)
            apply_vote_buying_effects(voters, campaign_state["vote_buying_rows"])
            time.sleep(4.5)

            progress_text.write("🎬Прекратяване на изборния ден...")
            progress_bar.progress(45)
            update_preferences_after_campaign(voters, PARTY_PROFILES)
            time.sleep(4.5)

            progress_text.write("📊Обработка на регионалните изборни протколи...")
            progress_bar.progress(75)
            campaign_state["results"] = run_baseline_election(voters, PARTY_PROFILES)
            time.sleep(4.5)

            progress_text.write("🗂️Обработка на изборните протоколи в ЦИК...")
            progress_bar.progress(100)
            campaign_state["stage"] = 9
            st.rerun()

    if stage >= 9 and campaign_state["results"] is not None:
        results = campaign_state["results"]

        st.success("Изборният Ден Приключи! Резултатите са обработени и говоти за оповестяване!")
        st.subheader("Резултати от Изборите")
        st.caption("Финалните резултати се оповостяват, след като бъдат обработени в края на изборние процес!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Избирателнта Активност", f"{results['turnout_rate'] * 100:.2f}%")
        col2.metric("Валидни гласове", f"{results['valid_votes']:,}")
        estimated_real_votes = int(results["valid_votes"] * (REAL_ACTIVE_VOTERS / SIM_POPULATION))
        col3.metric("Valid votes (estimated real)", f"{estimated_real_votes:,}")

        st.write("### Национални Резултати")
        st.dataframe(build_single_run_rows(results), use_container_width=True)
        st.bar_chart({
            row.get("Политическа Партия", "Unknown"): row.get("Резултати от Проучването %", 0)
            for row in build_poll_rows(campaign_state["early_poll_results"])
        })
        st.write("### Регионални резултати и избирателна активност")
        st.dataframe(build_regional_rows(results), use_container_width=True)

        st.write("### Защо партиите печелят в районите?")
        st.dataframe(build_regional_explanation_rows(results), use_container_width=True)

def build_debate_summary(debate_rows: list[dict]) -> str:
    if not debate_rows:
        return "Няма налични данни за дебата."
    score_map = {"силен отговор": 2, "избягване на въпроса": 1, "слаб отговор": 0}
    party_scores = {}

    for row in debate_rows:
        party = row["Политическа Партия"]
        score = score_map.get(row["Как е отговорила партията"], 1)
        party_scores[party] = party_scores.get(party, 0) + score

    if not party_scores:
        return "No debate summary available."

    ranked = sorted(party_scores.items(), key=lambda item: item[1], reverse=True)

    best_party, best_score = ranked[0]
    worst_party, worst_score = ranked[-1]

    if len(ranked) > 1 and ranked[1][1] == best_score:
        best_text = f"{best_party} и {ranked[1][0]} се справиха най-добре по време на дебата!"
    else:
        best_text = f"{best_party} се справи най-добре по време на дебата!"

    if len(ranked) > 1 and ranked[-2][1] == worst_score:
        worst_text = f"{worst_party} и {ranked[-2][0]} се справиха най-зле по време на дебата!"
    else:
        worst_text = f"{worst_party} се справи най-зле по време на дебата!"

    score_gap = best_score - worst_score
    if score_gap >= 4:
        effect_text = "Този дебат най-вероятно ще създаде забележителен ефект на моментум и ще затвърди подкрепата на най-добре справящата се партия!"  #This debate is likely to produce a noticeable momentum effect and strengthen the best-performing party’s support.
    elif score_gap >= 2:
        effect_text = "Този дебат най-вероятно ще създаде умерено затвърждаване на партиите, които се справиха добре, и ще повлия негативно на тези, които не се справиха толкова добре!" #"This debate may modestly strengthen силен отговорer performers and slightly слаб отговорen слаб отговорer parties."
    else:
        effect_text = "Този дебат бе изключително балансиран и най-вероятно няма да повлия сам по себе си на изборните резултати!"#"This debate was relatively balanced and is unlikely to transform the race on its own."

    return f"{best_text}, докато {worst_text}. {effect_text}"

def main() -> None:
    if st is not None:
        run_streamlit_app()
        return

    voters, results = run_cli_campaign()
    print_population_summary(voters)
    print_preference_summary(voters)
    print_election_results(results)


if __name__ == "__main__":
    main()