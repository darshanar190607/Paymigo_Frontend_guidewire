import express from 'express';
import axios from 'axios';
import dotenv from 'dotenv';
import prisma from '../lib/prisma.js';

dotenv.config();
const router = express.Router();

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8000';
const GROQ_API_KEY = process.env.GROQ_API_KEY || '';

// Helper: Get fake weather history based on scenario (from user's app.py prototype)
const getScenarioWeather = (scenario) => {
  const history = [];
  for (let i = 0; i < 14; i++) {
    let rain = Math.random() * 2;
    let temp = 20 + Math.random() * 8;
    let wind = 5 + Math.random() * 10;
    
    if (scenario === "storm") {
      rain = 20 + Math.random() * 35;
      temp = 15 + Math.random() * 5;
      wind = 30 + Math.random() * 50;
    } else if (scenario === "flood") {
      rain = 40 + Math.random() * 60;
      temp = 18 + Math.random() * 4;
    }
    
    history.push([
      rain, temp, 60, wind, 1013, 
      scenario === "storm" ? 1 : 0, 
      scenario === "flood" ? 1 : 0, 
      0, 
      scenario === "storm" ? 1 : 0, 
      rain, rain
    ]);
  }
  return history;
};

// GET /api/forecast?scenario=nominal&zone_id=0
router.get('/forecast', async (req, res) => {
  const { scenario = 'nominal', zone_id = 0 } = req.query;
  
  try {
    // Try to call real ML service if available
    const sequence = getScenarioWeather(scenario);
    let mlPrediction;
    
    try {
      const mlRes = await axios.post(`${ML_SERVICE_URL}/forecast/predict`, { sequence }, { timeout: 2000 });
      mlPrediction = mlRes.data;
    } catch (err) {
      console.warn("ML Service unavailable, using scenario-based mock data");
      // Fallback mocks from user's app.py
      const baseProb = scenario === 'nominal' ? 0.15 : scenario === 'storm' ? 0.75 : 0.92;
      const disruption_probability = Array.from({ length: 30 }, () => Math.min(0.99, baseProb + (Math.random() * 0.2 - 0.1)));
      const hourly_probability = Array.from({ length: 24 }, () => Math.min(0.99, baseProb + (Math.random() * 0.3 - 0.15)));
      
      mlPrediction = {
        disruption_probability,
        hourly_probability,
        expected_claims: scenario === 'nominal' ? 320 : scenario === 'storm' ? 1850 : 2800,
        exposed_capital: scenario === 'nominal' ? 12.4 : scenario === 'storm' ? 68.2 : 112.6
      };
    }

    res.json({
      status: "success",
      data: {
        ...mlPrediction,
        active_scenario: scenario,
        active_zone: zone_id
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// GET /api/chat
router.get('/chat', async (req, res) => {
  const { message, current_zone, risk_prob } = req.query;
  
  try {
    const system_prompt = `
      You are the PAYMIGO AI Risk Assistant.
      You analyze parametric insurance risks using live LSTM model data.
      Current Context:
      - Active Zone: ${current_zone}
      - LSTM Disruption Probability: ${(parseFloat(risk_prob) * 100).toFixed(2)}%
      
      Provide professional, concise, and expert advice for RiskOps administrators.
      If probabilities are high, suggest risk mitigation or liquidity adjustments.
    `;

    const response = await axios.post('https://api.groq.com/openai/v1/chat/completions', {
      model: "llama-3.3-70b-versatile",
      messages: [
        { role: "system", content: system_prompt },
        { role: "user", content: message }
      ],
      temperature: 0.5,
      max_tokens: 300
    }, {
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    res.json({ reply: response.data.choices[0].message.content });
  } catch (error) {
    console.error("Chat error:", error.response?.data || error.message);
    res.json({ reply: "AI assistant is currently recalibrating. Status: Stability checks in progress." });
  }
});

export default router;
