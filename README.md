# 📊 AI Model Monitoring with InfluxDB, Telegraf & Grafana

> Build a production-ready monitoring stack to track AI model performance in real-time — accuracy, latency, and resource usage.

![InfluxDB](https://img.shields.io/badge/InfluxDB-2.7-d81b60?style=flat-square)
![Telegraf](https://img.shields.io/badge/Telegraf-latest-22c55e?style=flat-square)
![Grafana](https://img.shields.io/badge/Grafana-latest-f97316?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square)

---
<div align="center">
  <h3>InfluxDB + Telegraf + Grafana for Beginners – Monitoring AI Models (2026)</h3>
  <a href="https://www.youtube.com/watch?v=ttS4Dh7Y9RU">
    <img src="https://img.youtube.com/vi/ttS4Dh7Y9RU/maxresdefault.jpg" alt="Watch the InfluxDB Telegraf Grafana Tutorial" style="width:100%; max-width:600px;">
  </a>
  <p><i>Click the image to watch the full monitoring stack setup on YouTube</i></p>
</div>

## 🎯 Why Monitor AI Models?

| Problem | Impact |
|---------|--------|
| **Model Drift** | AI models degrade over time as real-world data shifts |
| **Latency Spikes** | Slow predictions kill user experience |
| **Resource Waste** | Memory leaks and CPU overuse are invisible without tooling |
| **Silent Failures** | Models return wrong results without errors |

**Production AI needs observability.** This project gives you the TIG stack (Telegraf + InfluxDB + Grafana) to monitor your models 24/7.

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────┐      ┌──────────┐      ┌─────────┐
│  AI Model   │ ───▶ │ Telegraf │ ───▶ │ InfluxDB │ ◀─── │ Grafana │
│  (Python)   │      │  :8080   │      │  :8086   │      │  :3000  │
└─────────────┘      └──────────┘      └──────────┘      └─────────┘
     │                                       │                  │
     └─── Generates metrics                 │                  │
                                    Stores time-series    Visualizes &
                                         data              alerts
```

**Data Flow:**
1. Your AI model generates metrics (latency, accuracy, batch size)
2. Telegraf collects and forwards to InfluxDB
3. InfluxDB stores with nanosecond timestamps
4. Grafana queries and visualizes live

---

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Python 3.8+**
- **Terminal** (PowerShell, Bash, or CMD)
- An AI model (scikit-learn, TensorFlow, PyTorch, etc.)

---

## 🚀 Quick Start (10 Minutes)

### Step 1: Install InfluxDB

```bash
docker run -d -p 8086:8086 \
  --name influxdb \
  -v influxdb-data:/var/lib/influxdb2 \
  -v influxdb-config:/etc/influxdb2 \
  influxdb:2.7

# Verify it's running
docker ps
```

Open `http://localhost:8086` in your browser.

### Step 2: Configure InfluxDB

1. Click **"Get Started"**
2. Create admin credentials (save these!)
3. **Organization**: `myorg`
4. **Bucket**: `ai_metrics`
5. Click **"Configure Later"** → **Data** → **API Tokens** → **"Generate Token"**
6. **Copy and save your API token** (you won't see it again!)

### Step 3: Set Up Docker Network

```bash
# Create project folder
mkdir ai-monitoring && cd ai-monitoring

# Create shared network
docker network create monitoring

# Connect InfluxDB to network
docker network connect monitoring influxdb
```

### Step 4: Configure Telegraf

Create `telegraf.conf`:

```toml
[agent]
    interval = "10s"
    flush_interval = "10s"

# Output: send data to InfluxDB
[[outputs.influxdb_v2]]
    urls = ["http://influxdb:8086"]
    token = "YOUR_API_TOKEN_HERE"
    organization = "myorg"
    bucket = "ai_metrics"

# Input: listen for metrics over HTTP
[[inputs.http_listener_v2]]
    service_address = ":8080"
    paths = ["/metrics"]
    data_format = "influx"
```

**⚠️ Replace `YOUR_API_TOKEN_HERE` with your actual token from Step 2.**

Start Telegraf:

```bash
# Windows PowerShell
docker run -d --name telegraf --network monitoring `
  -v ${PWD}/telegraf.conf:/etc/telegraf/telegraf.conf:ro `
  telegraf

# Linux/macOS/Git Bash
docker run -d --name telegraf --network monitoring \
  -v $(pwd)/telegraf.conf:/etc/telegraf/telegraf.conf:ro \
  telegraf
```

### Step 5: Instrument Your AI Model

Install dependencies:

```bash
pip install influxdb-client psutil
```

Use the included `monitor.py`:

```python
from monitor import predict
import joblib

# Load your model
model = joblib.load("my_model.pkl")

# Wrap predictions with monitoring
result = predict(model, X, ground_truth=y_true)
```

**Metrics tracked:**
- `latency_ms` — inference time
- `accuracy` — model accuracy (if ground truth provided)
- `batch_size` — number of inputs
- `memory_mb` — process memory usage
- `error_rate` — 1.0 on failure, 0.0 on success

### Step 6: Install Grafana

```bash
docker run -d -p 3000:3000 \
  --name grafana --network monitoring \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana:latest

# Connect to monitoring network
docker network connect monitoring grafana
```

Open `http://localhost:3000`
- **Username**: `admin`
- **Password**: `admin` (you'll be prompted to change it)

### Step 7: Connect Grafana to InfluxDB

1. Go to **Connections** → **Data Sources** → **Add data source**
2. Select **InfluxDB**
3. **URL**: `http://influxdb:8086` (use container name, not localhost)
4. **Query Language**: **Flux**
5. **Organization**: `myorg`
6. **Token**: Paste your API token
7. **Default Bucket**: `ai_metrics`
8. Click **Save & Test** → should show green success ✅

### Step 8: Build Dashboard

1. Click **+** → **New Dashboard** → **Add new panel**
2. Switch to **Code** mode in query editor
3. Paste this Flux query:

```flux
from(bucket: "ai_metrics")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "ai_model_metrics")
  |> filter(fn: (r) => r._field == "latency_ms")
  |> aggregateWindow(every: 1m, fn: mean)
```

4. Click **Run query**
5. Add more panels for `accuracy`, `memory_mb`, `error_rate`, etc.
6. Click **Save dashboard**

### Step 9: Set Up Alerts

1. Click **🔔 Alerting** → **Alert rules** → **New alert rule**
2. **Condition**: `accuracy` IS BELOW `0.80`
3. **Evaluate**: every `1 minute` for `5 minutes`
4. **Notification channel**: Email, Slack, PagerDuty, etc.
5. Click **Save rule**

---

## 📊 Example Dashboard Metrics

| Panel | Metric | Description |
|-------|--------|-------------|
| Model Accuracy | `accuracy` | Track model performance over time |
| Inference Latency | `latency_ms` | Monitor prediction speed |
| Predictions/min | `batch_size` | Measure throughput |
| Memory Usage | `memory_mb` | Detect memory leaks |
| Error Rate | `error_rate` | Track failed predictions |

---

## 🐳 Docker Commands Cheat Sheet

```bash
# Start all containers
docker start influxdb telegraf grafana

# Stop all containers
docker stop influxdb telegraf grafana

# View logs
docker logs telegraf
docker logs influxdb

# Remove containers (keeps data)
docker rm influxdb telegraf grafana

# Full cleanup (removes data!)
docker volume rm influxdb-data influxdb-config grafana-data
```

---

## 📁 Project Structure

```
ai-monitoring/
├── README.md           # This file
├── telegraf.conf       # Telegraf configuration
└── monitor.py          # Python monitoring wrapper
```

---

## 🔧 Troubleshooting

### "Connection refused" error

- **Check containers are running**: `docker ps`
- **Verify network**: `docker network inspect monitoring`
- **Use container names**: Use `http://influxdb:8086`, not `localhost:8086` (from Grafana)

### No data in Grafana

- **Run your Python script**: `python monitor.py`
- **Check InfluxDB**: Go to `http://localhost:8086` → Data Explorer → verify data exists
- **Check Telegraf logs**: `docker logs telegraf`

### TOML syntax error

- **File encoding**: Ensure `telegraf.conf` is UTF-8 without BOM
- **Token format**: Make sure token is a single line with no quotes inside quotes

---

## 🛠️ Configuration Files

### telegraf.conf

Minimal configuration that:
- Collects metrics every 10 seconds
- Listens on port 8080 for HTTP metrics
- Forwards to InfluxDB using your API token

### monitor.py

Python wrapper that:
- Connects to InfluxDB
- Wraps any model's `predict()` call
- Measures latency, memory, accuracy
- Sends metrics to InfluxDB automatically

---

## 🤝 Contributing

Issues and pull requests welcome! This is a starter template — customize it for your needs.

---

## 📜 License

MIT License - This is created for educational purpose only.

---

## 🔗 Resources

- [InfluxDB Documentation](https://docs.influxdata.com/influxdb/v2/)
- [Telegraf Plugins](https://docs.influxdata.com/telegraf/latest/plugins/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Flux Query Language](https://docs.influxdata.com/flux/latest/)

---

**Built with ❤️ by Thetips4you**
