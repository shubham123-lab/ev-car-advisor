import json
import glob

# load_specs.py me update karo
def load_all_specs():
    all_specs = {}
    all_ncap = {}
    files = glob.glob("../data/specs/*.json")
    
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            car_data = json.load(f)
        
        car_name = car_data["car_name"]
        all_specs[car_name] = car_data["trims"]
        all_ncap[car_name] = car_data.get("ncap_rating", "N/A")
    
    return all_specs, all_ncap

def get_variant_features(all_specs, car_name, trim_name):
    """Ek specific trim ke features nikalta hai"""
    if car_name not in all_specs:
        return None
    
    for trim in all_specs[car_name]:
        if trim["variant_name"] == trim_name:
            return trim
    
    return None

# Test
if __name__ == "__main__":
    specs = load_all_specs()
    
    print(f"\nTotal cars with specs: {len(specs)}")
    
    # Test lookup - Sierra EV ka "Empowered" trim
    result = get_variant_features(specs, "Tata Sierra EV", "Empowered")
    print("\n--- Test Lookup: Sierra EV Empowered ---")
    print(json.dumps(result, indent=2))