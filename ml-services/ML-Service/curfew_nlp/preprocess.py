"""
GigKavach Curfew NLP — Preprocessing Pipeline
══════════════════════════════════════════════
Steps:
  1.  Load raw CSV (merged checkpoint output)
  2.  Text cleaning  (lowercase, remove HTML/URLs/punct/numbers)
  3.  Deduplication (MD5 hash of cleaned text)
  4.  Multi-label → single label (curfew > strike > normal priority)
  5.  Feature engineering:
        a. TF-IDF unigrams + bigrams  (max 15,000 features)
        b. Manual keyword presence flags (15 binary features)
        c. Text length + word count features
        d. Source encoding
  6.  Stratified train / val / test split
  7.  Class-weight computation
  8.  Save preprocessor + splits

Outputs (data/processed/):
  curfew_headlines_clean.csv   — cleaned text with labels
  curfew_features.csv          — full feature matrix (inspection)
  ../models_saved/tfidf_vectorizer.pkl
  ../models_saved/label_encoder.pkl
  ../models_saved/splits.pkl
"""

import os, sys, re
import numpy as np
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight
from scipy.sparse import hstack, save_npz, load_npz
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import (
    FINAL_RAW_CSV, CLEAN_CSV, FEATURES_CSV,
    DATA_PROC, MODEL_DIR,
    TFIDF_PATH, LABEL_PATH, RANDOM_STATE, TEST_SIZE, VAL_SIZE,
)
from utils import (
    deduplicate_df, get_logger, extract_keywords,
    clean_text, make_keyword_features, make_meta_features
)

logger = get_logger("preprocess")


# ──────────────────────────────────────────────────────────────────────
# Note: PRESERVE_PHRASES, clean_text, KW_FEATURES, make_keyword_features,
# and make_meta_features have been moved to utils.py for shared access.
# ──────────────────────────────────────────────────────────────────────

def is_too_short(text: str, min_words: int = 4) -> bool:
    return len(text.split()) < min_words

def load_raw(path: str) -> pd.DataFrame:
    logger.info(f"[LOAD] Reading {path}")
    df = pd.read_csv(path, dtype=str).fillna("")
    logger.info(f"       Shape: {df.shape}")
    return df


# ══════════════════════════════════════════════════════════════════════
# STEP 2 — LABEL CONSOLIDATION
# ══════════════════════════════════════════════════════════════════════

