import time
import psutil
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB connection settings
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "wwiSWp-NsUnLWljRyV0X6PPPaaNi9_ttFhXmifOyQukJYfzqjjrSdq1IUuW0f6q_pUwrZo-7BZgTcTmazC9qng=="
INFLUXDB_ORG = "myorg"
INFLUXDB_BUCKET = "ai_metrics"
MODEL_NAME = "my_model_v1"

# Connect to InfluxDB (once at startup)
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)


def _get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def predict(model, input_data, ground_truth=None):
    """
    Wrap any model's predict() call.
    Measures latency, memory usage, and optionally accuracy.

    Args:
        model: Any ML model with a .predict() method (sklearn, etc.)
        input_data: Input features to predict on
        ground_truth: Optional true labels to compute accuracy

    Returns:
        Model predictions
    """
    start = time.time()
    error_occurred = False

    try:
        result = model.predict(input_data)
    except Exception as e:
        error_occurred = True
        result = None
        print(f"[monitor] Prediction error: {e}")

    latency_ms = (time.time() - start) * 1000
    memory_mb = _get_memory_mb()
    batch_size = len(input_data) if hasattr(input_data, "__len__") else 1

    point = (
        Point("ai_model_metrics")
        .tag("model", MODEL_NAME)
        .field("latency_ms", latency_ms)
        .field("batch_size", batch_size)
        .field("memory_mb", memory_mb)
        .field("error_rate", 1.0 if error_occurred else 0.0)
    )

    # Compute accuracy if ground truth is provided
    if ground_truth is not None and result is not None:
        correct = sum(p == t for p, t in zip(result, ground_truth))
        accuracy = correct / len(ground_truth)
        point = point.field("accuracy", accuracy)

    write_api.write(bucket=INFLUXDB_BUCKET, record=point)

    return result


def predict_proba(model, input_data, ground_truth=None, threshold=0.5):
    """
    Wrap probabilistic models (e.g. sklearn classifiers with predict_proba).

    Args:
        model: Model with .predict_proba() method
        input_data: Input features
        ground_truth: Optional true labels
        threshold: Probability threshold for binary classification

    Returns:
        Probability predictions
    """
    start = time.time()
    error_occurred = False

    try:
        proba = model.predict_proba(input_data)
        result = (proba[:, 1] >= threshold).astype(int)
    except Exception as e:
        error_occurred = True
        proba = None
        result = None
        print(f"[monitor] Prediction error: {e}")

    latency_ms = (time.time() - start) * 1000
    memory_mb = _get_memory_mb()
    batch_size = len(input_data) if hasattr(input_data, "__len__") else 1

    point = (
        Point("ai_model_metrics")
        .tag("model", MODEL_NAME)
        .field("latency_ms", latency_ms)
        .field("batch_size", batch_size)
        .field("memory_mb", memory_mb)
        .field("error_rate", 1.0 if error_occurred else 0.0)
    )

    if ground_truth is not None and result is not None:
        correct = sum(p == t for p, t in zip(result, ground_truth))
        accuracy = correct / len(ground_truth)
        point = point.field("accuracy", accuracy)

    write_api.write(bucket=INFLUXDB_BUCKET, record=point)

    return proba


def close():
    """Call this on shutdown to flush and close the InfluxDB connection."""
    write_api.close()
    client.close()


# --- Example usage ---
if __name__ == "__main__":
    import joblib
    import numpy as np

    # Load your model
    # model = joblib.load("my_model.pkl")

    # Simulate a model for demo purposes
    class DemoModel:
        def predict(self, X):
            return np.random.randint(0, 2, size=len(X))

    model = DemoModel()

    print("Sending test metrics to InfluxDB...")
    for i in range(5):
        X = np.random.rand(10, 4)
        y_true = np.random.randint(0, 2, size=10)
        predictions = predict(model, X, ground_truth=y_true)
        print(f"  Batch {i+1}: predictions={predictions}, latency logged")
        time.sleep(1)

    close()
    print("Done. Check Grafana at http://localhost:3000")
