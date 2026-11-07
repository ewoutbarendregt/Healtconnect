"""
Configuration module for HealthConnect Document Automation.
"""
import os
from pathlib import Path

class Config:
    """Central configuration for the application."""

    # API Configuration
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    MODEL_COMPUTER_USE = "claude-sonnet-4-5-20250514"
    MODEL_EXTRACTION = "claude-sonnet-4-5-20250514"  # Can use Haiku for cost savings

    # URLs (use simulation app for testing)
    SIMULATION_APP_URL = os.environ.get("SIMULATION_APP_URL", "http://localhost:3000")
    HEALTHCONNECT_URL = os.environ.get("HEALTHCONNECT_URL", "https://healthconnect.example.com")
    USE_SIMULATION = os.environ.get("USE_SIMULATION", "true").lower() == "true"

    # Paths
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    DOWNLOAD_DIR = DATA_DIR / "downloads"
    PROCESSED_DIR = DATA_DIR / "processed"
    TRASH_DIR = DATA_DIR / "trash"
    CHECKPOINT_DIR = DATA_DIR / "checkpoints"
    LOG_DIR = DATA_DIR / "logs"

    # Limits
    MAX_ITERATIONS_PER_STEP = 10
    MAX_TOTAL_ITERATIONS = 50
    STEP_TIMEOUT_SECONDS = 120

    # Parallel Processing
    DEFAULT_BATCH_SIZE = 3  # Number of documents to process concurrently
    MAX_BATCH_SIZE = 10  # Maximum allowed batch size (to prevent overwhelming the system)

    # Browser settings for computer use
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    COMPUTER_USE_HOST = os.environ.get("COMPUTER_USE_HOST", "localhost")
    COMPUTER_USE_PORT = int(os.environ.get("COMPUTER_USE_PORT", "8080"))

    # Safety
    DELETE_AFTER_HOURS = 24  # Keep in trash before permanent delete
    REQUIRE_VERIFICATION = True  # Never skip verification step

    # Specialization codes mapping
    SPECIALIZATION_CODES = {
        "neurologie": "NEU",
        "longarts": "LON",
        "pulmonologie": "LON",
        "urologie": "URO",
        "psychiatrie": "PSY",
        "psychologie": "PSY",
        "cardiologie": "CAR",
        "dermatologie": "DER",
        "gynaecologie": "GYN",
        "interne": "INT",
        "interne geneeskunde": "INT",
        "oogheelkunde": "OOG",
        "orthopedie": "ORT",
        "kno": "KNO",
        "keel-neus-oorheelkunde": "KNO",
        "chirurgie": "CHI",
        "reumatologie": "REU",
        "geriatrie": "GER",
        "kindergeneeskunde": "KIN",
        "mdl": "MDL",
        "maag-darm-lever": "MDL",
        "radiologie": "RAD",
        "anesthesiologie": "ANA",
        "oncologie": "ONC",
        "nefrologie": "NEF",
        "hematologie": "HEM",
    }

    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist."""
        for dir_path in [
            cls.DOWNLOAD_DIR,
            cls.PROCESSED_DIR,
            cls.TRASH_DIR,
            cls.CHECKPOINT_DIR,
            cls.LOG_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate(cls):
        """Validate configuration."""
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
        cls.ensure_directories()
