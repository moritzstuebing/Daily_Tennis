import shutil
import kagglehub
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

path = kagglehub.dataset_download(
    "dissfya/atp-tennis-2000-2023daily-pull",
    path="atp_tennis.csv",
    output_dir=str(ROOT / "Data"),
    force_download=True,
)

