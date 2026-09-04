import json
from load_specs import load_all_specs, get_variant_features
from dotenv import load_dotenv

load_dotenv()

HOME_CHARGER_PRICE = 49000
HOME_CHARGER_NOTE = "Optional: 7.2 kW home charger — approx Rs 49,000 extra (installation varies by location)."

POLICYBAZAAR_LINK = "https://www.policybazaar.com/motor-insurance/car-insurance/"

def indian_format(num):
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

def calculate_price_breakdown(ex_showroom_lakh):
    ex_showroom = ex_showroom_lakh * 100000
    rto = 5000
    insurance = ex_showroom * 0.045
    cess = ex_showroom * 0.01
    fastag = 600
    accessories = 25000
    total = ex_showroom + rto + insurance + cess + fastag + accessories
    return {
        "Ex-Showroom": ex_showroom,
        "RTO (Delhi, approx)": rto,
        "Insurance (approx)": insurance,
        "Cess": cess,
        "FASTag": fastag,
        "Accessories": accessories,
        "Total": total
    }


def shorten_ncap(ncap_text):
    if "5-Star" in ncap_text:
        return "5-Star Bharat NCAP"
    elif "Not yet" in ncap_text:
        return "Not yet rated"
    return ncap_text


def get_flat_specs(trim_data, car_ncap_rating):
    battery_option = trim_data["battery_options"][0]
    features = set(trim_data.get("top_features", []))
    return {
        "Battery Capacity": f"{battery_option.get('battery_kwh', 'N/A')} kWh",
        "Range": f"{battery_option.get('range_km', 'N/A')} km",
        "DC Charging": trim_data.get('dc_charging_time', 'N/A'),
        "Power": f"{battery_option.get('power_bhp', 'N/A')} bhp",
        "Torque": f"{battery_option.get('torque_nm', 'N/A')} Nm",
        "Drive Type": battery_option.get('drive_type', 'N/A'),
        "Boot Space": trim_data.get('boot_space', 'N/A'),
        "Ground Clearance": trim_data.get('ground_clearance', 'N/A'),
        "Airbags": trim_data.get('airbags', 'N/A'),
        "ADAS": "Yes" if "ADAS" in features else "No",
        "360 Camera": "Yes" if any("360" in f for f in features) else "No",
        "Battery Warranty": trim_data.get('battery_warranty', 'N/A'),
        "Regen Levels": trim_data.get('regen_levels', 'N/A'),
        "Sunroof": "Yes" if "Sunroof" in features else "No",
        "NCAP Rating": shorten_ncap(car_ncap_rating),
    }


def get_feature_differences(trim_a, trim_b):
    features_a = set(trim_a.get("top_features", []))
    features_b = set(trim_b.get("top_features", []))
    return {
        "only_in_a": list(features_a - features_b),
        "only_in_b": list(features_b - features_a)
    }


def build_compare_data(car_a_name, trim_a_name, car_b_name, trim_b_name):
    all_specs, all_ncap = load_all_specs()

    trim_a = get_variant_features(all_specs, car_a_name, trim_a_name)
    trim_b = get_variant_features(all_specs, car_b_name, trim_b_name)

    if not trim_a or not trim_b:
        return None

    price_a = calculate_price_breakdown(trim_a["battery_options"][0]["price_lakh"])
    price_b = calculate_price_breakdown(trim_b["battery_options"][0]["price_lakh"])

    specs_a = get_flat_specs(trim_a, all_ncap.get(car_a_name, "N/A"))
    specs_b = get_flat_specs(trim_b, all_ncap.get(car_b_name, "N/A"))

    return {
        "car_a": f"{car_a_name} ({trim_a_name})",
        "car_b": f"{car_b_name} ({trim_b_name})",
        "price_a": price_a,
        "price_b": price_b,
        "specs_a": specs_a,
        "specs_b": specs_b,
        "feature_diff": get_feature_differences(trim_a, trim_b)
    }


