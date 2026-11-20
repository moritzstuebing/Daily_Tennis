from google import genai
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from google.genai import errors

load_dotenv()
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "Data"
client = genai.Client()

SYSTEM = (
    "You summarise recent tennis news for a match-preview page. "
    "Use only the headlines provided. In 2-3 sentences, note injuries, "
    "withdrawals, form and recent results. If nothing is relevant, say so."
)

def summarise(player, articles, retries=3):
    headlines = "\n".join(
        f"- {a['title']} ({a['source']}, {a['published']})" for a in articles
    )

    for attempt in range(retries):
        try:
            interaction = client.interactions.create(
            model="gemini-3.5-flash-lite",
            system_instruction=SYSTEM,
            input=f"Recent headlines about {player}:\n{headlines}",
            )
            text = interaction.output_text

            if not text:
                raise ValueError("Empty response (maybe blocked)")
            return text

        except errors.APIError as e:
            if e.code in (429, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt * 5)
                continue
            raise

def summarise_all(news):
    summaries = {}
    for item in news.items():
        if item[1]: # only if articles exist
            try:
                summaries[item[0]] = summarise(item[0], item[1])
            except Exception:
                raise
        else:
            summaries[item[0]] = f"No articles for {item[0]}"

    return summaries

def main():
    with open(DATA_DIR / "news_urls.json") as f:
        news = json.load(f)

    summaries = summarise_all(news)

    with open(DATA_DIR / "player_summaries.json", "w") as f:
        json.dump(summaries, f)


if __name__ == "__main__":
    main()

