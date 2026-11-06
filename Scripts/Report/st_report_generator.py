import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone
from geopy.geocoders import Nominatim

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"

def report_generator(today_matches, player_features, h2h_features, news_summaries):

    """
        Generates the streamlit report given all of the data that has beene extracted.
    """

    st.title(f"Match Report for {datetime.today().date()}")

    n_matches = len(today_matches)

    labels = [f"{match["Player"][0]} vs. {match["Player"][1]}, {match["Tournament/Round"]}" for match in today_matches]

    i = st.selectbox("Select a match",
                range(n_matches),
                format_func= lambda i: labels[i])

    st.dataframe({k : today_matches[i][k] for k in ["Player", "Age", "Nationality", "Points", "Hand", "Ranking"]})

    h2h_data = h2h_features[i]
    st.write(f"{today_matches[i]["Player"][0]} and {today_matches[i]["Player"][1]} have played against "
              f"each other {h2h_data["matches_played"]} times. The overall head-to-head record is"
              f"{h2h_data["Player_1"]} {h2h_data["p1_win_total"]} - {h2h_data["p2_win_total"]} {h2h_data["Player_2"]}."
                )
    
    if h2h_data["p1_win_total_surf"] != 0:
        st.write(f"On {today_matches[i]["Surface"]}, the record is {h2h_data["Player_1"]} {h2h_data["p1_win_total_surf"]} - {h2h_data["p2_win_total_surf"]} {h2h_data["Player_2"]}")
    else:
        st.write(f"{today_matches[i]["Player"][0]} and {today_matches[i]["Player"][1]} have not played against each other on {today_matches[i]["Surface"]}.")

    if h2h_data["p1_win_total_tourn"] != 0:
        st.write(f"In {today_matches[i]["Tournament"]}, the record is {h2h_data["Player_1"]} {h2h_data["p1_win_total_tourn"]} - {h2h_data["p2_win_total_tourn"]} {h2h_data["Player_2"]}")
    else:
        st.write(f"{today_matches[i]["Player"][0]} and {today_matches[i]["Player"][1]} have not played against each other in {today_matches[i]["Tournament"]}.")

    geolocator = Nominatim(user_agent="tennis_prediction")
    location = geolocator.geocode(today_matches[i]["Tournament"])

    st.map(pd.DataFrame({"lat": [location.latitude], "lon": [location.longitude]}), zoom=4)

    st.header("Player-Specific Stats:")

    p1 = player_features[2*i]
    p2 = player_features[2*i + 1]

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

    match_id = today_matches[i]["Match_ID"]
    st.header("News Summary")
    st.write(news_summaries[today_matches[i]["Player"][0]])
    st.write(news_summaries[today_matches[i]["Player"][1]])



def main():
    with open(DATA_DIR / "matches_today.json", encoding="utf-8") as f:
        today_matches = json.load(f)
    with open(DATA_DIR / "player_features.json", encoding="utf-8") as f:
        player_features = json.load(f)
    with open(DATA_DIR / "news_summaries.json", encoding="utf-8") as f:
        news_summaries = json.load(f)
    with open(DATA_DIR / "h2h_features.json", encoding="utf-8") as f:
        h2h_features = json.load(f)

    report_generator(today_matches, player_features, h2h_features, news_summaries)

if __name__ == "__main__":
    main()
