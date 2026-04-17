import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score

from preprocess import preprocess_features, remove_outliers, FEATURES, ENGINEERED

DATA_PATH   = Path("D:/Hackathon Projects/ML-Service/app/data/zone_risk_history_final_10k.csv")
MODEL_DIR   = Path(__file__).parent
MODEL_PATH  = MODEL_DIR / "kmeans_model.pkl"
SCALER_PATH = MODEL_DIR / "scaler.pkl"
PCA_PATH    = MODEL_DIR / "pca.pkl"

# =========================================
# STEP 1 — LOAD + DROP LOW-SIGNAL COLS
# =========================================
DROP_COLS = ["pincode", "city", "avg_rainfall", "avg_pressure",
             "avg_wind_speed", "disruption_frequency_score"]

df = pd.read_csv(DATA_PATH)
df = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
print(f"Shape after dropping low-signal cols: {df.shape}")
print(f"Columns used: {df.columns.tolist()}\n")

# =========================================
# STEP 2-3 — PREPROCESS + OUTLIER REMOVAL
# =========================================
X = preprocess_features(df, FEATURES)
mask = remove_outliers(X, iqr_factor=1.5)
X_clean = X[mask].reset_index(drop=True)
print(f"After IQR outlier removal: {X_clean.shape}")

# =========================================
# STEP 4 — SCALE
# =========================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_clean)

# =========================================
# STEP 5 — EXPERIMENT: PCA dims × K values
# =========================================
results = []
n_features = X_scaled.shape[1]
for n_comp in range(2, n_features + 1):
    Xp = PCA(n_components=n_comp, random_state=42).fit_transform(X_scaled)
    for k in range(2, 6):
        labels = KMeans(n_clusters=k, init="k-means++", n_init=50,
                        max_iter=500, random_state=42).fit_predict(Xp)
        results.append({
            "pca_components": n_comp, "k": k,
            "silhouette": round(silhouette_score(Xp, labels), 4),
            "db": round(davies_bouldin_score(Xp, labels), 4),
            "n_samples": len(X_clean)
        })

# =========================================
# STEP 6 — RANKED TABLE
# =========================================
results_df = (pd.DataFrame(results)
              .sort_values(["silhouette", "db"], ascending=[False, True])
              .reset_index(drop=True))
results_df.index += 1
print("=== Experiment Results (Ranked) ===")
print(results_df.to_string())

# =========================================
# STEP 7 — BEST CONFIG
# =========================================
best      = results_df.iloc[0]
best_pca  = int(best["pca_components"])
best_k    = int(best["k"])

print(f"\nBest config -> PCA={best_pca} | K={best_k}")
print(f"Silhouette={best['silhouette']} | DB={best['db']}")

# =========================================
# STEP 7 — RETRAIN FINAL MODEL
# =========================================
pca_final    = PCA(n_components=best_pca, random_state=42)
X_pca_final  = pca_final.fit_transform(X_scaled)

final_model  = KMeans(n_clusters=best_k, init="k-means++", n_init=50,
                      max_iter=500, random_state=42)
final_labels = final_model.fit_predict(X_pca_final)

joblib.dump(scaler,      SCALER_PATH)
joblib.dump(pca_final,   PCA_PATH)
joblib.dump(final_model, MODEL_PATH)

# =========================================
# STEP 8 — FINAL SCORES
# =========================================
final_sil = silhouette_score(X_pca_final, final_labels)
final_db  = davies_bouldin_score(X_pca_final, final_labels)

print("\n=== Final Model ===")
print(f"Features       : {FEATURES + [ENGINEERED]}")
print(f"PCA components : {best_pca}")
print(f"Best K         : {best_k}")
print(f"Silhouette     : {final_sil:.4f}")
print(f"DB Score       : {final_db:.4f}")
print(f"Train size     : {len(X_clean)}")

# =========================================
# STEP 9 — VALIDATION
# =========================================
df_clean = df[mask].reset_index(drop=True).copy()
df_clean["cluster"] = final_labels
assert df_clean["cluster"].isna().sum() == 0, "NaN clusters detected!"

print("\nCluster Distribution:")
print(df_clean["cluster"].value_counts().sort_index())
print("\nNo NaN values in cluster assignments.")

# =========================================
# SAVE METADATA
# =========================================
metadata = {
    "model": "KMeans",
    "n_clusters": best_k,
    "features": FEATURES,
    "engineered_features": [ENGINEERED],
    "pca_components": best_pca,
    "silhouette_score": round(final_sil, 4),
    "davies_bouldin_score": round(final_db, 4),
    "trained": True
}
(MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2))

print(f"\nModel saved  : {MODEL_PATH}")
print(f"Scaler saved : {SCALER_PATH}")
print(f"PCA saved    : {PCA_PATH}")
print(f"Metadata     : {MODEL_DIR / 'metadata.json'}")
print("\nTraining completed successfully.")
