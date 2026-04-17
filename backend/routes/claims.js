import express from "express";
import prisma from "../lib/prisma.js";
import { requireAuth } from "../middleware/authMiddleware.js";

const router = express.Router();

// GET /api/claims/my
// Returns all claims for the authenticated worker from the database.
// This serves as a reliable fallback if direct Firestore access is blocked.
router.get("/my", requireAuth, async (req, res) => {
  const workerId = req.user.workerId;
  
  try {
    const claims = await prisma.claim.findMany({
      where: { workerId },
      orderBy: { createdAt: 'desc' },
      include: {
        policy: true,
        triggerEvent: true
      }
    });
    
    // Map to a structure consistent with what the frontend expects
    const formattedClaims = claims.map(c => ({
      id: c.id,
      status: c.status,
      amount: c.payoutAmount,
      createdAt: c.createdAt,
      type: c.triggerEvent?.triggerType || "Weather Disruption",
      payoutAmount: c.payoutAmount
    }));

    res.json(formattedClaims);
  } catch (error) {
    console.error("Error fetching my claims:", error.message);
    res.status(500).json({ error: "Failed to fetch claims from database" });
  }
});

export default router;
