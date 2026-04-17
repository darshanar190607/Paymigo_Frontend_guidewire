import express from "express";
import prisma from "../lib/prisma.js";
import axios from "axios";
import { getZoneFeatures } from "../lib/csvLoader.js";

const router = express.Router();

// Create worker
router.post("/", async (req, res) => {
  const { phone, name, pincode } = req.body;

  try {
    const worker = await prisma.worker.create({
      data: { phone, name, pincode }
    });

    res.json(worker);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Onboard worker
router.put("/onboard", async (req, res) => {
  const { phone, name, pincode, zone, plan, age, jobType, experienceYears } = req.body;

  try {
    const zoneName = zone || "Unknown Zone";
    const zonePincode = pincode || "000000";
    
    // Upsert the zone based on pincode
    const zoneEntity = await prisma.zone.upsert({
      where: { pincode: zonePincode },
      update: { name: zoneName },
      create: {
        id: zoneName.toLowerCase().replace(/ /g, '_'),
        name: zoneName,
        city: zoneName.split(' ')[0],
        pincode: zonePincode,
        riskTier: 1,
        riskMultiplier: 1.0,
      }
    });

    let mlPremium = 69; // default fallback
    let clusterRisk = 1.0; 

    try {
      // 1. Get raw stats from CSV dictionary
      const stats = await getZoneFeatures(zoneEntity.id);
      
      // 2. Predict risk cluster
      const clusterRes = await axios.post("http://127.0.0.1:8000/cluster/predict", stats);
      // The ML returns e.g. {"cluster": 1, "risk_score": 1.25, "pca_coords": [...]}
      clusterRisk = clusterRes.data.risk_score || 1.0;

      // Update zone with ML risk multiplier dynamically
      await prisma.zone.update({
        where: { id: zoneEntity.id },
        data: { riskMultiplier: clusterRisk }
      });
      
      // 3. Predict premium via XGBoost model
      const premiumRes = await axios.post("http://127.0.0.1:8000/premium/predict", {
        age: age,
        zone_risk_tier: clusterRisk,
        job_type: jobType || "Delivery",
        experience_years: experienceYears,
        incident_history: 0
      });
      mlPremium = premiumRes.data.premium || 69;
    } catch (mlErr) {
      console.error("ML service failed. Defaulting premium:", mlErr.message);
    }

    // Base premium modifier based on plan
    if (plan === 'Pro') mlPremium += 20;
    if (plan === 'Premium') mlPremium += 50;

    // Update worker demographic and zone data
    const worker = await prisma.worker.update({
      where: { id: req.user.workerId },
      data: { 
        phone, 
        name, 
        pincode: zonePincode, 
        zoneId: zoneEntity.id,
        age: age || null,
        jobType: jobType || null,
        experienceYears: experienceYears || null
      }
    });
    
    // Create Policy utilizing the dynamically calculated ML premium
    if (plan) {
      await prisma.policy.create({
        data: {
          workerId: worker.id,
          tier: plan,
          weeklyPremium: Math.round(mlPremium),
          loyaltyPercent: 0,
          startDate: new Date()
        }
      });
    }

    res.json(worker);
  } catch (err) {
    if (err.code === 'P2002' && err.meta?.target?.includes('phone')) {
      return res.status(400).json({ error: "This phone number is already registered to another account." });
    }
    res.status(500).json({ error: err.message });
  }
});

// Get worker
router.get("/:id", async (req, res) => {
  const worker = await prisma.worker.findUnique({
    where: { id: req.params.id }
  });

  res.json(worker);
});

export default router;