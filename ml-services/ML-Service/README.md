# ML Service

FastAPI-based ML inference service with 7 models.

## Models
| # | Model | Algorithm | Endpoint |
|---|-------|-----------|----------|
| 1 | Zone Clusterer | KMeans | `POST /cluster/predict` |
| 2 | Premium Engine | XGBoost | `POST /premium/predict` |
| 3 | Trigger Classifier | Random Forest | `POST /trigger/predict` |
| 4 | Curfew NLP | TF-IDF + LR | `POST /curfew/predict` |
| 5 | Fraud Detector | Isolation Forest | `POST /fraud/detect` |
| 6 | GPS Classifier | Random Forest | `POST /fraud/gps` |
| 7 | Risk Forecaster | LSTM | `POST /forecast/predict` |

## Setup

```bash
pip install -r requirements.txt
```

## Train All Models

```bash
python -m app.pipelines.retrain
```

## Run Server

```bash
uvicorn app.main:app --reload
```

## Docker

```bash
docker build -t ml-service .
docker run -p 8000:8000 ml-service
```

## Docs
Visit `http://localhost:8000/docs` for interactive Swagger UI.
