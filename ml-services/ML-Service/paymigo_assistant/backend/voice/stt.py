import torch
from transformers import pipeline

class WhisperSTT:
    def __init__(self, model_name="openai/whisper-tiny"):
        print(f"Loading Whisper model: {model_name}...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=device
        )

    def transcribe(self, audio_path):
        try:
            result = self.pipe(audio_path)
            return result["text"]
        except Exception as e:
            print(f"Error in transcription: {e}")
            return None

if __name__ == "__main__":
    # Test stub - needs an actual audio file to work
    # stt = WhisperSTT()
    # print(stt.transcribe("sample.wav"))
    pass
