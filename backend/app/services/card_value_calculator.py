"""
Deterministic credit card value and reward calculator:
- Category-specific reward calculation with monthly caps
- Fee waiver threshold evaluation
- First-year and ongoing annual net benefit estimation
- Clear assumption logging
"""
from typing import Dict, Any, Optional
from backend.app.schemas.profile import SpendingDistribution
from backend.app.schemas.product import CreditCardTerms


def calculate_credit_card_annual_value(
    terms: CreditCardTerms,
    spending: SpendingDistribution,
    include_welcome_bonus: bool = True
) -> Dict[str, Any]:
    """
    Computes expected annual reward points/cashback and net financial benefit
    based on verified card terms and user spending distribution.
    """
    base_rate = terms.base_cashback_pct
    grocery_rate = terms.grocery_cashback_pct if terms.grocery_cashback_pct is not None else base_rate
    shopping_rate = terms.online_shopping_cashback_pct if terms.online_shopping_cashback_pct is not None else base_rate
    travel_rate = terms.travel_cashback_pct if terms.travel_cashback_pct is not None else base_rate
    dining_rate = terms.dining_cashback_pct if terms.dining_cashback_pct is not None else base_rate
    fuel_rate = terms.fuel_surcharge_waiver_pct if terms.fuel_surcharge_waiver_pct is not None else 0.0

    # Monthly raw reward by category
    grocery_rewards = round(spending.food_groceries * (grocery_rate / 100.0), 2)
    shopping_rewards = round(spending.online_shopping * (shopping_rate / 100.0), 2)
    travel_rewards = round(spending.travel * (travel_rate / 100.0), 2)
    dining_rewards = round(spending.dining_entertainment * (dining_rate / 100.0), 2)
    fuel_rewards = round(spending.fuel * (fuel_rate / 100.0), 2)
    other_rewards = round((spending.utility_bills + spending.other) * (base_rate / 100.0), 2)

    total_monthly_raw_rewards = (
        grocery_rewards
        + shopping_rewards
        + travel_rewards
        + dining_rewards
        + fuel_rewards
        + other_rewards
    )

    # Apply monthly reward cap if specified by the issuer
    monthly_rewards = total_monthly_raw_rewards
    cap_applied = False
    if terms.monthly_reward_cap is not None and terms.monthly_reward_cap > 0:
        if monthly_rewards > terms.monthly_reward_cap:
            monthly_rewards = terms.monthly_reward_cap
            cap_applied = True

    annual_spend = round(spending.total_monthly_spend * 12.0, 2)
    annual_rewards = round(monthly_rewards * 12.0, 2)

    # Check annual fee waiver condition
    fee_waived = False
    if terms.fee_waiver_spend_threshold is not None and terms.fee_waiver_spend_threshold > 0:
        if annual_spend >= terms.fee_waiver_spend_threshold:
            fee_waived = True

    annual_fee_effective = 0.0 if fee_waived else terms.annual_fee

    # Ongoing annual net benefit
    ongoing_annual_net_benefit = round(annual_rewards - annual_fee_effective, 2)

    # First-year net benefit accounting for joining fee & welcome perks
    welcome_bonus = terms.welcome_bonus_value or 0.0
    first_year_net_benefit = round(
        annual_rewards + welcome_bonus - terms.joining_fee - (0.0 if fee_waived else terms.annual_fee),
        2
    )

    assumptions = [
        f"Annual spending projected at ₹{annual_spend:,.0f} based on ₹{spending.total_monthly_spend:,.0f}/month.",
        f"Calculated reward rates: Grocery {grocery_rate}%, Online Shopping {shopping_rate}%, Travel {travel_rate}%, Dining {dining_rate}%, Fuel {fuel_rate}%, Base {base_rate}%.",
    ]
    if cap_applied:
        assumptions.append(f"Issuer monthly reward cap of ₹{terms.monthly_reward_cap:,.0f} was applied.")
    if fee_waived:
        assumptions.append(f"Annual fee of ₹{terms.annual_fee:,.0f} waived due to spend exceeding ₹{terms.fee_waiver_spend_threshold:,.0f}.")
    else:
        assumptions.append(f"Annual fee of ₹{terms.annual_fee:,.0f} is charged (spend threshold not met or no waiver published).")

    return {
        "total_monthly_spend": spending.total_monthly_spend,
        "estimated_annual_spend": annual_spend,
        "monthly_rewards": round(monthly_rewards, 2),
        "estimated_annual_rewards": annual_rewards,
        "annual_fee_effective": annual_fee_effective,
        "fee_waived": fee_waived,
        "net_annual_benefit": ongoing_annual_net_benefit,
        "first_year_net_benefit": first_year_net_benefit,
        "welcome_bonus_value": welcome_bonus,
        "reward_cap_applied": cap_applied,
        "reward_breakdown_by_category": {
            "food_groceries": round(grocery_rewards * 12.0, 2),
            "online_shopping": round(shopping_rewards * 12.0, 2),
            "travel": round(travel_rewards * 12.0, 2),
            "dining_entertainment": round(dining_rewards * 12.0, 2),
            "fuel": round(fuel_rewards * 12.0, 2),
            "other_and_utilities": round(other_rewards * 12.0, 2),
        },
        "assumptions": assumptions
    }
