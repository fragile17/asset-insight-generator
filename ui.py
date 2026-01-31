import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Asset Insight Generator", page_icon="📈", layout="wide")
HISTORY_PATH = "output/history.csv"

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://news.bitcoin.com/feed/",
]

analyzer = SentimentIntensityAnalyzer()

# ---------------- HELPERS ----------------
def sentiment_label(score: float) -> str:
    if score >= 0.2:
        return "positive"
    if score <= -0.2:
        return "negative"
    return "neutral"

def label_icon(label: str) -> str:
    return "🟢" if label == "positive" else "🔴" if label == "negative" else "🟡"

def conviction(score: float) -> str:
    s = abs(score)
    if s >= 0.6:
        return "high"
    if s >= 0.3:
        return "medium"
    return "low"

def generate_triggers(text: str, score: float) -> list:
    t = (text or "").lower()
    tags = set()

    if any(k in t for k in ["sec", "regulation", "regulatory", "ban", "lawsuit", "etf", "government", "court"]):
        tags.add("Regulatory")

    if any(k in t for k in ["hack", "breach", "exploit", "security", "attack", "phishing"]):
        tags.add("Exchange / Security")

    if any(k in t for k in ["fed", "interest rate", "rates", "inflation", "macro", "economy", "recession"]):
        tags.add("Macro")

    if any(k in t for k in ["adoption", "partnership", "institutional", "investment", "fund", "bank", "corporate"]):
        tags.add("Adoption / Institutional")

    if abs(score) >= 0.6:
        tags.add("High Volatility")

    return sorted(tags)

def is_high_impact(card: dict) -> bool:
    impact_triggers = {"High Volatility", "Regulatory", "Exchange / Security", "Macro"}
    return (card["conviction"] == "high") or (len(set(card["triggers"]).intersection(impact_triggers)) > 0)

def ensure_output_folder():
    os.makedirs("output", exist_ok=True)

def append_history(cards: list):
    ensure_output_folder()
    now = datetime.now(timezone.utc).isoformat()

    df_new = pd.DataFrame([{
        "logged_at": now,
        "headline": c["headline"],
        "source": c["source"],
        "score": c["score"],
        "label": c["label"],
        "conviction": c["conviction"],
        "triggers": " | ".join(c["triggers"]),
        "link": c["link"]
    } for c in cards])

    if os.path.exists(HISTORY_PATH):
        df_old = pd.read_csv(HISTORY_PATH)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new

    df_all.to_csv(HISTORY_PATH, index=False)

def load_last_24h():
    if not os.path.exists(HISTORY_PATH):
        return None
    df = pd.read_csv(HISTORY_PATH)
    df["logged_at"] = pd.to_datetime(df["logged_at"], utc=True, errors="coerce")
    df = df.dropna(subset=["logged_at"])
    cutoff = pd.Timestamp.now(tz="UTC") - pd.Timedelta(hours=24)
    return df[df["logged_at"] >= cutoff].copy()

def fetch_news(per_feed: int):
    items = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        source = getattr(feed.feed, "title", "Unknown Source")

        for e in feed.entries[:per_feed]:
            title = (e.get("title", "") or "").strip()
            summary = (e.get("summary", "") or "").strip()
            link = (e.get("link", "") or "").strip()
            published = getattr(e, "published", None) or getattr(e, "updated", None)

            items.append({
                "source": source,
                "title": title,
                "summary": summary,
                "link": link,
                "published": published
            })

    # Dedupe
    seen = set()
    out = []
    for it in items:
        key = (it["link"] or "") + (it["title"] or "")
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out

# ---------------- UI ----------------
st.title("📈 AI-Powered Asset Insight Generator")
st.caption("News → sentiment → smart trigger tags → high-impact filter → 24h sentiment trend")

with st.sidebar:
    st.header("Settings")
    asset = st.selectbox("Asset", ["BTC", "ETH", "SOL", "XRP", "BNB"], index=0)
    per_feed = st.slider("Articles per source", 3, 12, 6)
    max_cards = st.slider("Show top insights", 5, 25, 10)
    view_mode = st.radio("View", ["All news", "High-impact only"], index=0)
    run = st.button("Generate")

# Trend panel
st.subheader("Sentiment trend (last 24h)")
hist = load_last_24h()
if hist is None or hist.empty:
    st.caption("No history yet. Click **Generate** a few times to build a 24h trend.")
else:
    hist = hist.sort_values("logged_at").set_index("logged_at")
    hourly_avg = hist["score"].resample("1H").mean()
    hourly_cnt = hist["score"].resample("1H").count()
    st.line_chart(hourly_avg)
    st.caption("Average sentiment score by hour (UTC).")
    st.bar_chart(hourly_cnt)
    st.caption("Number of generated insights per hour (UTC).")

st.divider()

if "cards" not in st.session_state:
    st.session_state.cards = []

if run:
    with st.spinner("Fetching news and generating insights..."):
        news = fetch_news(per_feed)

        cards = []
        for it in news:
            text = f"{it['title']}\n{it['summary']}".strip()
            score = analyzer.polarity_scores(text)["compound"]
            label = sentiment_label(score)
            conv = conviction(score)
            triggers = generate_triggers(text, score)

            # Clean summary (RSS summaries can have HTML)
            summary = (it["summary"] or "").replace("<p>", "").replace("</p>", "").strip()
            if len(summary) > 350:
                summary = summary[:350].rsplit(" ", 1)[0] + "..."

            cards.append({
                "headline": it["title"],
                "source": it["source"],
                "published": it["published"],
                "link": it["link"],
                "score": float(score),
                "label": label,
                "conviction": conv,
                "triggers": triggers,
                "summary": summary
            })

        # Sort: conviction then magnitude
        rank = {"high": 3, "medium": 2, "low": 1}
        cards.sort(key=lambda c: (rank[c["conviction"]], abs(c["score"])), reverse=True)

        st.session_state.cards = cards
        append_history(cards)

cards = st.session_state.cards[:]
if not cards:
    st.info("Click **Generate** to fetch crypto news and show insight cards.")
    st.stop()

if view_mode == "High-impact only":
    cards = [c for c in cards if is_high_impact(c)]

cards = cards[:max_cards]

# Overview table
st.subheader("Overview")
df = pd.DataFrame([{
    "Headline": c["headline"],
    "Source": c["source"],
    "Sentiment": f"{label_icon(c['label'])} {c['label']}",
    "Score": round(c["score"], 2),
    "Conviction": c["conviction"],
    "Triggers": " • ".join(c["triggers"]),
    "Link": c["link"]
} for c in cards])

st.dataframe(df, use_container_width=True, hide_index=True)

# Insight Cards
st.subheader("Insight Cards")
for c in cards:
    badge = f"{label_icon(c['label'])} **{c['label'].upper()}** | score `{c['score']:.2f}` | conviction **{c['conviction']}**"
    with st.container(border=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"### {c['headline']}")
            st.markdown(f"- **Source:** {c['source']}")
            if c.get("published"):
                st.markdown(f"- **Published:** {c['published']}")
            if c.get("link"):
                st.markdown(f"- **Link:** {c['link']}")
        with col2:
            st.markdown(badge)

        if c["triggers"]:
            st.markdown("**Smart Triggers**")
            st.write(" • ".join(c["triggers"]))

        st.markdown("**Summary**")
        st.write(c["summary"])

st.divider()
st.caption("Demo only — not investment advice.")
