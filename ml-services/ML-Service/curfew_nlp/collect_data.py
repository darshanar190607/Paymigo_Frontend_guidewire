"""
GigKavach Curfew NLP — Hybrid Data Collection
═══════════════════════════════════════════════════════════════
SOURCES (12 total — each retried up to 12 times independently):

CURFEW / STRIKE headlines:
  1.  NewsAPI.org          — keyword search for curfew/Section144/bandh
  2.  Google News RSS      — 8 curfew/strike queries (no key needed)
  3.  PIB RSS              — Press Information Bureau official feeds
  4.  AIR RSS              — All India Radio news feeds
  5.  Hindu RSS            — thehindu.com (open RSS)
  6.  NDTV RSS             — ndtv.com news feed
  7.  India Today RSS      — indiatoday.in (open RSS)
  8.  Times of India RSS   — timesofindia.com (open RSS)
  9.  Wayback/CDX API      — CommonCrawl historical headlines

NORMAL headlines:
  10. Google News RSS      — municipal / civic / development queries
  11. PIB RSS              — infrastructure / health / education feeds
  12. Synthetic generation — balanced fill-up to target counts

CHECKPOINT: Saves to CSV after EVERY source. Resume-safe.
═══════════════════════════════════════════════════════════════
Run: python 01_collect_data.py
"""

import os, sys, time, json, re
import feedparser
import pandas as pd
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    CHECKPOINT_CURFEW, CHECKPOINT_NORMAL, FINAL_RAW_CSV,
    NEWSAPI_KEY, RANDOM_STATE, TARGET_CURFEW, TARGET_STRIKE, TARGET_NORMAL,
    DATA_RAW,
)
from utils import (
    robust_get, save_checkpoint, load_checkpoint,
    get_existing_texts, normalise_row, deduplicate_df, get_logger,
)

np.random.seed(RANDOM_STATE)
logger = get_logger("collect")


# ══════════════════════════════════════════════════════════════════════
# HELPER: parse a feedparser feed into normalised rows
# ══════════════════════════════════════════════════════════════════════

CURFEW_KW = {
    "curfew", "section 144", "prohibitory", "shutdown", "bandh",
    "hartal", "chakka jam", "rail roko", "internet shutdown",
    "night curfew", "day curfew", "prohibitory order",
}
STRIKE_KW = {
    "strike", "bandh", "hartal", "chakka jam", "transport strike",
    "delivery strike", "truck strike", "auto strike", "bus strike",
    "rail roko", "workers strike",
}


def classify_headline(text: str) -> tuple[int, int, int]:
    """Returns (label_curfew, label_strike, label_normal) from headline text."""
    t = text.lower()
    is_curfew = any(k in t for k in CURFEW_KW)
    is_strike = any(k in t for k in STRIKE_KW)
    if is_curfew:
        return 1, 0, 0
    if is_strike:
        return 0, 1, 0
    return 0, 0, 1


def parse_feed_entries(feed, source_name: str, existing: set) -> list[dict]:
    """Parse feedparser result into normalised rows, skipping already-collected texts."""
    rows = []
    for entry in feed.entries:
        title = getattr(entry, "title", "").strip()
        if not title or len(title) < 10:
            continue
        # skip if already collected
        import hashlib
        h = hashlib.md5(title.lower().strip().encode()).hexdigest()
        if h in existing:
            continue
        pub = getattr(entry, "published", str(datetime.now().date()))
        lc, ls, ln = classify_headline(title)
        rows.append(normalise_row(
            text=title, source=source_name, published_at=pub,
            label_curfew=lc, label_strike=ls, label_normal=ln,
        ))
    return rows


# ══════════════════════════════════════════════════════════════════════
# SOURCE 1: NewsAPI.org
# ══════════════════════════════════════════════════════════════════════

NEWSAPI_CURFEW_QUERIES = [
    "curfew India",
    "Section 144 India",
    "prohibitory orders India",
    "internet shutdown India",
    "night curfew India city",
    "bandh India state",
    "complete shutdown India",
    "curfew lifted India",
]

NEWSAPI_STRIKE_QUERIES = [
    "transport strike India delivery",
    "bandh hartal India",
    "chakka jam India",
    "truck strike India",
    "auto strike India city",
    "bus workers strike India",
]

