import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils import match_table_maker
from datetime import datetime, timezone

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
match_info_path = DATA_DIR / "matches_today.json"
date = datetime.now(timezone.utc).date().isoformat()

st.title(f"Report for {date}")

st.header("Matches Today:")

match_table_maker(match_info_path)


def report_maker(stats_df, h2h_df, i, columns=None):

    """
        Makes the report using streamlit. Expects a dataframe and index for the first player
        in the match. columns should be a list of headers for each column.
    """

    p1 = stats_df.loc[i, "Player"]
    p2 = stats_df.loc[i+1, "Player"]

    h2h = h2h_df[h2h_df["Player_1"] == p1]

    st.header("Head to Head Information")
    st.markdown(
        f"{p1} and {p2} have played against each other {h2h["matches_played"].item()} times. "
        f"Of these matches, {p1} has won {h2h["matches_won"].item()} times, "
        f"and {p2} has won {h2h["matches_lost"].item()} times. This gives an overall "
        f"head to head as {p1} {h2h["matches_won"].item()} - {h2h["matches_lost"].item()} {p2}")

    p1_data = stats_df.iloc[i]
    p2_data = stats_df.iloc[i+1]

    st.header(f"{p1_data["Player"]}")
    if columns is None:
        st.write(p1_data.rename("Stats").drop(columns="Player"))

    else:
        st.write(p1_data.rename("Stats").drop(columns="Player"), columns=columns)

    st.header(f"{p2_data["Player"]}")
    if columns is None:
        st.write(p2_data.rename("Stats").drop(columns="Player"))
    
    else:
        st.write(p2_data.rename("Stats").drop(columns="Player"), columns=columns)

stats_df = pd.read_csv("./Data/current_data.csv")
h2h_df = pd.read_csv("./Data/head_to_head_current.csv")

h2h_df

df_list = []
matches = []

n_matches = int(stats_df.shape[0] / 2)

st.title(f"Match report for {datetime.today().strftime("%Y-%m-%d")}")

labels = [f"{stats_df.iloc[2*i]["Player"]}" + " vs. " + f"{stats_df.iloc[2*i+1]["Player"]}"
        for i in range(n_matches)]
i = st.selectbox("Matches", range(n_matches), format_func= lambda i: labels[i])
report_maker(stats_df, h2h_df, 2 * i)
