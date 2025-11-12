# backend/calculator/utils/calculations.py
from .rates_loader import RateTable

# Initialize rate loader
rate_loader = RateTable()

# ===================== EDUCATION ENDOWMENT =====================

def get_rate_for_education_endowment(discounted_age, term):
    return rate_loader.get_rate("education_endowment", discounted_age, term)


def get_education_endowment_benefits(sum_assured, term):
    benefits = {
        "Grade 9": round(0.15 * sum_assured, 2),
        "Grade 10": round(0.15 * sum_assured, 2),
        "Grade 11": round(0.15 * sum_assured, 2),
        "Grade 12": round(0.15 * sum_assured, 2),
    }
    accrued_bonus = 0.10 * sum_assured * term
    maturity = 0.50 * sum_assured + accrued_bonus
    benefits["1st Year University/College (Maturity)"] = round(maturity, 2)
    benefits["Accrued Bonus (included above)"] = round(accrued_bonus, 2)
    return benefits


def calculate_premium_logic(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "education_endowment":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_education_endowment(discounted_age, term)
    if rate_per_1000 is None:
        raise ValueError(f"No rate found for discounted age {discounted_age}, term {term}")

    basic_premium = (sum_assured / 1000.0) * rate_per_1000
    dab = sum_assured * 0.001 if dab_included else 0
    wp = 0
    total_before_phcf = basic_premium + dab + wp
    phcf = total_before_phcf * 0.0025
    annual_premium = total_before_phcf + phcf

    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    installment_premium = annual_premium * factor

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "basic_premium": round(basic_premium, 2),
        "dab": round(dab, 2),
        "wp": round(wp, 2),
        "phcf": round(phcf, 2),
        "annual_premium": round(annual_premium, 2),
        "installment_premium": round(installment_premium, 2),
        "benefits": get_education_endowment_benefits(sum_assured, term),
    }


def calculate_sum_assured_logic(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "education_endowment":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_education_endowment(discounted_age, term)

    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    annual_premium = premium / factor
    total_before_phcf = annual_premium / 1.0025
    dab_rate = 0.001 if dab_included else 0
    sum_assured = total_before_phcf / (rate_per_1000 / 1000 + dab_rate)

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "estimated_sum_assured": round(sum_assured, 2),
        "benefits": get_education_endowment_benefits(sum_assured, term),
    }


# ===================== ACADEMIC ADVANTAGE =====================

def get_rate_for_academic_advantage(discounted_age, term):
    return rate_loader.get_rate("academic_advantage", discounted_age, term)


def get_academic_advantage_benefits(sum_assured, term):
    accrued_bonus = 0.10 * sum_assured * term
    return {
        f"Year {term - 3}": round(0.20 * sum_assured, 2),
        f"Year {term - 2}": round(0.20 * sum_assured, 2),
        f"Year {term - 1}": round(0.30 * sum_assured, 2),
        f"Year {term} (Maturity)": round(0.30 * sum_assured + accrued_bonus, 2),
        "Accrued Bonus (included above)": round(accrued_bonus, 2),
    }


def calculate_premium_logic_academic_advantage(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "academic_advantage":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_academic_advantage(discounted_age, term)
    basic_premium = (sum_assured / 1000.0) * rate_per_1000
    dab = sum_assured * 0.001 if dab_included else 0
    wp = 0.02 * basic_premium
    total_before_phcf = basic_premium + dab + wp
    phcf = total_before_phcf * 0.0025
    annual_premium = total_before_phcf + phcf

    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    installment_premium = annual_premium * factor

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "basic_premium": round(basic_premium, 2),
        "dab": round(dab, 2),
        "wp": round(wp, 2),
        "phcf": round(phcf, 2),
        "annual_premium": round(annual_premium, 2),
        "installment_premium": round(installment_premium, 2),
        "benefits": get_academic_advantage_benefits(sum_assured, term),
    }


def calculate_sum_assured_logic_academic_advantage(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "academic_advantage":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_academic_advantage(discounted_age, term)
    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    annual_premium = premium / factor
    total_before_phcf = annual_premium / 1.0025
    dab_rate = 0.001 if dab_included else 0
    sum_assured = total_before_phcf / ((rate_per_1000 / 1000) * 1.02 + dab_rate)

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "estimated_sum_assured": round(sum_assured, 2),
        "benefits": get_academic_advantage_benefits(sum_assured, term),
    }


