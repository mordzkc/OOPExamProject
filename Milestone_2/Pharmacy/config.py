from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "pharmacy.db"
DEFAULT_CAPACITY = 1000          # max units of one medicine at one branch
CONTROLLED_MAX_PER_LINE = 30
NARCOTIC_MAX_PER_LINE = 10
PATIENT_ID_PATTERN = r"PT-\d{4}"  # fictional identifiers only
