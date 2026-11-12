import pandas as pd
import streamlit as st
import csv
import unicodedata
from datetime import datetime, timezone, timedelta
import anthropic
from typing import Literal
from pydantic import BaseModel
from  dotenv import load_dotenv
load_dotenv()
client = anthropic.Anthropic()

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

import unicodedata

# Letters that have no separate accent mark, so normalize() can't strip them
SPECIAL_LETTERS = str.maketrans({
    "đ": "d", "Đ": "D",
    "ø": "o", "Ø": "O",
    "ł": "l", "Ł": "L",
    "ß": "ss",
    "æ": "ae", "Æ": "Ae",
})


def normalise_name(name: str) -> str:
    """Removes accents and turns apostrophes into spaces to match the Kaggle names."""
    name = name.translate(SPECIAL_LETTERS)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(char for char in name if not unicodedata.combining(char))
    return name.replace("'", " ").replace("’", " ")


# Claude system prompts

SYSTEM = """You are a highly-skilled tennis analyst that researches pre-match tennis
news for a prediction dashboard.
Search for news from the last 7 days about each player in the given match.
Relevant: injuries, illness, withdrawals, retirements in recent matches, coaching changes,
travel/scheduling issues, surface or conditions comments, notable recent form.

Structure:
- One report per player. The header for each report should be the player's name, 
nationality, age and current rank. You do not need to reference where you got this 
information. If you cannot find some part of this information for one of the 
players, do not list it for the other player. 
- One bullet point each one 'Injury and Fitness', 'Last Match', 'Workload', 
'Form and Mindset'. Do not add any extra bullet points or miss any out in this list. 
If you can't find any information for one of the bullet points, write 
'No information found in this category'. Be honest: if you can't find anything, 
say that.
"""

SUMMARY_SYSTEM = """
You are a highly-skilled and well-written sports journalist. 
Provide a paragraph comparison of information about each player you have been provided.
Give a concluding remark at the end of this paragraph indicating whether any pre-match 
news could affect the outcome of the match.
"""

def research_match(p1, p2, tournament, date):

    """
        Uses Claude API to research match news.
    """

    messages = [{"role" : "user",
                "content" : f"Match: {p1} vs {p2}, {tournament}, {date}. Find relevant news."}]

    while True:
        resp = client.messages.create(
            model="claude-sonnet-5-5",
            max_tokens=2000,
            system=SYSTEM,
            messages=messages,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 4}]
        )

        if resp.stop_reason != "pause_turn":
            break

        messages = messages.append({"role" : "assistant", "content" : resp.content})

    return resp

def unpack(resp):

    """
        Unpacks the information returned from the research with Claude API.
    """

    text = "".join(b.text for b in resp.content if b.type == "text")
    sources = []
    for b in resp.content:
        if b.type == "web_search_tool_result" and isinstance(b.content, list):  # list = success
            sources += [{"url": r.url, "title": r.title, "page_age": r.page_age} for r in b.content]
    return text, sources, resp.usage.server_tool_use.web_search_requests



class NewsItem(BaseModel):
    player: str
    category: Literal["injury", "withdrawal", "form", "coaching", "conditions", "other"]
    summary: str          # one sentence
    source_url: str
    published: str        # as stated by source, or "unknown"

class MatchNews(BaseModel):
    match_id: str
    has_relevant_news: bool
    headline: str         # one-line takeaway for the dashboard
    items: list[NewsItem]


def structure(research_text, sources):

    """
        Turns the research into a structured schema.
    """

    resp = client.messages.parse(
        model="claude-haiku-5-5",
        max_tokens=4000,
        output_format=MatchNews,
        messages=[{"role": "user", "content":
            f"Research notes:\n{research_text}\n\n"
            f"Available sources:\n{sources}\n\n"
            "Convert to the schema. Only use source_url values from the list above."}],
    )

    if resp.stop_reason == "max_tokens":
        raise RuntimeError(f"Output truncated for this match; raise max_tokens")

    return resp.parsed_output

def summarise(parsed_output):

    """
        Provides a final paragraph summary of the extracted match news.
    """

    re = client.messages.create(system=SUMMARY_SYSTEM,
                                model="claude-haiku-5-5",
                                max_tokens=2000,
                                messages=[{"role" : "user", "content" : f"Summarise the content of this parsed output {parsed_output}."}])

    return "".join(b.text for b in re.content if b.type == "text")

def news_pipeline(p1, p2, tournament, date):

    """
        Runs the entire news pipeline.
    """

    text, sources, search_requests = unpack(research_match(p1, p2, tournament, date))
    parsed_output = structure(text, sources)
    summary = summarise(parsed_output)

    return summary, parsed_output
