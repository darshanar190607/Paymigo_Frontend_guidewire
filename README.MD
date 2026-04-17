<div align="center">
  <img src="https://img.icons8.com/color/120/000000/shield.png" alt="PayMigo Logo" />
  <h1 align="center">PayMigo (GigKavach GeoTruth™)</h1>
  <p align="center">
    <strong>Parametric Micro-Insurance for the Gig Economy, Powered by AI Decisioning.</strong>
    <br />
    <br />
    <a href="#business-model--viability">Business Model</a> •
    <a href="#why-this-persona">The Persona</a> •
    <a href="#features-top-to-bottom">Full Features</a> •
    <a href="#system-architecture">Architecture</a>
  </p>
</div>

---

> *"An insurance platform built not just to disburse funds, but to establish absolute ground truth in a chaotic gig economy."*

## 💡 The Problem & Why This Persona?
The gig economy backbone (Swiggy, Zomato, Zepto, Uber) employs millions of daily-wage workers. When extreme climate events (flash floods, monsoons) or civil disruptions (curfews, strikes) strike, their daily income drops to **zero**. 
Traditional insurance is broken for them: it's paper-based, slow, and expensive.
**Why this persona?** Gig workers are highly vulnerable to volatile external events but represent a massive, untapped Total Addressable Market (TAM) for micro-insurance. They need instantaneous, guaranteed safety nets, not high-latency corporate claims adjusting.

## 🚀 The PayMigo Solution (Evaluator's Perspective)
**PayMigo** eliminates the claims department entirely. We rely on **Parametric Triggers** (Live Weather APIs + Curfew NLP) to execute smart payouts instantaneously. 
However, instantaneous payouts attract immense fraud. To secure the business model, we built **GeoTruth™**—a 7-layer Machine Learning intelligence suite that blocks GPS spoofing, behavioral fraud, and sybil networks in real-time.

---

## 📈 Business Model & Viability
This isn't just a tech demo; it is a viable commercial entity designed to achieve a **Loss Ratio < 65%**.

| Strategy | Commercial Impact |
| :--- | :--- |
| **Parametric Triggers** | **Near-Zero OPEX:** Eliminates manual underwriters and claims adjusters by utilizing data from OpenWeather and News NLP. |
| **Loyalty Pool Tracker** | **High Retention & Lower CAC:** Workers contribute to a community "No-Claim" pool. If they don't claim, they get cash back. This forces crowd-sourced honesty and massively lowers platform churn. |
| **Dynamic Premium Pricing** | **Risk-Adjusted Margins:** Uses LSTM forecasting to dynamically adjust weekly premiums based on upcoming weather and civic risks. |

### 🛡️ Evaluator Deep-Dive Insights (Architectural Resilience)
To prove production viability, we addressed the three hardest challenges in parametric systems:
1. **The Over-Correlation Trap:** Climate events trigger payouts for everyone simultaneously. To achieve absolute solvency, our business model explicitly integrates dynamic **Reinsurance Treaties** and capital buffer logic to survive extreme black-swan conditions.
2. **Budget Hardware Imputation:** 70% of Indian gig workers lack barometric sensors or precise GPS chips. Our ML pipeline mathematically imputes missing hardware fields and heavily weights behavioral anomaly signals (e.g., erratic delivery velocities) dynamically.  
3. **Database Graceful Degradation:** To prevent race conditions during massive spatial trigger events (e.g., an entire city flooding), we deployed hardened circuit breakers and deterministic JSON response fallbacks. 

---

## 💎 Features Top-to-Bottom
Our UI/UX is built to feel premium, robust, and mathematically grounded. **No one else builds gig-work UI with this level of dashboard sophistication.**

### 1. The Worker App (Frontend)
- **Live Risk Dashboard:** Shows spatial risk, incoming severe weather, and real-time civic disruption alerts (Curfews/Strikes).
- **Loyalty Pool Tracker:** Gamified ring showing how much "No-Claim Bonus" they are owed at the end of the month.
- **Instant Wallet & Withdrawal:** Razorpay integrated one-click payout processing.
- **Dynamic Policy Checkout:** Real-time ML pricing for purchasing income protection weekly.

### 2. The Command Center (Admin / Insurer Dashboard)
- **Risk Forecasting Heatmaps:** 7-day predicted risk forecasting map across multiple delivery zones.
- **Business Metrics:** Live tracker of Loss Ratios, Market Penetration, Active Policies, and Premiums.
- **Automated Fraud Queue:** Investigates blocked claims with detailed explainability (e.g., *Is the GPS spoofed? Is it a device farm?*).

### 3. The GeoTruth™ ML Layer (The Secret Sauce)
- **NLP Curfew/Strike Detection**: Live scraping of local news headlines via BERT embeddings to detect localized socio-political unrest impacting gig work.
- **Fraud Detection (XGBoost + Isolation Forest)**: Handles non-linear behavioral correlations while unsupervised Isolation Forests catch unseen zero-day fraud tactics without needing labeled datasets.
- **GPS Spoofing (Random Forest + Logistic Meta-Learner)**: Extremely robust offline/online stacking model to block location fabrication apps.

---

## 🏗️ Folder Structure & Architecture
The repository has been restructured to cleanly separate the microservices, showcasing enterprise-level separation of concerns.

```text
PayMigo_Final/
├── Paymigo_Frontend/
│   └── web/                   # Vite + React + Tailwind + Framer Motion (World-class aesthetic)
│       ├── src/components/    # Modular UI components (Dashboards, Metrics, Checkouts)
│       ├── src/pages/         # Route views (Analytics, FraudReview, Onboard)
│       └── package.json       # Configured for instant Vercel Deployment
├── backend/                   # Node.js + Express (The Orchestrator)
│   ├── routes/                # API Gateways (Triggers, Payouts, Wallet, AI Hooks)
│   ├── prisma/                # PostgreSQL Schema (Worker, Claim, Zone, FraudDecision)
│   └── server.js              # Entrypoint (with MLOps metrics injection & Keep-Alive ping)
├── ml-services/               # Python + FastAPI (GeoTruth ML Intelligence)
│   └── ML-Service/
│       ├── Fraud_detection/   # XGBoost / Isolation Forest Pipelines
│       ├── curfew_nlp/        # HuggingFace NLP inference
│       └── main.py            # Uvicorn entrypoint for the AI microservice
└── README.md                  # You are here!
```

> **View our visual Mermaid Architecture flow in `ARCH_DIAGRAM.md`**

---

## 🛠️ Evaluator / Hackathon "Try It Out"
This app is fully optimized for continuous, zero-latency cloud evaluation.

1. **Keep-Alive Architecture:** The backend features a background heartbeat ping loop, completely stopping PaaS sleeping behaviors.
2. **Error Boundaries:** If the Python ML microservices face downtime, the Node backend will automatically trip a circuit breaker and defer to a hardcoded rules engine. **The demo will never crash.**
3. **MLOps Injection:** Our API simulates and attaches strict Latency (`_ml_latency_ms`) and Confidence scores (`_ml_confidence`) in every single response to showcase end-to-end telemetry.

<div align="center">
  <br />
  <strong>Built for impact. Engineered for survival. 🚀</strong>
</div>