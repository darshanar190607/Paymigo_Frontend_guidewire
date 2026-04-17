"""
GigKavach GeoTruth™ — Master Pipeline Runner
Runs all 5 stages in sequence:
  Step 1 → Data collection (hybrid)
  Step 2 → Preprocessing + SMOTE
  Step 3 → GPS Spoofing model training
  Step 4 → Fraud Detection model training
  Step 5 → Evaluation + testing

Usage:
  python run_pipeline.py            # full pipeline
  python run_pipeline.py --from 3  # start from step 3 (skip data + preprocessing)
"""

import sys, os, time, subprocess, argparse

STEPS = {
    1: ("01_data_hybrid_collection.py",  "Data Collection"),
    2: ("02_preprocessing_pipeline.py",  "Preprocessing + SMOTE"),
    3: ("03_gps_spoofing_model.py",       "GPS Spoofing Model"),
    4: ("04_fraud_detection_model.py",    "Fraud Detection Model"),
    5: ("05_evaluate_test.py",            "Evaluation & Testing"),
}

ROOT = os.path.dirname(os.path.abspath(__file__))


def run_step(step_num: int, script: str, label: str) -> bool:
    print(f"\n{'═'*65}")
    print(f"  STEP {step_num} / {len(STEPS)} — {label}")
    print(f"{'═'*65}")
    path = os.path.join(ROOT, script)
    t0   = time.time()
    result = subprocess.run(
        [sys.executable, path],
        cwd=ROOT,
    )
    elapsed = time.time() - t0
    if result.returncode == 0:
        print(f"\n  ✓  Step {step_num} complete  ({elapsed:.1f}s)")
        return True
    else:
        print(f"\n  ✗  Step {step_num} FAILED (return code {result.returncode})")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GigKavach Pipeline Runner")
    parser.add_argument("--from", dest="start_from", type=int, default=1,
                        help="Start from step N (1-5). Default: 1")
    args = parser.parse_args()

    print("\n" + "█" * 65)
    print("  GigKavach GeoTruth™  —  End-to-End Pipeline")
    print("█" * 65)

    # Check requirements
    req_path = os.path.join(ROOT, "requirements.txt")
    print(f"\n[PRE-CHECK] Install requirements with:")
    print(f"  pip install -r {req_path}\n")

    total_start = time.time()
    for step_num, (script, label) in STEPS.items():
        if step_num < args.start_from:
            print(f"[SKIP] Step {step_num} — {label}")
            continue
        ok = run_step(step_num, script, label)
        if not ok:
            print(f"\n[ABORT] Pipeline stopped at step {step_num}.")
            sys.exit(1)

    total = time.time() - total_start
    print(f"\n{'█'*65}")
    print(f"  PIPELINE COMPLETE  ({total/60:.1f} min total)")
    print(f"{'█'*65}")
    print("\nOutput files:")
    print(f"  data/gps_spoof_dataset.csv")
    print(f"  data/fraud_dataset.csv")
    print(f"  models_saved/gps_spoof_model.pkl")
    print(f"  models_saved/fraud_model.pkl")
    print(f"  models_saved/gps_preprocessor.pkl")
    print(f"  models_saved/fraud_preprocessor.pkl")
    print(f"  plots/  (confusion matrices, ROC/PR curves, SHAP, feature importance)\n")