NEWSAPI_NORMAL_QUERIES = [
    "municipality road repair India",
    "water supply scheme India city",
    "school reopening India",
    "hospital inauguration India",
    "smart city project India",
    "local election campaign India",
    "metro expansion India",
    "power outage India city",
]


def collect_newsapi(checkpoint_path: str, target_type: str = "curfew") -> int:
    """
    Collect from NewsAPI.org. Saves checkpoint after each query.
    target_type: "curfew" | "strike" | "normal"
    """
    if NEWSAPI_KEY == "27d940b61f2d4d30a8f08a0bf8b3c2cd":
        logger.warning("[NEWSAPI] Key not set — skipping NewsAPI source.")
        return 0

    queries = {
        "curfew": NEWSAPI_CURFEW_QUERIES,
        "strike": NEWSAPI_STRIKE_QUERIES,
        "normal": NEWSAPI_NORMAL_QUERIES,
    }[target_type]

    BASE_URL   = "https://newsapi.org/v2/everything"
    collected  = 0
    existing   = get_existing_texts(checkpoint_path)

    for i, q in enumerate(queries, 1):
        logger.info(f"[NEWSAPI/{target_type.upper()}] Query {i}/{len(queries)}: '{q}'")
        for page in range(1, 4):   # up to 3 pages per query
            resp = robust_get(
                BASE_URL,
                params={
                    "q": q, "language": "en",
                    "pageSize": 100, "page": page,
                    "sortBy": "publishedAt",
                    "apiKey": NEWSAPI_KEY,
                },
                source_label=f"NEWSAPI-{target_type}",
            )
            if resp is None:
                break
            data = resp.json()
            if data.get("status") != "ok":
                logger.warning(f"  [NEWSAPI] Non-ok status: {data.get('message','')}")
                break
            articles = data.get("articles", [])
            if not articles:
                break

            rows = []
            import hashlib
            for a in articles:
                title = (a.get("title") or "").strip()
                if not title or len(title) < 10:
                    continue
                h = hashlib.md5(title.lower().strip().encode()).hexdigest()
                if h in existing:
                    continue
                pub = a.get("publishedAt", "")
                lc, ls, ln = classify_headline(title)
                row = normalise_row(
                    text=title,
                    source=a.get("source", {}).get("name", "NewsAPI"),
                    published_at=pub,
                    label_curfew=lc, label_strike=ls, label_normal=ln,
                )
                rows.append(row)
                existing.add(h)

            n = save_checkpoint(rows, checkpoint_path, label=f"NEWSAPI/{target_type}/q{i}/p{page}")
            collected += len(rows)
            time.sleep(0.4)

    logger.info(f"[NEWSAPI/{target_type.upper()}] Done — collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 2: Google News RSS  (no key needed)
# ══════════════════════════════════════════════════════════════════════

GOOGLE_RSS_CURFEW = [
    "curfew+India",
    "Section+144+India",
    "bandh+India",
    "prohibitory+order+India",
    "internet+shutdown+India",
    "hartal+India",
    "chakka+jam+India",
    "night+curfew+India+city",
    "complete+shutdown+India",
    "curfew+lifted+India+state",
]

GOOGLE_RSS_STRIKE = [
    "transport+strike+India",
    "delivery+workers+strike+India",
    "truck+strike+India",
    "auto+strike+India",
    "bus+strike+India",
    "rail+roko+India",
]

GOOGLE_RSS_NORMAL = [
    "water+supply+scheme+India+municipal",
    "road+repair+India+city+PWD",
    "hospital+inauguration+India",
    "school+reopening+India+state",
    "metro+project+India+city",
    "smart+city+India+infrastructure",
    "election+campaign+India+local",
    "power+plant+India+commissioned",
    "bridge+inauguration+India",
    "park+development+India+city",
]

GOOGLE_BASE = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def collect_google_rss(checkpoint_path: str, target_type: str = "curfew") -> int:
    queries_map = {
        "curfew": GOOGLE_RSS_CURFEW,
        "strike": GOOGLE_RSS_STRIKE,
        "normal": GOOGLE_RSS_NORMAL,
    }
    queries   = queries_map[target_type]
    collected = 0
    existing  = get_existing_texts(checkpoint_path)

    for i, q in enumerate(queries, 1):
        url = GOOGLE_BASE.format(q=q)
        logger.info(f"[GOOGLE-RSS/{target_type.upper()}] Feed {i}/{len(queries)}: {q}")

        # feedparser doesn't support retries natively — use robust_get then feedparser
        resp = robust_get(url, source_label=f"GOOGLE-RSS-{target_type}")
        if resp is None:
            continue

        feed = feedparser.parse(resp.content)
        rows = parse_feed_entries(feed, source_name="Google News", existing=existing)

        # Re-label based on query intent
        for r in rows:
            if target_type == "curfew" and r["label_curfew"] == 0 and r["label_strike"] == 0:
                r["label_curfew"] = 1   # query-anchored positive
            elif target_type == "normal":
                r["label_curfew"] = 0
                r["label_strike"] = 0
                r["label_normal"] = 1

        n = save_checkpoint(rows, checkpoint_path, label=f"GOOGLE-RSS/{target_type}/q{i}")
        import hashlib
        for r in rows:
            existing.add(hashlib.md5(r["text"].lower().strip().encode()).hexdigest())
        collected += len(rows)
        time.sleep(1.0)   # be gentle with Google

    logger.info(f"[GOOGLE-RSS/{target_type.upper()}] Done — collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 3: PIB RSS  (Press Information Bureau — official govt orders)
# ══════════════════════════════════════════════════════════════════════

PIB_FEEDS = [
    ("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",   "PIB-MHA"),
    ("https://pib.gov.in/RssMain.aspx?ModId=3&Lang=1&Regid=3",   "PIB-Home"),
    ("https://pib.gov.in/RssMain.aspx?ModId=4&Lang=1&Regid=3",   "PIB-Defence"),
    ("https://pib.gov.in/RssMain.aspx?ModId=22&Lang=1&Regid=3",  "PIB-Urban"),
    ("https://pib.gov.in/RssMain.aspx?ModId=14&Lang=1&Regid=3",  "PIB-Transport"),
]

def collect_pib_rss(checkpoint_curfew: str, checkpoint_normal: str) -> int:
    collected = 0
    existing_c = get_existing_texts(checkpoint_curfew)
    existing_n = get_existing_texts(checkpoint_normal)

    for feed_url, feed_name in PIB_FEEDS:
        logger.info(f"[PIB-RSS] Feed: {feed_name}")
        resp = robust_get(feed_url, source_label=feed_name)
        if resp is None:
            continue
        feed = feedparser.parse(resp.content)

        curfew_rows = []; normal_rows = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            if not title or len(title) < 10:
                continue
            pub = getattr(entry, "published", "")
            lc, ls, ln = classify_headline(title)
            import hashlib
            h = hashlib.md5(title.lower().strip().encode()).hexdigest()
            row = normalise_row(text=title, source=feed_name, published_at=pub,
                                label_curfew=lc, label_strike=ls, label_normal=ln)
            if lc == 1 or ls == 1:
                if h not in existing_c:
                    curfew_rows.append(row); existing_c.add(h)
            else:
                if h not in existing_n:
                    normal_rows.append(row); existing_n.add(h)

        save_checkpoint(curfew_rows, checkpoint_curfew, label=feed_name)
        save_checkpoint(normal_rows, checkpoint_normal, label=f"{feed_name}-normal")
        collected += len(curfew_rows) + len(normal_rows)
        time.sleep(0.5)

    logger.info(f"[PIB-RSS] Done — collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 4: AIR (All India Radio) RSS News Feeds
# ══════════════════════════════════════════════════════════════════════

AIR_FEEDS = [
    ("https://newsonair.gov.in/rss/english-news.xml",    "AIR-English"),
    ("https://newsonair.gov.in/rss/national-news.xml",   "AIR-National"),
]

def collect_air_rss(checkpoint_curfew: str, checkpoint_normal: str) -> int:
    collected = 0
    existing_c = get_existing_texts(checkpoint_curfew)
    existing_n = get_existing_texts(checkpoint_normal)

    for feed_url, feed_name in AIR_FEEDS:
        logger.info(f"[AIR-RSS] Feed: {feed_name}")
        resp = robust_get(feed_url, source_label=feed_name)
        if resp is None:
            continue
        feed = feedparser.parse(resp.content)
        curfew_rows = []; normal_rows = []
        import hashlib
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            if not title or len(title) < 10:
                continue
            h = hashlib.md5(title.lower().strip().encode()).hexdigest()
            pub = getattr(entry, "published", "")
            lc, ls, ln = classify_headline(title)
            row = normalise_row(text=title, source=feed_name, published_at=pub,
                                label_curfew=lc, label_strike=ls, label_normal=ln)
            if lc == 1 or ls == 1:
                if h not in existing_c:
                    curfew_rows.append(row); existing_c.add(h)
            else:
                if h not in existing_n:
                    normal_rows.append(row); existing_n.add(h)

        save_checkpoint(curfew_rows, checkpoint_curfew, label=feed_name)
        save_checkpoint(normal_rows, checkpoint_normal, label=f"{feed_name}-normal")
        collected += len(curfew_rows) + len(normal_rows)
        time.sleep(0.5)
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 5-8: Indian News RSS Feeds (Hindu, NDTV, India Today, TOI)
# ══════════════════════════════════════════════════════════════════════

NEWS_RSS_FEEDS = [
    ("https://www.thehindu.com/news/national/feeder/default.rss",  "TheHindu"),
    ("https://feeds.feedburner.com/ndtvnews-india-news",           "NDTV"),
    ("https://www.indiatoday.in/rss/1206578",                      "IndiaToday"),
    ("https://timesofindia.indiatimes.com/rss/804809347.cms",      "TOI-India"),
    ("https://www.deccanherald.com/rss/national.rss",               "DeccanHerald"),
    ("https://indianexpress.com/section/india/feed/",              "IndianExpress"),
]

def collect_news_rss(checkpoint_curfew: str, checkpoint_normal: str) -> int:
    collected = 0
    existing_c = get_existing_texts(checkpoint_curfew)
    existing_n = get_existing_texts(checkpoint_normal)

    for feed_url, feed_name in NEWS_RSS_FEEDS:
        logger.info(f"[NEWS-RSS] Feed: {feed_name}")
        resp = robust_get(feed_url, source_label=feed_name)
        if resp is None:
            continue
        feed = feedparser.parse(resp.content)
        curfew_rows = []; normal_rows = []
        import hashlib
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            if not title or len(title) < 10:
                continue
            h = hashlib.md5(title.lower().strip().encode()).hexdigest()
            pub = getattr(entry, "published", "")
            lc, ls, ln = classify_headline(title)
            row = normalise_row(text=title, source=feed_name, published_at=pub,
                                label_curfew=lc, label_strike=ls, label_normal=ln)
            if lc == 1 or ls == 1:
                if h not in existing_c:
                    curfew_rows.append(row); existing_c.add(h)
            else:
                if h not in existing_n:
                    normal_rows.append(row); existing_n.add(h)

        save_checkpoint(curfew_rows, checkpoint_curfew, label=feed_name)
        save_checkpoint(normal_rows, checkpoint_normal, label=f"{feed_name}-normal")
        collected += len(curfew_rows) + len(normal_rows)
        time.sleep(0.8)

    logger.info(f"[NEWS-RSS] Done — collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 9: Wayback Machine CDX API  (historical archived news)
# ══════════════════════════════════════════════════════════════════════

WAYBACK_QUERIES = [
    ("thehindu.com/news/national/*curfew*",          "WB-Hindu-Curfew"),
    ("ndtv.com/india-news/*section-144*",            "WB-NDTV-S144"),
    ("thehindu.com/news/national/*bandh*",            "WB-Hindu-Bandh"),
    ("timesofindia.indiatimes.com/india/*strike*",   "WB-TOI-Strike"),
    ("indiatoday.in/india/*curfew*",                 "WB-IT-Curfew"),
]

def collect_wayback(checkpoint_curfew: str) -> int:
    """Use Wayback CDX API to pull historical curfew/strike headline URLs."""
    BASE   = "http://web.archive.org/cdx/search/cdx"
    collected = 0
    existing = get_existing_texts(checkpoint_curfew)

    for pattern, label in WAYBACK_QUERIES:
        logger.info(f"[WAYBACK] Pattern: {pattern}")
        resp = robust_get(
            BASE,
            params={
                "url": pattern,
                "output": "json",
                "fl": "original,timestamp,statuscode",
                "filter": "statuscode:200",
                "limit": 200,
                "from": "20190101",
                "to": "20240101",
            },
            source_label=label,
        )
        if resp is None:
            continue

        try:
            records = resp.json()
            if len(records) <= 1:   # only header row
                continue
            rows = []
            import hashlib
            for rec in records[1:]:   # skip header
                url, ts, _ = rec[0], rec[1], rec[2]
                # Extract headline from URL slug (proxy for title)
                slug = url.split("/")[-1].replace("-", " ").replace("_", " ")
                slug = re.sub(r"\.(html?|php|aspx)$", "", slug, flags=re.I).strip()
                if len(slug) < 15:
                    continue
                # Title-case it as a headline proxy
                title = slug.title()
                h = hashlib.md5(title.lower().strip().encode()).hexdigest()
                if h in existing:
                    continue
                pub = ts[:4] + "-" + ts[4:6] + "-" + ts[6:8]
                lc, ls, ln = classify_headline(title)
                # Force curfew label if slug contains curfew keywords
                if any(k.replace(" ","-") in url.lower() or k in url.lower()
                       for k in ["curfew","section-144","bandh","strike","shutdown"]):
                    lc, ls, ln = (1, 0, 0) if "curfew" in url.lower() else (0, 1, 0)
                rows.append(normalise_row(
                    text=title, source="WaybackMachine",
                    published_at=pub,
                    label_curfew=lc, label_strike=ls, label_normal=ln,
                ))
                existing.add(h)

            n = save_checkpoint(rows, checkpoint_curfew, label=label)
            collected += len(rows)
        except Exception as e:
            logger.warning(f"  [WAYBACK] Parse error for {label}: {e}")
        time.sleep(1.0)

    logger.info(f"[WAYBACK] Done — collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 10: Indian Kanoon (legal order RSS — Section 144 verdicts)
# ══════════════════════════════════════════════════════════════════════

def collect_indiankanoon(checkpoint_curfew: str) -> int:
    """Fetch Section 144 / curfew legal order summaries from IndianKanoon RSS."""
    KANOON_QUERIES = [
        "https://indiankanoon.org/search/?formInput=section+144+curfew&pagenum=0",
        "https://indiankanoon.org/search/?formInput=prohibitory+order+144&pagenum=0",
        "https://indiankanoon.org/search/?formInput=internet+shutdown+order&pagenum=0",
    ]
    collected = 0
    existing  = get_existing_texts(checkpoint_curfew)

    for url in KANOON_QUERIES:
        resp = robust_get(url, source_label="IndianKanoon",
                          headers={"User-Agent": "Mozilla/5.0 (research bot)"})
        if resp is None:
            continue
        # Simple regex extract of case titles from the response
        titles = re.findall(r'<div class="result_title".*?>(.*?)</div>', resp.text, re.S)
        rows = []
        import hashlib
        for raw_title in titles[:50]:
            title = re.sub(r"<.*?>", "", raw_title).strip()
            if len(title) < 10:
                continue
            h = hashlib.md5(title.lower().strip().encode()).hexdigest()
            if h in existing:
                continue
            rows.append(normalise_row(
                text=title, source="IndianKanoon", published_at="",
                label_curfew=1, label_strike=0, label_normal=0,
            ))
            existing.add(h)
        save_checkpoint(rows, checkpoint_curfew, label="IndianKanoon")
        collected += len(rows)
        time.sleep(1.0)

    logger.info(f"[INDIANKANOON] Collected {collected} rows")
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 11: Govt Press Release Search (data.gov.in RSS-style)
# ══════════════════════════════════════════════════════════════════════

DATAGOV_FEEDS = [
    ("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=3&Regid=3", "PIB-Tamil"),   # Tamil
    ("https://pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3", "PIB-Hindi"),
    ("https://pib.gov.in/RssMain.aspx?ModId=23&Lang=1&Regid=3", "PIB-Law"),
]

def collect_govt_feeds(checkpoint_curfew: str, checkpoint_normal: str) -> int:
    collected = 0
    existing_c = get_existing_texts(checkpoint_curfew)
    existing_n = get_existing_texts(checkpoint_normal)
    import hashlib

    for feed_url, feed_name in DATAGOV_FEEDS:
        logger.info(f"[GOVT-FEED] {feed_name}")
        resp = robust_get(feed_url, source_label=feed_name)
        if resp is None:
            continue
        feed = feedparser.parse(resp.content)
        curfew_rows = []; normal_rows = []
        for entry in feed.entries:
            title = getattr(entry, "title", "").strip()
            if len(title) < 5:
                continue
            h = hashlib.md5(title.lower().strip().encode()).hexdigest()
            pub = getattr(entry, "published", "")
            lc, ls, ln = classify_headline(title)
            row = normalise_row(text=title, source=feed_name, published_at=pub,
                                label_curfew=lc, label_strike=ls, label_normal=ln)
            if lc == 1 or ls == 1:
                if h not in existing_c:
                    curfew_rows.append(row); existing_c.add(h)
            else:
                if h not in existing_n:
                    normal_rows.append(row); existing_n.add(h)

        save_checkpoint(curfew_rows, checkpoint_curfew, label=feed_name)
        save_checkpoint(normal_rows, checkpoint_normal, label=f"{feed_name}-normal")
        collected += len(curfew_rows) + len(normal_rows)
        time.sleep(0.5)
    return collected


# ══════════════════════════════════════════════════════════════════════
# SOURCE 12: SYNTHETIC GENERATION  (fills gap to target counts)
# ══════════════════════════════════════════════════════════════════════

INDIAN_CITIES = [
    "Chennai", "Coimbatore", "Madurai", "Trichy", "Salem",
    "Tiruppur", "Mumbai", "Delhi", "Bengaluru", "Hyderabad",
    "Kolkata", "Ahmedabad", "Jaipur", "Surat", "Pune",
    "Bhopal", "Nagpur", "Lucknow", "Kanpur", "Agra",
    "Varanasi", "Patna", "Guwahati", "Kochi", "Visakhapatnam",
]

CURFEW_TEMPLATES = [
    "Curfew imposed in {city} following {reason}; prohibitory orders under Section 144",
    "Section 144 CrPC imposed in {city} district amid {reason}; gatherings banned",
    "Indefinite curfew in {city} after violent {reason}; security forces deployed",
    "{city} on edge as curfew extended for 48 hours after {reason}",
    "Prohibitory orders in {city} extended till further notice following {reason}",
    "Night curfew imposed in {city} from 10 PM to 6 AM due to {reason}",
    "Complete shutdown in {city} after {reason}; Section 144 clamped",
    "Internet services suspended in {city} district amid {reason} curfew",
    "{city} curfew lifted after {days} days; normalcy slowly returning",
    "Section 144 imposed in {city} ahead of {event}; prohibitory orders in force",
    "Curfew relaxed for {hours} hours in {city} for essential supplies",
    "Government imposes Section 144 in {city} following clashes during {reason}",
]

STRIKE_TEMPLATES = [
    "{city} transport workers call indefinite strike from Monday over {reason}",
    "Auto-rickshaw drivers in {city} go on strike demanding {reason}",
    "Gig delivery workers in {city} protest against {reason}; strike called",
    "Truck operators launch indefinite bandh in {city} over {reason}",
    "Nationwide transport bandh: {city} gig workers join chakka jam over {reason}",
    "Bus services hit in {city} as workers strike over {reason}",
    "Hartal called in {city} over {reason}; gig platforms affected",
    "Rail Roko agitation disrupts {city} transport links over {reason}",
    "{city} delivery workers threaten strike if {reason} not resolved",
    "Trade unions call {city} bandh on {date}; gig sector joins over {reason}",
]

NORMAL_TEMPLATES = [
    "{city} municipal corporation launches {project} scheme worth ₹{amount} crore",
    "PWD begins road repair work on {city} highway; commuters advised alternate route",
    "New water supply project inaugurated in {city} residential areas",
    "{city} Smart City Mission project inaugurated by district collector",
    "Schools in {city} to reopen from {date} after {reason}",
    "{city} metro rail expansion work begins; {km} km stretch approved",
    "Civic body conducts anti-encroachment drive in {city} market areas",
    "{city} to get {number} new hospitals under government health scheme",
    "Power outage in parts of {city} for {hours} hours maintenance on {date}",
    "Local body elections in {city} district scheduled for {date}",
    "{city} receives ₹{amount} crore under SMART Cities Mission for {project}",
    "District administration conducts review meeting on {project} in {city}",
]

CURFEW_REASONS = [
    "communal tensions", "violent protests", "political rally clash",
    "mob violence", "religious unrest", "stone-pelting incident",
    "student protests", "farmers agitation", "election-related violence",
    "rumour-triggered violence",
]

STRIKE_REASONS = [
    "fuel price hike", "increase in insurance premiums", "low platform rates",
    "lack of workers protection policy", "arbitrary deactivation",
    "gig workers rights", "algorithm-based penalisation",
    "no income protection during disruptions", "high commission deduction",
    "inadequate incentives during peak hours",
]

NORMAL_PROJECTS = [
    "underground drainage", "rainwater harvesting", "solid waste management",
    "LED street lighting", "CCTV surveillance", "park beautification",
    "flyover construction", "bus rapid transit", "cycling track",
]

EVENTS = ["Republic Day", "Independence Day", "state elections", "sensitive court verdict"]


def generate_synthetic(n_curfew: int, n_strike: int, n_normal: int) -> tuple[list, list]:
    """Generate synthetic headlines to fill remaining target counts."""
    import random
    random.seed(RANDOM_STATE)
    curfew_rows = []
    strike_rows = []
    normal_rows = []

    dates = pd.date_range("2019-01-01", "2024-06-01", freq="3D")

    for i in range(n_curfew):
        city   = random.choice(INDIAN_CITIES)
        tmpl   = random.choice(CURFEW_TEMPLATES)
        reason = random.choice(CURFEW_REASONS)
        event  = random.choice(EVENTS)
        date   = str(random.choice(dates).date())
        text   = tmpl.format(
            city=city, reason=reason, event=event,
            days=random.randint(1, 7), hours=random.randint(2, 8),
        )
        curfew_rows.append(normalise_row(
            text=text, source="Synthetic",
            published_at=date,
            label_curfew=1, label_strike=0, label_normal=0,
            city=city,
        ))

    for i in range(n_strike):
        city   = random.choice(INDIAN_CITIES)
        tmpl   = random.choice(STRIKE_TEMPLATES)
        reason = random.choice(STRIKE_REASONS)
        date   = str(random.choice(dates).date())
        text   = tmpl.format(
            city=city, reason=reason,
            date=date,
        )
        strike_rows.append(normalise_row(
            text=text, source="Synthetic",
            published_at=date,
            label_curfew=0, label_strike=1, label_normal=0,
            city=city,
        ))

    for i in range(n_normal):
        city    = random.choice(INDIAN_CITIES)
        tmpl    = random.choice(NORMAL_TEMPLATES)
        project = random.choice(NORMAL_PROJECTS)
        date    = str(random.choice(dates).date())
        text    = tmpl.format(
            city=city, project=project,
            amount=random.randint(10, 500),
            km=random.randint(5, 50),
            number=random.randint(5, 50),
            hours=random.randint(2, 8),
            date=date,
            reason="maintenance work",
        )
        normal_rows.append(normalise_row(
            text=text, source="Synthetic",
            published_at=date,
            label_curfew=0, label_strike=0, label_normal=1,
            city=city,
        ))

    return curfew_rows + strike_rows, normal_rows


# ══════════════════════════════════════════════════════════════════════
# MAIN  —  runs all 12 sources in sequence, checkpointing after each
# ══════════════════════════════════════════════════════════════════════

def count_label(checkpoint_path: str, col: str) -> int:
    if not os.path.exists(checkpoint_path):
        return 0
    df = pd.read_csv(checkpoint_path)
    return int(df[col].sum()) if col in df.columns else 0


if __name__ == "__main__":
    logger.info("=" * 65)
    logger.info("  GigKavach Curfew NLP — Data Collection Pipeline")
    logger.info("  12 sources  |  Up to 12 retries per source")
    logger.info("  Checkpointed after every source")
    logger.info("=" * 65)

    # ── Source 1: NewsAPI ────────────────────────────────────────────
    logger.info("\n[SOURCE 1/12] NewsAPI — Curfew headlines")
    collect_newsapi(CHECKPOINT_CURFEW, target_type="curfew")
    logger.info("[SOURCE 1/12] NewsAPI — Strike headlines")
    collect_newsapi(CHECKPOINT_CURFEW, target_type="strike")
    logger.info("[SOURCE 1/12] NewsAPI — Normal headlines")
    collect_newsapi(CHECKPOINT_NORMAL, target_type="normal")

    # ── Source 2: Google News RSS ─────────────────────────────────────
    logger.info("\n[SOURCE 2/12] Google News RSS — Curfew")
    collect_google_rss(CHECKPOINT_CURFEW, target_type="curfew")
    logger.info("[SOURCE 2/12] Google News RSS — Strike")
    collect_google_rss(CHECKPOINT_CURFEW, target_type="strike")
    logger.info("[SOURCE 2/12] Google News RSS — Normal")
    collect_google_rss(CHECKPOINT_NORMAL, target_type="normal")

    # ── Source 3: PIB RSS ─────────────────────────────────────────────
    logger.info("\n[SOURCE 3/12] PIB RSS — Govt press releases")
    collect_pib_rss(CHECKPOINT_CURFEW, CHECKPOINT_NORMAL)

    # ── Source 4: AIR RSS ─────────────────────────────────────────────
    logger.info("\n[SOURCE 4/12] All India Radio RSS")
    collect_air_rss(CHECKPOINT_CURFEW, CHECKPOINT_NORMAL)

    # ── Source 5-8: Indian News RSS ───────────────────────────────────
    logger.info("\n[SOURCE 5-8/12] Indian News RSS (Hindu/NDTV/IndiaToday/TOI)")
    collect_news_rss(CHECKPOINT_CURFEW, CHECKPOINT_NORMAL)

    # ── Source 9: Wayback Machine CDX ─────────────────────────────────
    logger.info("\n[SOURCE 9/12] Wayback Machine CDX — Historical")
    collect_wayback(CHECKPOINT_CURFEW)

    # ── Source 10: IndianKanoon ───────────────────────────────────────
    logger.info("\n[SOURCE 10/12] IndianKanoon — Section 144 legal orders")
    collect_indiankanoon(CHECKPOINT_CURFEW)

    # ── Source 11: Govt additional feeds ─────────────────────────────
    logger.info("\n[SOURCE 11/12] Govt additional RSS feeds")
    collect_govt_feeds(CHECKPOINT_CURFEW, CHECKPOINT_NORMAL)

    # ── Count what we have ────────────────────────────────────────────
    df_c = load_checkpoint(CHECKPOINT_CURFEW)
    df_n = load_checkpoint(CHECKPOINT_NORMAL)
    n_curfew = int(df_c["label_curfew"].sum()) if "label_curfew" in df_c.columns else 0
    n_strike = int(df_c["label_strike"].sum()) if "label_strike" in df_c.columns else 0
    n_normal = len(df_n)

    logger.info(f"\nCurrent counts — Curfew: {n_curfew}  Strike: {n_strike}  Normal: {n_normal}")

    # ── Source 12: Synthetic fill-up ─────────────────────────────────
    need_curfew = max(0, TARGET_CURFEW - n_curfew)
    need_strike = max(0, TARGET_STRIKE - n_strike)
    need_normal = max(0, TARGET_NORMAL - n_normal)

    logger.info(f"\n[SOURCE 12/12] Synthetic generation — "
                f"curfew +{need_curfew}  strike +{need_strike}  normal +{need_normal}")

    if need_curfew + need_strike + need_normal > 0:
        synth_curfew, synth_normal = generate_synthetic(need_curfew, need_strike, need_normal)
        save_checkpoint(synth_curfew, CHECKPOINT_CURFEW, label="Synthetic-curfew/strike")
        save_checkpoint(synth_normal, CHECKPOINT_NORMAL, label="Synthetic-normal")

    # ── Merge and deduplicate ─────────────────────────────────────────
    logger.info("\n[MERGE] Combining all checkpoints...")
    df_c = load_checkpoint(CHECKPOINT_CURFEW)
    df_n = load_checkpoint(CHECKPOINT_NORMAL)
    df_all = pd.concat([df_c, df_n], ignore_index=True)
    df_all = deduplicate_df(df_all, text_col="text")
    df_all["headline_id"] = [f"HL{i:07d}" for i in range(len(df_all))]

    df_all.to_csv(FINAL_RAW_CSV, index=False, encoding="utf-8")
    logger.info(f"\n[DONE] Final raw dataset → {FINAL_RAW_CSV}")
    logger.info(f"       Total rows    : {len(df_all):,}")
    logger.info(f"       Curfew rows   : {int(df_all['label_curfew'].sum()):,}")
    logger.info(f"       Strike rows   : {int(df_all['label_strike'].sum()):,}")
    logger.info(f"       Normal rows   : {int(df_all['label_normal'].sum()):,}")
    logger.info(f"       Sources       : {df_all['source'].nunique()}")