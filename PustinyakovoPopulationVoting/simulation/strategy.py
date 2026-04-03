import random

from simulation.utils import clip

ACTION_TYPES = [
    "boost_campaign",
    "attack_opponent",
    "fabricate_scandal",
]

PRIMARY_ACTION_SUCCESS = {
    "boost_campaign": 0.60,
    "attack_opponent": 0.50,
    "fabricate_scandal": 0.40,
}

SECONDARY_ACTION_SUCCESS = {
    "boost_campaign": 0.40,
    "attack_opponent": 0.30,
    "fabricate_scandal": 0.20,
}

PRIMARY_ACTION_MULTIPLIER = 1.0
SECONDARY_ACTION_MULTIPLIER = 0.60

AGGRESSIVE_ACTIONS = {
    "attack_opponent",
    "fabricate_scandal",
}

ACTION_VARIANTS = {
    "boost_campaign": [
        "social_media_outreach",
        "national_tour",
        "tv_interview",
        "policy_announcement",
    ],
    "attack_opponent": [
        "corruption_accusation",
        "policy_attack",
        "leader_attack",
        "negative_ads",
    ],
    "fabricate_scandal": [
        "fake_corruption_scandal",
        "leaked_documents",
        "identity_based_scandal",
        "foreign_influence_accusation",
    ],
}


def choose_action_variant(action_type: str) -> str:
    return random.choice(ACTION_VARIANTS[action_type])



def choose_party_actions(parties: dict) -> dict:
    party_actions = {}

    for party_name in parties.keys():
        primary_action = random.choice(ACTION_TYPES)
        available_secondary_actions = [action for action in ACTION_TYPES if action != primary_action]
        secondary_action = random.choice(available_secondary_actions)

        attack_targets = [name for name in parties.keys() if name != party_name]
        primary_target = random.choice(attack_targets) if primary_action in {"attack_opponent", "fabricate_scandal"} else None
        secondary_target = random.choice(attack_targets) if secondary_action in {"attack_opponent", "fabricate_scandal"} else None
        primary_variant = choose_action_variant(primary_action)
        secondary_variant = choose_action_variant(secondary_action)

        party_actions[party_name] = {
            "primary_action": primary_action,
            "primary_variant": primary_variant,
            "primary_target": primary_target,
            "secondary_action": secondary_action,
            "secondary_variant": secondary_variant,
            "secondary_target": secondary_target,
        }

    return party_actions



def resolve_party_action(party_name: str, action_type: str, variant: str, target_party: str | None, action_slot: str) -> dict:
    if action_slot == "primary":
        success_chance = PRIMARY_ACTION_SUCCESS[action_type]
        multiplier = PRIMARY_ACTION_MULTIPLIER
    else:
        success_chance = SECONDARY_ACTION_SUCCESS[action_type]
        multiplier = SECONDARY_ACTION_MULTIPLIER

    success = random.random() < success_chance

    return {
        "party": party_name,
        "action_slot": action_slot,
        "action_type": action_type,
        "variant": variant,
        "target_party": target_party,
        "success": success,
        "success_chance": success_chance,
        "multiplier": multiplier,
    }



def resolve_all_party_actions(party_actions: dict) -> list[dict]:
    resolved_actions = []

    for party_name, actions in party_actions.items():
        resolved_actions.append(
            resolve_party_action(
                party_name=party_name,
                action_type=actions["primary_action"],
                variant=actions["primary_variant"],
                target_party=actions["primary_target"],
                action_slot="primary",
            )
        )

        resolved_actions.append(
            resolve_party_action(
                party_name=party_name,
                action_type=actions["secondary_action"],
                variant=actions["secondary_variant"],
                target_party=actions["secondary_target"],
                action_slot="secondary",
            )
        )

    return resolved_actions



def apply_action_to_voter(voter, action_result: dict) -> None:
    action_type = action_result["action_type"]
    variant = action_result["variant"]
    actor_party = action_result["party"]
    target_party = action_result["target_party"]
    success = action_result["success"]
    multiplier = action_result["multiplier"]

    if action_type == "boost_campaign":
        if voter.current_preference == actor_party:
            if success:
                if variant == "social_media_outreach":
                    voter.campaign_interest = clip(voter.campaign_interest + 0.10 * multiplier)
                    voter.turnout_probability = clip(voter.turnout_probability + 0.05 * multiplier)
                elif variant == "national_tour":
                    voter.party_loyalty = clip(voter.party_loyalty + 0.10 * multiplier)
                    voter.campaign_interest = clip(voter.campaign_interest + 0.04 * multiplier)
                elif variant == "tv_interview":
                    voter.party_loyalty = clip(voter.party_loyalty + 0.06 * multiplier)
                    voter.campaign_interest = clip(voter.campaign_interest + 0.03 * multiplier)
                elif variant == "policy_announcement":
                    voter.party_loyalty = clip(voter.party_loyalty + 0.07 * multiplier)
                    voter.campaign_interest = clip(voter.campaign_interest + 0.02 * multiplier)
            else:
                voter.campaign_interest = clip(voter.campaign_interest + 0.01 * multiplier)

    elif action_type == "attack_opponent":
        if voter.current_preference == target_party:
            if success:
                if variant == "corruption_accusation":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.10 * multiplier)
                    voter.anger = clip(voter.anger + 0.05 * multiplier)
                elif variant == "policy_attack":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.06 * multiplier)
                elif variant == "leader_attack":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.08 * multiplier)
                    voter.anger = clip(voter.anger + 0.03 * multiplier)
                elif variant == "negative_ads":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.05 * multiplier)
                    voter.campaign_interest = clip(voter.campaign_interest + 0.03 * multiplier)
            else:
                if voter.current_preference == actor_party:
                    voter.party_loyalty = clip(voter.party_loyalty - 0.03 * multiplier)

        if success:
            voter.campaign_interest = clip(voter.campaign_interest + 0.02 * multiplier)

    elif action_type == "fabricate_scandal":
        if success:
            if voter.current_preference == target_party:
                if variant == "fake_corruption_scandal":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.15 * multiplier)
                elif variant == "leaked_documents":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.12 * multiplier)
                    voter.campaign_interest = clip(voter.campaign_interest + 0.05 * multiplier)
                elif variant == "identity_based_scandal":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.13 * multiplier)
                    voter.anger = clip(voter.anger + 0.07 * multiplier)
                elif variant == "foreign_influence_accusation":
                    voter.party_loyalty = clip(voter.party_loyalty - 0.11 * multiplier)
                    voter.anger = clip(voter.anger + 0.05 * multiplier)
        else:
            if voter.current_preference == actor_party:
                voter.party_loyalty = clip(voter.party_loyalty - 0.07 * multiplier)
                voter.anger = clip(voter.anger + 0.04 * multiplier)



