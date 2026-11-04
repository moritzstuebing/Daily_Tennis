import feedparser
import os
from pathlib import Path
import json
from urllib.parse import quote

DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

with open(DATA_DIR / "matches_today.json") as f:
    matches = json.load(f)

players = []
for match in matches:
    players.extend(match["Player"])

url_dict = {}
for player in players:

    query = quote(f'"{player}"')
    d = feedparser.parse(f'https://news.google.com/rss/search?q={query}%20when%3A7d&hl=en-GB&gl=GB&ceid=GB:en')
    links = [entry.link for entry in d.entries[:10]]
    url_dict[player] = links

with open(DATA_DIR / "news_urls.json", "w") as f:
    json.dump(url_dict, f)

