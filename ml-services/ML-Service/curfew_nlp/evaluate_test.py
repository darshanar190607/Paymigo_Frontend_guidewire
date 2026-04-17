"""
GigKavach Curfew NLP — Evaluation, Testing & Inference
═══════════════════════════════════════════════════════
• Full classification report on test set
• Confusion matrix (saved PNG)
• ROC-AUC curves per class (OvR)
• Per-source accuracy breakdown
• 20 live headline inference tests
• Production inference function (importable)
"""

import os, sys, re, warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.sparse import load_npz
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, f1_score, accuracy_score,
)
from sklearn.preprocessing import label_binarize
warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import DATA_PROC, MODEL_DIR, PLOTS_DIR, PIPELINE_PATH
from utils import get_logger, clean_text, make_keyword_features, make_meta_features

logger = get_logger("evaluate")
sns.set_style("whitegrid")


# ══════════════════════════════════════════════════════════════════════
# LOAD EVERYTHING
# ══════════════════════════════════════════════════════════════════════

logger.info("[LOAD] Loading pipeline artifact and test data...")
art = joblib.load(PIPELINE_PATH)

vectorizer     = art["vectorizer"]
lr_model       = art["lr_model"]
svc_model      = art["svc_model"]
xgb_model      = art["xgb_model"]
w_lr, w_svc, w_xgb = art["voting_weights"]
label_names    = art["label_names"]   # {0: "normal", 1: "curfew", 2: "strike"}

splits     = joblib.load(os.path.join(MODEL_DIR, "splits.pkl"))
y_test     = splits["y_test"].values
X_test     = load_npz(os.path.join(DATA_PROC, "X_test.npz"))
test_df    = pd.read_csv(os.path.join(DATA_PROC, "test_df.csv"))
logger.info(f"[LOAD] Test set: {X_test.shape}  rows: {len(y_test)}")


# ══════════════════════════════════════════════════════════════════════
# ENSEMBLE HELPERS
# ══════════════════════════════════════════════════════════════════════

def ensemble_proba(X):
    p1 = lr_model.predict_proba(X)
    p2 = svc_model.predict_proba(X)
    p3 = xgb_model.predict_proba(X)
    return (w_lr * p1 + w_svc * p2 + w_xgb * p3) / (w_lr + w_svc + w_xgb)

def ensemble_predict(X):
    return np.argmax(ensemble_proba(X), axis=1)


# ══════════════════════════════════════════════════════════════════════
# PLOT: CONFUSION MATRIX
# ══════════════════════════════════════════════════════════════════════

def plot_confusion_matrix(y_true, y_pred, save_path):
    cm = confusion_matrix(y_true, y_pred)
    names = [label_names[i] for i in range(3)]
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=names, yticklabels=names, ax=ax,
                annot_kws={"size": 13})
    ax.set_title("Curfew NLP — Confusion Matrix (Test Set)", fontsize=13, pad=12)
    ax.set_xlabel("Predicted", fontsize=11); ax.set_ylabel("Actual", fontsize=11)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"[PLOT] Confusion matrix → {save_path}")


# ══════════════════════════════════════════════════════════════════════
# PLOT: ROC-AUC (one-vs-rest per class)
# ══════════════════════════════════════════════════════════════════════

def plot_roc_curves(y_true, proba, save_path):
    from sklearn.metrics import roc_curve
    y_bin  = label_binarize(y_true, classes=[0, 1, 2])
    colors = ["#2563eb", "#dc2626", "#16a34a"]
    fig, ax = plt.subplots(figsize=(7, 5))
    for i, (name, col) in enumerate(zip([label_names[j] for j in range(3)], colors)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], proba[:, i])
        auc = roc_auc_score(y_bin[:, i], proba[:, i])
        ax.plot(fpr, tpr, color=col, lw=2, label=f"{name} (AUC={auc:.3f})")
    ax.plot([0,1],[0,1],"k--",lw=0.8)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("Curfew NLP — ROC Curves (OvR)", fontsize=13)
    ax.legend(loc="lower right"); ax.set_xlim([0,1]); ax.set_ylim([0,1.02])
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"[PLOT] ROC curves → {save_path}")


# ══════════════════════════════════════════════════════════════════════
# PER-SOURCE ACCURACY
# ══════════════════════════════════════════════════════════════════════

