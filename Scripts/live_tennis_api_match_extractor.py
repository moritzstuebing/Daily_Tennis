import anthropic
from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
from utils import data_extractor
import json
from pathlib import Path

# Load API key
load_dotenv()
base = "https://api.livetennisapi.com/api/public/v1"
HEADERS = {"X-API-Key": os.getenv("LIVE_TENNIS_API_KEY")}
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
DATA_DIR.mkdir(exist_ok=True) # makes folder if missing

def todays_matches_extraction(date=None):

    """
        Uses the Live Tennis API to extract all matches today
    """

    if date is None:
        date = datetime.now(timezone.utc).date().isoformat()
    
    re = requests.get(f"{base}/matches", headers=HEADERS, 
                            params={"status" : "upcoming",
                                    "tour" : "atp",
                                    "draw" : "singles",
                                    "from" : f"{date}",
                                    "to" : f"{date}"}).json()
    data = data_extractor(re["data"])
    return data

def main():
    data = todays_matches_extraction()
    with open(DATA_DIR / 'matches_today.json', "w") as file:
        json.dump(data, file)

if __name__ == "__main__":
    main()
