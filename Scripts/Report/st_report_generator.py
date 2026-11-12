import streamlit as st
import pandas as pd
from pathlib import Path
import json
from datetime import datetime, timezone
from geopy.geocoders import Nominatim

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"

def report_generator(today_matches, player_features, h2h_features, news_summaries, status):

    """
        Generates the streamlit report given all of the data that has beene extracted.
    """

    with open(DATA_DIR / "status.json") as f:
        status = json.load(f)

    if not status["status"]:
        st.write(f"Report could not be generated. Reason: {status["message"]}")

    else:

        st.title(f"Match Report for {datetime.today().date()}")

        n_matches = len(today_matches)

        labels = [f"{match["Player"][0]} vs. {match["Player"][1]}, {match["Tournament/Round"]}" for match in today_matches]

        i = st.selectbox("Select a match",
                range(n_matches),
                format_func= lambda i: labels[i])

        st.dataframe({k : today_matches[i][k] for k in ["Player", "Age", "Nationality", "Points", "Hand", "Ranking"]})

        p1, p2 = today_matches[i]["Player"]
        surface = today_matches[i]["Surface"]
        tournament = today_matches[i]["Tournament"]
        h = h2h_features[i]

        lines = [
        f"{p1} and {p2} have played each other {h['matches_played']} times. "
        f"The overall head-to-head record is {p1} {h['p1_win_total']} - "
        f"{h['p2_win_total']} {p2}."
        ]

        if h["p1_win_total_surf"] + h["p2_win_total_surf"] > 0:
            lines.append(f"On {surface}, the record is {p1} {h['p1_win_total_surf']} - "
                 f"{h['p2_win_total_surf']} {p2}.")
        else:
            lines.append(f"They have not played each other on {surface}.")

        if h["p1_tourn_win"] + h["p2_tourn_win"] > 0:
            lines.append(f"At {tournament}, the record is {p1} {h['p1_tourn_win']} - "
                 f"{h['p2_tourn_win']} {p2}.")
        else:
            lines.append(f"They have not played each other at {tournament}.")

        st.write(" ".join(lines))

        try:
            geolocator = Nominatim(user_agent="tennis_prediction", timeout=10)
            location = geolocator.geocode(today_matches[i]["Tournament"])
        except Exception as e:
            st.write(f"Map cannot be generated: {e!r}")

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
    with open(DATA_DIR / "status.json", encoding="utf-8") as f:
        status = json.load(f)

    report_generator(today_matches, player_features, h2h_features, news_summaries, status)

if __name__ == "__main__":
    main()
