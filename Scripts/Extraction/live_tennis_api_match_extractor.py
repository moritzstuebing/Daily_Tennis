from dotenv import load_dotenv
import os
import requests
from datetime import datetime, timezone
from utils import data_extractor
import json
from pathlib import Path
import pandas as pd

# Load API key
load_dotenv()
base = "https://api.livetennisapi.com/api/public/v1"
HEADERS = {"X-API-Key": os.getenv("LIVE_TENNIS_API_KEY")}
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"
DATA_DIR.mkdir(exist_ok=True) # makes folder if missing

today = datetime.now(timezone.utc).date()

def data_extractor(matches):

    """
        Given the data on today's matches as a json file from the live_tennis_api, extracts 
        the information we need, and cleans.
    """

    match_info_list = []

    for match in matches:
        # all info in (p1, p2) format
        match_info_dict = {"Match_ID" : match["id"],
                            "Player" : (match['players']['p1']['name'], match['players']['p2']['name']),
                           "Age" : ((today - pd.to_datetime(match['players']['p1']['birthday']).date()).days // 365, (today - pd.to_datetime(match['players']['p2']['birthday']).date()).days // 365),
                           "Nationality" : ((match['players']['p1']['country'] or "").upper(), (match['players']['p2']['country'] or "").upper()),
                           "Hand" : (match['players']['p1']['hand'], match['players']['p2']['hand']),
                           "Ranking" : (match['players']['p1']['ranking'], match['players']['p2']['ranking']),
                           "Points" : (match['players']['p1']['ranking_points'], match['players']['p2']['ranking_points']),
                           "Tournament" : match['tournament'],
                           "Tournament_id" : match["id"],
                           "Surface" : match['surface'].capitalize(),
                           "Tournament/Round" : match['round'],
                           "Round" : match['round_code'],
                           "Is_indoor" : match['indoor']}
        match_info_list.append(match_info_dict)

    return match_info_list

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