def per_source_accuracy(y_true, y_pred, test_df):
    df = pd.DataFrame({"y_true": y_true, "y_pred": y_pred,
                       "source": test_df["source"].values})
    logger.info("\n[PER-SOURCE ACCURACY]")
    logger.info(f"  {'Source':<25}  {'N':>5}  {'Acc':>6}  {'F1-macro':>8}")
    logger.info("  " + "─" * 50)
    for src in sorted(df["source"].unique()):
        sub = df[df["source"] == src]
        if len(sub) < 5:
            continue
        acc = accuracy_score(sub["y_true"], sub["y_pred"])
        f1  = f1_score(sub["y_true"], sub["y_pred"], average="macro", zero_division=0)
        logger.info(f"  {src:<25}  {len(sub):>5}  {acc:>6.3f}  {f1:>8.3f}")


# ══════════════════════════════════════════════════════════════════════
# PRODUCTION INFERENCE FUNCTION
# ══════════════════════════════════════════════════════════════════════

import scipy.sparse as sp

def predict_headline(text: str, artifact: dict = None) -> dict:
    """
    Production-ready single-headline inference.
    Returns dict with label, confidence, per-class probabilities.

    Usage:
        from 04_evaluate_test import predict_headline
        import joblib
        art = joblib.load("models_saved/curfew_full_pipeline.pkl")
        result = predict_headline("Curfew imposed in Chennai", art)
    """
    if artifact is None:
        artifact = art

    text_clean = clean_text(text)
    vec        = artifact["vectorizer"]
    lr         = artifact["lr_model"]
    svc        = artifact["svc_model"]
    xgb        = artifact["xgb_model"]
    w          = artifact["voting_weights"]

    # Build a 1-row DataFrame for meta/keyword features
    # NOTE: source is set to 'live' which maps to is_synthetic=0 and is_rss=0
    dummy_df = pd.DataFrame([{
        "text":         text,
        "text_clean":   text_clean,
        "source":       "live",
    }])

    # TF-IDF
    X_tfidf = vec.transform([text_clean])
    
    # Keyword flags (using shared util)
    X_kw = sp.csr_matrix(make_keyword_features(dummy_df["text_clean"]).values, dtype=float)
    
    # Meta features (using shared util)
    X_meta = sp.csr_matrix(make_meta_features(dummy_df, "text_clean").values, dtype=float)
    
    X = sp.hstack([X_tfidf, X_kw, X_meta], format="csr")
    X = sp.hstack([X_tfidf, X_kw, X_meta], format="csr")

    p1 = lr.predict_proba(X)[0]
    p2 = svc.predict_proba(X)[0]
    p3 = xgb.predict_proba(X)[0]
    proba = (w[0] * p1 + w[1] * p2 + w[2] * p3) / sum(w)

    label_id = int(np.argmax(proba))
    lnames   = artifact["label_names"]

    return {
        "label":       label_id,
        "label_name":  lnames[label_id],
        "confidence":  float(proba[label_id]),
        "prob_normal": float(proba[0]),
        "prob_curfew": float(proba[1]),
        "prob_strike": float(proba[2]),
    }


# ══════════════════════════════════════════════════════════════════════
# LIVE INFERENCE TESTS — 20 REAL-WORLD HEADLINES
# ══════════════════════════════════════════════════════════════════════

LIVE_TESTS = [
    # Curfew
    ("Curfew imposed in Chennai following communal clashes; Section 144 in force",            1),
    ("Section 144 CrPC clamped in Coimbatore district amid protests; gatherings banned",      1),
    ("Internet services suspended in Kashmir districts amid curfew order",                    1),
    ("Night curfew imposed in Bengaluru from 10 PM to 6 AM due to unrest",                   1),
    ("Prohibitory orders in three Hyderabad zones extended till further notice",              1),
    ("Curfew relaxed for 4 hours in Jaipur; essential services allowed",                      1),
    ("Complete shutdown in Surat after violence; Section 144 clamped",                        1),
    # Strike
    ("Swiggy and Zomato delivery workers in Mumbai launch indefinite strike over low wages",  2),
    ("Auto-rickshaw drivers in Chennai call 48-hour bandh demanding meter revision",          2),
    ("Truck owners call chakka jam across India over fuel price hike",                         2),
    ("Gig workers protest: Blinkit riders in Delhi refuse deliveries over policy",            2),
    ("Bus transport strike in Bengaluru hits commuters; hartal called by unions",             2),
    ("Rail Roko agitation disrupts trains in Pune over pending demands",                      2),
    # Normal civic news
    ("Chennai corporation launches underground drainage scheme worth ₹200 crore",             0),
    ("Coimbatore Smart City Mission project inaugurated by district collector",               0),
    ("PWD begins road repair on Chennai-Salem highway; commuters use alternate route",        0),
    ("Mumbai metro extension: 14 km new stretch approved by state cabinet",                  0),
    ("Hyderabad municipal body to open 20 new health clinics in outer zones",                0),
    ("School reopening in Tamil Nadu from June 5 after summer vacation ends",                0),
    ("Delhi power grid maintenance: planned outage in 5 areas on Thursday morning",          0),
]


