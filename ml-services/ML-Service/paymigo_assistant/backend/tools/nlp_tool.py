import joblib
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPTool:
    def __init__(self):
        model_path = "paymigo_assistant/models/curfew_model.pkl"
        vectorizer_path = "paymigo_assistant/models/vectorizer.pkl"
        
        try:
            if os.path.exists(model_path) and os.path.exists(vectorizer_path):
                self.model = joblib.load(model_path)
                self.vectorizer = joblib.load(vectorizer_path)
                self.ready = True
                logger.info("NLP Models loaded successfully.")
            else:
                self.ready = False
                logger.warning(f"NLP Models not found at {model_path}. Fallback enabled.")
        except Exception as e:
            self.ready = False
            logger.error(f"Error loading NLP models: {e}")

    def detect_curfew(self, text):
        if not self.ready:
            return {"label": "unknown", "status": "error", "message": "Model not loaded"}
        
        try:
            vec = self.vectorizer.transform([text])
            pred = self.model.predict(vec)[0]
            # Assuming 1 is High Risk, 0 is Low Risk
            label = "high" if pred == 1 else "low"
            return {"label": label, "status": "success"}
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return {"label": "error", "status": "error", "message": str(e)}
