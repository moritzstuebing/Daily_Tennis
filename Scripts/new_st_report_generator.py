import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone
from geopy.geocoders import Nominatim

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
with open(DATA_DIR / "matches_today.json", encoding="utf-8") as f:
    matches = json.load(f)
with open(DATA_DIR / "player_specifics.json", encoding="utf-8") as f:
    player_specifics = json.load(f)
with open(DATA_DIR / "today_summaries.json", encoding="utf-8") as f:
    summaries = json.load(f)



st.title(f"Match Report for {datetime.today().date()}")

n_matches = len(matches)

labels = [f"{match["Player"][0]} vs. {match["Player"][1]}, {match["Tournament/Round"]}" for match in matches]

i = st.selectbox("Select a match",
             range(n_matches),
             format_func= lambda i: labels[i])

st.dataframe({k : matches[i][k] for k in ["Player", "Age", "Nationality", "Points", "Hand", "Ranking"]})

geolocator = Nominatim(user_agent="tennis_prediction")
location = geolocator.geocode(matches[i]["Tournament"])

st.map(pd.DataFrame({"lat": [location.latitude], "lon": [location.longitude]}), zoom=4)

st.header("Player-Specific Stats:")

p1 = player_specifics[2*i][0]
p2 = player_specifics[2*i + 1][0]

stats = pd.DataFrame({
    p1["Player"]: {k: v for k, v in p1.items() if k != "Player"},
    p2["Player"]: {k: v for k, v in p2.items() if k != "Player"},
})

stats = stats.rename(index={"five_sma" : "Five-Match Win Rate",
                    "twenty_sma" : "Twenty-Match Win Rate",
                    "year_win_pct" : "Yearly Win Percentage",
                    "matches_last_30" : "Matches Played Last 30 Days",
                    "year_surface_winrate" : "Surface-Specific Yearly Win Rate"})

st.dataframe(stats)

match_id = matches[i]["Match_ID"]
st.header("News Summary")
st.write(summaries.get(str(match_id), "No news summary available for this match."))



