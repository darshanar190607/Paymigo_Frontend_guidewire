"""
GigKavach — Curfew NLP Model : Central Configuration
"""

import os

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_RAW  = os.path.join(BASE_DIR, "data", "raw")
DATA_PROC = os.path.join(BASE_DIR, "data", "processed")
MODEL_DIR = os.path.join(BASE_DIR, "models_saved")
PLOTS_DIR = os.path.join(BASE_DIR, "plots")
LOG_DIR   = os.path.join(BASE_DIR, "logs")

for _d in [DATA_RAW, DATA_PROC, MODEL_DIR, PLOTS_DIR, LOG_DIR]:
    os.makedirs(_d, exist_ok=True)

# ── Checkpoint file paths (saved after every API source) ──────────────
CHECKPOINT_CURFEW  = os.path.join(DATA_RAW, "checkpoint_curfew.csv")
CHECKPOINT_NORMAL  = os.path.join(DATA_RAW, "checkpoint_normal.csv")
FINAL_RAW_CSV      = os.path.join(DATA_RAW, "curfew_headlines_raw.csv")
CLEAN_CSV          = os.path.join(DATA_PROC, "curfew_headlines_clean.csv")
FEATURES_CSV       = os.path.join(DATA_PROC, "curfew_features.csv")

# ── Model save paths ──────────────────────────────────────────────────
TFIDF_PATH    = os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl")
LABEL_PATH    = os.path.join(MODEL_DIR, "label_encoder.pkl")
MODEL_PATH    = os.path.join(MODEL_DIR, "curfew_model.pkl")
PIPELINE_PATH = os.path.join(MODEL_DIR, "curfew_full_pipeline.pkl")

# ── API Keys — fill yours here ────────────────────────────────────────
NEWSAPI_KEY = "YOUR_NEWSAPI_KEY_HERE"      # newsapi.org (free 100/day)
# No key needed for: PIB RSS, Google News RSS, AIR RSS, all govt feeds

# ── Reproducibility ───────────────────────────────────────────────────
RANDOM_STATE = 42
TEST_SIZE    = 0.15
VAL_SIZE     = 0.10

# ── Label mapping ─────────────────────────────────────────────────────
LABEL_CURFEW = 1   # curfew / section 144 / prohibitory orders
LABEL_STRIKE = 2   # bandh / hartal / transport/delivery strike
LABEL_NORMAL = 0   # regular civic/local news, no disruption

# ── Text feature columns ─────────────────────────────────────────────
TEXT_COL = "text"
LABEL_COL = "label"
META_COLS = ["headline_id", "source", "published_at",
             "pincode", "city", "state",
             "keyword_zone", "keyword_duration", "keyword_order_type",
             "label_curfew", "label_strike", "label_normal"]

# ── Retry config (applies to every API call) ──────────────────────────
MAX_RETRIES  = 12
RETRY_DELAY  = 3    # seconds base; exponential backoff applied
REQUEST_TIMEOUT = 15

# ── Collection targets ────────────────────────────────────────────────
TARGET_CURFEW   = 2000   # minimum curfew headlines
TARGET_STRIKE   = 1000   # minimum strike headlines
TARGET_NORMAL   = 3000   # minimum normal headlines