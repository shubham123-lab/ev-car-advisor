from guardrails import handle_query
from agent import agent
import difflib
import re
from compare_tool import compare_cars

BASE_TRIMS = {
    "Tata Sierra EV": "Pure",
    "Tata Harrier EV": "Adventure",
    "Mahindra BE 6": "SPORTEQ One",
    "Mahindra XEV 9e": "Pack One",
    "Mahindra XEV 9s": "Pack One Above",
}

NUM_WORDS = {"1": "one", "2": "two", "3": "three", "4": "four",
             "5": "five", "6": "six", "7": "seven"}

CONNECTORS = [" versus ", " vs. ", " vs ", " v/s ", " V/S ", "with ", " and ", ","]


def _normalize(text):
    """Lowercase, and turn standalone digits into words (3 -> three)."""
    t = text.lower().replace("-", " ")
    for digit, word in NUM_WORDS.items():
        t = re.sub(rf"\b{digit}\b", word, t)
    return t


def _split_query_for_two_cars(question):
    """Split the query around a connector so each car searches its own half."""
    q = question.lower()
    for conn in CONNECTORS:
        idx = q.find(conn)
        if idx != -1:
            return q[:idx], q[idx + len(conn):]
    return q, q      # no connector found — both search the full query

def extract_trim_from_query(segment, car_name, all_trims):
    """Returns (trim_name, matched_exactly)"""
    q = _normalize(segment)

    # Exact substring match
    matches = [t for t in all_trims if _normalize(t) in q]
    if matches:
        return max(matches, key=len), True

    # Fuzzy match — score every trim, pick the best
    words = q.split()
    best_trim, best_score = None, 0.0

    for trim in all_trims:
        trim_words = _normalize(trim).split()
        score, matched_count = 0.0, 0

        for tw in trim_words:
            close = difflib.get_close_matches(tw, words, n=1, cutoff=0.75)
            if close:
                score += difflib.SequenceMatcher(None, tw, close[0]).ratio()
                matched_count += 1

        score = score / len(trim_words) + matched_count * 0.3

        if score > best_score:
            best_score, best_trim = score, trim

    if best_trim and best_score >= 1.0:
        return best_trim, True

    return BASE_TRIMS.get(car_name), False
    


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

            seg_a, seg_b = _split_query_for_two_cars(question)
            trim_a, matched_a = extract_trim_from_query(seg_a, car_a, trims_a)
            trim_b, matched_b = extract_trim_from_query(seg_b, car_b, trims_b)
            
            result = compare_cars(car_a, trim_a, car_b, trim_b)

            if matched_a and matched_b:
                result += f"\n\nShowing {trim_a} vs {trim_b}. Want to compare different Variant?"
            else:
                result += (f"\n\nCouldn't identify the exact variant you meant, so showing "
                           f"{trim_a} vs {trim_b}. Tell me which variant you'd like instead.")
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