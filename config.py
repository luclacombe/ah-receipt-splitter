"""Application configuration and constants."""

from pathlib import Path

# Directories
BASE_DIR: Path = Path(__file__).parent
RECEIPTS_DIR: Path = BASE_DIR / "receipts"
PROCESSED_DIR: Path = BASE_DIR / "processed"

# External assets
AH_LOGO_URL: str = (
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/"
    "Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png"
)

# LLM models
HAIKU_MODEL: str = "claude-haiku-4-5"
OLLAMA_MODEL: str = "llama3.2:3b"

# Cache files
TRANSLATIONS_FILE: Path = BASE_DIR / "translations.json"
BONUS_MATCHES_FILE: Path = BASE_DIR / "bonus_matches.json"
