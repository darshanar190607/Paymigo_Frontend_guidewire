import express from "express";
import axios from "axios";
import { getZoneFeatures } from "../lib/csvLoader.js";

const router = express.Router();

router.post("/calculate", async (req, res) => {
  const { age, jobType, experienceYears, zone } = req.body;
  
  try {
    const zoneName = zone || "Unknown Zone";
    let cityName = "unknown";
    if (zoneName.includes('Coimbatore')) cityName = "coimbatore";
    else if (zoneName.includes('Chennai')) cityName = "chennai";
    else if (zoneName.includes('Bangalore')) cityName = "bengaluru";
    else if (zoneName.includes('Mumbai')) cityName = "mumbai";
    else cityName = zoneName.split(' ')[0].toLowerCase().replace(/ /g, '_');
    
    let mlPremium = 69;
    let clusterRisk = 1.0;
    let aiFactors = [];

    try {
      const stats = await getZoneFeatures(cityName);
      
      if (stats.zone_risk_tier !== null) {
        clusterRisk = stats.zone_risk_tier;
      } else {
        const clusterRes = await axios.post("http://127.0.0.1:8000/cluster/predict", stats);
        clusterRisk = clusterRes.data.zone_risk_tier || 1.0;
      }

      if (clusterRisk > 1.2) {
        aiFactors.push('High historical risk profile', '+Risk premium applied');
      } else if (clusterRisk < 1.0) {
        aiFactors.push('Low historical risk profile', '-Risk discount applied');
      } else {
        aiFactors.push('Standard risk profile');
      }

      const premiumRes = await axios.post("http://127.0.0.1:8000/premium/predict", {
        age: age ? parseInt(age) : 30,
        zone_risk_tier: clusterRisk,
        job_type: jobType || "Delivery",
        experience_years: experienceYears ? parseInt(experienceYears) : 0,
        incident_history: 0
      });
      mlPremium = premiumRes.data.premium || 69;

    } catch (mlErr) {
      console.error("ML prediction failed:", mlErr.message);
      aiFactors.push('Pricing ML service offline', 'Default rating applied');
    }

    res.json({
      basePremium: Math.round(mlPremium),
      riskMultiplier: clusterRisk,
      aiFactors
    });
  } catch (err) {
    console.error("Error calculating premium:", err);
    res.status(500).json({ error: "Failed to calculate premium" });
  }
});

export default router;