import shutil
from pathlib import Path
import kagglehub

ROOT = Path(__file__).resolve().parent.parent
DATASET = "dissfya/atp-tennis-2000-2023daily-pull"
FILENAME = "atp_tennis.csv"


def download_historical_data(force: bool = True) -> Path:
    """Download the latest ATP results from Kaggle into Data/ and return the file path."""
    cached = kagglehub.dataset_download(DATASET, path=FILENAME, force_download=force)
    dest = ROOT / "Data" / FILENAME
    shutil.copy(cached, dest)
    return dest


if __name__ == "__main__":
    print(f"Saved to {download_historical_data()}")