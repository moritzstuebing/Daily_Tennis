from google import genai
from dotenv import load_dotenv
from pathlib import Path
import json

load_dotenv()
DATA_DIR = Path(__file__).resolve().parent.parent / "Data"
client = genai.Client()

with open(DATA_DIR / "news_urls.json") as f:
    news = json.load(f)

SYSTEM = (
    "You summarise recent tennis news for a match-preview page. "
    "Use only the headlines provided. In 2-3 sentences, note injuries, "
    "withdrawals, form and recent results. If nothing is relevant, say so."
)

def summarise(player, articles):
    headlines = "\n".join(
        f"- {a['title']} ({a['source']}, {a['published']})" for a in articles
    )
    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        system_instruction=SYSTEM,
        input=f"Recent headlines about {player}:\n{headlines}",
    )
    return interaction.output_text

summaries = {}
for item in news.items():
    summaries[item[0]] = summarise(item[0], item[1])

with open(DATA_DIR / "player_summaries.json", "w") as f:
    json.dump(summaries, f)