def format_compare_response(data):
    car_a = data["car_a"]
    car_b = data["car_b"]

    def split_name(full):
        if "(" in full:
            name, _, trim = full.partition("(")
            return name.strip(), trim.replace(")", "").strip()
        return full, ""

    name_a, trim_a = split_name(car_a)
    name_b, trim_b = split_name(car_b)

    short_a = name_a.replace("Mahindra ", "").replace("Tata ", "")
    short_b = name_b.replace("Mahindra ", "").replace("Tata ", "")

    LABEL_W = 24
    COL_W = 30
    SHORT_W = 10

    lines = []
    lines.append("")
    lines.append(f"[[IMAGES]]{name_a}|{name_b}")

    # ===== WIDE (desktop/tablet) =====
    lines.append("[[WIDE_START]]")
    lines.append(f"{'':<{LABEL_W}}{name_a:<{COL_W}}{name_b}")
    lines.append(f"{'':<{LABEL_W}}{trim_a:<{COL_W}}{trim_b}")
    lines.append("")
    lines.append("PRICE")
    for key in data["price_a"]:
        if key == "Total":
            continue
        va = f"Rs {indian_format(data['price_a'][key])}"
        vb = f"Rs {indian_format(data['price_b'][key])}"
        lines.append(f"{key:<{LABEL_W}}{va:<{COL_W}}{vb}")
    ta = f"Rs {indian_format(data['price_a']['Total'])}"
    tb = f"Rs {indian_format(data['price_b']['Total'])}"
    lines.append(f"[[TOTAL]]{'Total':<{LABEL_W}}{ta:<{COL_W}}{tb}")
    lines.append("")
    lines.append("SPECS")
    for key in data["specs_a"]:
        lines.append(f"{key:<{LABEL_W}}{str(data['specs_a'][key]):<{COL_W}}{data['specs_b'][key]}")
    lines.append("[[WIDE_END]]")

    # ===== NARROW (mobile) =====
    lines.append("[[NARROW_START]]")
    lines.append(f"[[HEADER]]{name_a} ({trim_a})")
    lines.append(f"[[HEADER]]vs {name_b} ({trim_b})")
    lines.append("")
    lines.append("PRICE")
    for key in data["price_a"]:
        if key == "Total":
            continue
        lines.append(key)
        lines.append(f"   {short_a + ':':<{SHORT_W}} Rs {indian_format(data['price_a'][key])}")
        lines.append(f"   {short_b + ':':<{SHORT_W}} Rs {indian_format(data['price_b'][key])}")
        lines.append("")   
    lines.append(f"[[TOTAL]]Total")
    lines.append(f"[[TOTAL]]   {short_a + ':':<{SHORT_W}} Rs {indian_format(data['price_a']['Total'])}")
    lines.append(f"[[TOTAL]]   {short_b + ':':<{SHORT_W}} Rs {indian_format(data['price_b']['Total'])}")
    lines.append("")
    lines.append("SPECS")
    for key in data["specs_a"]:
        lines.append(key)
        lines.append(f"   {short_a + ':':<{SHORT_W}} {data['specs_a'][key]}")
        lines.append(f"   {short_b + ':':<{SHORT_W}} {data['specs_b'][key]}")
        lines.append("")   
    lines.append("[[NARROW_END]]")

    # ===== COMMON =====
    lines.append("")
    lines.append("FEATURE DIFFERENCES")
    fd = data["feature_diff"]
    if fd["only_in_a"]:
        lines.append(f"{name_a} ({trim_a}) has: {', '.join(fd['only_in_a'])}")
    if fd["only_in_b"]:
        lines.append(f"{name_b} ({trim_b}) has: {', '.join(fd['only_in_b'])}")
    lines.append("")
    lines.append(f"Note: {HOME_CHARGER_NOTE} RTO & Insurance are approximate and vary by state/insurer.")
    lines.append(f"Get accurate insurance quotes: {POLICYBAZAAR_LINK}")
    lines.append("")
    lines.append("Would you like detailed interior/exterior features for either car?")

    return "\n".join(lines)


def format_single_car_response(car_name, trim_name, price_data, specs_data):
    LABEL_W = 24

    lines = []
    lines.append("")
    lines.append(f"[[IMAGES]]{car_name}")
    lines.append(f"{car_name} ({trim_name})")
    lines.append("")

    lines.append("PRICE")
    for key, val in price_data.items():
        if key == "Total":
            continue
        lines.append(f"{key:<{LABEL_W}}Rs {indian_format(val)}")

    lines.append(f"[[TOTAL]]{'Total':<{LABEL_W}}Rs {indian_format(price_data['Total'])}")
    lines.append("")

    lines.append("SPECS")
    for key, val in specs_data.items():
        lines.append(f"{key:<{LABEL_W}}{val}")
    lines.append("")

    lines.append(f"Note: {HOME_CHARGER_NOTE} RTO & Insurance are approximate and vary by state/insurer.")
    lines.append(f"Get accurate insurance quotes: {POLICYBAZAAR_LINK}")

    return "\n".join(lines)