def run_live_inference_tests():
    logger.info("\n" + "═" * 65)
    logger.info("  LIVE INFERENCE TESTS — 20 Headlines")
    logger.info("═" * 65)
    correct = 0
    lname   = {0: "normal", 1: "curfew", 2: "strike"}

    for headline, expected in LIVE_TESTS:
        result = predict_headline(headline)
        pred   = result["label"]
        conf   = result["confidence"]
        status = "✓" if pred == expected else "✗"
        if pred == expected:
            correct += 1
        short = headline[:60] + "..." if len(headline) > 60 else headline
        logger.info(
            f"  {status}  [{lname[expected]:<7}→{lname[pred]:<7}]  "
            f"conf={conf:.3f}  {short}"
        )

    acc = correct / len(LIVE_TESTS)
    logger.info(f"\n  Live Inference Accuracy: {correct}/{len(LIVE_TESTS)} = {acc*100:.1f}%")
    return acc


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logger.info("=" * 65)
    logger.info("  GigKavach Curfew NLP — Evaluation Suite")
    logger.info("=" * 65)

    # ── Ensemble predictions on test set ─────────────────────────────
    test_proba = ensemble_proba(X_test)
    test_preds = np.argmax(test_proba, axis=1)

    # ── Full classification report ────────────────────────────────────
    names = [label_names[i] for i in range(3)]
    logger.info("\n[TEST SET] Classification Report:")
    logger.info(classification_report(y_test, test_preds, target_names=names))

    macro_f1 = f1_score(y_test, test_preds, average="macro")
    acc       = accuracy_score(y_test, test_preds)
    y_bin     = label_binarize(y_test, classes=[0, 1, 2])
    roc_auc   = roc_auc_score(y_bin, test_proba, multi_class="ovr", average="macro")

    logger.info(f"  Accuracy   : {acc:.4f}")
    logger.info(f"  Macro F1   : {macro_f1:.4f}")
    logger.info(f"  ROC-AUC    : {roc_auc:.4f}  (macro OvR)")

    # ── Individual model performance ──────────────────────────────────
    logger.info("\n[INDIVIDUAL MODELS — test set]")
    for name, model in [("LR", lr_model), ("SVC", svc_model), ("XGB", xgb_model)]:
        preds = model.predict(X_test)
        f1  = f1_score(y_test, preds, average="macro")
        a   = accuracy_score(y_test, preds)
        logger.info(f"  {name:<4} macro-F1={f1:.4f}  Acc={a:.4f}")

    # ── Confusion matrix ──────────────────────────────────────────────
    plot_confusion_matrix(
        y_test, test_preds,
        os.path.join(PLOTS_DIR, "curfew_confusion_matrix.png")
    )

    # ── ROC curves ────────────────────────────────────────────────────
    plot_roc_curves(
        y_test, test_proba,
        os.path.join(PLOTS_DIR, "curfew_roc_curves.png")
    )

    # ── Per-source accuracy ───────────────────────────────────────────
    per_source_accuracy(y_test, test_preds, test_df)

    # ── Live inference tests ──────────────────────────────────────────
    live_acc = run_live_inference_tests()

    # ── Summary card ──────────────────────────────────────────────────
    logger.info("\n" + "█" * 65)
    logger.info("  CURFEW NLP MODEL — SUMMARY CARD")
    logger.info("█" * 65)
    logger.info(f"  Architecture  : LR + SVC + XGBoost (soft voting ensemble)")
    logger.info(f"  Features      : TF-IDF (15k) + keyword flags (15) + meta (7)")
    logger.info(f"  Labels        : normal / curfew / strike  (3-class)")
    logger.info(f"  Test Accuracy : {acc:.4f}")
    logger.info(f"  Macro F1      : {macro_f1:.4f}")
    logger.info(f"  ROC-AUC OvR  : {roc_auc:.4f}")
    logger.info(f"  Live Inf Acc  : {live_acc*100:.1f}%")
    logger.info(f"  Pipeline saved: {PIPELINE_PATH}")
    logger.info("█" * 65)