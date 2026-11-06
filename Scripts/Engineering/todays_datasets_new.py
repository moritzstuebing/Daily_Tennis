import duckdb as db
import pandas as pd
from pathlib import Path
import json
import re
import unicodedata

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"
DB_PATH = DATA_DIR.parent / "all_time_db_today.db"

tourn_lookup = pd.read_csv(DATA_DIR / "tournament_lookup.csv")

# Letters that have no separate accent mark, so normalize() can't strip them
SPECIAL_LETTERS = str.maketrans({
    "đ": "d", "Đ": "D",
    "ø": "o", "Ø": "O",
    "ł": "l", "Ł": "L",
    "ß": "ss",
    "æ": "ae", "Æ": "Ae",
})

# The surname, then initials that must contain a dot: "Struff J.L.", "Blanch Dar."
KAGGLE_NAME = re.compile(r"^(?P<surname>.+?) (?P<initials>[A-Z][a-z]{0,2}\.(?: ?[A-Z][a-z]{0,2}\.?)*)$")

# For names the matcher can't work out
NAME_OVERRIDES = {"Novak Đoković": "Djokovic N."}


def normalise_name(name: str) -> str:
    """Removes accents and turns apostrophes into spaces to match the Kaggle names."""
    name = name.translate(SPECIAL_LETTERS)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(char for char in name if not unicodedata.combining(char))
    return name.replace("'", " ").replace("’", " ")


def load_kaggle_names() -> list:
    """Returns every Kaggle player name, split into surname and initials, with their latest match date."""
    rows = db.sql(f"""
        SELECT TRIM(name), MAX(Date)
        FROM (SELECT Player_1 AS name, Date FROM read_csv_auto('{DATA_DIR.as_posix()}/atp_tennis.csv')
              UNION ALL
              SELECT Player_2, Date FROM read_csv_auto('{DATA_DIR.as_posix()}/atp_tennis.csv'))
        GROUP BY 1
    """).fetchall()

    kaggle_names = []
    for name, last_played in rows:
        parts = KAGGLE_NAME.match(name)
        if parts:
            kaggle_names.append({
                "name": name,
                "surname": re.split(r"[ -]", parts["surname"].lower()),
                "initials": [i.lower() for i in re.findall(r"[A-Z][a-z]*", parts["initials"])],
                "last_played": last_played,
            })
    return kaggle_names


def find_kaggle_name(api_name: str, kaggle_names: list) -> str | None:
    """Returns the most recently active Kaggle name that fits the API name, or None."""
    if api_name in NAME_OVERRIDES:
        return NAME_OVERRIDES[api_name]

    words = re.split(r"[ -]+", normalise_name(api_name).lower().strip())
    matches = []
    for kaggle in kaggle_names:
        n = len(kaggle["surname"])
        given = words[:-n]
        if (words[-n:] == kaggle["surname"]
                and len(kaggle["initials"]) <= len(given)
                and all(g.startswith(i) for g, i in zip(given, kaggle["initials"]))):
            matches.append(kaggle)

    return max(matches, key=lambda k: k["last_played"])["name"] if matches else None


def names_formatter(today_matches: list) -> list:
    """Reformats the live_tennis_api player names into the Kaggle ATP format."""
    kaggle_names = load_kaggle_names()

    for match in today_matches:
        formatted = []
        for player in match["Player"]:
            kaggle_name = find_kaggle_name(player, kaggle_names)
            if kaggle_name is None:
                print(f"WARNING: no Kaggle match for {player}")
                kaggle_name = normalise_name(player)
            formatted.append(kaggle_name)
        match["Player"] = formatted

    return today_matches

def tournament_formatter(today_matches: list, tourn_lookup: pd.DataFrame) -> list:

    """
        Turns the tournament entries of the today_matches data into Kaggle names.
    """
    mapping = dict(zip(tourn_lookup["API_Name"], tourn_lookup["Dataset_Name"]))

    for match in today_matches:
        api_name = match["Tournament"]
        if api_name in mapping:
            match["Tournament"] = mapping[api_name]
        else:
            print(f"Warning: no Kaggle name for tournament '{api_name}'")

    return today_matches
    
def formatting(today_matches: list, tourn_lookup: pd.DataFrame) -> list:
    return tournament_formatter(names_formatter(today_matches), tourn_lookup)

