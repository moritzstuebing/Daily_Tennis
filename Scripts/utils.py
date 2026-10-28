import pandas as pd
import streamlit as st
import csv
import unicodedata
from datetime import datetime, timezone, timedelta

today = datetime.now(timezone.utc).date()

def generate_lookup_table(data):
    lookup = (data.sort_values("Date")
              .groupby("Tournament")[["Surface", "Series", "Court"]]
              .last()
              .reset_index()
    )
    return lookup

def log_usage(resp, path="token_log.csv"):
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(),
            resp.model,
            resp.usage.input_tokens,
            resp.usage.output_tokens,
            resp.stop_reason,
        ])

def data_extractor(matches):

    """
        Given the data on today's matches as a json file from the live_tennis_api, extracts 
        the information we need, and cleans.
    """

    match_info_list = []

    for match in matches:
        # all info in (p1, p2) format
        match_info_dict = {"Player" : (match['players']['p1']['name'], match['players']['p2']['name']),
                           "Age" : ((today - pd.to_datetime(match['players']['p1']['birthday']).date()).days // 365, (today - pd.to_datetime(match['players']['p2']['birthday']).date()).days // 365),
                           "Nationality" : (match['players']['p1']['country'].upper(), match['players']['p2']['country'].upper()),
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

def match_table_maker(path):

    """
        Produces a table of all matches occuring today, players, tournament, etc.
    """

    df = pd.read_json(path)
    st.write(df[["Players", "Tournament/Round"]])

def player_names_transformer(name):

    """
        Transforms the full name of a player into the format used in the kaggle dataset.
    """

    # strip accents (e.g. "Menšik" -> "Mensik"), the kaggle dataset is ASCII only
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()

    items = name.split(" ")
    new_name = items[1] + " " + items[0][0] + "."

    return new_name

