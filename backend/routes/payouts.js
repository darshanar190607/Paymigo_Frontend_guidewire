import express from "express";
import prisma from "../lib/prisma.js";
import axios from "axios";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = express.Router();

// POST /api/payouts/claim/{payout_id}
router.post("/claim/:weather_event_id", requireAuth, async (req, res) => {
  const { weather_event_id } = req.params;
  const userId = req.user.workerId;
  
  try {
    const weatherEvent = await prisma.weatherEvent.findUnique({ where: { id: weather_event_id } });
    if (!weatherEvent) return res.status(404).json({ error: "Weather event not found" });

    // ML Payout Orchestrator evaluates the claim
    const mlResponse = await axios.post(`http://127.0.0.1:8000/orchestrator/pipeline/payout/validate`, {
      user_id: userId,
      weather_event_id: weather_event_id,
      intensity: weatherEvent.intensity,
      weather_type: weatherEvent.weatherType
    });

    const trigger = await prisma.payoutTrigger.create({
      data: {
        userId,
        weatherEventId: weather_event_id,
        amount: mlResponse.data.amount || 0,
        decision: mlResponse.data.decision || "REJECTED",
        confidence: mlResponse.data.confidence || 0.0,
        status: mlResponse.data.decision === "APPROVED" ? "PENDING_TRANSFER" : "DECLINED"
      }
    });

    res.json(trigger);
  } catch (error) {
    console.error("Claim validation error:", error.message);
    res.status(500).json({ error: "Failed to validate claim against ML Orchestrator" });
  }
});

export default router;
