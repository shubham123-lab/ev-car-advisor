import json

power_torque_ncap_data = {
    "Tata Sierra EV": {
        "ncap_rating": "Not yet crash-tested (targeting 5-star Bharat NCAP)",
        "battery_warranty_short": "Lifetime (15 yrs)",
        "battery_warranty_full": "Lifetime (15 years) for first owner",
        "power_torque_by_battery": {
            63: {"power_bhp": 235, "torque_nm": 315},
            75: {"power_bhp": 313, "torque_nm": 504}
        }
    },
    "Tata Harrier EV": {
        "ncap_rating": "5-Star Bharat NCAP",
        "battery_warranty_short": "Lifetime (15 yrs)",
        "battery_warranty_full": "Lifetime (15 years) for first owner",
        "power_torque_by_battery": {
            65: {"power_bhp": 235, "torque_nm": 315},
            75: {"power_bhp": 235, "torque_nm": 315}
        }
    },
    "Mahindra BE 6": {
        "ncap_rating": "5-Star Bharat NCAP (31.97/32)",
        "battery_warranty_short": "Lifetime (1st owner)",
        "battery_warranty_full": "Lifetime for first owner; 10 years / 2 lakh km if ownership transfers",
        "power_torque_by_battery": {
            59: {"power_bhp": 231, "torque_nm": 380},
            70: {"power_bhp": 245, "torque_nm": 380},
            79: {"power_bhp": 286, "torque_nm": 380}
        }
    },
    "Mahindra XEV 9e": {
        "ncap_rating": "5-Star Bharat NCAP (32/32 - perfect score)",
        "battery_warranty_short": "Lifetime (1st owner)",
        "battery_warranty_full": "Lifetime for first owner; 10 years / 2 lakh km if ownership transfers",
        "power_torque_by_battery": {
            59: {"power_bhp": 231, "torque_nm": 380},
            79: {"power_bhp": 282, "torque_nm": 380}
        }
    },
    "Mahindra XEV 9s": {
        "ncap_rating": "Not yet crash-tested",
        "battery_warranty_short": "Lifetime (1st owner)",
        "battery_warranty_full": "Lifetime for first owner; 10 years / 2 lakh km if ownership transfers",
        "power_torque_by_battery": {
            59: {"power_bhp": 231, "torque_nm": 380},
            70: {"power_bhp": 245, "torque_nm": 380},
            79: {"power_bhp": 282, "torque_nm": 380}
        }
    }
}

file_map = {
    "Tata Sierra EV": "../data/specs/tata_sierra-ev.json",
    "Tata Harrier EV": "../data/specs/tata_harrier-ev.json",
    "Mahindra BE 6": "../data/specs/mahindra_be-6.json",
    "Mahindra XEV 9e": "../data/specs/mahindra_xev-9e.json",
    "Mahindra XEV 9s": "../data/specs/mahindra_xev-9s.json",
}

for car_name, filepath in file_map.items():
    with open(filepath, "r", encoding="utf-8") as f:
        car_data = json.load(f)

    ref_data = power_torque_ncap_data[car_name]
    car_data["ncap_rating"] = ref_data["ncap_rating"]

    for trim in car_data["trims"]:
        trim["battery_warranty"] = ref_data["battery_warranty_short"]
        trim["battery_warranty_full"] = ref_data["battery_warranty_full"]

        for battery_option in trim["battery_options"]:
            kwh = battery_option["battery_kwh"]
            pt_data = ref_data["power_torque_by_battery"].get(kwh, {})
            battery_option["power_bhp"] = pt_data.get("power_bhp", "N/A")
            battery_option["torque_nm"] = pt_data.get("torque_nm", "N/A")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(car_data, f, indent=2, ensure_ascii=False)

    print(f"Updated: {car_name}")

print("\nDone! Power, torque, NCAP, aur battery warranty (short + full) add ho gaye.")