def create_player_datasets(matches: list) -> pd.DataFrame:

    """
        Builds the engineered player features for today's matches.

        Expects matches whose player names are already in Kaggle format (see names_formatter).
        Returns one dataframe with a row per player and saves it to Data/player_specifics.json.
        Each player's match-level history is kept in the player_match_history table in the database.
    """

    # One row per player, keeping today's surface for the features below
    todays_players = pd.DataFrame(
        [(player, match["Surface"])
         for match in matches
         for player in match["Player"]],
        columns=["Player", "Today_Surface"],
        dtype="object",
    )
    todays_players["player_order"] = range(len(todays_players))

    with db.connect(str(DB_PATH)) as con:
        con.register("todays_players", todays_players)

        con.sql(f"""
        CREATE OR REPLACE TABLE raw_matches AS
        SELECT * FROM read_csv_auto('{DATA_DIR.as_posix()}/atp_tennis.csv')
        """)

        # Every historical match for today's players, one row per player per match
        con.sql("""
            CREATE OR REPLACE TABLE player_match_history AS
            SELECT
                t.Player,
                t.player_order,
                m.* EXCLUDE (Pts_1, Pts_2, Odd_1, Odd_2, Rank_1, Rank_2, Score),
                CASE WHEN m.Player_1 = t.Player THEN m.Player_2 ELSE m.Player_1 END AS Opponent,
                CASE WHEN m.Player_1 = t.Player THEN m.Pts_1 ELSE m.Pts_2 END AS player_pts,
                CASE WHEN m.Player_1 = t.Player THEN m.Pts_2 ELSE m.Pts_1 END AS opp_pts,
                CASE WHEN m.Player_1 = t.Player THEN m.Rank_1 ELSE m.Rank_2 END AS player_rank,
                CASE WHEN m.Player_1 = t.Player THEN m.Rank_2 ELSE m.Rank_1 END AS opp_Rank,
                CASE WHEN m.Winner = t.Player THEN 1 ELSE 0 END AS player_win,
                CASE WHEN m.Court = 'Outdoor' THEN 1 ELSE 0 END AS is_outdoor,
                CASE WHEN m."Best of" = 5 THEN 1 ELSE 0 END AS is_five_sets
            FROM (SELECT DISTINCT Player, player_order FROM todays_players) t
            JOIN raw_matches m
                ON t.Player = m.Player_1 OR t.Player = m.Player_2
        """)

        # Rolling/engineered features
        player_features = con.sql("""
            WITH player_matches AS (
                SELECT
                    t.player_order,
                    t.Player,
                    t.Today_Surface,
                    h.Surface,
                    h.Date,
                    h.player_win,
                    row_number() OVER (PARTITION BY t.player_order ORDER BY h.Date DESC) AS rn
                FROM todays_players t
                LEFT JOIN player_match_history h
                    ON t.Player = h.Player
            )
            SELECT
                Player,
                AVG(player_win) FILTER (WHERE rn <= 5)  AS five_sma,
                AVG(player_win) FILTER (WHERE rn <= 20) AS twenty_sma,
                AVG(player_win) FILTER (WHERE YEAR(Date) = YEAR(current_date)) AS year_win_pct,
                COUNT(*) FILTER (WHERE Date >= current_date - INTERVAL 30 DAY
                                AND Date <  current_date) AS matches_last_30,
                AVG(player_win) FILTER (WHERE Surface = Today_Surface AND YEAR(Date) = YEAR(current_date)) AS year_surface_winrate
            FROM player_matches
            GROUP BY player_order, Player
            ORDER BY player_order
        """).df()

    # Blank stats become null, which is valid JSON (NaN is not)
    records = player_features.astype(object).where(player_features.notna(), None).to_dict(orient="records")

    return records

def create_h2h_datasets(matches):
    
    """
        Takes all matches happening today and forms head-to-head data.
    """

    todays_matches = pd.DataFrame(
            [(match["Player"][0], match["Player"][1], match["Surface"], match["Tournament"])
             for match in matches
             ],
            columns=["Player_1", "Player_2", "Today_Surface", "Today_Tournament"],
            dtype="object",
        )
    todays_matches["match_order"] = range(len(todays_matches))

    with db.connect(str(DB_PATH)) as con:
        con.register("todays_matches", todays_matches)

        con.sql(f"""
                CREATE OR REPLACE TABLE raw_matches AS
                SELECT * FROM read_csv_auto('{DATA_DIR.as_posix()}/atp_tennis.csv')
                """)

        con.sql("""
        CREATE OR REPLACE TABLE historical_matchups AS (
            SELECT 
                m.match_order, 
                m.Player_1, 
                m.Player_2,
                m.Today_Surface,
                m.Today_Tournament,
                h.* EXCLUDE (Player_1, Player_2, Pts_1, Pts_2, Odd_1, Odd_2, Rank_1, Rank_2, Score)
            FROM todays_matches m
            LEFT JOIN raw_matches h
                ON ((m.Player_1 = h.Player_1) AND (m.Player_2 = h.Player_2))
                OR ((m.Player_1 = h.Player_2) AND (m.Player_2 = h.Player_1))
        )
        """)

        h2h_features = con.sql("""
            SELECT
                Player_1,
                Player_2,
                COUNT(Winner)                                                               AS matches_played,
                COUNT(*) FILTER (WHERE Winner = Player_1)                                   AS p1_win_total,
                COUNT(*) FILTER (WHERE Winner = Player_2)                                   AS p2_win_total,
                COUNT(*) FILTER (WHERE Winner = Player_1 AND Surface = Today_Surface)       AS p1_win_total_surf,
                COUNT(*) FILTER (WHERE Winner = Player_2 AND Surface = Today_Surface)       AS p2_win_total_surf,
                COUNT(*) FILTER (WHERE Winner = Player_1 AND Tournament = Today_Tournament) AS p1_tourn_win,
                COUNT(*) FILTER (WHERE Winner = Player_2 AND Tournament = Today_Tournament) AS p2_tourn_win
            FROM historical_matchups
            GROUP BY match_order, Player_1, Player_2
            ORDER BY match_order
        """).df()

    records = h2h_features.astype(object).where(h2h_features.notna(), None).to_dict(orient="records")

    return records

def main():
    with open(DATA_DIR / "matches_today.json", encoding="UTF-8") as f:
        matches_today = json.load(f)
    matches_today = formatting(matches_today, tourn_lookup)
    create_player_datasets(matches_today)
    create_h2h_datasets(matches_today)


if __name__ == "__main__":
    main()
