from app.models.zone_clusterer.train import train as train_cluster
from app.models.premium_engine.train import train as train_premium
from app.models.trigger_classifier.train import train as train_trigger
# from app.models.curfew_nlp.train import train as train_curfew  # DISABLED
# from app.models.fraud_detector.train import train as train_fraud  # DISABLED
# from app.models.gps_classifier.train import train as train_gps  # DISABLED
from app.models.risk_forecaster.train import train as train_forecast

def retrain_all():
    print("Starting full retrain...")
    train_cluster()
    train_premium()
    train_trigger()
    # train_curfew()  # DISABLED
    # train_fraud()  # DISABLED
    # train_gps()  # DISABLED
    train_forecast()
    print("All models retrained.")

if __name__ == "__main__":
    retrain_all()
