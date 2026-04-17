"""
GeoTruth — Inertial Layer Integration Test
===========================================
Run this AFTER training the model to verify the full pipeline:
  generate_dataset → train_model → inertial.py inference

Usage:
  cd geotruth/
  python examples/test_inertial.py

Expected output for all 5 scenarios:
  Scenario 1 (genuine stranded):     score=1.0, genuine approved
  Scenario 2 (stayed home):          score=0.0, suspicious
  Scenario 3 (spoof activation):     score=0.0, reverse delta
  Scenario 4 (budget phone, genuine):available=False, grace_flag=True
  Scenario 5 (mock location):        score=0.0, mock detected
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from geotruth.layers.inertial import score_raw, LayerResult


def print_result(label: str, result: LayerResult):
    status = "APPROVED" if result.score == 1.0 else ("UNAVAILABLE" if not result.available else "SUSPICIOUS")
    print(f"\n{'─'*55}")
    print(f"Scenario : {label}")
    print(f"Status   : {status}")
    print(f"Score    : {result.score} | Weight: {result.weight} | Confidence: {result.confidence:.3f}")
    print(f"Grace    : {result.grace_flag}")
    print(f"Reason   : {result.reason}")


def main():
    print("GeoTruth — Inertial Layer Inference Tests")
    print("=" * 55)

    # Scenario 1: Genuine worker caught mid-delivery
    # Was actively riding (variance=0.82) → took shelter (variance=0.04)
    r1 = score_raw(variance_prior=0.82, variance_current=0.04)
    print_result("Genuine — Took shelter mid-delivery", r1)

    # Scenario 2: Fraud — stayed home all day
    # Both windows show sedentary behavior
    r2 = score_raw(variance_prior=0.05, variance_current=0.03)
    print_result("Fraud — Stayed home, both windows static", r2)

    # Scenario 3: Fraud — spoof app activation
    # Home prior variance, then picked up phone (current > prior)
    r3 = score_raw(variance_prior=0.08, variance_current=0.28)
    print_result("Fraud — Spoof app activated (reverse delta)", r3)

    # Scenario 4: Budget phone — no accelerometer data
    r4 = score_raw(variance_prior=None, variance_current=None)
    print_result("Budget phone — variance fields missing", r4)

    # Scenario 5: Mock location detected by Android OS
    r5 = score_raw(variance_prior=0.75, variance_current=0.05, is_mock_location=True)
    print_result("Mock location flag = True", r5)

    # Scenario 6: No gyroscope (reduced weight, grace flag)
    r6 = score_raw(variance_prior=0.70, variance_current=0.06, gyroscope_available=False)
    print_result("Genuine — No gyroscope (reduced weight)", r6)

    print(f"\n{'='*55}")
    print("All scenarios tested. Check scores and reasons above.")


if __name__ == "__main__":
    main()