# AI-Powered Asset Insight Generator

An AI-driven, customer-facing analytics tool that transforms raw crypto market news into
clear, actionable investment insights. The system aggregates multi-source news data,
analyzes sentiment, assigns smart trigger tags, and highlights high-impact developments
to help users quickly understand market context.

This project is designed with a strong focus on **clarity, signal prioritization, and
customer usability**, similar to real fintech investment platforms.

---

## Key Features

- **Multi-source News Aggregation**
  - Pulls real-time crypto news from trusted RSS sources (CoinDesk, CoinTelegraph, Bitcoin.com)

- **AI-based Sentiment Analysis**
  - Classifies news as positive, neutral, or negative using NLP sentiment scoring

- **Smart Trigger Tagging**
  - Automatically labels news with contextual tags such as:
    - Regulatory
    - Macro-economic
    - Exchange / Security
    - Adoption / Institutional
    - High Volatility

- **High-Impact Signal Filtering**
  - Toggle between *All News* and *High-Impact Only* insights
  - Prioritizes high-conviction and market-moving events

- **24-Hour Sentiment Trend Tracking**
  - Stores generated insights and visualizes rolling sentiment trends over time

- **Customer-Friendly Insight Cards**
  - Clean summaries designed to be easily understood by non-technical users

---

## Tech Stack

- **Python**
- **Streamlit** (UI & interaction layer)
- **Pandas** (data handling & trend analysis)
- **VADER Sentiment Analyzer** (NLP sentiment scoring)
- **RSS Feeds** (real-time market news ingestion)

---

## How It Works (High-Level)

1. Fetches live crypto news from multiple sources  
2. Cleans and processes textual content  
3. Performs sentiment analysis and conviction scoring  
4. Assigns smart trigger tags based on contextual keywords  
5. Filters and ranks insights by impact  
6. Displays results via an interactive Streamlit UI  
7. Logs insights to build a rolling 24-hour sentiment trend  

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run ui.py
