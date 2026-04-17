import express from "express";
import prisma from "../lib/prisma.js";
import axios from "axios";

const router = express.Router();

const ML_URL = process.env.ML_URL || 'http://127.0.0.1:8000';

// GET /api/weather/live/{zone_id}
router.get("/live/:zone_id", async (req, res) => {
  const { zone_id } = req.params;
  try {
    const zone = await prisma.zone.findUnique({ where: { id: zone_id } });
    if (!zone) return res.status(404).json({ error: "Zone not found" });

    // Directly call the Python ML backend Pipeline
    const mlResponse = await axios.get(`${ML_URL}/orchestrator/pipeline/weather/live/${zone_id}`);
    
    // Create Weather Event directly from backend Orchestrator output
    const event = await prisma.weatherEvent.create({
      data: {
        zoneId: zone.id,
        weatherType: mlResponse.data.weather_type || "UNKNOWN",
        intensity: mlResponse.data.intensity || 0.0,
        confidenceScore: mlResponse.data.confidence || 1.0,
      }
    });

    res.json({ event, live_data: mlResponse.data });
  } catch (error) {
    console.error("Live weather fetch error:", error.message);
    res.status(500).json({ error: "Failed to fetch live weather" });
  }
});

// GET /api/weather/user/{user_id}
router.get("/user/:user_id", async (req, res) => {
  const { user_id } = req.params;
  try {
    const worker = await prisma.worker.findUnique({
      where: { id: user_id },
      include: { userLocation: true }
    });
    
    if (!worker) return res.status(404).json({ error: "User not found" });

    const payload = {
      user_id,
      gps_coordinates: worker.userLocation?.gpsCoordinates || null,
      zone_id: worker.zoneId
    };

    const mlResponse = await axios.post(`${ML_URL}/orchestrator/pipeline/weather/user`, payload);
    
    res.json(mlResponse.data);
  } catch (error) {
    console.error("User weather fetch error:", error.message);
    res.status(500).json({ error: "Failed to fetch user localized weather" });
  }
});

// GET /api/weather/forecast/5day/:loc_id - AccuWeather Core API Integration
router.get("/forecast/5day/:loc_id", async (req, res) => {
  const { loc_id } = req.params;
  const apiKey = process.env.ACCUWEATHER_API_KEY;
  
  if (!apiKey) {
    console.warn("⚠️ ACCUWEATHER_API_KEY is missing! Using dynamic mocked fallback to prevent demo crash.");
    // Simulated AccuWeather 5-day response for Hackathon Demo
    return res.json({
      Headline: { Text: "Heavy Monsoon Rains Expected", Category: "rain" },
      DailyForecasts: Array.from({length: 5}).map((_, i) => ({
        Date: new Date(Date.now() + i * 86400000).toISOString(),
        Temperature: { Minimum: { Value: 24, Unit: "C" }, Maximum: { Value: 32, Unit: "C" } },
        Day: { IconPhrase: i === 1 ? "Thunderstorms" : "Partly sunny", HasPrecipitation: i === 1 },
        Night: { IconPhrase: "Clear" },
        _demo: true,
        _simulated: true
      }))
    });
  }

  try {
    const accRes = await axios.get(`https://dataservice.accuweather.com/forecasts/v1/daily/5day/${loc_id}`, {
      params: { apikey: apiKey, metric: true }
    });
    res.json(accRes.data);
  } catch (error) {
    console.error("AccuWeather fetch error:", error.message);
    res.status(500).json({ error: "Failed to fetch AccuWeather data", reason: error.message });
  }
});

export default router;
