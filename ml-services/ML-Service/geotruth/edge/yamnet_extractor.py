"""
GeoTruth — YAMNet Edge Extractor (Audio Simulator)
====================================================
Simulates what the PayMigo Android app does on-device.
Processes a .wav file using yamnet.tflite and extracts
a 5-dimensional probability vector for our target classes.

Target Classes (YAMNet indices):
    0   → Speech / Human Voice
    326 → Traffic / Street Noise
    422 → Rain
    426 → Wind
    506 → Silence / Indoor Quiet

Usage:
    python edge/yamnet_extractor.py --wav path/to/audio.wav

Run from geotruth/ root directory after activating venv.
"""

import os
import sys
import urllib.request
import numpy as np
import wave
import struct
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
log = logging.getLogger("yamnet_extractor")

# ── Constants ──────────────────────────────────────────────────────────────────

YAMNET_TFLITE_URL = (
    "https://storage.googleapis.com/download.tensorflow.org/models/tflite/task_library/audio_classification/android/lite-model_yamnet_classification_tflite_1.tflite"
)
FALLBACK_URL = (
    "https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1?lite-format=tflite"
)

MODELS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "models")
)
YAMNET_MODEL_PATH = os.path.join(MODELS_DIR, "yamnet.tflite")

# YAMNet class indices for our 5 target signals
TARGET_CLASSES = {
    "speech":  0,
    "traffic": 326,
    "rain":    422,
    "wind":    426,
    "silence": 506,
}

YAMNET_SAMPLE_RATE = 16000      # YAMNet expects 16 kHz mono WAV
YAMNET_PATCH_HOP   = 0.48       # seconds per hop
YAMNET_PATCH_WINDOW = 0.96      # seconds per patch


# ── Model Download ─────────────────────────────────────────────────────────────

def download_yamnet_if_missing(model_path: str = YAMNET_MODEL_PATH) -> bool:
    """
    Download yamnet.tflite from TensorFlow Hub if not present.
    Returns True if the model is available (already existed or was downloaded).
    """
    if os.path.exists(model_path) and os.path.getsize(model_path) > 100_000:
        log.info(f"YAMNet model already present at: {model_path}")
        return True

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    log.info("Downloading YAMNet TFLite model (~3 MB) …")

    # Try primary URL, then fallback
    for url in [YAMNET_TFLITE_URL, FALLBACK_URL]:
        try:
            urllib.request.urlretrieve(url, model_path)
            size_mb = os.path.getsize(model_path) / 1_048_576
            log.info(f"Downloaded YAMNet model ({size_mb:.1f} MB) → {model_path}")
            return True
        except Exception as e:
            log.warning(f"Download failed from {url}: {e}")

    log.error("All YAMNet download attempts failed.")
    return False


# ── WAV Loading ────────────────────────────────────────────────────────────────

def load_wav_mono_16k(wav_path: str) -> np.ndarray:
    """
    Load a WAV file, convert to mono, and resample to 16 000 Hz.
    Returns a float32 numpy array normalised to [-1.0, 1.0].

    Handles:
      • Stereo → mono (average channels)
      • 8/16/24/32-bit PCM
      • Sample-rate conversion (simple linear resample for simulator purposes)
    """
    if not os.path.exists(wav_path):
        raise FileNotFoundError(f"WAV file not found: {wav_path}")

    with wave.open(wav_path, "rb") as wf:
        n_channels  = wf.getnchannels()
        sample_rate = wf.getframerate()
        sampwidth   = wf.getsampwidth()     # bytes per sample
        n_frames    = wf.getnframes()
        raw_bytes   = wf.readframes(n_frames)

    # Decode PCM bytes → numpy
    fmt_map = {1: np.int8, 2: np.int16, 4: np.int32}
    dtype = fmt_map.get(sampwidth, np.int16)
    audio = np.frombuffer(raw_bytes, dtype=dtype).astype(np.float32)

    # Normalise to [-1, 1]
    max_val = float(2 ** (8 * sampwidth - 1))
    audio /= max_val

    # Stereo → mono
    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    # Resample to 16 kHz (linear interpolation — good enough for simulator)
    if sample_rate != YAMNET_SAMPLE_RATE:
        target_len = int(len(audio) * YAMNET_SAMPLE_RATE / sample_rate)
        indices = np.linspace(0, len(audio) - 1, target_len)
        audio = np.interp(indices, np.arange(len(audio)), audio)
        log.info(f"Resampled {sample_rate} Hz → {YAMNET_SAMPLE_RATE} Hz")

    return audio.astype(np.float32)


# ── TFLite Inference ───────────────────────────────────────────────────────────

