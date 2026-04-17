import express from "express";
import cors from "cors";
import dotenv from "dotenv";

dotenv.config();

const app = express();

app.use(cors());
app.use(express.json());

// API Routes
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", message: "Paymigo API is live" });
});

// Workers
app.post("/api/workers/onboard", (req, res) => {
  res.json({ success: true, message: "Worker onboarded successfully" });
});

app.get("/api/workers/:id/dashboard", (req, res) => {
  res.json({
    worker: { name: "Ravi", zone: "Chennai-4", plan: "Pro" },
    wallet: { available: 1504, loyalty: 336, total: 1840 },
    status: "AMBER"
  });
});

// Wallet
app.post("/api/wallet/withdraw", (req, res) => {
  const { amount } = req.body;
  res.json({ success: true, transactionId: "TXN_" + Math.random().toString(36).substr(2, 9), amount });
});

// Insurer
app.get("/api/insurer/overview", (req, res) => {
  res.json({
    activePolicies: 12459,
    grossPremium: 1200000,
    claimsInitiated: 142,
    lossRatio: 32.4
  });
});

// Mock ML Premium Calculation
app.post("/api/premium/calculate", (req, res) => {
  const { city, zone } = req.body;
  let base = 69;
  if (city === "Chennai") base = 119;
  if (city === "Mumbai") base = 179;
  res.json({ premium: base, currency: "INR", period: "weekly" });
});

// Mock Weather Proxy
app.get("/api/weather/:city", (req, res) => {
  const { city } = req.params;
  res.json({
    city,
    temp: 28,
    condition: "Rainy",
    rainfall: 12.5,
    aqi: 45,
    riskLevel: "HIGH"
  });
});

// Real-time Triggers for Dashboard
app.get("/api/triggers", (req, res) => {
  const rainfall = (Math.random() * 15 + 5).toFixed(1); 
  const windSpeed = (Math.random() * 40 + 10).toFixed(1); 
  const waterLogging = (Math.random() * 30).toFixed(1); 
  
  const rainTriggered = parseFloat(rainfall) > 15;
  const windTriggered = parseFloat(windSpeed) > 45;
  const waterTriggered = parseFloat(waterLogging) > 20;
  
  const isTriggered = rainTriggered || windTriggered || waterTriggered;
  
  res.json({
    rainfall: parseFloat(rainfall),
    windSpeed: parseFloat(windSpeed),
    waterLogging: parseFloat(waterLogging),
    thresholds: {
      rainfall: 15,
      windSpeed: 45,
      waterLogging: 20
    },
    status: isTriggered ? "PAYOUT_TRIGGERED" : "MONITORING",
    triggerType: rainTriggered ? "HEAVY_RAIN" : windTriggered ? "HIGH_WIND" : waterTriggered ? "WATER_LOGGING" : "NONE",
    lastUpdated: new Date().toISOString(),
    zone: "Chennai-4"
  });
});

// AI-Powered Dynamic Premium Calculation
app.post("/api/ai/calculate-premium", async (req, res) => {
  const { zone } = req.body;
  const riskScores: Record<string, number> = {
    'Chennai Zone 4': 0.85,
    'Chennai Zone 2': 0.65,
    'Bangalore East': 0.45,
    'Mumbai West': 0.95,
  };

  const riskScore = riskScores[zone] || 0.5;
  const basePremium = 100;
  let adjustedPremium = basePremium * riskScore + 50;
  
  if (riskScore < 0.5) {
    adjustedPremium -= 2;
  }

  res.json({
    premium: Math.round(adjustedPremium),
    riskScore,
    factors: [
      riskScore > 0.7 ? "High water logging history" : "Safe zone history",
      "Predictive weather model: Moderate rain expected",
      "Zone-specific disruption probability: " + (riskScore * 100).toFixed(0) + "%"
    ]
  });
});

// Automated Zero-Touch Claim Trigger
app.post("/api/ai/trigger-payout", (req, res) => {
  const { rainfall, threshold } = req.body;
  
  if (rainfall > threshold) {
    res.json({
      success: true,
      message: "Automated payout triggered successfully",
      amount: 1500,
      reason: `Rainfall (${rainfall}mm) exceeded threshold (${threshold}mm)`
    });
  } else {
    res.status(400).json({ success: false, message: "Threshold not met" });
  }
});

export default app;