# ===================== 15-YEAR MONEY BACK PLAN =====================

def get_rate_for_money_back_15(discounted_age, term):
    return rate_loader.get_rate("money_back_15", discounted_age, term)




def get_money_back_15_benefits(sum_assured, term):
    """
    Benefits for 15-Year Money Back Plan:
      - 15% of Sum Assured at end of 3rd year
      - 15% of Sum Assured at end of 6th year
      - 15% of Sum Assured at end of 9th year
      - 15% of Sum Assured at end of 12th year
      - 100% of Sum Assured + Accrued Bonus at maturity (end of 15th year)
      - Accrued Bonus = 10% × Sum Assured × Term
    """
    # This plan is defined for a 15-year term; validate to avoid silent mistakes.
    if int(term) != 15:
        raise ValueError("15-Year Money Back Plan benefits are defined for a 15-year term.")

    accrued_bonus = 0.10 * sum_assured * term

    benefits = {
        "End of 3rd Year": round(0.15 * sum_assured, 2),
        "End of 6th Year": round(0.15 * sum_assured, 2),
        "End of 9th Year": round(0.15 * sum_assured, 2),
        "End of 12th Year": round(0.15 * sum_assured, 2),
        "Maturity (15th Year)": round(1.00 * sum_assured + accrued_bonus, 2),
        "Accrued Bonus (included above)": round(accrued_bonus, 2),
    }
    return benefits


def calculate_premium_logic_money_back_15(product, term, mode, sum_assured, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "money_back_15":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_money_back_15(discounted_age, term)
    if rate_per_1000 is None:
        raise ValueError(f"No rate found for discounted age {discounted_age}, term {term}")

    basic_premium = (sum_assured / 1000.0) * rate_per_1000
    dab = sum_assured * 0.001 if dab_included else 0
    wp = 0.01 * basic_premium
    total_before_phcf = basic_premium + dab + wp
    phcf = total_before_phcf * 0.0025
    annual_premium = total_before_phcf + phcf

    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    installment_premium = annual_premium * factor

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "basic_premium": round(basic_premium, 2),
        "dab": round(dab, 2),
        "wp": round(wp, 2),
        "phcf": round(phcf, 2),
        "annual_premium": round(annual_premium, 2),
        "installment_premium": round(installment_premium, 2),
        "benefits": get_money_back_15_benefits(sum_assured, term),
    }




def calculate_sum_assured_logic_money_back_15(product, term, mode, premium, age_next_birthday, gender, smoker, dab_included):
    if product.lower() != "money_back_15":
        raise ValueError(f"Unsupported product '{product}'")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount
    rate_per_1000 = get_rate_for_money_back_15(discounted_age, term)
    if rate_per_1000 is None:
        raise ValueError(f"No rate found for discounted age {discounted_age}, term {term}")

    mode_factors = {"yearly": 1.0, "half-yearly": 0.5150, "quarterly": 0.2625, "monthly": 0.0885}
    factor = mode_factors.get(mode.lower())
    if factor is None:
        raise ValueError(f"Invalid payment mode: {mode}")

    # Step 1: Convert installment premium → annual
    annual_premium = premium / factor

    # Step 2: Remove PHCF (0.25%)
    total_before_phcf = annual_premium / 1.0025

    # Step 3: Remove DAB and WP (1% of basic premium)
    dab_rate = 0.001 if dab_included else 0
    basic_rate_per_1000 = rate_per_1000 / 1000.0
    wp_factor = 1.01  # Because WP = 1% of basic premium → total risk = 1.01 × basic

    # Final formula: total_before_phcf = (SA / 1000) × (basic_rate + DAB_rate) × 1.01
    sum_assured = total_before_phcf / (basic_rate_per_1000 * wp_factor + dab_rate)

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "estimated_sum_assured": round(sum_assured, 2),
        "benefits": get_money_back_15_benefits(sum_assured, term),
    }
# === End of calculations.py ===











# === 10-YEAR MONEY BACK PLAN (KUMI BORA WITH PROFIT) ===

def get_rate_for_money_back_10(discounted_age, term):
    """Fetch rate per 1,000 for the 10-Year Money Back plan (1D table)."""
    return rate_loader.get_rate("money_back_10", discounted_age, term)  # term ignored


