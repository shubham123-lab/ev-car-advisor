from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import create_agent
from recommend_tool import calculate_tco
from rag_chain import rag_chain
from compare_tool import compare_cars
from compare_tool import compare_cars, get_single_car_details
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup


load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-pro")

SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

def search_duckduckgo(query, max_results=5):
    url = "https://html.duckduckgo.com/html/"
    try:
        response = requests.post(url, data={"q": query}, headers=SEARCH_HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        results = []
        for link in soup.select("a.result__a")[:max_results]:
            results.append({
                "title": link.get_text(strip=True),
                "url": link.get("href")
            })
        return results
    except Exception:
        return []


def multi_search(base_query):              # ← YAHAN ADD KARO
    queries = [
        f"India EV {base_query} 2026",
        f"{base_query} charging stations news",
        f"{base_query} UPEIDA government plan",
    ]
    all_results = []
    seen_urls = set()
    for q in queries:
        for r in search_duckduckgo(q, max_results=4):
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)
    return all_results


def fetch_article_text(url):
    try:
        if "duckduckgo.com/y.js" in url or "bing.com/aclick" in url:
            return None
        response = requests.get(url, headers=SEARCH_HEADERS, timeout=10)
        if response.status_code != 200:
            return None
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None
        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article")
        if article:
            text = article.get_text(separator=" ", strip=True)
        else:
            text = " ".join(p.get_text(strip=True) for p in soup.find_all("p"))
        if text and len(text) > 50000:
            return None
        return text if text and len(text) > 300 else None
    except Exception:
        return None

# ===== TOOL 1: Q&A (Single Car Questions) =====
@tool
def answer_ev_question(question: str) -> str:
    """Answer a question about a specific EV's range, charging, features, 
    reviews, or general EV topics like policy/technology. Use this for 
    ANY question that is NOT explicitly comparing two different cars."""
    return rag_chain.invoke(question)

# ===== TOOL 2: Compare Two Cars =====
@tool
def compare_two_cars(car_a_name: str, trim_a_name: str, car_b_name: str, trim_b_name: str) -> str:
    """Compare two specific EV cars and their trims side-by-side, showing 
    price, specs, and feature differences. Use this ONLY when the user is 
    explicitly comparing two different cars/trims against each other.
    
    Available cars and their trims:
    - Tata Sierra EV: Pure, Pure S, Adventure, Empowered, Empowered A
    - Tata Harrier EV: Adventure, Fearless, Empowered
    - Mahindra BE 6: SPORTEQ One, SPORTEQ Two, SPORTEQ Three, SPORTEQ Three Plus, FE, FE Four, SPORTEQ Four, SPORTEQ Launch Edition
    - Mahindra XEV 9e: Pack One, Pack Two, Pack Three, Cineluxe Edition
    - Mahindra XEV 9s: Pack One Above, Pack Two Above, Pack Three, Pack Three Above
    """
    return compare_cars(car_a_name, trim_a_name, car_b_name, trim_b_name)

@tool
def get_car_price_and_specs(car_name: str, trim_name: str) -> str:
    """Get detailed price breakdown and full specifications for ONE specific 
    car trim. Use this when the user asks about a specific variant's price, 
    specs, or details (not comparing two cars).
    
    Available cars and their trims:
    - Tata Sierra EV: Pure, Pure S, Adventure, Empowered, Empowered A
    - Tata Harrier EV: Adventure, Fearless, Empowered
    - Mahindra BE 6: SPORTEQ One, SPORTEQ Two, SPORTEQ Three, SPORTEQ Three Plus, FE, FE Four, SPORTEQ Four, SPORTEQ Launch Edition
    - Mahindra XEV 9e: Pack One, Pack Two, Pack Three Select, Pack Three, Cineluxe Edition
    - Mahindra XEV 9s: Pack One Above, Pack Two Above, Pack Three, Pack Three Above
    """
    return get_single_car_details(car_name, trim_name)