def compare_cars(car_a_name, trim_a_name, car_b_name, trim_b_name):
    data = build_compare_data(car_a_name, trim_a_name, car_b_name, trim_b_name)
    if not data:
        return "Sorry, ek ya dono trims ka data nahi mila."
    return format_compare_response(data)


def get_single_car_details(car_name, trim_name):
    all_specs, all_ncap = load_all_specs()
    trim = get_variant_features(all_specs, car_name, trim_name)
    if not trim:
        return f"Sorry, {car_name} ka {trim_name} trim nahi mila."

    price_data = calculate_price_breakdown(trim["battery_options"][0]["price_lakh"])
    specs_data = get_flat_specs(trim, all_ncap.get(car_name, "N/A"))
    return format_single_car_response(car_name, trim_name, price_data, specs_data)

def find_cars_by_budget(budget_lakh, count=3):
    """Budget ke nearest trims dhoondta hai, actual data se"""
    all_specs, all_ncap = load_all_specs()

    options = []
    for car_name, trims in all_specs.items():
        for trim in trims:
            for battery in trim["battery_options"]:
                options.append({
                    "car_name": car_name,
                    "trim_name": trim["variant_name"],
                    "price_lakh": battery["price_lakh"],
                    "battery_kwh": battery.get("battery_kwh"),
                    "range_km": battery.get("range_km"),
                    "ncap": shorten_ncap(all_ncap.get(car_name, "N/A")),
                })

    options.sort(key=lambda x: abs(x["price_lakh"] - budget_lakh))
    nearest = options[:count]

    cheapest = min(options, key=lambda x: x["price_lakh"])

    lines = []
    lines.append(f"Your budget: Rs {budget_lakh} Lakh")
    lines.append(f"Cheapest option in our data: {cheapest['car_name']} ({cheapest['trim_name']}) at Rs {cheapest['price_lakh']} Lakh")
    lines.append("")
    lines.append("Closest matches:")
    for o in nearest:
        diff = o["price_lakh"] - budget_lakh
        sign = "+" if diff > 0 else ""
        lines.append(
            f"- {o['car_name']} ({o['trim_name']}): Rs {o['price_lakh']} Lakh "
            f"({sign}{diff:.2f}L) | {o['battery_kwh']} kWh | {o['range_km']} km | {o['ncap']}"
        )

    return "\n".join(lines)

def list_all_variants(car_name):
    """Ek car ke saare variants ek clean table me"""
    all_specs, all_ncap = load_all_specs()

    if car_name not in all_specs:
        return f"Sorry, {car_name} ka data nahi mila."

    trims = all_specs[car_name]

    LABEL_W = 24
    COL_W = 16

    lines = []
    lines.append("")
    lines.append(f"[[IMAGES]]{car_name}")
    lines.append(f"{car_name} — All Variants")
    lines.append("")
    lines.append(f"{'Variant':<{LABEL_W}}{'Price':<{COL_W}}{'Battery':<{COL_W}}{'Range':<{COL_W}}{'Drive'}")

    for trim in trims:
        name = trim["variant_name"]
        for i, bat in enumerate(trim["battery_options"]):
            display_name = name if i == 0 else ""
            price = f"Rs {bat['price_lakh']}L"
            battery = f"{bat.get('battery_kwh', 'N/A')} kWh"
            rng = f"{bat.get('range_km', 'N/A')} km"
            drive = bat.get("drive_type", "N/A")
            lines.append(f"{display_name:<{LABEL_W}}{price:<{COL_W}}{battery:<{COL_W}}{rng:<{COL_W}}{drive}")

    lines.append("")
    lines.append(f"NCAP Rating: {shorten_ncap(all_ncap.get(car_name, 'N/A'))}")
    lines.append("")
    lines.append(f"Note: {HOME_CHARGER_NOTE}")
    lines.append("")
    lines.append(f"Note: Prices are ex-showroom, RTO & Insurance extra. {HOME_CHARGER_NOTE}")
    lines.append("")
    lines.append("Which variant would you like full specs and on-road price for?")

    return "\n".join(lines)

if __name__ == "__main__":
    print(compare_cars("Tata Sierra EV", "Pure", "Mahindra BE 6", "SPORTEQ Two"))
    print("\n" + "=" * 70 + "\n")
    print(get_single_car_details("Tata Sierra EV", "Empowered"))