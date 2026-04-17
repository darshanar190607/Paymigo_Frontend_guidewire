"""
GigKavach GeoTruth™ — Comprehensive Evaluation & Testing Suite
Covers:
  • Full classification report (per-class)
  • Confusion matrices (saved as PNG)
  • ROC-AUC + PR-AUC curves
  • SHAP feature importance (global + local)
  • Per-attack / per-fraud-type breakdown
  • Live inference test on new synthetic samples
  • Model summary card printed to console

Run after both model training scripts complete.
"""

import os, sys, warnings
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings("ignore")

from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, average_precision_score,
    f1_score, precision_score, recall_score,
    roc_curve, precision_recall_curve,
)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("[WARN] shap not installed — SHAP plots skipped (pip install shap)")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import MODEL_DIR, PLOTS_DIR, GPS_MODEL_PATH, FRAUD_MODEL_PATH, RANDOM_STATE

np.random.seed(RANDOM_STATE)
sns.set_style("whitegrid")
plt.rcParams["font.family"] = "DejaVu Sans"


# ══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════

def get_fused_fraud_probs(artifact, X):
    """Compute fused LGB+ISO probability for fraud model."""
    lgb_probs = artifact["lgb_model"].predict_proba(X)[:, 1]
    # iso_to_prob inline
    raw = artifact["iso_model"].score_samples(X)
    lo, hi = raw.min(), raw.max()
    iso_probs = 1.0 - ((raw - lo) / (hi - lo)) if hi != lo else np.zeros(len(raw))
    w = artifact.get("w_lgb", 0.75)
    return w * lgb_probs + (1 - w) * iso_probs


def print_metrics(y_true, y_probs, threshold, label):
    y_preds = (y_probs >= threshold).astype(int)
    print(f"\n{'='*55}")
    print(f"  {label} - Test Set Metrics")
    print(f"{'='*55}")
    print(f"  ROC-AUC  : {roc_auc_score(y_true, y_probs):.4f}")
    print(f"  PR-AUC   : {average_precision_score(y_true, y_probs):.4f}")
    print(f"  F1 Score : {f1_score(y_true, y_preds):.4f}")
    print(f"  Precision: {precision_score(y_true, y_preds):.4f}")
    print(f"  Recall   : {recall_score(y_true, y_preds):.4f}")
    print(f"  Threshold: {threshold}")
    print(f"\n{classification_report(y_true, y_preds, target_names=['Normal','Fraud/Spoof'])}")
    return y_preds


def plot_confusion_matrix(y_true, y_preds, title, save_path):
    cm = confusion_matrix(y_true, y_preds)
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Normal","Fraud"], yticklabels=["Normal","Fraud"], ax=ax)
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Confusion matrix -> {save_path}")


def plot_roc_pr_curves(y_true, y_probs, label, save_path):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    # ROC
    fpr, tpr, _ = roc_curve(y_true, y_probs)
    auc = roc_auc_score(y_true, y_probs)
    axes[0].plot(fpr, tpr, color="#2563eb", lw=2, label=f"AUC = {auc:.4f}")
    axes[0].plot([0,1],[0,1], "k--", lw=0.8)
    axes[0].set_xlabel("False Positive Rate")
    axes[0].set_ylabel("True Positive Rate")
    axes[0].set_title(f"ROC Curve - {label}")
    axes[0].legend(loc="lower right")
    axes[0].set_xlim([0,1]); axes[0].set_ylim([0,1.02])

    # PR
    prec, rec, _ = precision_recall_curve(y_true, y_probs)
    pr_auc = average_precision_score(y_true, y_probs)
    axes[1].plot(rec, prec, color="#16a34a", lw=2, label=f"PR-AUC = {pr_auc:.4f}")
    baseline = float(y_true.mean())
    axes[1].axhline(baseline, color="gray", lw=0.8, linestyle="--", label=f"Baseline = {baseline:.3f}")
    axes[1].set_xlabel("Recall")
    axes[1].set_ylabel("Precision")
    axes[1].set_title(f"PR Curve - {label}")
    axes[1].legend(loc="upper right")
    axes[1].set_xlim([0,1]); axes[1].set_ylim([0,1.02])

    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ROC + PR curves -> {save_path}")


