import pandas as pd
from app.models.zone_clusterer.predict import predict as cluster_predict
from app.models.fraud_detector.predict import predict as fraud_predict

def run_batch_inference(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)
    df["cluster"] = df.apply(lambda row: cluster_predict(row.to_dict()), axis=1)
    df["is_fraud"] = df.apply(lambda row: fraud_predict(row.to_dict()), axis=1)
    df.to_csv(output_csv, index=False)
    print(f"Batch inference complete. Results saved to {output_csv}")

if __name__ == "__main__":
    run_batch_inference("app/data/workers_final_10k.csv", "app/data/batch_results.csv")
