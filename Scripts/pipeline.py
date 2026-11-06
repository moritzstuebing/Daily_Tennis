import Engineering.todays_datasets_new
import Extraction.kaggle_data_retriever, Extraction.live_tennis_api_match_extractor
import News.gemini_headlines_summariser, News.news_url_retriever
import Report.new_st_report_generator
from pathlib import Path
import json


DATA_DIR = Path(__file__).resolve().parent.parent / "Data"

def pipeline(date=None):

    """
        Runs the extraction and engineering pipeline. Date can be specified, the default is today.
    """

    # Data extraction
    Extraction.kaggle_data_retriever.download_historical_data()
    matches_today = Extraction.live_tennis_api_match_extractor.todays_matches_extraction(date)
    with open(DATA_DIR / "matches_today.json", "w") as f:
        json.dump(matches_today, f)

    # News extraction
    news = News.news_url_retriever.get_headlines(matches_today)
    with open(DATA_DIR / "news_urls.json", "w") as f:
        json.dump(news, f)
    summaries = News.gemini_headlines_summariser.summarise_all(news)
    with open(DATA_DIR / "news_summaries.json", "w") as f:
        json.dump(summaries, f)

    # Feature engineering
    matches_today = Engineering.todays_datasets_new.formatting(matches_today, Engineering.todays_datasets_new.tourn_lookup)
    h2h_features = Engineering.todays_datasets_new.create_h2h_datasets(matches_today)
    with open(DATA_DIR / "h2h_features.json", "w") as f:
        json.dump(h2h_features, f)
    player_features = Engineering.todays_datasets_new.create_player_datasets(matches_today)
    with open(DATA_DIR / "player_features.json", "w") as f:
        json.dump(player_features, f)

    return matches_today, player_features, h2h_features, summaries


def main():
    matches_today, player_features, h2h_features, summaries = pipeline()

if __name__ == "__main__":
    main()