def apply_resolved_actions_to_voters(voters: list, resolved_actions: list[dict]) -> None:
    for action_result in resolved_actions:
        for voter in voters:
            apply_action_to_voter(voter, action_result)



def build_action_outcome_summary(action: dict) -> str:
    action_type = action["action_type"]
    variant = action["variant"]
    party = action["party"]
    target = action["target_party"]
    success = action["success"]
    slot = action["action_slot"]

    slot_text = "primary" if slot == "primary" else "secondary"

    if action_type == "boost_campaign":
        if variant == "social_media_outreach":
            if success:
                return f"{party}'s {slot_text} social-media push worked and increased youth engagement and turnout among supporters."
            return f"{party}'s {slot_text} social-media push drew attention but had only a limited effect."
        if variant == "national_tour":
            if success:
                return f"{party}'s {slot_text} national tour strengthened supporter loyalty and improved campaign energy."
            return f"{party}'s {slot_text} national tour failed to generate much momentum."
        if variant == "tv_interview":
            if success:
                return f"{party}'s {slot_text} TV interview improved the leader's public image and reinforced support."
            return f"{party}'s {slot_text} TV interview failed to persuade many voters."
        if variant == "policy_announcement":
            if success:
                return f"{party}'s {slot_text} policy announcement gave supporters clearer reasons to stay loyal."
            return f"{party}'s {slot_text} policy announcement had little impact on voter enthusiasm."

    elif action_type == "attack_opponent":
        if variant == "corruption_accusation":
            if success:
                return f"{party}'s {slot_text} corruption attack damaged {target}'s credibility and weakened some of its supporters."
            return f"{party}'s {slot_text} corruption attack against {target} failed and slightly hurt the attacker's own image."
        if variant == "policy_attack":
            if success:
                return f"{party}'s {slot_text} policy attack undermined confidence in {target}'s programme."
            return f"{party}'s {slot_text} policy attack on {target} failed to gain traction."
        if variant == "leader_attack":
            if success:
                return f"{party}'s {slot_text} personal attack weakened confidence in {target}'s leadership."
            return f"{party}'s {slot_text} personal attack on {target} backfired and looked excessive."
        if variant == "negative_ads":
            if success:
                return f"{party}'s {slot_text} negative ads hurt {target} while raising campaign attention."
            return f"{party}'s {slot_text} negative ads failed to convince voters and produced little effect."

    elif action_type == "fabricate_scandal":
        if variant == "fake_corruption_scandal":
            if success:
                return f"{party}'s {slot_text} fabricated corruption scandal shook {target}'s supporters and caused a strong drop in loyalty."
            return f"{party}'s {slot_text} fabricated corruption scandal against {target} failed and damaged the attacker's credibility."
        if variant == "leaked_documents":
            if success:
                return f"{party}'s {slot_text} leaked-documents operation hurt {target} and intensified campaign attention."
            return f"{party}'s {slot_text} leaked-documents attempt against {target} failed and produced backlash."
        if variant == "identity_based_scandal":
            if success:
                return f"{party}'s {slot_text} identity-based scandal increased anger among {target}'s supporters and weakened their attachment."
            return f"{party}'s {slot_text} identity-based scandal failed and made the attacker look manipulative."
        if variant == "foreign_influence_accusation":
            if success:
                return f"{party}'s {slot_text} foreign-influence accusation damaged trust in {target} and raised political tension."
            return f"{party}'s {slot_text} foreign-influence accusation against {target} failed and hurt the attacker's reputation."

    return f"{party}'s {slot_text} action produced no clearly interpretable campaign effect."



def build_action_log_rows(resolved_actions: list[dict]) -> list[dict]:
    rows = []

    for action in resolved_actions:
        rows.append(
            {
                "Party": action["party"],
                "Action slot": action["action_slot"],
                "Action": action["action_type"],
                "Variant": action["variant"],
                "Target": action["target_party"],
                "Success": "Yes" if action["success"] else "No",
                "Success chance": int(action["success_chance"] * 100),
                "Effect strength": round(action["multiplier"], 2),
                "Outcome summary": build_action_outcome_summary(action),
            }
        )

    return rows