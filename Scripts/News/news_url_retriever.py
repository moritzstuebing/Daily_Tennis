import feedparser
import os
from pathlib import Path
import json
from urllib.parse import quote

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"

def player_names(matches):

    """
        Extracts all player names from the matches today json into a single list.
    """

    players = []
    for match in matches:
        players.extend(match["Player"])

    return players

import time
import requests
import feedparser
from urllib.parse import quote

def get_news(players):
    """
    Takes all players today and finds news urls using Google News RSS.
    """
    url_dict = {}
    failures = 0

    for player in players:
        try:
            query = quote(f'"{player}" tennis')
            url = f"https://news.google.com/rss/search?q={query}%20when%3A7d&hl=en-GB&gl=GB&ceid=GB:en"
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()                  # 429 / 503 now raise

            d = feedparser.parse(resp.content)
            if d.bozo and not d.entries:             # genuinely broken feed
                raise ValueError(f"Malformed feed: {d.bozo_exception}")

            url_dict[player] = [{"title": e.get("title"),
                                 "link": e.get("link"),
                                 "published": e.get("published"),
                                 "source": e.get("source", {}).get("title")}
                                for e in d.entries[:10]]
        except Exception as e:
            print(f"News lookup failed for {player}: {e!r}")
            url_dict[player] = []
            failures += 1

        time.sleep(1)  # spacing out requests

    if players and failures == len(players):
        raise RuntimeError("News lookup failed for every player")

    return url_dict, failures


def get_headlines(matches):

    return get_news(player_names(matches))

def main():
    with open(DATA_DIR / "matches_today.json") as f:
        matches = json.load(f)
    news, failures = get_news(player_names(matches))
    with open(DATA_DIR / "news_urls.json", "w") as f:
        json.dump(news, f, indent=2)


if __name__ == "__main__":
    main()

