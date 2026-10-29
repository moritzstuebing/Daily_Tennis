import duckdb as db
import pandas as pd
from pathlib import Path
import json
from utils import player_names_transformer

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

with open(DATA_DIR / "matches_today.json") as f:
    matches = json.load(f)


# Player-Specific Stats
players_info = []

for match in matches:
    players_info.append((player_names_transformer(match["Player"][0]), match["Surface"]))
    players_info.append((player_names_transformer(match["Player"][1]), match["Surface"]))

con = db.connect("all_time_db_today.db")

con.sql("""
CREATE OR REPLACE TABLE raw_matches AS
SELECT * FROM read_csv_auto('./Data/atp_tennis.csv')
""")

rows = []

for player, surface in players_info:

    con.sql(f"""
        CREATE OR REPLACE TABLE "{player}" AS 
        SELECT * FROM raw_matches
        WHERE Player_1 = '{player}'
        OR Player_2 = '{player}'
    """)
    
    con.sql(f"""
            CREATE OR REPLACE TABLE "{player}" AS
            SELECT *,
            CASE WHEN Player_1 = '{player}' THEN Player_2 ELSE Player_1 END AS Opponent,
            CASE WHEN Player_1 = '{player}' THEN Pts_1 ELSE Pts_2 END AS player_pts,
            CASE WHEN Player_1 = '{player}' THEN Pts_2 ELSE Pts_1 END AS opp_pts,
            CASE WHEN Player_1 = '{player}' THEN Rank_1 ELSE Rank_2 END AS player_rank,
            CASE WHEN Player_1 = '{player}' THEN Rank_2 ELSE Rank_1 END AS opp_Rank,
            CASE WHEN Winner = '{player}' THEN 1 ELSE 0 END AS player_win,
            CASE WHEN Court = 'Outdoor' THEN 1 ELSE 0 END AS is_outdoor,
            CASE WHEN "Best of" = 5 THEN 1 ELSE 0 END AS is_five_sets
            FROM "{player}"
            """)
    
    con.sql(f"""
            CREATE OR REPLACE TABLE "{player}" AS
            SELECT * EXCLUDE (Pts_1, Pts_2, Odd_1, Odd_2, Rank_1, Rank_2, Score)
            FROM "{player}"
            """)
    
        # New table with rolling/engineered features
    
    con.sql(f"""
            CREATE OR REPLACE TABLE "{player}_current" AS
            WITH recent AS (
                SELECT
                    *,
                    row_number() OVER (ORDER BY Date DESC) AS rn
                FROM "{player}"
            )
            SELECT
                '{player}' AS Player,
                AVG(player_win) FILTER (WHERE rn <= 5)  AS five_sma,
                AVG(player_win) FILTER (WHERE rn <= 20) AS twenty_sma,
                AVG(player_win) FILTER (WHERE YEAR(Date) = YEAR(current_date)) AS year_win_pct,
                COUNT(*) FILTER (WHERE Date >= current_date - INTERVAL 30 DAY
                                AND Date <  current_date) AS matches_last_30,
                AVG(player_win) FILTER (WHERE Surface = '{surface}' AND YEAR(Date) = YEAR(Current_Date)) AS year_surface_winrate,
    
            FROM recent
        """)

    rows.append(con.sql(f'SELECT * FROM "{player}_current"').df().to_dict(orient="records"))
    

with open(DATA_DIR / "player_specifics.json", "w", encoding="UTF-8") as f:
    json.dump(rows, f)

    