# Daily Tennis Report

This repository provides a data and news extraction pipeline for daily tennis matches. It is automated through Github Actions, and produces a Streamlit report available at https://dailytennis-g8lfgnmbq6ycrvvquwfseu.streamlit.app/

   
```
Kaggle dataset + Live Tennis API
              ↓
Feature engineering (DuckDB)
              ↓
News retrieval (Google RSS)
              ↓
Gemini headline summaries
              ↓
JSON files in Data/
              ↓
Streamlit report
```

## Data Extraction
#### kaggle_data_retriever.py
Extracts the most recent Kaggle ATP tennis dataset, which can be found at https://www.kaggle.com/datasets/dissfya/atp-tennis-2000-2023daily-pull/discussion?sort=undefined
The dataset is downloaded into Data/atp_tennis.csv, and is later used to engineer features.

#### live_tennis_api_match_extractor.py
Extracts all tennis matches happening today from the Live Tennis API found at https://livetennisapi.com/. It outputs a structured JSON file of the data for each match that we want. 

## Data Engineering
#### todays_datasets_new.py
Engineers both player-specific and head-to-head features/statistics. Firstly reformats information from the Live Tennis API into the format of the Kaggle data, and then uses a Python to SQL pipeline to produce the desired information. Outputs are JSON files, one for player features, and one for head-to-head.

## News
#### claude_news_extractor.py
Uses Claude API to extract relevant pre-match news through a web search. CURRENTLY NOT IN USE IN THE PIPELINE.

#### news_url_retriever.py
Uses google search RSS to find relevant news articles for upcoming matches.

#### gemini_headlines_summariser
Uses Google Gemini API to summarise the headlines produced by the news retrieval script. Outputs a JSON file, one entry for each player in each match.

## Report
#### st_report_generator.py
File that produces the Streamlit report. Linked to Streamlit community cloud, so automatically runs whenever web app is accessed.

## Pipeline
#### pipeline.py
Links together all of the non-report modules (Extraction, Engineering, News) into one pipeline. Runs daily at 06:17 UTC via GitHub Actions (.github/workflows/daily.yaml), and commits refreshed data to Data/, which triggers the Streamlit app to update.

## Running Locally
   ```pip install -r requirements.txt
   python Scripts/pipeline.py
   streamlit run Scripts/Report/st_report_generator.py
   ```

   Requires these environment variables (in a `.env` file locally, or as GitHub Actions secrets):
   - `LIVE_TENNIS_API_KEY`
   - `GEMINI_API_KEY`