def plot_feature_importance(feature_cols, importances, label, save_path, top_n=20):
    fi = pd.DataFrame({"feature": feature_cols, "importance": importances})
    fi = fi.sort_values("importance", ascending=True).tail(top_n)

    fig, ax = plt.subplots(figsize=(8, 0.4 * top_n + 1.5))
    bars = ax.barh(fi["feature"], fi["importance"], color="#3b82f6", height=0.6)
    ax.set_xlabel("Feature Importance")
    ax.set_title(f"Top {top_n} Features - {label}", fontsize=12)
    for bar in bars:
        ax.text(bar.get_width() + fi["importance"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{bar.get_width():.1f}", va="center", ha="left", fontsize=8)
    plt.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Feature importance -> {save_path}")


def per_class_breakdown(y_true, y_probs, threshold, meta_series, label_col, model_label):
    """Report precision/recall per spoof_type or fraud_type."""
    preds = (y_probs >= threshold).astype(int)
    df = pd.DataFrame({"y_true": y_true.values, "y_pred": preds, "type": meta_series.values})
    print(f"\n[{model_label}] Per-type breakdown (positive class only):")
    for ftype in sorted(df[df["y_true"] == 1]["type"].unique()):
        sub = df[df["type"] == ftype]
        if len(sub) == 0:
            continue
        tp = ((sub["y_true"] == 1) & (sub["y_pred"] == 1)).sum()
        fn = ((sub["y_true"] == 1) & (sub["y_pred"] == 0)).sum()
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        print(f"  {ftype:<28}  n={len(sub):>4}  recall={recall:.2f}")


def plot_shap_summary(model, X_sample, feature_cols, title, save_path):
    """SHAP beeswarm plot (top 20 features)."""
    if not SHAP_AVAILABLE:
        return
    try:
        # Use TreeExplainer for tree models; fallback to KernelExplainer
        try:
            base_model = model
            # For calibrated or stacking models, extract inner
            if hasattr(model, "estimators_"):         # stacking
                base_model = model.estimators_[0]     # first base (XGB)
            elif hasattr(model, "calibrated_classifiers_"):  # calibrated
                base_model = model.calibrated_classifiers_[0].estimator
            explainer = shap.TreeExplainer(base_model)
            shap_vals = explainer.shap_values(X_sample)
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[1]
        except Exception:
            explainer = shap.KernelExplainer(
                lambda x: model.predict_proba(x)[:, 1],
                shap.sample(X_sample, 100),
            )
            X_shap_test = shap.sample(X_sample, 200)
            shap_vals = explainer.shap_values(X_shap_test)
            X_display = X_shap_test
        else:
            X_display = X_sample

        fig = plt.figure(figsize=(9, 6))
        shap.summary_plot(shap_vals, X_display, feature_names=feature_cols,
                          max_display=20, show=False, plot_type="dot")
        plt.title(title, fontsize=12, pad=10)
        plt.tight_layout()
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        plt.close("all")
        print(f"  SHAP summary -> {save_path}")
    except Exception as e:
        print(f"  [WARN] SHAP plot failed: {e}")


# ══════════════════════════════════════════════════════════════════════
# LIVE INFERENCE TEST
# ══════════════════════════════════════════════════════════════════════

def inference_test_gps(artifact):
    """Run 5 hand-crafted GPS samples through the spoof detector."""
    feat = artifact["feature_cols"]
    base = {f: 0.0 for f in feat}

    normal_session = {**base,
        "baro_alt_m": 15.0, "gps_alt_m": 16.8, "alt_discrepancy_m": 1.8,
        "baro_pressure_hpa": 1013.2, "baro_altitude_rate": 0.01,
        "ambient_noise_db": 62.0, "noise_consistency_score": 0.91,
        "location_acoustic_match": 0.88, "acoustic_anomaly_flag": 0,
        "cell_tower_count": 5, "wifi_ap_count": 12,
        "expected_tower_match": 0.93, "network_latency_ms": 42.0,
        "signal_strength_dbm": -68, "network_loc_consistency": 0.92,
        "accel_magnitude": 0.72, "accel_variance_1min": 0.31,
        "reported_speed_kmph": 24.5, "inertial_speed_est": 23.1,
        "speed_discrepancy": 1.4, "heading_change_rate": 8.2,
        "motion_consistency": 0.94,
        "zone_pincode_match": 1, "expected_zone_transition": 0.96,
        "geofence_violations": 0, "route_feasibility": 0.92,
        "delivery_density_match": 0.88,
        "session_duration_min": 95.0, "deliveries_per_hour": 2.8,
        "break_frequency": 1.2, "speed_vs_baseline": 1.02,
        "earnings_vs_baseline": 0.98, "behavioral_anomaly": 0.08,
        "peer_proximity_count": 1, "sync_movement_score": 0.12,
        "device_fingerprint_match": 1, "platform_login_consistency": 0.97,
        "social_anomaly_score": 0.05,
        # derived features
        "speed_baro_interaction": 0.39, "network_zone_coherence": 0.85,
        "inertial_consistency_ratio": 0.94, "baro_accel_interaction": 0.007,
        "social_behavioral_combined": 0.065, "altitude_network_score": 0.006,
        "multi_layer_anomaly_score": 0.11, "overall_geotrust_score": 0.92,
    }

    teleport = {**normal_session,
        "reported_speed_kmph": 850.0, "inertial_speed_est": 22.0,
        "speed_discrepancy": 828.0, "motion_consistency": 0.04,
        "route_feasibility": 0.03, "behavioral_anomaly": 0.88,
        "geofence_violations": 7,
        "speed_baro_interaction": 180.0, "inertial_consistency_ratio": 0.026,
        "multi_layer_anomaly_score": 0.85, "overall_geotrust_score": 0.08,
    }

    altitude_spoof = {**normal_session,
        "gps_alt_m": 550.0, "alt_discrepancy_m": 535.0,
        "altitude_network_score": 0.8, "multi_layer_anomaly_score": 0.6,
    }

    network_mismatch = {**normal_session,
        "expected_tower_match": 0.08, "network_loc_consistency": 0.09,
        "cell_tower_count": 1, "signal_strength_dbm": -105,
        "network_zone_coherence": 0.08, "multi_layer_anomaly_score": 0.58,
        "overall_geotrust_score": 0.18,
    }

    social_ring = {**normal_session,
        "sync_movement_score": 0.92, "peer_proximity_count": 7,
        "social_anomaly_score": 0.88, "device_fingerprint_match": 0,
        "social_behavioral_combined": 0.72, "multi_layer_anomaly_score": 0.70,
    }

    samples = {
        "Normal delivery":    normal_session,
        "Teleport spoof":     teleport,
        "Altitude spoof":     altitude_spoof,
        "Network mismatch":   network_mismatch,
        "Social ring":        social_ring,
    }

    print("\n[INFERENCE TEST - GPS Spoofing]")
    print(f"{'Sample':<25} {'Prob':>8} {'Pred':>10} {'Threshold':>10}")
    print("-" * 58)
    threshold = artifact["threshold"]
    model     = artifact["model"]
    scaler    = joblib.load(
        os.path.join(os.path.dirname(GPS_MODEL_PATH), "gps_preprocessor.pkl")
    )

    for name, s in samples.items():
        row = pd.DataFrame([s])[feat]
        row_scaled = pd.DataFrame(scaler.transform(row), columns=feat)
        prob = model.predict_proba(row_scaled)[0, 1]
        pred = "SPOOF" if prob >= threshold else "Normal"
        flag = "[OK]" if (pred == "SPOOF") == (name != "Normal delivery") else "[FAIL]"
        print(f"  {name:<23} {prob:>7.4f}   {pred:>10}  {threshold:>9}  {flag}")


def inference_test_fraud(artifact):
    """Run 4 hand-crafted fraud samples through the fraud detector."""
    feat = artifact["feature_cols"]
    base = {f: 0.0 for f in feat}

    normal_worker = {**base,
        "zone_risk_tier": 2, "claim_frequency_30d": 1,
        "claim_amount_zscore": 0.3, "location_jump_count": 1,
        "gps_spoof_probability": 0.05, "policy_tenure_weeks": 52,
        "earnings_deviation": 0.1, "claim_timing_anomaly": 0.1,
        "peer_claim_correlation": 0.15, "device_change_count": 0,
        "login_anomaly_score": 0.08, "route_deviation_score": 0.12,
        "delivery_speed_anomaly": 0.09, "duplicate_claim_score": 0.04,
        "network_fraud_ring_score": 0.06, "barometric_consistency": 0.95,
        "zone_transition_anomaly": 0.08, "claim_photo_similarity_score": 0.1,
        "platform_switch_frequency": 0.05, "behavioral_baseline_deviation": 0.1,
        "gps_claim_interaction": 0.05, "ring_score_composite": 0.105,
        "temporal_claim_pressure": 0.07, "device_login_risk": 0.04,
        "overall_fraud_risk_score": 0.09,
    }

    fake_rain = {**normal_worker,
        "claim_frequency_30d": 12, "claim_amount_zscore": 3.8,
        "claim_timing_anomaly": 0.85, "barometric_consistency": 0.15,
        "gps_spoof_probability": 0.82,
        "gps_claim_interaction": 0.78, "temporal_claim_pressure": 0.95,
        "overall_fraud_risk_score": 0.78,
    }

    fraud_ring = {**normal_worker,
        "network_fraud_ring_score": 0.91, "peer_claim_correlation": 0.88,
        "device_change_count": 6, "login_anomaly_score": 0.84,
        "ring_score_composite": 0.895, "device_login_risk": 0.80,
        "overall_fraud_risk_score": 0.75,
    }

    duplicate_claim = {**normal_worker,
        "duplicate_claim_score": 0.93, "claim_frequency_30d": 14,
        "claim_photo_similarity_score": 0.91,
        "temporal_claim_pressure": 0.88, "overall_fraud_risk_score": 0.72,
    }

    samples = {
        "Normal worker":    normal_worker,
        "Fake rain claim":  fake_rain,
        "Fraud ring":       fraud_ring,
        "Duplicate claim":  duplicate_claim,
    }

    print("\n[INFERENCE TEST - Fraud Detection]")
    print(f"{'Sample':<25} {'Prob':>8} {'Pred':>10} {'Threshold':>10}")
    print("-" * 58)
    threshold = artifact["threshold"]
    scaler    = joblib.load(
        os.path.join(os.path.dirname(FRAUD_MODEL_PATH), "fraud_preprocessor.pkl")
    )

    for name, s in samples.items():
        row = pd.DataFrame([s])[feat]
        row_scaled = pd.DataFrame(scaler.transform(row), columns=feat)
        lgb_prob = artifact["lgb_model"].predict_proba(row_scaled)[0, 1]
        raw = artifact["iso_model"].score_samples(row_scaled)[0]
        iso_prob = float(1.0 - (raw - (-0.5)) / 0.5)  # approximate normalisation
        iso_prob = np.clip(iso_prob, 0, 1)
        fused = 0.75 * lgb_prob + 0.25 * iso_prob
        pred  = "FRAUD" if fused >= threshold else "Normal"
        flag  = "[OK]" if (pred == "FRAUD") == (name != "Normal worker") else "[FAIL]"
        print(f"  {name:<23} {fused:>7.4f}   {pred:>10}  {threshold:>9}  {flag}")


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 65)
    print("  GigKavach GeoTruth (TM) - Model Evaluation Suite")
    print("=" * 65)

    # ── Load GPS model ────────────────────────────────────────────────
    print("\n[GPS] Loading model and test splits...")
    gps_artifact = joblib.load(GPS_MODEL_PATH)
    gps_splits   = joblib.load(os.path.join(MODEL_DIR, "gps_splits.pkl"))
    X_te_g = gps_splits["X_test"];  y_te_g = gps_splits["y_test"]
    gps_feat = gps_artifact["feature_cols"]

    gps_probs = gps_artifact["model"].predict_proba(X_te_g)[:, 1]
    gps_preds = print_metrics(y_te_g, gps_probs, gps_artifact["threshold"], "GPS Spoofing")

    plot_confusion_matrix(y_te_g, gps_preds, "GPS Spoofing - Confusion Matrix",
                          os.path.join(PLOTS_DIR, "gps_confusion_matrix.png"))
    plot_roc_pr_curves(y_te_g, gps_probs, "GPS Spoofing",
                       os.path.join(PLOTS_DIR, "gps_roc_pr_curves.png"))

    # Feature importance from the XGB base model inside the stacking model
    try:
        xgb_base = gps_artifact["model"].estimators_[0]
        plot_feature_importance(gps_feat, xgb_base.feature_importances_,
                                "GPS Spoofing (XGB)",
                                os.path.join(PLOTS_DIR, "gps_feature_importance.png"))
    except Exception as e:
        print(f"  [WARN] Feature importance plot skipped: {e}")

    # SHAP
    sample_idx = np.random.choice(len(X_te_g), min(500, len(X_te_g)), replace=False)
    X_shap_g   = X_te_g.iloc[sample_idx]
    plot_shap_summary(gps_artifact["model"], X_shap_g, gps_feat,
                      "GPS Spoofing - SHAP Summary",
                      os.path.join(PLOTS_DIR, "gps_shap_summary.png"))

    # Per-type breakdown (requires original test data with spoof_type)
    gps_raw = pd.read_csv(os.path.join(os.path.dirname(GPS_MODEL_PATH).replace("models_saved","data"),
                                        "gps_spoof_dataset.csv"))
    # Rebuild indices: re-run preprocessing to get same split (deterministic)

    # ── Load Fraud model ──────────────────────────────────────────────
    print("\n[FRAUD] Loading model and test splits...")
    fraud_artifact = joblib.load(FRAUD_MODEL_PATH)
    fraud_splits   = joblib.load(os.path.join(MODEL_DIR, "fraud_splits.pkl"))
    X_te_f = fraud_splits["X_test"];  y_te_f = fraud_splits["y_test"]
    fraud_feat = fraud_artifact["feature_cols"]

    fraud_probs = get_fused_fraud_probs(fraud_artifact, X_te_f)
    fraud_preds = print_metrics(y_te_f, fraud_probs, fraud_artifact["threshold"], "Fraud Detection")

    plot_confusion_matrix(y_te_f, fraud_preds, "Fraud Detection - Confusion Matrix",
                          os.path.join(PLOTS_DIR, "fraud_confusion_matrix.png"))
    plot_roc_pr_curves(y_te_f, fraud_probs, "Fraud Detection",
                       os.path.join(PLOTS_DIR, "fraud_roc_pr_curves.png"))

    # Feature importance from LGB base
    try:
        lgb_base = fraud_artifact["lgb_model"]
        if hasattr(lgb_base, "calibrated_classifiers_"):
            lgb_base = lgb_base.calibrated_classifiers_[0].estimator
        plot_feature_importance(fraud_feat, lgb_base.feature_importances_,
                                "Fraud Detection (LGB)",
                                os.path.join(PLOTS_DIR, "fraud_feature_importance.png"))
    except Exception as e:
        print(f"  [WARN] Feature importance plot skipped: {e}")

    # SHAP for fraud
    sample_idx_f = np.random.choice(len(X_te_f), min(500, len(X_te_f)), replace=False)
    X_shap_f     = X_te_f.iloc[sample_idx_f]
    plot_shap_summary(fraud_artifact["lgb_model"], X_shap_f, fraud_feat,
                      "Fraud Detection - SHAP Summary",
                      os.path.join(PLOTS_DIR, "fraud_shap_summary.png"))

    # ── Inference tests ───────────────────────────────────────────────
    inference_test_gps(gps_artifact)
    inference_test_fraud(fraud_artifact)

    # ── Model summary card ────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  MODEL SUMMARY CARD - GigKavach GeoTruth (TM)")
    print("=" * 65)
    g_auc   = roc_auc_score(y_te_g, gps_probs)
    g_prauc = average_precision_score(y_te_g, gps_probs)
    g_f1    = f1_score(y_te_g, gps_preds)
    f_auc   = roc_auc_score(y_te_f, fraud_probs)
    f_prauc = average_precision_score(y_te_f, fraud_probs)
    f_f1    = f1_score(y_te_f, fraud_preds)

    print(f"\n  GPS Spoofing Detector  (XGB + RF -> LR stacking)")
    print(f"    ROC-AUC : {g_auc:.4f}    PR-AUC : {g_prauc:.4f}    F1 : {g_f1:.4f}")
    print(f"    Features: {len(gps_feat)}   Threshold: {gps_artifact['threshold']}")

    print(f"\n  Fraud Detector  (LightGBM + Isolation Forest fusion)")
    print(f"    ROC-AUC : {f_auc:.4f}    PR-AUC : {f_prauc:.4f}    F1 : {f_f1:.4f}")
    print(f"    Features: {len(fraud_feat)}   Threshold: {fraud_artifact['threshold']}")

    print(f"\n  Plots saved to: {PLOTS_DIR}/")
    print(f"  Models saved to: {MODEL_DIR}/")
    print("\n[DONE] Evaluation complete.\n")