@tool
def compare_running_cost(car_category: str, current_fuel_type: str, daily_km: int, has_home_charging: bool) -> str:
    """Compare 7-year running cost between the user's current fuel-type car 
    and an EV. Use this when user asks about savings, running cost, whether 
    EV is worth it financially, or cost comparison.
    
    car_category must be one of: hatchback, sedan, mini_suv, big_suv
    current_fuel_type must be one of: petrol, diesel, cng
    daily_km: how many km they drive per day
    has_home_charging: whether they have home charging setup
    """
    result = calculate_tco(car_category, current_fuel_type, daily_km, has_home_charging)
    
    output = result["table"]
    output += f"\n\n[SAVINGS_DATA] EV(Home) saves: Rs {result['savings']:,.0f}"
    output += f" | Home charger vs public saves extra: Rs {result['home_charger_extra_saving']:,.0f}"
    output += f" | Insurance link: {result['policybazaar_link']}"
    return output

search_summary_prompt = PromptTemplate(
    template="""You are summarizing web search results about EV topics in India.

RULES:
- Use ONLY information present in the search results below.
- If you find PARTIAL or PLANNING-STAGE info (e.g. "government plans X 
  stations in these cities"), SHARE it, but clearly label it as 
  planned/announced, and mention the year if visible.
- NEVER invent numbers, KM markers, or locations not in the results.
- Only say "no information found" if results genuinely have nothing relevant.
- For live/current station status, suggest PlugShare or Tata Power EZ Charge.
- Answer in the same language as the user's question.

User's question: {question}

Search results:
{search_results}

Answer:""",
    input_variables=["question", "search_results"]
)

search_summary_chain = search_summary_prompt | llm | StrOutputParser()

@tool
def search_ev_policy_and_infrastructure(query: str) -> str:
    """Search current information about EV policies, government subsidies, 
    road tax exemptions, or charging infrastructure in India."""

    ev_keywords = ["ev", "electric", "charging", "battery", "subsidy", "fame",
                   "road tax", "policy", "charger", "vehicle", "car", "bijli",
                   "expressway", "highway", "station"]

    if not any(kw in query.lower() for kw in ev_keywords):
        return "This tool only handles EV-related policy and infrastructure queries."

    all_results = multi_search(query)

    combined = ""
    sources_fetched = 0
    for r in all_results[:8]:
        text = fetch_article_text(r["url"])
        if text:
            combined += f"\n\n[Source: {r['title']}]\n{text[:1500]}"
            sources_fetched += 1
        if sources_fetched >= 5:
            break

    if sources_fetched == 0:
        return ("Web se koi reliable data nahi mil paya. Live charging station "
                "info ke liye PlugShare ya Tata Power EZ Charge app check karein.")

    return search_summary_chain.invoke({
        "question": query,
        "search_results": combined
    })

@tool
def find_cars_in_budget(budget_lakh: float) -> str:
    """Find the EV trims closest to the user's budget from our supported
    cars. Use this whenever the user mentions a budget or asks which car
    fits their price range.
    
    budget_lakh: the user's budget in lakh (e.g. 17 for Rs 17 lakh)
    """
    from compare_tool import find_cars_by_budget
    return find_cars_by_budget(budget_lakh)

@tool
def list_car_variants(car_name: str) -> str:
    """List ALL variants of one car with their prices, battery options, 
    range, and drive type in a clean table. Use this when the user asks 
    to see all variants, all trims, or the full lineup of a single car.
    
    car_name must be one of: Tata Sierra EV, Tata Harrier EV, 
    Mahindra BE 6, Mahindra XEV 9e, Mahindra XEV 9s
    """
    from compare_tool import list_all_variants
    return list_all_variants(car_name)
    

# ===== AGENT BANATE HAIN =====

