from zoneinfo import ZoneInfo
from datetime import datetime, timedelta, timezone
import requests
from dotenv import load_dotenv
import os
import requests
import pandas as pd
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

load_dotenv()

API_KEY = os.environ["ODDS_API_KEY"]
base = "https://api.the-odds-api.com/v4/sports"

sports = requests.get(base, params={"apiKey" : API_KEY, "regions" : "uk"}).json()
atp_keys = [s["key"] for s in sports if s["group"] == "Tennis" and "atp" in s["key"]]

uk = ZoneInfo("Europe/London")
day = datetime.now(uk).date() + timedelta(days=1) # change back when done testing (doing for tomorrow rn)
start = datetime.combine(day, datetime.min.time(), tzinfo=uk).astimezone(timezone.utc)
end = start + timedelta(days=1, seconds=-1)
fmt = "%Y-%m-%dT%H:%M:%SZ"

events_today_dict = {}

all_events_today = []
keys_list = []
p1_list = []
p2_list = []

for key in atp_keys:
    events_today = requests.get(f"{base}/{key}/odds",
                                params={"apiKey" : API_KEY,
                                        "regions" : "uk",
                                        "markets" : "h2h",
                                        "commenceTimeFrom" : start.strftime(fmt),
                                        "commenceTimeTo" : end.strftime(fmt)}).json()
    
    if events_today:   # if there actually are any events
        for event in events_today:
            keys_list.append(key)   # append key each time for easy pandas dataframe conversion
            p1_list.append(event["home_team"])
            p2_list.append(event["away_team"])

# Form dictionary
if p1_list:
    events_today_dict["Tournament"] = keys_list 
    events_today_dict["Player_1"] = p1_list
    events_today_dict["Player_2"] = p2_list

else:
    print("No new match today")

df = pd.DataFrame(events_today_dict)
df = df.rename(columns={0 : "Tournament_Key", 1 : "Player_1", 2 : "Player_2"})
df.to_csv(DATA_DIR / "matches_today.csv", index=False)
