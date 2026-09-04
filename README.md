# EV Car Advisor

An India-focused conversational advisor for electric vehicles — built to answer the questions people actually get stuck on when buying an EV: what range they will really get, what the car costs to own over seven years, and how two variants genuinely differ.

Powered by a RAG pipeline over 1,000+ real owner reviews and expert sources, with structured specification data for accurate, verifiable answers.

---

## The Problem

Buying an EV in India means navigating a confusing information landscape:

- **Claimed vs real range** — manufacturers advertise 665 km; owners report 500 km. Which is it?
- **Hidden running costs** — is charging really cheaper if you do not have a home charger?
- **Variant confusion** — five trims, two battery packs, and no clear picture of what the extra money buys you
- **Scattered reviews** — CarDekho says one thing, YouTube reviewers say another, expert articles say a third

Existing sites list specifications. They do not synthesise what owners actually experienced, and they do not tell you whether an EV makes financial sense for your specific usage.

---

## What This Does

**Conversational Q&A grounded in real reviews**
Ask anything about range, charging, reliability, or ownership experience. Answers are synthesised from real owner reviews and expert content — not generated from model memory.

**Variant comparison with real numbers**
Side-by-side price breakdown (ex-showroom, RTO, insurance, cess, FASTag, accessories) and 15 core specifications, showing only what genuinely differs between two cars.

**7-year total cost of ownership calculator**
Compares your current petrol, diesel, or CNG car against an EV across fuel, service, tyres, insurance, and repairs — with separate columns for home and public charging, because that difference is often decisive.

**Budget-based recommendations**
Give a budget, get the closest matching variants from actual price data — no guessing, no hallucinated figures.

**Live policy and infrastructure lookup**
Current information on FAME schemes, state road-tax exemptions, and charging infrastructure, fetched live because this data changes too fast to store.

**Multi-language support**
Responds in the language you ask in — Hindi, English, Hinglish, Kannada, Telugu — while keeping car names in their original form.

---

## Design Decisions

A few choices that shaped how this works:

**Specifications are looked up, not retrieved.** Price and spec data lives in structured JSON with direct dictionary access. Putting exact figures through a similarity search invites the wrong variant's numbers into an answer — so specs bypass RAG entirely.

**Formatting happens in Python, not the prompt.** Comparison tables and cost breakdowns are assembled in code and passed through unchanged. Asking an LLM to format a table produces something different every time.

**The system says "I do not know."** If a question falls outside the five supported cars, or if retrieval confidence is low, the response says so rather than filling the gap with plausible-sounding invention. Verified this repeatedly during development — it was the hardest behaviour to get right.

**Live data is not cached.** Charging-station counts and subsidy amounts go stale within months. Those queries hit the web at request time; only stable content lives in the vector store.

---

## Architecture

```
User Query
    │
    ├─→ Guardrail Layer
    │     Car coverage check · Scope validation · Multi-language fallback
    │
    ├─→ Agent (LangChain + Gemini)
    │     Routes to the appropriate tool based on intent
    │
    ├─→ Tools
    │     ├── RAG Q&A ............ FAISS retrieval over 1,773 chunks
    │     ├── Compare ............ Structured spec + price comparison
    │     ├── Specs .............. Direct lookup, single variant
    │     ├── TCO Calculator ..... 7-year cost model
    │     ├── Budget Matcher ..... Nearest variants by price
    │     ├── Variant Lister ..... Full lineup for one car
    │     └── Live Search ........ Policy and infrastructure queries
    │
    └─→ Response
          Streamlit UI (formatted, with images) or REST API (clean text)
```

---

## Data

| Source | Content | Volume |
|---|---|---|
| CarDekho | Owner reviews with aspect tags | 786 documents |
| CarWale | Owner reviews via internal API | 130 documents |
| Web articles | Expert reviews, range tests, charging guides | 46 documents |
| YouTube | Review video transcripts | 15 documents |
| Domain knowledge | Battery tech, policy, infrastructure | 40 documents |
| Specifications | 25 trims across 5 cars, 15 specs each | Structured JSON |

**Total: 1,017 documents → 1,773 chunks → FAISS vector store**

**Covered vehicles:** Tata Sierra EV · Tata Harrier EV · Mahindra BE 6 · Mahindra XEV 9e · Mahindra XEV 9s

---

## Tech Stack

**Core:** Python · LangChain · Google Gemini · FAISS
**Backend:** FastAPI with API-key authentication
**Frontend:** Streamlit
**Data:** BeautifulSoup · Requests · YouTube Transcript API
**Deployment:** Docker · Docker Compose

---

## API

Six authenticated endpoints for programmatic access:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Service status |
| `/cars` | GET | Supported vehicles and trims |
| `/chat` | POST | Conversational query |
| `/compare` | POST | Two-variant comparison |
| `/specs` | POST | Single variant details |
| `/tco` | POST | Cost of ownership analysis |
| `/budget` | POST | Budget-matched recommendations |
| `/variants` | POST | Full lineup for one car |

All endpoints except `/health` require an `X-API-Key` header.

**Example**

```bash
curl -X POST http://localhost:8000/compare \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "car_a_name": "Tata Sierra EV",
    "trim_a_name": "Pure",
    "car_b_name": "Mahindra BE 6",
    "trim_b_name": "SPORTEQ Two"
  }'
```

Interactive documentation available at `/docs` when running.

---

## Running Locally

**With Docker (recommended)**

```bash
git clone https://github.com/shubham123-lab/ev-car-advisor.git
cd ev-car-advisor

# Create .env with your keys
cat > .env << 'EOF'
GOOGLE_API_KEY=your_gemini_key
API_KEYS=your-api-key-here
EOF

docker compose up --build
```

Frontend at `localhost:8501`, API at `localhost:8000/docs`.

**Without Docker**

```bash
python -m venv env && source env/bin/activate
pip install -r requirements.txt

# Terminal 1 — API
cd api && uvicorn main:app --reload

# Terminal 2 — Frontend
cd frontend && streamlit run app.py
```

---

## Project Structure

```
ev-car-advisor/
├── scrapers/          Data collection from each source
├── processing/        RAG pipeline, agent, tools, guardrails
├── api/               FastAPI application
├── frontend/          Streamlit interface
├── data/
│   ├── specs/         Structured specifications
│   ├── faiss_index/   Vector store
│   └── images/        Vehicle images
├── Dockerfile.api
├── Dockerfile.frontend
└── docker-compose.yml
```

---

## Roadmap

- User-submitted reviews to build a proprietary dataset independent of third-party sources
- Expanded coverage as more EVs launch in India
- Rate limiting and usage tiers for the API
- Charging-network integration for live station availability

---

## Notes

Cost calculations are estimates based on Delhi fuel and electricity rates and typical usage patterns. Actual costs vary by city, driving style, and current prices. This tool provides general guidance, not financial advice.

Review data was collected for research and educational purposes. Raw scraped content is excluded from this repository.
