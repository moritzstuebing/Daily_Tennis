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

# Obtain json file for today's matches from API, and extract the information we want
today = datetime.now(timezone.utc).date().isoformat()
re = requests.get(f"{base}/matches", headers=HEADERS, 
                  params={"status" : "upcoming",
                          "tour" : "atp",
                          "draw" : "singles",
                          "from" : f"{today}",
                          "to" : f"{today}"}).json()
data = data_extractor(re["data"])

# Load the json file to our datasets
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
DATA_DIR.mkdir(exist_ok=True) # makes folder if missing
with open(DATA_DIR / 'matches_today.json', "w") as file:
    json.dump(data, file)

"""
I should eventually use the live_tennis_api to extract historical information aswell, since it
is more up to date
"""