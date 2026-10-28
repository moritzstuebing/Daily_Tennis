import pandas as pd
from pathlib import Path
import duckdb

DATA_DIR = Path(__file__).parent.parent / "Data"

df = pd.read_csv(DATA_DIR / "matches_today.csv").astype(str)
df_all_time = pd.read_csv(DATA_DIR / "atp_tennis.csv")

# Reformatting for kaggle dataset
player_names = []
matchups = [] # all match player name pairs as tuples
match_info = {} # dict for each match info. key is tuple of player pairs

tournament_lookup_df = pd.read_csv(DATA_DIR / 'lookup_table.csv')

for i in range(df.shape[0]):    # loop over matches 
    match = []
    tournament_key = df.iloc[i, 0]
    tournament_name = tournament_lookup_df.loc[
    tournament_lookup_df["Odds_Key"] == tournament_key, "Dataset_Name"].item()
    surface = tournament_lookup_df.loc[tournament_lookup_df["Dataset_Name"] == tournament_name, "Surface"].item()

    for j in range(1, df.shape[1]):
        string_list = df.iloc[i, j].split(" ")
        new_string = " ".join(string_list[1:])
        new_string = new_string + " " + string_list[0][0] + "."
        df.iloc[i, j] = new_string
        player_names.append((new_string, tournament_name, surface))
        match.append(new_string)
    
    match.append(tournament_name)
    matchups.append(tuple(match))

con = duckdb.connect("all_time_db_today.db")

con.sql("""
CREATE OR REPLACE TABLE raw_matches AS
SELECT * FROM read_csv_auto('./Data/atp_tennis.csv')
""")

# (player, tournament, surface)

for i in range(len(player_names)):
    con.sql(f"""
        CREATE OR REPLACE TABLE "{player_names[i][0]}" AS
        SELECT * FROM raw_matches
        WHERE Player_1 = '{player_names[i][0]}'
        OR Player_2 = '{player_names[i][0]}'
        """)

    con.sql(f"""
        CREATE OR REPLACE TABLE "{player_names[i][0]}" AS
        SELECT *,
        CASE WHEN Player_1 = '{player_names[i][0]}' THEN Player_2 ELSE Player_1 END AS Opponent,
        CASE WHEN Player_1 = '{player_names[i][0]}' THEN Pts_1 ELSE Pts_2 END AS player_pts,
        CASE WHEN Player_1 = '{player_names[i][0]}' THEN Pts_2 ELSE Pts_1 END AS opp_pts,
        CASE WHEN Player_1 = '{player_names[i][0]}' THEN Rank_1 ELSE Rank_2 END AS player_rank,
        CASE WHEN Player_1 = '{player_names[i][0]}' THEN Rank_2 ELSE Rank_1 END AS opp_Rank,
        CASE WHEN Winner = '{player_names[i][0]}' THEN 1 ELSE 0 END AS player_win,
        CASE WHEN Court = 'Outdoor' THEN 1 ELSE 0 END AS is_outdoor,
        CASE WHEN "Best of" = 5 THEN 1 ELSE 0 END AS is_five_sets
        FROM "{player_names[i][0]}"
        """)

    con.sql(f"""
        CREATE OR REPLACE TABLE "{player_names[i][0]}" AS
        SELECT * EXCLUDE (Pts_1, Pts_2, Odd_1, Odd_2, Rank_1, Rank_2, Score)
        FROM "{player_names[i][0]}"
        """)

    con.sql(f"""
        COPY (SELECT * FROM "{player_names[i][0]}") TO './Data/{player_names[i][0].replace(" ", "_")}.csv'
        """)

    # New table with rolling/engineered features

    con.sql(f"""
        CREATE OR REPLACE TABLE "{player_names[i][0]}_current" AS
        WITH recent AS (
            SELECT
                *,
                row_number() OVER (ORDER BY Date DESC) AS rn
            FROM "{player_names[i][0]}"
        )
        SELECT
            '{player_names[i][0]}' AS Player,
            AVG(player_win) FILTER (WHERE rn <= 5)  AS five_sma,
            AVG(player_win) FILTER (WHERE rn <= 20) AS twenty_sma,
            AVG(player_win) FILTER (WHERE YEAR(Date) = YEAR(current_date)) AS year_win_pct,
            COUNT(*) FILTER (WHERE Date >= current_date - INTERVAL 30 DAY
                            AND Date <  current_date) AS matches_last_30,
            COUNT(*) FILTER (WHERE Tournament == '{player_names[i][1]}') AS match_in_this_tourn,
            AVG(player_win) FILTER (WHERE Tournament == '{player_names[i][1]}') AS wins_in_this_tourn,
            AVG(player_win) FILTER (WHERE Surface = '{player_names[i][2]}' AND YEAR(Date) = YEAR(Current_Date)) AS year_surface_winrate,

        FROM recent
    """)

    con.sql(f"""
            COPY (SELECT * FROM "{player_names[i][0]}_current") TO './Data/{player_names[i][0].replace(" ", "_").replace(".", "")}_current.csv'
            """)

# Head-to-head data
for i in range(int(len(player_names)/2)):
    con.sql(f"""
    CREATE OR REPLACE TABLE "{player_names[2*i][0]}vs{player_names[2*i+1][0]}" AS 
    SELECT * FROM "{player_names[2*i][0]}"
    WHERE Opponent = '{player_names[2*i+1][0]}'
    """)

    con.sql(f"""
    CREATE OR REPLACE TABLE "{player_names[2*i][0]}vs{player_names[2*i+1][0]}" AS
    SELECT '{player_names[2*i][0]}' AS Player_1,
    COUNT(*) AS matches_played, 
    SUM(player_win) AS matches_won,
    COUNT(*) AS total_matches,
    COUNT(*) - SUM(player_win) AS matches_lost
    FROM "{player_names[2*i][0]}vs{player_names[2*i+1][0]}"
    """)

    con.sql(f"""
                COPY (SELECT * FROM "{player_names[2*i][0]}vs{player_names[2*i+1][0]}") TO './Data/{player_names[2*i][0]}vs{player_names[2*i+1][0].replace(" ", "_")}_current.csv'
                """)

# All data in unified dataframes

for i in range(1, len(player_names)):
    con.sql(f"""
    CREATE OR REPLACE TABLE "{player_names[i][0]}_current"
    AS SELECT * FROM "{player_names[i-1][0]}_current"
    UNION ALL
    SELECT * FROM "{player_names[i][0]}_current"
    """)

con.sql(f"""
            COPY (SELECT * FROM "{player_names[-1][0]}_current") TO './Data/current_data.csv'
            """)

for i in range(1, int(len(player_names) / 2)):
    con.sql(f"""
        CREATE OR REPLACE TABLE "{player_names[2*i][0]}vs{player_names[2*i+1][0]}"
        AS SELECT * FROM "{player_names[2*(i-1)][0]}vs{player_names[2*i-1][0]}"
        UNION ALL
        SELECT * FROM "{player_names[2*i][0]}vs{player_names[2*i+1][0]}"
        """)

con.sql(f"""
                COPY (SELECT * FROM "{player_names[-2][0]}vs{player_names[-1][0]}") TO './Data/head_to_head_current.csv'
                """)