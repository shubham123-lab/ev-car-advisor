import config

from fastapi import FastAPI, HTTPException, Header, Depends
from typing import Optional
import time

from schemas import (
    ChatRequest, ChatResponse,
    CompareRequest, CompareResponse,
    SpecsRequest, SpecsResponse,
    TCORequest, TCOResponse,
    BudgetRequest, BudgetResponse,
    VariantsRequest, VariantsResponse,
)

from main_pipeline import get_response
from compare_tool import compare_cars, get_single_car_details, find_cars_by_budget, list_all_variants
from recommend_tool import calculate_tco
from load_specs import load_all_specs

app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
)


def clean_markers(text):
    """Frontend-specific markers hata deta hai API response se"""
    lines = []
    for line in text.split("\n"):
        if line.startswith("[[IMAGES]]"):
            continue
        line = line.replace("[[TOTAL]]", "")
        line = line.replace("[[SELECTED]]", "")
        line = line.replace("[[HEADER]]", "")
        line = line.replace("[[SUBHEADER]]", "")
        lines.append(line)
    return "\n".join(lines)


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if x_api_key not in config.VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.get("/health")
def health_check():
    return {"status": "ok", "service": config.API_TITLE}


@app.get("/cars")
def get_supported_cars(api_key: str = Depends(verify_api_key)):
    all_specs, all_ncap = load_all_specs()
    cars = [
        {
            "car_name": car_name,
            "ncap_rating": all_ncap.get(car_name, "N/A"),
            "trims": [t["variant_name"] for t in trims],
        }
        for car_name, trims in all_specs.items()
    ]
    return {"supported_cars": cars, "total": len(cars)}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            answer = get_response(request.question)
            return ChatResponse(question=request.question, answer=clean_markers(answer))
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                raise HTTPException(status_code=429, detail="Service busy. Try again shortly.")
            raise HTTPException(status_code=500, detail=err)


@app.post("/compare", response_model=CompareResponse)
def compare(request: CompareRequest, api_key: str = Depends(verify_api_key)):
    try:
        result = compare_cars(
            request.car_a_name, request.trim_a_name,
            request.car_b_name, request.trim_b_name,
        )
        return CompareResponse(comparison=clean_markers(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/specs", response_model=SpecsResponse)
def specs(request: SpecsRequest, api_key: str = Depends(verify_api_key)):
    try:
        result = get_single_car_details(request.car_name, request.trim_name)
        return SpecsResponse(details=clean_markers(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tco", response_model=TCOResponse)
def tco(request: TCORequest, api_key: str = Depends(verify_api_key)):
    try:
        result = calculate_tco(
            request.car_category, request.current_fuel_type,
            request.daily_km, request.has_home_charging,
        )
        return TCOResponse(
            table=clean_markers(result["table"]),
            savings=result["savings"],
            home_charger_extra_saving=result["home_charger_extra_saving"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/budget", response_model=BudgetResponse)
def budget(request: BudgetRequest, api_key: str = Depends(verify_api_key)):
    try:
        result = find_cars_by_budget(request.budget_lakh)
        return BudgetResponse(matches=clean_markers(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/variants", response_model=VariantsResponse)
def variants(request: VariantsRequest, api_key: str = Depends(verify_api_key)):
    try:
        result = list_all_variants(request.car_name)
        return VariantsResponse(variants=clean_markers(result))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))