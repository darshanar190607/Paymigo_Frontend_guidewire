import express from "express";
import axios from "axios";

const router = express.Router();

// POST /api/trigger/scenario
router.post("/scenario", async (req, res) => {
  const { command } = req.body;
  
  if (!command) return res.status(400).json({ error: "Missing command string" });

  try {
    // Send comment tag to Testing Framework on ML Side
    const mlResponse = await axios.post(`http://127.0.0.1:8000/orchestrator/testing/parse`, {
      comment: command
    });
    
    // Simulate pipeline workflow manually internally if requested
    res.json(mlResponse.data);
  } catch (error) {
    console.error("Scenario execution error:", error.message);
    res.status(500).json({ error: "Failed to execute scenario via ML Orchestrator Testing Framework" });
  }
});

export default router;