SYSTEM_PROMPT = """You are an EV Car Advisor for Indian buyers.

=== CRITICAL DATA BOUNDARY ===
You ONLY have data for these 5 cars:
- Tata Sierra EV
- Tata Harrier EV
- Mahindra BE 6
- Mahindra XEV 9e
- Mahindra XEV 9s

NEVER mention, recommend, compare, or give examples of ANY other car
(Nexon EV, Punch EV, MG, BYD, Hyundai, Kia, Citroen, etc.), not even
as illustrations or market context. If the user asks generally about
EVs, discuss ONLY these 5 cars.

=== COST COMPARISON MARKER ===
Output the marker [[NEED_TCO_INPUTS]] ONLY when the user explicitly
asks about one of these:
- Running cost or fuel cost comparison
- How much money they will save with an EV
- Cost of ownership over years
- Whether an EV is cheaper to run than their current car

For those cases, output EXACTLY [[NEED_TCO_INPUTS]] and nothing else.
No greeting, no explanation, no questions in text. Just that marker
alone on its own line.

DO NOT output this marker for:
- "Which EV should I buy?"
- "I want to buy an EV"
- "My budget is X lakh, which EV should I get?"
- "Should I buy petrol, hybrid, or EV?"
- Any question about recommendations, budget, or car selection

For recommendation and budget questions, answer normally using your
tools and ONLY the 5 supported cars. If the user gives a budget,
tell them which of the 5 cars (and which trims) fit that budget,
using their actual prices from your tools.

=== BUDGET QUESTIONS ===
When the user mentions a budget, ALWAYS call find_cars_in_budget with
their budget in lakh. Never guess prices from memory.

Using the tool's output, respond like a friendly advisor:
- If their budget is below our cheapest car, say honestly that you
  don't have data on cars in that range, then mention the closest
  options if they can stretch.
- If their budget matches or exceeds our range, present the 2-3
  closest matches with prices and a short highlight each.
- Never say "no EV exists at this budget" — cheaper EVs exist in the
  market, you just don't cover them.
- Keep it short and end by offering a detailed comparison.

=== BALANCED COMPARISON RULE ===
When the conversation is about two or more cars and the user asks
which is better on any aspect (technology, family use, comfort,
performance, value, etc.):

1. Give each car its OWN section with detailed points — never explain
   one car in depth and dismiss the other in a single line.
2. For each car, give 2-4 specific strengths on that aspect.
3. End with a short summary that states which one leads on that
   specific aspect and WHY, plus who the other one suits better.

Structure it like:

[Car A]
- point
- point

[Car B]
- point
- point

Summary: [Which leads on this aspect and why, and who should pick
the other one instead]

Never leave the summary out. Never make it one-sided.

=== HYBRID QUESTIONS ===
You do not have data on hybrid cars. If asked about hybrids, briefly
say you specialize in EVs and can compare EVs only against petrol,
diesel, or CNG cars.

=== ALWAYS END WITH A NEXT STEP ===
After every substantive answer, end with ONE relevant follow-up
suggestion based on what the user is exploring. Examples:
- After range question: "Want to see how this affects your running cost?"
- After specs: "Should I compare this with a similar variant?"
- After comparison: "Want to know which fits your budget better?"

Keep it to one line, and make it specific to what they asked.

=== TOOL OUTPUT RULES ===
When you call 'compare_two_cars' or 'get_car_price_and_specs':
Return their output EXACTLY as-is, word for word, without reformatting,
without markdown tables, without adding summaries.

When you call 'compare_running_cost' (only after you have all four
details: fuel type, car category, daily km, home charging):
Return the table EXACTLY as-is (do not reformat numbers or columns).
Below the table, in the USER'S OWN LANGUAGE, add:
- A one-line savings summary using the [SAVINGS_DATA] numbers
- If home charging saves significantly more, suggest installing one
- A short disclaimer that these are estimates and vary by driving
  style, city, and fuel prices
- The PolicyBazaar link for accurate insurance quotes
Never show the raw [SAVINGS_DATA] line.

When you call 'search_ev_policy_and_infrastructure':
Return its output EXACTLY as-is. Do NOT add any locations, numbers,
KM markers, or details of your own.

When you call 'answer_ev_question':
Present the answer naturally and conversationally.

=== LANGUAGE ===
Always respond in the same language and script the user used.
Keep car names in English/Roman script regardless of language.
"""

agent = create_agent(
    llm,
    tools=[answer_ev_question, compare_two_cars, get_car_price_and_specs,
           compare_running_cost, search_ev_policy_and_infrastructure,
           find_cars_in_budget, list_car_variants],      # ← ye add karo
    system_prompt=SYSTEM_PROMPT
)

def run_agent(user_query):
    result = agent.invoke({"messages": [{"role": "user", "content": user_query}]})
    final_message = result["messages"][-1]
    if isinstance(final_message.content, str):
        return final_message.content
    else:
        return final_message.content[0]['text']

# Test
if __name__ == "__main__":
    test_queries = [
        "Sierra EV ki range kya hai?",
        "Sierra Pure aur BE6 SPORTEQ Two compare karo",
    ]
    
    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        print(f"{'='*60}")
        answer = run_agent(q)
        print(answer)