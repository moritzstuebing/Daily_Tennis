import anthropic
from dotenv import load_dotenv; load_dotenv()
from pathlib import Path
import json
from utils import *
from datetime import datetime, timezone

today = datetime.now(timezone.utc).date().isoformat()

load_dotenv()
client = anthropic.Anthropic()

# Pipeline

# All matches -> Extract Summary -> Return json ready for dashboard

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

with open(DATA_DIR / "matches_today.json") as f:
    matches_today = json.load(f)

summaries = {}

for match in matches_today:
    p1 = match["Player"][0]
    p2 = match["Player"][1]
    tournament = match["Tournament"]
    date = today
    match_id = match["Match_ID"]

    summary, _ = news_pipeline(p1, p2, tournament, date)

    summaries[str(match_id)] = summary

with open(DATA_DIR / "today_summaries.json", "w") as f:
    json.dump(summaries, f)
