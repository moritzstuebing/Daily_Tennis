import Engineering.todays_datasets_new
import Extraction.kaggle_data_retriever, Extraction.live_tennis_api_match_extractor
import News.gemini_headlines_summariser, News.news_url_retriever
import Report.new_st_report_generator

def pipeline(date=None):

    """
        Runs the extraction and engineering pipeline. Date can be specified, the default is today.
    """

    # Data extraction
    Extraction.kaggle_data_retriever.download_historical_data()
    matches_today = Extraction.live_tennis_api_match_extractor.todays_matches_extraction(date)

    # News extraction
    news = News.news_url_retriever.get_headlines(matches_today)
    summaries = News.gemini_headlines_summariser.summarise_all(news)

    # Feature engineering
    h2h_features = Engineering.todays_datasets_new.create_h2h_datasets(matches_today)
    player_features = Engineering.todays_datasets_new.create_player_datasets(matches_today)

    return matches_today, player_features, h2h_features, summaries