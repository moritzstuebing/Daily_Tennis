import Engineering.todays_datasets_new
import Extraction.kaggle_data_retriever, Extraction.live_tennis_api_match_extractor
import News.gemini_headlines_summariser, News.news_url_retriever
from pathlib import Path
import json
from datetime import datetime, timezone

today = datetime.now(timezone.utc).date().isoformat()


DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

def write_status(ok, message, run_date):
    with open(DATA_DIR / "status.json", "w") as f:
        json.dump({"status" : ok, "message" : message, "run_date" : run_date}, f)

def pipeline(date=today):

    """
        Runs the extraction and engineering pipeline. Date can be specified, the default is today.
    """

    # Data extraction
    try:
        Extraction.kaggle_data_retriever.download_historical_data()
        matches_today = Extraction.live_tennis_api_match_extractor.todays_matches_extraction(date)

    # Handling errors during API call
    except Exception as e:
        write_status(False, f"Error when extracting match data: {e}", date)
        raise

    # Handling no new matches today
    if not matches_today:
        write_status(False, "No matches today", date)
        return

    # Only runs if no API errors and matches actually exist today
    with open(DATA_DIR / "matches_today.json", "w") as f:
        json.dump(matches_today, f)

    # News extraction
    try:
        news, player_news_failures = News.news_url_retriever.get_headlines(matches_today)

    # Catches and raises errors in Google RSS extraction
    except Exception as e:
        write_status(False, f"Error when extracting news headlines: {e}", date)
        raise

    # Only runs if no error during headline extraction
    with open(DATA_DIR / "news_urls.json", "w") as f:
        json.dump(news, f)

    try:
        summaries = News.gemini_headlines_summariser.summarise_all(news)
    except Exception as e:
        write_status(False, f"Error when summarising articels: {e}", date)
        raise

    with open(DATA_DIR / "news_summaries.json", "w") as f:
        json.dump(summaries, f)

    # Feature engineering
    try:
        matches_today = Engineering.todays_datasets_new.formatting(matches_today, Engineering.todays_datasets_new.tourn_lookup)
        h2h_features = Engineering.todays_datasets_new.create_h2h_datasets(matches_today)
        player_features = Engineering.todays_datasets_new.create_player_datasets(matches_today)
    except Exception as e:
        write_status(False, f"Error during feature engineering: {e!r}, date")
        raise

    with open(DATA_DIR / "h2h_features.json", "w") as f:
        json.dump(h2h_features, f)
    with open(DATA_DIR / "player_features.json", "w") as f:
        json.dump(player_features, f)

    write_status(True, "All good", date)

    return matches_today, player_features, h2h_features, summaries, player_news_failures


def main():
    matches_today, player_features, h2h_features, summaries, news_failures = pipeline()

if __name__ == "__main__":
    main()