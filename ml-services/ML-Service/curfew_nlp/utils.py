"""
GigKavach Curfew NLP — Shared Utilities
  • robust_get()     : HTTP GET with 12-retry exponential backoff
  • save_checkpoint(): append rows to CSV immediately after each API call
  • load_checkpoint(): resume from saved rows so no data is ever lost
  • deduplicate()    : remove duplicate headlines by text similarity
  • normalise_row()  : standardise a raw headline dict into schema
"""

import os, sys, time, logging, hashlib, re
import requests
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (DATA_RAW, LOG_DIR, MAX_RETRIES, RETRY_DELAY,
                    REQUEST_TIMEOUT, META_COLS, TEXT_COL, LABEL_COL)

# ── Logger ────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    log_path = os.path.join(LOG_DIR, f"{name}.log")
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    fh.setFormatter(fmt); ch.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(ch)
    return logger

logger = get_logger("utils")


# ══════════════════════════════════════════════════════════════════════
# ROBUST HTTP GET  (12 retries, exponential backoff, full logging)
# ══════════════════════════════════════════════════════════════════════

def robust_get(
    url: str,
    params: dict = None,
    headers: dict = None,
    source_label: str = "API",
    attempt_log: bool = True,
) -> requests.Response | None:
    """
    GET with up to MAX_RETRIES attempts.
    Backs off exponentially: 3, 6, 12, 24 … seconds (capped at 60s).
    Returns Response on success, None if all attempts fail.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if attempt_log and attempt > 1:
                logger.info(f"  [{source_label}] Retry {attempt}/{MAX_RETRIES} → {url[:70]}")
            resp = requests.get(
                url, params=params, headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            if resp.status_code == 200:
                return resp
            elif resp.status_code == 429:
                wait = min(RETRY_DELAY * (2 ** attempt), 90)
                logger.warning(f"  [{source_label}] 429 Rate-limited — waiting {wait}s")
                time.sleep(wait)
            elif resp.status_code in (401, 403):
                logger.error(f"  [{source_label}] Auth error {resp.status_code} — check API key")
                return None
            elif resp.status_code >= 500:
                wait = min(RETRY_DELAY * (2 ** attempt), 60)
                logger.warning(f"  [{source_label}] Server error {resp.status_code} — waiting {wait}s")
                time.sleep(wait)
            else:
                logger.warning(f"  [{source_label}] HTTP {resp.status_code} — skipping")
                return None
        except requests.exceptions.Timeout:
            wait = min(RETRY_DELAY * attempt, 30)
            logger.warning(f"  [{source_label}] Timeout (attempt {attempt}) — waiting {wait}s")
            time.sleep(wait)
        except requests.exceptions.ConnectionError:
            wait = min(RETRY_DELAY * attempt, 30)
            logger.warning(f"  [{source_label}] Connection error (attempt {attempt}) — waiting {wait}s")
            time.sleep(wait)
        except Exception as e:
            logger.error(f"  [{source_label}] Unexpected error: {e}")
            time.sleep(RETRY_DELAY)

    logger.error(f"  [{source_label}] All {MAX_RETRIES} attempts failed for: {url[:80]}")
    return None


# ══════════════════════════════════════════════════════════════════════
# CHECKPOINT  —  save + load so no data is ever lost
# ══════════════════════════════════════════════════════════════════════

SCHEMA_COLS = [
    "headline_id", "text", "source", "published_at",
    "pincode", "city", "state",
    "label_curfew", "label_strike", "label_normal",
    "keyword_zone", "keyword_duration", "keyword_order_type",
]

def _ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    for col in SCHEMA_COLS:
        if col not in df.columns:
            df[col] = ""
    return df[SCHEMA_COLS]


def save_checkpoint(rows: list[dict], checkpoint_path: str, label: str = "") -> int:
    """
    Appends rows to checkpoint CSV immediately.
    Creates file with header if it doesn't exist.
    Returns total rows in checkpoint after save.
    """
    if not rows:
        return _count_checkpoint(checkpoint_path)
    new_df = pd.DataFrame(rows)
    new_df = _ensure_schema(new_df)

    if os.path.exists(checkpoint_path):
        existing = pd.read_csv(checkpoint_path)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df

    # Deduplicate within checkpoint by text hash
    combined["_hash"] = combined["text"].str.lower().str.strip().apply(
        lambda x: hashlib.md5(str(x).encode()).hexdigest()
    )
    combined = combined.drop_duplicates(subset="_hash").drop(columns="_hash")
    combined.to_csv(checkpoint_path, index=False, encoding="utf-8")
    n = len(combined)
    logger.info(f"  [CHECKPOINT] {label} saved → {n} total rows in {os.path.basename(checkpoint_path)}")
    return n


def load_checkpoint(checkpoint_path: str) -> pd.DataFrame:
    """Load checkpoint if it exists, else return empty DataFrame."""
    if os.path.exists(checkpoint_path):
        df = pd.read_csv(checkpoint_path)
        logger.info(f"  [CHECKPOINT] Loaded {len(df)} existing rows from {os.path.basename(checkpoint_path)}")
        return df
    return pd.DataFrame(columns=SCHEMA_COLS)


def _count_checkpoint(path: str) -> int:
    if os.path.exists(path):
        return sum(1 for _ in open(path, encoding="utf-8")) - 1
    return 0


def get_existing_texts(checkpoint_path: str) -> set:
    """Return set of already-collected text hashes to skip duplicates."""
    if not os.path.exists(checkpoint_path):
        return set()
    df = pd.read_csv(checkpoint_path, usecols=["text"])
    return set(
        df["text"].str.lower().str.strip().apply(
            lambda x: hashlib.md5(str(x).encode()).hexdigest()
        )
    )


# ══════════════════════════════════════════════════════════════════════
# TEXT CLEANING & PREPROCESSING
# ══════════════════════════════════════════════════════════════════════

PRESERVE_PHRASES = {
    "section 144", "section 188", "prohibitory order", "internet shutdown",
    "chakka jam", "rail roko", "night curfew", "day curfew",
}

def clean_text(text: str) -> str:
    """
    Cleans a headline for NLP:
      • Preserve important compound phrases
      • Remove HTML tags & URLs
      • Remove special characters (keep letters, digits, spaces)
      • Lowercase & collapse whitespace
    """
    if not isinstance(text, str):
        return ""
    t = text.strip()

    # Preserve phrases
    for phrase in PRESERVE_PHRASES:
        t = t.replace(phrase, phrase.replace(" ", "_"))

    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"https?://\S+|www\.\S+", " ", t)
    t = re.sub(r"[^a-zA-Z0-9_\s]", " ", t)
    t = t.lower()
    t = re.sub(r"\s+", " ", t).strip()

    # Restore phrases
    for phrase in PRESERVE_PHRASES:
        t = t.replace(phrase.replace(" ", "_"), phrase)

    return t


# ══════════════════════════════════════════════════════════════════════
# KEYWORD FEATURE FLAGS
# ══════════════════════════════════════════════════════════════════════

KW_FEATURES = {
    "has_kw_section144":      ["section 144", "section144", "sec 144"],
    "has_kw_curfew":          ["curfew"],
    "has_kw_prohibitory":     ["prohibitory", "prohibitory order"],
    "has_kw_internet_shut":   ["internet shutdown", "internet ban", "mobile shutdown"],
    "has_kw_night_curfew":    ["night curfew", "nighttime curfew"],
    "has_kw_shutdown":        ["complete shutdown", "total shutdown", "city shutdown"],
    "has_kw_lifted":          ["curfew lifted", "curfew relaxed", "lifted curfew", "relaxed curfew"],
    "has_kw_bandh":           ["bandh", "hartal", "chakka jam", "bharat bandh"],
    "has_kw_strike":          ["strike", "on strike", "go on strike"],
    "has_kw_roko":            ["rail roko", "rasta roko", "jam"],
    "has_kw_transport":       ["transport", "auto strike", "bus strike", "truck"],
    "has_kw_gig":             ["gig worker", "delivery worker", "swiggy", "zomato", "blinkit"],
    "has_kw_section188":      ["section 188", "sec 188"],
    "has_kw_forces":          ["security forces", "army deployed", "paramilitary", "police"],
    "has_kw_duration":        ["24 hour", "48 hour", "indefinite", "till further", "3 day", "7 day"],
}

def make_keyword_features(texts: pd.Series) -> pd.DataFrame:
    feat_dict = {}
    for feat_name, keywords in KW_FEATURES.items():
        pattern = "|".join(re.escape(k) for k in keywords)
        feat_dict[feat_name] = texts.str.lower().str.contains(pattern, regex=True).astype(int)
    return pd.DataFrame(feat_dict)


# ══════════════════════════════════════════════════════════════════════
# META FEATURES
# ══════════════════════════════════════════════════════════════════════

MAX_TEXT_LEN = 200
MAX_WORD_COUNT = 40

def make_meta_features(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    texts = df[text_col].fillna("")
    meta  = pd.DataFrame()
    meta["text_len"]     = texts.str.len().astype(float)
    meta["word_count"]   = texts.str.split().str.len().astype(float)
    meta["has_numbers"]  = texts.str.contains(r"\d+", regex=True).astype(int)
    meta["is_synthetic"] = (df["source"].str.lower() == "synthetic").astype(int)
    meta["is_rss"]       = df["source"].isin([
        "PIB-MHA","PIB-Home","PIB-Tamil","PIB-Hindi","PIB-Law","PIB-Defence",
        "PIB-Urban","PIB-Transport","AIR-English","AIR-National",
        "Google News","TheHindu","NDTV","IndiaToday","TOI-India",
        "DeccanHerald","IndianExpress",
    ]).astype(int)
    meta["has_city_kw"]  = texts.str.lower().str.contains(
        "|".join(["chennai","coimbatore","mumbai","delhi","bengaluru",
                  "hyderabad","kolkata","jaipur","pune","surat"]),
        regex=True
    ).astype(int)

    # Normalise numeric features
    meta["text_len"]   = meta["text_len"] / MAX_TEXT_LEN
    meta["word_count"] = meta["word_count"] / MAX_WORD_COUNT
    
    # Clip to [0, 1] range to avoid extreme values in live inference
    meta["text_len"]   = meta["text_len"].clip(0, 1.2)
    meta["word_count"] = meta["word_count"].clip(0, 1.2)
    
    return meta


# ══════════════════════════════════════════════════════════════════════
# ROW NORMALISER
# ══════════════════════════════════════════════════════════════════════

ZONE_KEYWORDS = [
    "chennai", "coimbatore", "madurai", "trichy", "salem", "tiruppur",
    "mumbai", "delhi", "bengaluru", "bangalore", "hyderabad", "kolkata",
    "ahmedabad", "jaipur", "surat", "pune", "india",
]

DURATION_PATTERNS = [
    "24 hour", "48 hour", "72 hour", "indefinite", "till further",
    "3 day", "7 day", "week", "night curfew", "day curfew",
    "from morning", "until evening", "from 6", "from 8", "from 10",
    "until midnight", "24-hour", "48-hour",
]

ORDER_TYPES = [
    "section 144", "curfew", "prohibitory", "shutdown", "bandh",
    "hartal", "lockdown", "internet shutdown", "night curfew",
    "day curfew", "complete shutdown", "total bandh", "rail roko",
    "strike", "chakka jam", "transport strike", "delivery strike",
]


def extract_keywords(text: str) -> dict:
    t = str(text).lower()
    zone     = next((k for k in ZONE_KEYWORDS    if k in t), "")
    duration = next((k for k in DURATION_PATTERNS if k in t), "")
    order    = next((k for k in ORDER_TYPES       if k in t), "")
    return {
        "keyword_zone":       zone,
        "keyword_duration":   duration,
        "keyword_order_type": order,
    }


def normalise_row(
    text: str,
    source: str,
    published_at: str,
    label_curfew: int,
    label_strike: int,
    label_normal: int,
    city: str = "",
    state: str = "",
    pincode: str = "",
) -> dict:
    kw = extract_keywords(text)
    # Infer city from text if not provided
    if not city:
        for z in ZONE_KEYWORDS[:-1]:  # skip "india"
            if z in text.lower():
                city = z.title()
                break
    return {
        "headline_id":        "",        # filled in during merge
        "text":               str(text).strip(),
        "source":             source,
        "published_at":       published_at,
        "pincode":            pincode,
        "city":               city,
        "state":              state,
        "label_curfew":       int(label_curfew),
        "label_strike":       int(label_strike),
        "label_normal":       int(label_normal),
        "keyword_zone":       kw["keyword_zone"],
        "keyword_duration":   kw["keyword_duration"],
        "keyword_order_type": kw["keyword_order_type"],
    }


# ══════════════════════════════════════════════════════════════════════
# DEDUPLICATION
# ══════════════════════════════════════════════════════════════════════

def deduplicate_df(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    """Remove exact + near-exact duplicates using MD5 of lowercased text."""
    df = df.copy()
    df["_hash"] = df[text_col].str.lower().str.strip().apply(
        lambda x: hashlib.md5(str(x).encode()).hexdigest()
    )
    before = len(df)
    df = df.drop_duplicates(subset="_hash").drop(columns="_hash")
    after = len(df)
    if before != after:
        logger.info(f"  [DEDUP] Removed {before - after} duplicate headlines")
    return df.reset_index(drop=True)