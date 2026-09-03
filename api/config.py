import sys
import os

PROCESSING_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "processing")

if PROCESSING_PATH not in sys.path:
    sys.path.insert(0, PROCESSING_PATH)

API_TITLE = "EV Car Advisor API"
API_DESCRIPTION = "India-focused EV review intelligence, comparison, and cost analysis"
API_VERSION = "1.0.0"

VALID_API_KEYS = set(
    k.strip() for k in os.getenv("API_KEYS", "demo-key-12345").split(",") if k.strip()
)