def make_single_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Priority: curfew (1) > strike (2) > normal (0)
    Multi-label rows → pick highest priority.
    Adds 'label' column (0/1/2) and 'label_name' column.
    """
    df = df.copy()
    df["label_curfew"] = pd.to_numeric(df["label_curfew"], errors="coerce").fillna(0).astype(int)
    df["label_strike"] = pd.to_numeric(df["label_strike"], errors="coerce").fillna(0).astype(int)
    df["label_normal"] = pd.to_numeric(df["label_normal"], errors="coerce").fillna(0).astype(int)

    def resolve(row):
        if row["label_curfew"] == 1:
            return 1
        if row["label_strike"] == 1:
            return 2
        return 0

    df["label"] = df.apply(resolve, axis=1)
    df["label_name"] = df["label"].map({0: "normal", 1: "curfew", 2: "strike"})
    return df


# ══════════════════════════════════════════════════════════════════════
# STEP 5 — TF-IDF VECTORIZER
# ══════════════════════════════════════════════════════════════════════

TFIDF_STOPWORDS = [
    "the","a","an","is","are","was","were","be","been","being",
    "have","has","had","do","does","did","will","would","could",
    "should","may","might","shall","can","it","its","in","on",
    "at","by","for","of","to","and","or","but","not","with",
    "from","as","this","that","these","those","after","during",
    "amid","over","under","into","through","also","about",
]

def fit_tfidf(texts: pd.Series, max_features: int = 15_000) -> TfidfVectorizer:
    logger.info(f"[TFIDF] Fitting vectorizer on {len(texts):,} texts (max_features={max_features})")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        max_features=max_features,
        min_df=2,
        max_df=0.90,
        sublinear_tf=True,
        strip_accents="unicode",
        stop_words=TFIDF_STOPWORDS,
        analyzer="word",
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9_]{1,}\b",
    )
    vectorizer.fit(texts)
    logger.info(f"[TFIDF] Vocabulary size: {len(vectorizer.vocabulary_):,}")
    return vectorizer


# ══════════════════════════════════════════════════════════════════════
# STEP 6 — BUILD FULL FEATURE MATRIX
# ══════════════════════════════════════════════════════════════════════

def build_feature_matrix(df: pd.DataFrame, vectorizer: TfidfVectorizer, text_col: str):
    """
    Returns scipy sparse matrix: TF-IDF (15k) + keyword flags (15) + meta (7)
    Total: ~15,022 features
    """
    X_tfidf = vectorizer.transform(df[text_col].fillna(""))
    X_kw    = sp.csr_matrix(make_keyword_features(df[text_col]).values, dtype=float)
    X_meta  = sp.csr_matrix(make_meta_features(df, text_col).values, dtype=float)
    X       = sp.hstack([X_tfidf, X_kw, X_meta], format="csr")
    logger.info(f"[FEATURES] Matrix shape: {X.shape}")
    return X


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("=" * 65)
    logger.info("  GigKavach Curfew NLP — Preprocessing Pipeline")
    logger.info("=" * 65)

    # ── Step 1: Load ──────────────────────────────────────────────────
    df = load_raw(FINAL_RAW_CSV)

    # ── Step 2: Clean text ────────────────────────────────────────────
    logger.info("\n[STEP 2] Cleaning text...")
    df["text_clean"] = df["text"].apply(clean_text)
    before = len(df)
    df = df[df["text_clean"].apply(lambda x: not is_too_short(x))].reset_index(drop=True)
    logger.info(f"         Removed {before - len(df)} too-short rows. Remaining: {len(df):,}")

    # ── Step 3: Deduplicate on cleaned text ───────────────────────────
    logger.info("\n[STEP 3] Deduplicating on cleaned text...")
    df = deduplicate_df(df, text_col="text_clean")
    logger.info(f"         After dedup: {len(df):,}")

    # ── Step 4: Single label ──────────────────────────────────────────
    logger.info("\n[STEP 4] Consolidating labels...")
    df = make_single_label(df)
    dist = df["label_name"].value_counts()
    for label, cnt in dist.items():
        logger.info(f"         {label:<10}: {cnt:>6,}  ({cnt/len(df)*100:.1f}%)")

    # ── Save clean CSV ────────────────────────────────────────────────
    df.to_csv(CLEAN_CSV, index=False, encoding="utf-8")
    logger.info(f"\n[SAVED] Clean CSV → {CLEAN_CSV}")

    # ── Step 5: Train / Val / Test split BEFORE fitting vectorizer ────
    # (vectorizer MUST be fit only on train set)
    logger.info("\n[STEP 5] Stratified split...")
    X_text = df["text_clean"]
    y      = df["label"]

    X_train_text, X_temp_text, y_train, y_temp = train_test_split(
        X_text, y,
        test_size=TEST_SIZE + VAL_SIZE,
        stratify=y,
        random_state=RANDOM_STATE,
    )
    val_ratio = VAL_SIZE / (TEST_SIZE + VAL_SIZE)
    X_val_text, X_test_text, y_val, y_test = train_test_split(
        X_temp_text, y_temp,
        test_size=1 - val_ratio,
        stratify=y_temp,
        random_state=RANDOM_STATE,
    )
    logger.info(f"         Train: {len(X_train_text):,}  Val: {len(X_val_text):,}  Test: {len(X_test_text):,}")

    # Get corresponding full-row DataFrames for feature building
    train_df = df.loc[X_train_text.index].reset_index(drop=True)
    val_df   = df.loc[X_val_text.index].reset_index(drop=True)
    test_df  = df.loc[X_test_text.index].reset_index(drop=True)

    # ── Step 6: Fit TF-IDF on TRAIN only ─────────────────────────────
    logger.info("\n[STEP 6] Fitting TF-IDF on training set...")
    vectorizer = fit_tfidf(train_df["text_clean"], max_features=15_000)
    joblib.dump(vectorizer, TFIDF_PATH)
    logger.info(f"[SAVED] TF-IDF vectorizer → {TFIDF_PATH}")

    # ── Step 7: Build feature matrices ───────────────────────────────
    logger.info("\n[STEP 7] Building feature matrices...")
    X_train = build_feature_matrix(train_df, vectorizer, "text_clean")
    X_val   = build_feature_matrix(val_df,   vectorizer, "text_clean")
    X_test  = build_feature_matrix(test_df,  vectorizer, "text_clean")

    # Save sparse matrices
    save_npz(os.path.join(DATA_PROC, "X_train.npz"), X_train)
    save_npz(os.path.join(DATA_PROC, "X_val.npz"),   X_val)
    save_npz(os.path.join(DATA_PROC, "X_test.npz"),  X_test)

    y_train.reset_index(drop=True).to_csv(os.path.join(DATA_PROC, "y_train.csv"), index=False)
    y_val.reset_index(drop=True).to_csv(os.path.join(DATA_PROC, "y_val.csv"),   index=False)
    y_test.reset_index(drop=True).to_csv(os.path.join(DATA_PROC, "y_test.csv"),  index=False)

    # Save text for reference
    train_df.to_csv(os.path.join(DATA_PROC, "train_df.csv"), index=False)
    val_df.to_csv(os.path.join(DATA_PROC, "val_df.csv"),     index=False)
    test_df.to_csv(os.path.join(DATA_PROC, "test_df.csv"),   index=False)

    # ── Step 8: Class weights ─────────────────────────────────────────
    classes    = np.array([0, 1, 2])
    weights    = compute_class_weight("balanced", classes=classes, y=y_train.values)
    class_wt   = dict(zip(classes, weights))
    logger.info(f"\n[CLASS WEIGHTS] {class_wt}")

    # Save everything into a single splits dict
    splits = {
        "y_train": y_train.reset_index(drop=True),
        "y_val":   y_val.reset_index(drop=True),
        "y_test":  y_test.reset_index(drop=True),
        "class_weight": class_wt,
        "label_names":  {0: "normal", 1: "curfew", 2: "strike"},
        "n_features":   X_train.shape[1],
    }
    joblib.dump(splits, os.path.join(MODEL_DIR, "splits.pkl"))
    logger.info(f"[SAVED] Splits → {MODEL_DIR}/splits.pkl")

    # ── Step 9: Encode labels ─────────────────────────────────────────
    le = LabelEncoder()
    le.fit([0, 1, 2])
    joblib.dump(le, LABEL_PATH)

    logger.info("\n" + "=" * 65)
    logger.info("  Preprocessing complete.")
    logger.info(f"  Feature matrix size: {X_train.shape}")
    logger.info(f"  Train: {X_train.shape[0]}  Val: {X_val.shape[0]}  Test: {X_test.shape[0]}")
    logger.info("=" * 65)