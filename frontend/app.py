import sys
import os

PROCESSING_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "processing")
if PROCESSING_PATH not in sys.path:
    sys.path.insert(0, PROCESSING_PATH)

import streamlit as st

try:
    for key in ["GOOGLE_API_KEY", "API_KEYS", "YOUTUBE_API_KEY"]:
        if key in st.secrets:
            os.environ[key] = st.secrets[key]
except Exception:
    pass  # Local run - .env file se load hoga

from main_pipeline import get_response
from load_specs import load_all_specs

st.set_page_config(page_title="EV Car Advisor", page_icon="🚗", layout="centered")

st.markdown("""
<style>
.ev-mono {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: clamp(10.5px, 2.6vw, 13.5px);
    line-height: 1.8;
    white-space: pre;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    color: #d4d4d4;
    padding-bottom: 6px;
}
.ev-total {
    font-family: ui-monospace, SFMono-Regular, monospace;
    font-size: clamp(11px, 2.8vw, 14px);
    font-weight: 600;
    color: #81c784;
    background: #0f2b18;
    border: 1px solid #2e7d32;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 6px 0;
    white-space: pre;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}
.ev-heading {
    font-size: clamp(15px, 3.2vw, 17px);
    font-weight: 600;
    color: #4da6ff;
    margin-top: 18px;
    margin-bottom: 8px;
    letter-spacing: 0.5px;
}
.ev-note {
    background: #1a2733;
    border-left: 3px solid #4da6ff;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: clamp(12.5px, 2.9vw, 14px);
    margin: 14px 0;
    color: #c9d6e0;
}
.ev-suggest {
    font-style: italic;
    font-size: clamp(13px, 3vw, 15px);
    color: #8ab4a0;
    margin: 18px 0 8px 0;
}
.ev-selected {
    background: #1a2733;
    border-radius: 6px;
    padding: 10px 14px;
    font-size: clamp(11.5px, 2.7vw, 13px);
    color: #9fc5e8;
    margin-bottom: 12px;
}
.ev-header-big {
    font-size: clamp(16px, 4vw, 20px);
    font-weight: 600;
    color: #e8e8e8;
    margin-bottom: 4px;
}
.ev-subheader {
    font-size: clamp(11px, 2.6vw, 13px);
    color: #9aa0a6;
    margin-bottom: 2px;
}
.ev-link {
    font-size: clamp(12.5px, 2.9vw, 14px);
    margin: 10px 0;
}
.ev-link a { color: #4da6ff; font-weight: 500; }

.ev-wide { display: block; }
.ev-narrow { display: none; }

@media (max-width: 700px) {
    .ev-wide { display: none; }
    .ev-narrow { display: block; }
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def get_cars_data():
    all_specs, all_ncap = load_all_specs()
    return all_specs, all_ncap


def _cls(base, view_mode):
    if view_mode == "wide":
        return f"{base} ev-wide"
    if view_mode == "narrow":
        return f"{base} ev-narrow"
    return base


def render_answer(answer):
    is_table = (
        ("PRICE" in answer and "SPECS" in answer)
        or "7-Year Running Cost" in answer
        or "All Variants" in answer
    )

    if not is_table:
        st.markdown(answer)
        return

    lines = answer.split("\n")
    buffer = []
    state = {"view": None}

    def flush():
        if buffer:
            body = "<br>".join(l.replace(" ", "&nbsp;") for l in buffer)
            st.markdown(
                f"<div class='{_cls('ev-mono', state['view'])}'>{body}</div>",
                unsafe_allow_html=True
            )
            buffer.clear()

    for line in lines:
        stripped = line.strip()

        if line.startswith("[[WIDE_START]]"):
            flush()
            state["view"] = "wide"
            continue
        if line.startswith("[[WIDE_END]]"):
            flush()
            state["view"] = None
            continue
        if line.startswith("[[NARROW_START]]"):
            flush()
            state["view"] = "narrow"
            continue
        if line.startswith("[[NARROW_END]]"):
            flush()
            state["view"] = None
            continue

        if line.startswith("[[IMAGES]]"):
            flush()
            names = [n.strip() for n in line.replace("[[IMAGES]]", "").split("|")]
            IMAGES_DIR = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "images"
            )
            valid = []
            for n in names:
                base = n.lower().replace(" ", "_")
                for ext in [".png", ".jpg", ".jpeg", ".webp"]:
                    path = os.path.join(IMAGES_DIR, base + ext)
                    if os.path.exists(path):
                        valid.append((path, n))
                        break

            if valid:
                if len(valid) == 1:
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c2:
                        st.image(valid[0][0], caption=valid[0][1], use_container_width=True)
                else:
                    cols = st.columns(len(valid))
                    for col, (path, cap) in zip(cols, valid):
                        with col:
                            st.image(path, caption=cap, use_container_width=True)

        elif line.startswith("[[SELECTED]]"):
            flush()
            st.markdown(
                f"<div class='{_cls('ev-selected', state['view'])}'>"
                f"{line.replace('[[SELECTED]]', '')}</div>",
                unsafe_allow_html=True
            )
        elif line.startswith("[[HEADER]]"):
            flush()
            st.markdown(
                f"<div class='{_cls('ev-header-big', state['view'])}'>"
                f"{line.replace('[[HEADER]]', '')}</div>",
                unsafe_allow_html=True
            )
        elif line.startswith("[[SUBHEADER]]"):
            flush()
            st.markdown(
                f"<div class='{_cls('ev-subheader', state['view'])}'>"
                f"{line.replace('[[SUBHEADER]]', '')}</div>",
                unsafe_allow_html=True
            )
        elif line.startswith("[[TOTAL]]"):
            flush()
            content = line.replace("[[TOTAL]]", "").replace(" ", "&nbsp;")
            st.markdown(
                f"<div class='{_cls('ev-total', state['view'])}'>{content}</div>",
                unsafe_allow_html=True
            )
        elif stripped in ("PRICE", "SPECS", "FEATURE DIFFERENCES") or stripped.endswith("All Variants"):
            flush()
            heading_text = stripped if stripped.endswith("All Variants") else stripped.title()
            st.markdown(
                f"<div class='{_cls('ev-heading', state['view'])}'>{heading_text}</div>",
                unsafe_allow_html=True
            )
        elif stripped.startswith("Note:"):
            flush()
            st.markdown(f"<div class='ev-note'>{stripped}</div>", unsafe_allow_html=True)
        elif "policybazaar" in stripped.lower():
            flush()
            idx = stripped.find("http")
            label = stripped[:idx].strip() if idx > 0 else "Insurance quotes:"
            url = stripped[idx:].strip() if idx > 0 else "https://www.policybazaar.com/motor-insurance/car-insurance/"
            st.markdown(
                f"<div class='ev-link'>{label} "
                f"<a href='{url}' target='_blank'>Check on PolicyBazaar</a></div>",
                unsafe_allow_html=True
            )
        elif stripped.startswith("Would you like") or stripped.startswith("Chahenge"):
            flush()
            st.markdown(f"<div class='ev-suggest'>{stripped}</div>", unsafe_allow_html=True)
        elif not stripped:
            if buffer:
                buffer.append("")      # buffer me space add karo
            continue
        else:
            buffer.append(line)

    flush()


def render_tco_form():
    st.markdown("**Let me calculate your savings. A few quick questions:**")

    if "tco_step" not in st.session_state:
        st.session_state.tco_step = 1

    step = st.session_state.tco_step
    k = f"tco_{step}"

    selected = []
    if st.session_state.get("tco_no_car"):
        selected.append("No car currently")
    elif st.session_state.get("tco_fuel"):
        selected.append(f"{st.session_state.tco_fuel.title()} car")
    if st.session_state.get("tco_cat"):
        selected.append(st.session_state.tco_cat.replace("_", " ").title())
    if st.session_state.get("tco_km"):
        selected.append(f"{st.session_state.tco_km} km/day")

    if selected:
        st.markdown(
            f"<div style='font-size:13px;color:#8ab4a0;margin-bottom:12px;'>"
            f"Selected: {' • '.join(selected)}</div>",
            unsafe_allow_html=True
        )

    if step == 1:
        fuel = st.radio(
            "Do you currently own a car? If yes, what fuel does it use?",
            ["Petrol", "Diesel", "CNG", "I don't own a car yet"],
            index=None, key=f"{k}_fuel"
        )
        if st.button("Next", key=f"{k}_btn", disabled=(fuel is None)):
            if fuel == "I don't own a car yet":
                st.session_state.tco_no_car = True
                st.session_state.tco_fuel = "petrol"
                st.session_state.tco_cat = "mini_suv"
                st.session_state.tco_step = 3
            else:
                st.session_state.tco_no_car = False
                st.session_state.tco_fuel = fuel.lower()
                st.session_state.tco_step = 2
            st.rerun()

    elif step == 2:
        cat = st.radio(
            "Which category is your current car?",
            ["Hatchback", "Sedan", "Mini SUV", "Big SUV"],
            index=None, key=f"{k}_cat"
        )
        if st.button("Next", key=f"{k}_btn", disabled=(cat is None)):
            m = {"Hatchback": "hatchback", "Sedan": "sedan",
                 "Mini SUV": "mini_suv", "Big SUV": "big_suv"}
            st.session_state.tco_cat = m[cat]
            st.session_state.tco_step = 3
            st.rerun()

    elif step == 3:
        km = st.slider("How many km do you drive daily?", 10, 200, 50, key=f"{k}_km")
        if st.button("Next", key=f"{k}_btn"):
            st.session_state.tco_km = km
            st.session_state.tco_step = 4
            st.rerun()

    elif step == 4:
        ch = st.radio(
            "Can you install a home charging point?",
            ["Yes", "No"],
            index=None, key=f"{k}_ch"
        )
        if st.button("Show results", key=f"{k}_btn", type="primary", disabled=(ch is None)):
            from recommend_tool import calculate_tco, indian_format

            result = calculate_tco(
                st.session_state.tco_cat,
                st.session_state.tco_fuel,
                st.session_state.tco_km,
                ch == "Yes"
            )

            summary = []
            if st.session_state.get("tco_no_car"):
                summary.append("No car currently (compared against a typical petrol Mini SUV)")
            else:
                summary.append(f"{st.session_state.tco_fuel.title()} {st.session_state.tco_cat.replace('_', ' ').title()}")
            summary.append(f"{st.session_state.tco_km} km/day")
            summary.append(f"Home charging: {ch}")

            out = f"[[SELECTED]]Your inputs: {' • '.join(summary)}\n"
            out += result["table"]
            out += f"\n\nEV se 7 saal me approx Rs {indian_format(result['savings'])} ki bachat"
            if ch == "No":
                out += f"\nHome charger lagwane se extra Rs {indian_format(result['home_charger_extra_saving'])} bachenge"
            out += "\n\nNote: These are estimates and vary by driving style, city, and fuel prices."
            out += f"\nGet accurate insurance quotes: {result['policybazaar_link']}"

            st.session_state.messages.append({"role": "assistant", "content": out})
            st.session_state.tco_step = 1
            for key_to_clear in ["tco_fuel", "tco_cat", "tco_km", "tco_no_car"]:
                st.session_state.pop(key_to_clear, None)
            st.rerun()


all_specs, all_ncap = get_cars_data()

if "messages" not in st.session_state:
    st.session_state.messages = []


with st.sidebar:
    st.markdown("### EV Car Advisor")
    st.caption("India-focused EV intelligence")
    st.divider()

    st.markdown("**Supported Cars**")
    for car_name, trims in all_specs.items():
        with st.expander(car_name):
            st.caption(f"NCAP: {all_ncap.get(car_name, 'N/A')}")
            for t in trims:
                st.markdown(f"- {t['variant_name']}")

    st.divider()
    if st.button("New conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.tco_step = 1
        for key_to_clear in ["tco_fuel", "tco_cat", "tco_km", "tco_no_car", "pending_prompt"]:
            st.session_state.pop(key_to_clear, None)
        st.rerun()


prompt = None
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pop("pending_prompt")


if not st.session_state.messages:
    st.markdown("## EV Car Advisor")
    st.caption("Reviews, specs, comparisons, and cost analysis for India's top EVs")
    st.markdown("")
    st.markdown("**Try asking:**")

    suggestions = [
        "What's the real-world range of Tata Sierra EV?",
        "Compare Sierra Pure with BE 6 SPORTEQ Two",
        "How much will I save switching from petrol to EV?",
        "Show me Mahindra XEV 9e Pack Two specs and price",
    ]

    for i, s in enumerate(suggestions):
        if st.button(s, key=f"sug_{i}", use_container_width=True):
            st.session_state.pending_prompt = s
            st.rerun()


last_idx = len(st.session_state.messages) - 1

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            if "[[NEED_TCO_INPUTS]]" in msg["content"]:
                if i == last_idx:
                    render_tco_form()
                else:
                    st.caption("(cost calculator)")
            else:
                render_answer(msg["content"])
        else:
            st.markdown(msg["content"])


typed = st.chat_input("Ask about range, price, specs, savings, or comparisons...")
if typed:
    prompt = typed


if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.processing = True
    st.rerun()

if st.session_state.get("processing"):
    st.session_state.processing = False
    last_user_msg = st.session_state.messages[-1]["content"]
    history = st.session_state.messages[:-1]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = get_response(last_user_msg, chat_history=history)
            except Exception as e:
                answer = f"Something went wrong: {e}"

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()