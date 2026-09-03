from guardrails import handle_query
from agent import agent
from compare_tool import compare_cars

BASE_TRIMS = {
    "Tata Sierra EV": "Pure",
    "Tata Harrier EV": "Adventure",
    "Mahindra BE 6": "SPORTEQ One",
    "Mahindra XEV 9e": "Pack One",
    "Mahindra XEV 9s": "Pack One Above",
}


def extract_trim_from_query(question, car_name, all_trims):
    """Query me se trim name dhoondta hai, warna base trim deta hai"""
    q_lower = question.lower()
    matches = [t for t in all_trims if t.lower() in q_lower]
    if matches:
        return max(matches, key=len)
    return BASE_TRIMS.get(car_name)


def get_response(question, chat_history=None):
    guard_result = handle_query(question, chat_history)

    if guard_result["status"] == "not_covered":
        return guard_result["response"]

    detected = guard_result.get("detected_car", "")

    if detected.startswith("COMPARE:"):
        from load_specs import load_all_specs
        all_specs, _ = load_all_specs()

        cars_part = detected.replace("COMPARE:", "").strip()
        car_names = [c.strip() for c in cars_part.split(",")]

        if len(car_names) == 2 and all(c in all_specs for c in car_names):
            car_a, car_b = car_names
            trims_a = [t["variant_name"] for t in all_specs[car_a]]
            trims_b = [t["variant_name"] for t in all_specs[car_b]]

            trim_a = extract_trim_from_query(question, car_a, trims_a)
            trim_b = extract_trim_from_query(question, car_b, trims_b)

            result = compare_cars(car_a, trim_a, car_b, trim_b)
            result += f"\n\nShowing {trim_a} vs {trim_b}. Want to compare different trims?"
            return result

    messages = []
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": question})

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = agent.invoke({"messages": messages})
            final_message = result["messages"][-1]
            if isinstance(final_message.content, str):
                return final_message.content
            return final_message.content[0]["text"]
        except Exception as e:
            if ("429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)) and attempt < max_retries - 1:
                import time
                time.sleep(5 * (attempt + 1))
                continue
            raise


if __name__ == "__main__":
    print(get_response("compare tata sierra and xev 9e"))