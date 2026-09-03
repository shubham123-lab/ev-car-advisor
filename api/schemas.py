from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User's EV-related question")


class ChatResponse(BaseModel):
    question: str
    answer: str


class CompareRequest(BaseModel):
    car_a_name: str
    trim_a_name: str
    car_b_name: str
    trim_b_name: str


class CompareResponse(BaseModel):
    comparison: str


class SpecsRequest(BaseModel):
    car_name: str
    trim_name: str


class SpecsResponse(BaseModel):
    details: str


class TCORequest(BaseModel):
    car_category: str = Field(..., description="hatchback / sedan / mini_suv / big_suv")
    current_fuel_type: str = Field(..., description="petrol / diesel / cng")
    daily_km: int = Field(..., gt=0, description="Daily driving distance in km")
    has_home_charging: bool


class TCOResponse(BaseModel):
    table: str
    savings: float
    home_charger_extra_saving: float

class BudgetRequest(BaseModel):
    budget_lakh: float = Field(..., gt=0, description="Budget in lakh, e.g. 20.5")


class BudgetResponse(BaseModel):
    matches: str


class VariantsRequest(BaseModel):
    car_name: str = Field(..., description="Full car name, e.g. 'Tata Sierra EV'")


class VariantsResponse(BaseModel):
    variants: str