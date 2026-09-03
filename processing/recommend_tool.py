POLICYBAZAAR_LINK = "https://www.policybazaar.com/motor-insurance/car-insurance/"

FUEL_PRICES = {"petrol": 102, "diesel": 95, "cng": 85}
ELECTRICITY_RATE = {"home": 8, "public": 20}

ICE_CAR_DATA = {
    "hatchback": {"mileage": 19, "service_cost": 5000, "tyre_life_km": 55000, "tyre_set": 20000},
    "sedan":     {"mileage": 17, "service_cost": 6000, "tyre_life_km": 55000, "tyre_set": 24000},
    "mini_suv":  {"mileage": 16, "service_cost": 7000, "tyre_life_km": 55000, "tyre_set": 28000},
    "big_suv":   {"mileage": 12, "service_cost": 10000, "tyre_life_km": 55000, "tyre_set": 36000},
}

FUEL_MILEAGE_BONUS = {"petrol": 1.0, "diesel": 1.20, "cng": 1.35}

EV_DATA = {
    "efficiency_kwh_per_100km": 15,
    "service_cost": 2750,
    "tyre_life_km": 37500,
    "tyre_set": 32000,
}

INSURANCE_BASE_YEARLY = {"ice": 10000, "ev": 12000}
INSURANCE_DEPRECIATION = [1.00, 0.85, 0.80, 0.70, 0.60, 0.50, 0.45]
UNEXPECTED_REPAIRS = {
    "ice": [0, 0, 0, 5000, 8000, 12000, 18000],
    "ev":  [0, 0, 0, 3000, 5000, 7000, 10000],
}

YEARS = 7


def calculate_ice_cost(car_category, fuel_type, daily_km):
    data = ICE_CAR_DATA[car_category]
    total_km = daily_km * 365 * YEARS

    effective_mileage = data["mileage"] * FUEL_MILEAGE_BONUS[fuel_type]
    fuel_cost = (total_km / effective_mileage) * FUEL_PRICES[fuel_type]

    service_cost = (total_km / 10000) * data["service_cost"]
    tyre_cost = (total_km / data["tyre_life_km"]) * data["tyre_set"]
    insurance_cost = INSURANCE_BASE_YEARLY["ice"] * sum(INSURANCE_DEPRECIATION)
    repairs_cost = sum(UNEXPECTED_REPAIRS["ice"])

    return {
        "Fuel Cost": fuel_cost,
        "Service Cost": service_cost,
        "Tyre Cost": tyre_cost,
        "Insurance": insurance_cost,
        "Unexpected Repairs": repairs_cost,
        "Total": fuel_cost + service_cost + tyre_cost + insurance_cost + repairs_cost
    }


def calculate_ev_cost(daily_km, has_home_charging):
    total_km = daily_km * 365 * YEARS
    rate = ELECTRICITY_RATE["home"] if has_home_charging else ELECTRICITY_RATE["public"]

    units_needed = (total_km / 100) * EV_DATA["efficiency_kwh_per_100km"]
    charging_cost = units_needed * rate

    service_cost = (total_km / 10000) * EV_DATA["service_cost"]
    tyre_cost = (total_km / EV_DATA["tyre_life_km"]) * EV_DATA["tyre_set"]
    insurance_cost = INSURANCE_BASE_YEARLY["ev"] * sum(INSURANCE_DEPRECIATION)
    repairs_cost = sum(UNEXPECTED_REPAIRS["ev"])

    return {
        "Fuel Cost": charging_cost,
        "Service Cost": service_cost,
        "Tyre Cost": tyre_cost,
        "Insurance": insurance_cost,
        "Unexpected Repairs": repairs_cost,
        "Total": charging_cost + service_cost + tyre_cost + insurance_cost + repairs_cost
    }


def build_tco_data(car_category, fuel_type, daily_km, has_home_charging):
    return {
        "daily_km": daily_km,
        "total_km": daily_km * 365 * YEARS,
        "fuel_type": fuel_type,
        "has_home_charging": has_home_charging,
        "ice": calculate_ice_cost(car_category, fuel_type, daily_km),
        "ev_home": calculate_ev_cost(daily_km, True),
        "ev_public": calculate_ev_cost(daily_km, False),
    }


def indian_format(num):
    """1234567 -> 12,34,567"""
    s = f"{int(round(num))}"
    if len(s) <= 3:
        return s
    last3 = s[-3:]
    rest = s[:-3]
    parts = []
    while len(rest) > 2:
        parts.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        parts.insert(0, rest)
    return ",".join(parts) + "," + last3


def format_tco_table(data):
    LABEL_W = 24
    COL_W = 20

    label_ice = f"{data['fuel_type'].title()} Car"
    fuel_rate = FUEL_PRICES[data['fuel_type']]
    fuel_unit = "kg" if data['fuel_type'] == "cng" else "L"

    lines = []
    lines.append("")
    lines.append(f"[[HEADER]]7-Year Running Cost Comparison")
    lines.append(f"[[SUBHEADER]]{data['daily_km']} km/day  •  {indian_format(data['total_km'])} km total")
    lines.append(f"[[SUBHEADER]]{data['fuel_type'].title()} Rs {fuel_rate}/{fuel_unit}  •  Public charging Rs {ELECTRICITY_RATE['public']}/unit  •  Home charging Rs {ELECTRICITY_RATE['home']}/unit")
    lines.append("")
    lines.append(f"{'':<{LABEL_W}}{label_ice:<{COL_W}}{'EV (Public)':<{COL_W}}{'EV (Home)'}")

    for key in data["ice"]:
        if key == "Total":
            continue
        v_ice = f"Rs {indian_format(data['ice'][key])}"
        v_public = f"Rs {indian_format(data['ev_public'][key])}"
        v_home = f"Rs {indian_format(data['ev_home'][key])}"
        lines.append(f"{key:<{LABEL_W}}{v_ice:<{COL_W}}{v_public:<{COL_W}}{v_home}")

    ti = f"Rs {indian_format(data['ice']['Total'])}"
    tp = f"Rs {indian_format(data['ev_public']['Total'])}"
    th = f"Rs {indian_format(data['ev_home']['Total'])}"
    lines.append(f"[[TOTAL]]{'Total':<{LABEL_W}}{ti:<{COL_W}}{tp:<{COL_W}}{th}")

    return "\n".join(lines)

def calculate_tco(car_category, fuel_type, daily_km, has_home_charging):
    data = build_tco_data(car_category, fuel_type, daily_km, has_home_charging)
    table = format_tco_table(data)

    ev_used = data["ev_home"] if has_home_charging else data["ev_public"]
    savings = data["ice"]["Total"] - ev_used["Total"]
    home_charger_extra_saving = data["ev_public"]["Total"] - data["ev_home"]["Total"]

    return {
        "table": table,
        "savings": savings,
        "has_home_charging": has_home_charging,
        "home_charger_extra_saving": home_charger_extra_saving,
        "policybazaar_link": POLICYBAZAAR_LINK
    }


if __name__ == "__main__":
    r1 = calculate_tco("mini_suv", "petrol", 50, True)
    print(r1["table"])
    print(f"\nSavings: Rs {r1['savings']:,.0f}")

    print("\n" + "=" * 70)

    r2 = calculate_tco("hatchback", "cng", 50, False)
    print(r2["table"])
    print(f"\nSavings: Rs {r2['savings']:,.0f}")
    print(f"Home charger extra saving: Rs {r2['home_charger_extra_saving']:,.0f}")