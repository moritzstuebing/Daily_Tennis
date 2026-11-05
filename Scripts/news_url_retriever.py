import feedparser
import os
from pathlib import Path
import json
from urllib.parse import quote

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
with open(DATA_DIR / "matches_today.json") as f:
    matches = json.load(f)

def player_names(matches):

    """
        Extracts all player names from the matche json today.
    """

    players = []
    for match in matches:
        players.extend(match["Player"])

    return players

def get_news(players):

    """
        Takes all players today and finds news urls using Google News RSS.
    """

    url_dict = {}
    for player in players:
        query = quote(f'"{player}"') # double quotes needed to ensure whole name gets searched
        d = feedparser.parse(f'https://news.google.com/rss/search?q={query}%20when%3A7d&hl=en-GB&gl=GB&ceid=GB:en')
        url_dict[player] = [{"title": entry.title,
                        "link": entry.link,         
                        "published": entry.get("published"),
                        "source": entry.get("source", {}).get("title")
                        } for entry in d.entries[:10]]

    return url_dict



def get_headlines(matches):

    return get_news(player_names(matches))



def main():
    with open(DATA_DIR / "matches_today.json") as f:
        matches = json.load(f)
    news = get_news(matches)
    with open(DATA_DIR / "news_urls.json", "w") as f:
        json.dump(news, f, indent=2)


if __name__ == "__main__":
    main()

