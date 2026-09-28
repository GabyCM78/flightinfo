"""Settings for the FlightInfo app. The API key is read from .env, never hardcoded."""

import os

from dotenv import load_dotenv

# Read .env (if it exists) and put its values into the environment variables.
load_dotenv()

BASE_URL = "https://api.swedavia.se/flightinfo/v2"

# Seconds to wait for the API before giving up (so the app never hangs).
TIMEOUT = 10

# Swedavia airports: IATA code -> name.
AIRPORTS = {
    "ARN": "Stockholm Arlanda",
    "BMA": "Stockholm Bromma",
    "GOT": "Göteborg Landvetter",
    "MMX": "Malmö",
    "LLA": "Luleå",
    "UME": "Umeå",
    "OSD": "Åre Östersund",
    "VBY": "Visby",
    "RNB": "Ronneby",
    "KRN": "Kiruna",
}


class MissingApiKeyError(Exception):
    """Raised when SWEDAVIA_API_KEY is not set."""


def get_api_key():
    """Return the API key from the environment, or raise a clear error."""
    key = os.getenv("SWEDAVIA_API_KEY", "").strip()
    if not key:
        raise MissingApiKeyError(
            "SWEDAVIA_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    return key