def _run_tflite_inference(audio: np.ndarray, model_path: str) -> np.ndarray:
    """
    Run YAMNet TFLite inference and return averaged class probabilities
    across all patches in the audio clip.
    Returns shape (521,) float32 array.
    """
    try:
        import tflite_runtime.interpreter as tflite
    except ImportError:
        try:
            import tensorflow as tf
            tflite = tf.lite
        except ImportError:
            raise ImportError(
                "Install tflite_runtime or tensorflow:\n"
                "  pip install tflite-runtime   (lightweight)\n"
                "  pip install tensorflow        (full)"
            )

    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details  = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # YAMNet expects exactly 15 600 samples (0.975 s at 16 kHz)
    patch_size = 15600
    hop_size   = int(YAMNET_PATCH_HOP * YAMNET_SAMPLE_RATE)

    all_scores = []

    # Pad audio to at least one patch
    if len(audio) < patch_size:
        audio = np.pad(audio, (0, patch_size - len(audio)))

    start = 0
    while start + patch_size <= len(audio):
        patch = audio[start : start + patch_size].reshape(1, -1)
        interpreter.set_tensor(input_details[0]["index"], patch)
        interpreter.invoke()
        scores = interpreter.get_tensor(output_details[0]["index"])  # (1, 521)
        all_scores.append(scores[0])
        start += hop_size

    if not all_scores:
        return np.zeros(521, dtype=np.float32)

    return np.mean(all_scores, axis=0)   # Average across patches → (521,)


# ── Public API ─────────────────────────────────────────────────────────────────

def process_audio(wav_file_path: str, model_path: str = YAMNET_MODEL_PATH) -> list[float]:
    """
    Process a .wav file through YAMNet TFLite and return a 5-dimensional
    probability vector for GeoTruth's acoustic layer.

    Vector layout (matches acoustic.py expectations):
        [0] → P(Rain)    — YAMNet class 422
        [1] → P(Wind)    — YAMNet class 426
        [2] → P(Traffic) — YAMNet class 326
        [3] → P(Silence) — YAMNet class 506
        [4] → P(Speech)  — YAMNet class 0

    Args:
        wav_file_path: Path to a mono or stereo .wav file (any sample rate).
        model_path:    Path to yamnet.tflite (auto-downloaded if missing).

    Returns:
        list of 5 floats in [0.0, 1.0]
    """
    if not download_yamnet_if_missing(model_path):
        log.warning("YAMNet unavailable — returning zero vector")
        return [0.0, 0.0, 0.0, 0.0, 0.0]

    audio = load_wav_mono_16k(wav_file_path)
    log.info(f"Audio loaded: {len(audio) / YAMNET_SAMPLE_RATE:.2f}s @ 16 kHz")

    all_probs = _run_tflite_inference(audio, model_path)

    vector = [
        float(all_probs[TARGET_CLASSES["rain"]]),
        float(all_probs[TARGET_CLASSES["wind"]]),
        float(all_probs[TARGET_CLASSES["traffic"]]),
        float(all_probs[TARGET_CLASSES["silence"]]),
        float(all_probs[TARGET_CLASSES["speech"]]),
    ]

    log.info(
        f"Acoustic vector → rain={vector[0]:.3f} wind={vector[1]:.3f} "
        f"traffic={vector[2]:.3f} silence={vector[3]:.3f} speech={vector[4]:.3f}"
    )
    return vector


def generate_synthetic_vector(scenario: str = "rain") -> list[float]:
    """
    Generate a realistic synthetic acoustic vector without a real WAV file.
    Used for unit tests and CI pipelines where audio hardware is unavailable.

    Scenarios: 'rain', 'wind', 'indoor', 'street', 'speech'
    """
    profiles = {
        "rain":    [0.82, 0.21, 0.05, 0.03, 0.01],
        "wind":    [0.15, 0.78, 0.08, 0.04, 0.02],
        "indoor":  [0.01, 0.02, 0.04, 0.88, 0.12],
        "street":  [0.04, 0.11, 0.73, 0.06, 0.18],
        "speech":  [0.02, 0.03, 0.08, 0.15, 0.79],
    }
    base = profiles.get(scenario, profiles["indoor"])
    # Add small Gaussian noise to simulate real variability
    noisy = [max(0.0, min(1.0, v + np.random.normal(0, 0.02))) for v in base]
    return noisy


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GeoTruth YAMNet Edge Extractor")
    parser.add_argument("--wav", type=str, help="Path to .wav file")
    parser.add_argument(
        "--synthetic", type=str,
        choices=["rain", "wind", "indoor", "street", "speech"],
        help="Generate a synthetic vector instead of processing a real WAV"
    )
    parser.add_argument("--download-only", action="store_true",
                        help="Just download the YAMNet model and exit")
    args = parser.parse_args()

    if args.download_only:
        success = download_yamnet_if_missing()
        sys.exit(0 if success else 1)

    if args.synthetic:
        vec = generate_synthetic_vector(args.synthetic)
        print(f"\nSynthetic vector ({args.synthetic}): {vec}")
        sys.exit(0)

    if not args.wav:
        parser.print_help()
        sys.exit(1)

    vec = process_audio(args.wav)
    print(f"\nAcoustic feature vector (5-dim):")
    print(f"  Rain    : {vec[0]:.4f}")
    print(f"  Wind    : {vec[1]:.4f}")
    print(f"  Traffic : {vec[2]:.4f}")
    print(f"  Silence : {vec[3]:.4f}")
    print(f"  Speech  : {vec[4]:.4f}")
    print(f"\nPass this to ClaimVector.acoustic_feature_vector: {vec}")