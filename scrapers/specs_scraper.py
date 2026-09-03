import requests
from bs4 import BeautifulSoup
import re
import json
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def fetch_variant_list(slug):
    url = f"https://www.cardekho.com/{slug}/variants.htm"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("table.allvariant tbody tr")
    variants = []

    for row in rows:
        variant_name = row.get("data-variant", "")
        link_tag = row.select_one("a")
        if not link_tag:
            continue

        overview_url = "https://www.cardekho.com" + link_tag.get("href", "")
        row_text = row.get_text(separator="|", strip=True)

        price_match = re.search(r'₹?([\d.]+)\s*Lakh', row_text)
        price_lakh = float(price_match.group(1)) if price_match else None

        battery_range_match = re.search(r'(\d+)\s*kWh,\s*(\d+)\s*km', row_text)
        battery_kwh = int(battery_range_match.group(1)) if battery_range_match else None
        range_km = int(battery_range_match.group(2)) if battery_range_match else None

        is_acfc = "ACFC" in variant_name
        is_awd = "AWD" in variant_name

        variants.append({
            "variant_name": variant_name,
            "overview_url": overview_url,
            "price_lakh": price_lakh,
            "battery_kwh": battery_kwh,
            "range_km": range_km,
            "is_acfc": is_acfc,
            "is_awd": is_awd
        })

    return variants

def extract_trim_name(variant_name):
    # IMPORTANT: Lambe/specific naam PEHLE, chhote baad me
    # (warna "Pack Three" "Pack Three Select" ko pehle hi match kar lega, galat)
    known_trims = [
        "Empowered A", "Empowered", "Adventure", "Fearless", "Pure S", "Pure",
        "Pack One Above", "Pack Two Above", "Pack Three Above", "Pack Three Select",
        "Pack Three", "Pack Two", "Pack One",
        "SPORTEQ Three Plus", "SPORTEQ Launch Edition", "SPORTEQ Four",
        "SPORTEQ Three", "SPORTEQ Two", "SPORTEQ One",
        "Cineluxe Edition", "FE Four", "FE",
    ]
    
    for trim in known_trims:
        if trim in variant_name:
            return trim
    
    return variant_name  # fallback, agar kuch match na ho


def group_by_trim(variants):
    trims = {}
    for v in variants:
        trim_name = extract_trim_name(v["variant_name"])
        if v["is_acfc"]:
            continue

        if trim_name not in trims:
            trims[trim_name] = {
                "variant_name": trim_name,
                "battery_options": [],
                "representative_url": None
            }

        trims[trim_name]["battery_options"].append({
            "battery_kwh": v["battery_kwh"],
            "range_km": v["range_km"],
            "price_lakh": v["price_lakh"],
            "drive_type": "AWD" if v["is_awd"] else "RWD"
        })

        if trims[trim_name]["representative_url"] is None:
            trims[trim_name]["representative_url"] = v["overview_url"]

    return list(trims.values())

def fetch_trim_features(overview_url):
    """Top Features + 6 additional numeric specs nikalta hai"""
    try:
        response = requests.get(overview_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Top Features (jo pehle se tha)
        top_features = []
        feature_section = soup.select_one('div[data-track-section="Top Features"]')
        if feature_section:
            items = feature_section.select("ul li span.iconsname")
            top_features = [item.get_text(strip=True) for item in items]

        # Saari spec-tables se label:value pairs nikalo
        spec_dict = {}
        for row in soup.select("table tr"):
            cells = row.select("td, th")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                if value:  # sirf non-empty values
                    spec_dict[label] = value

        extra_specs = {
            "dc_charging_time": spec_dict.get("Charging Time (D.C)", "N/A"),
            "boot_space": spec_dict.get("Boot Space", "N/A"),
            "ground_clearance": spec_dict.get("Ground Clearance Unladen", "N/A"),
            "airbags": spec_dict.get("No. of Airbags", "N/A"),
            "battery_warranty": spec_dict.get("Battery Warranty", "N/A"),
            "regen_levels": spec_dict.get("Regenerative Braking Levels", "N/A"),
        }

        return top_features, extra_specs
    except Exception as e:
        print(f"    Error fetching features: {e}")
        return [], {}

def collect_specs(car_name, slug):
    print(f"\n{'='*50}")
    print(f"Collecting specs for: {car_name} ({slug})")
    print(f"{'='*50}")

    print("Fetching variant list...")
    raw_variants = fetch_variant_list(slug)
    print(f"  → {len(raw_variants)} raw variants mile")

    grouped_trims = group_by_trim(raw_variants)
    print(f"  → {len(grouped_trims)} trims after grouping")

    for trim in grouped_trims:
        print(f"  Fetching features for: {trim['variant_name']}...")
        features, extra_specs = fetch_trim_features(trim["representative_url"])
        trim["top_features"] = features
        trim.update(extra_specs)
        print(f"    → {len(features)} features + {len(extra_specs)} extra specs mile")
        time.sleep(2)

    # Safety check
    if len(grouped_trims) == 0:
        print("  ⚠️ Koi trim nahi mila - purani file safe rakhi ja rahi hai")
        return {"car_name": car_name, "skipped_save": True}

    car_data = {
        "car_name": car_name,
        "source": "cardekho",
        "trims": grouped_trims
    }

    filename = f"../data/specs/{slug.replace('/', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"Saved to {filename}")
    return car_data

# ===== TEST - PEHLE SIRF SIERRA EV =====
# ===== SAB 5 CARS =====
cars_to_collect = [
    ("Tata Sierra EV", "tata/sierra-ev"),
    ("Tata Harrier EV", "tata/harrier-ev"),
    ("Mahindra BE 6", "mahindra/be-6"),
    ("Mahindra XEV 9e", "mahindra/xev-9e"),
    ("Mahindra XEV 9s", "mahindra/xev-9s"),
]

all_results = []
for car_name, slug in cars_to_collect:
    result = collect_specs(car_name, slug)
    all_results.append(result)
    time.sleep(3)

print(f"\n\n{'='*50}")
print("DONE! Summary:")
for r in all_results:
    if r.get("skipped_save"):
        print(f"  - {r['car_name']}: SKIPPED")
    else:
        trim_count = len(r.get("trims", []))
        print(f"  - {r['car_name']}: {trim_count} trims")