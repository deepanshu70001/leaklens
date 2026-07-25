"""
LeakLens Configuration — All tunable constants from §2, env-overridable.
"""
from pydantic_settings import BaseSettings
from typing import Dict, Tuple
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables with sane defaults."""

    # ── MongoDB ──────────────────────────────────────────────────────
    MONGODB_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "leaklens"

    # ── Groq LLM ────────────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_EXTRACTION_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_REASONING_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT_SECONDS: int = 8

    # ── JWT Auth ─────────────────────────────────────────────────────
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60 * 24  # 24 hours

    # ── CORS ─────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Rate Limiting ────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "60/minute"

    # ── Upload ───────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 5

    # ── Merchant Normalization ───────────────────────────────────────
    FUZZY_MATCH_THRESHOLD: int = 85  # rapidfuzz ratio, 0-100

    # ── Recurring Detection ──────────────────────────────────────────
    RECURRING_MIN_OCCURRENCES: int = 2
    RECURRING_GAP_TOLERANCE_DAYS: int = 3

    # ── Price Hike Detection ─────────────────────────────────────────
    PRICE_HIKE_THRESHOLD_PCT: float = 5.0  # % increase to flag

    # ── Leak Score ───────────────────────────────────────────────────
    UNUSED_DAYS_CAP: int = 90

    # ── Growth Simulation ────────────────────────────────────────────
    ASSUMED_ANNUAL_RETURN_PCT: float = 8.0  # clearly labeled as illustrative

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# ── Constants (not env-overridable, fixed by spec) ───────────────────

LEAK_SCORE_WEIGHTS: Dict[str, float] = {
    "unused": 0.40,
    "price_hike": 0.30,
    "redundancy": 0.20,
    "relative_cost": 0.10,
}

LEAK_SCORE_BANDS: Dict[str, Tuple[int, int]] = {
    "keep": (0, 30),
    "downgrade": (31, 55),
    "renegotiate": (56, 75),
    "cancel": (76, 100),
}

# Category mapping for common subscription merchants
CATEGORY_MAP: Dict[str, str] = {
    "netflix": "streaming",
    "spotify": "streaming",
    "amazon prime": "streaming",
    "disney": "streaming",
    "hotstar": "streaming",
    "youtube premium": "streaming",
    "apple tv": "streaming",
    "hbo": "streaming",
    "hulu": "streaming",
    "jio cinema": "streaming",
    "zee5": "streaming",
    "sonyliv": "streaming",
    "adobe": "software",
    "microsoft 365": "software",
    "microsoft": "software",
    "google one": "cloud_storage",
    "icloud": "cloud_storage",
    "dropbox": "cloud_storage",
    "onedrive": "cloud_storage",
    "gym": "fitness",
    "cult.fit": "fitness",
    "fitbit": "fitness",
    "strava": "fitness",
    "peloton": "fitness",
    "linkedin": "professional",
    "medium": "professional",
    "notion": "productivity",
    "slack": "productivity",
    "canva": "productivity",
    "figma": "productivity",
    "chatgpt": "ai_tools",
    "openai": "ai_tools",
    "grammarly": "ai_tools",
    "nordvpn": "security",
    "expressvpn": "security",
    "mcafee": "security",
    "norton": "security",
    "swiggy": "food_delivery",
    "zomato": "food_delivery",
    "uber eats": "food_delivery",
    "doordash": "food_delivery",
}

CATEGORY_DISPLAY_NAMES: Dict[str, str] = {
    "streaming": "Streaming & Entertainment",
    "software": "Software & Tools",
    "cloud_storage": "Cloud Storage",
    "fitness": "Fitness & Health",
    "professional": "Professional & Learning",
    "productivity": "Productivity",
    "ai_tools": "AI Tools",
    "security": "Security & VPN",
    "food_delivery": "Food Delivery",
    "other": "Other",
}


# Singleton settings instance
settings = Settings()