def get_money_back_10_benefits(sum_assured, term):
    """
    Benefits:
      • 10% SA at end of years 4, 6, 8
      • 100% SA + Accrued Bonus at maturity (year 10)
      • Accrued Bonus = 10% × SA × 10 = 100% of SA
    """
    if int(term) != 10:
        raise ValueError("10-Year Money Back Plan is only for 10-year term.")

    accrued_bonus = 0.10 * sum_assured * term  # = 1.0 × sum_assured

    return {
        "End of 4th Year": round(0.10 * sum_assured, 2),
        "End of 6th Year": round(0.10 * sum_assured, 2),
        "End of 8th Year": round(0.10 * sum_assured, 2),
        "Maturity (10th Year)": round(1.00 * sum_assured + accrued_bonus, 2),
        "Accrued Bonus (included above)": round(accrued_bonus, 2),
    }


def calculate_premium_logic_money_back_10(
    product, term, mode, sum_assured, age_next_birthday,
    gender, smoker, dab_included
):
    """SA → Premium (Forward Calculation)"""
    if product.lower() != "money_back_10":
        raise ValueError(f"Unsupported product '{product}'")

    if int(term) != 10:
        raise ValueError("Term must be 10 for 10-Year Money Back Plan")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount

    rate_per_1000 = get_rate_for_money_back_10(discounted_age, term)
    if rate_per_1000 is None:
        raise ValueError(f"No rate found for discounted age {discounted_age}")

    # Basic Premium
    basic_premium = (sum_assured / 1000.0) * rate_per_1000

    # Riders
    dab = sum_assured * 0.001 if dab_included else 0        # 0.1% of SA
    wp = basic_premium * 0.01                               # 1% of Basic

    # Total before PHCF
    total_before_phcf = basic_premium + dab + wp

    # PHCF 0.25%
    phcf = total_before_phcf * 0.0025
    annual_premium = total_before_phcf + phcf

    # Installment Premium
    mode_factors = {
        "yearly": 1.0000,
        "half-yearly": 0.5150,
        "quarterly": 0.2625,
        "monthly": 0.0885,
    }
    factor = mode_factors.get(mode.lower())
    if factor is None:
        raise ValueError(f"Invalid mode: {mode}")

    installment_premium = annual_premium * factor

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "basic_premium": round(basic_premium, 2),
        "dab": round(dab, 2),
        "wp": round(wp, 2),
        "phcf": round(phcf, 2),
        "annual_premium": round(annual_premium, 2),
        "installment_premium": round(installment_premium, 2),
        "benefits": get_money_back_10_benefits(sum_assured, term),
    }


def calculate_sum_assured_logic_money_back_10(
    product, term, mode, premium, age_next_birthday,
    gender, smoker, dab_included
):
    """Premium → SA (Reverse Calculation)"""
    if product.lower() != "money_back_10":
        raise ValueError(f"Unsupported product '{product}'")

    if int(term) != 10:
        raise ValueError("Term must be 10 for 10-Year Money Back Plan")

    discount = 4 if gender.lower() == "female" else 2
    discounted_age = age_next_birthday - discount

    rate_per_1000 = get_rate_for_money_back_10(discounted_age, term)
    if rate_per_1000 is None:
        raise ValueError(f"No rate found for age {discounted_age}")

    mode_factors = {
        "yearly": 1.0000,
        "half-yearly": 0.5150,
        "quarterly": 0.2625,
        "monthly": 0.0885,
    }
    factor = mode_factors.get(mode.lower())
    if factor is None:
        raise ValueError(f"Invalid mode: {mode}")

    # 1. Installment → Annual
    annual_premium = premium / factor

    # 2. Remove PHCF
    total_before_phcf = annual_premium / 1.0025

    # 3. Solve for SA
    # total_before_phcf = (SA/1000 × rate) + (SA × 0.001) + (SA/1000 × rate × 0.01)
    #                   = SA × (rate/1000 × 1.01 + 0.001)

    basic_rate_per_unit = rate_per_1000 / 1000.0
    wp_multiplier = 1.01
    dab_rate_per_unit = 0.001 if dab_included else 0

    total_rate_per_unit = basic_rate_per_unit * wp_multiplier + dab_rate_per_unit
    sum_assured = total_before_phcf / total_rate_per_unit

    return {
        "discounted_age": discounted_age,
        "rate_per_1000": rate_per_1000,
        "estimated_sum_assured": round(sum_assured, 2),
        "benefits": get_money_back_10_benefits(sum_assured, term),
    }