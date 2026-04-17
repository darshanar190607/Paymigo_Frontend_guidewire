import express from 'express';
import prisma from '../lib/prisma.js';
import { requireAuth } from '../middleware/authMiddleware.js';

const router = express.Router();

// ── Mock Fraud Detection Scenarios ────────────────────────────────────────────

const FRAUD_SCENARIOS = {
  // Low risk - normal worker
  normal: {
    fraudScore: 0.12,
    riskLevel: 'LOW',
    flags: [],
    recommendation: 'APPROVE',
    message: 'All verification checks passed. Worker profile looks legitimate.',
  },
  
  // Medium risk - suspicious patterns
  suspicious: {
    fraudScore: 0.58,
    riskLevel: 'MEDIUM',
    flags: [
      'Multiple claims in short timeframe',
      'Location jump detected',
      'Claim timing outside normal hours',
    ],
    recommendation: 'REVIEW',
    message: 'Some suspicious patterns detected. Manual review recommended.',
  },
  
  // High risk - likely fraud
  fraud: {
    fraudScore: 0.89,
    riskLevel: 'HIGH',
    flags: [
      'GPS spoofing detected',
      'Device fingerprint mismatch',
      'Claim pattern matches known fraud ring',
      'Barometric pressure inconsistent',
      'Network topology anomaly',
    ],
    recommendation: 'REJECT',
    message: 'High fraud probability. Multiple red flags detected.',
  },
  
  // GPS spoofing specific
  gps_spoof: {
    fraudScore: 0.76,
    riskLevel: 'HIGH',
    flags: [
      'Mock location provider detected',
      'GPS coordinates inconsistent with cell tower',
      'Altitude discrepancy with barometric data',
    ],
    recommendation: 'REJECT',
    message: 'GPS spoofing detected. Location data is not trustworthy.',
  },
  
  // Social ring fraud
  ring_fraud: {
    fraudScore: 0.92,
    riskLevel: 'CRITICAL',
    flags: [
      'Part of coordinated fraud ring',
      'Synchronized claims with 5+ workers',
      'Shared device fingerprints',
      'Identical claim patterns',
    ],
    recommendation: 'FREEZE',
    message: 'Critical: Worker is part of a fraud ring. Account frozen.',
  },
};

// ── POST /fraud-mock/detect ───────────────────────────────────────────────────
// Mock fraud detection endpoint for testing
router.post('/detect', requireAuth, async (req, res) => {
  const { workerId, claimId, scenario = 'normal' } = req.body;

  try {
    // Get worker data
    const worker = await prisma.worker.findFirst({
      where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
      include: {
        zone: true,
        claims: {
          orderBy: { createdAt: 'desc' },
          take: 10,
        },
      },
    });

    if (!worker) {
      return res.status(404).json({ error: 'Worker not found' });
    }

    // Select fraud scenario
    const fraudData = FRAUD_SCENARIOS[scenario] || FRAUD_SCENARIOS.normal;

    // Calculate dynamic fraud score based on worker history
    let adjustedScore = fraudData.fraudScore;
    
    // Increase score if multiple recent claims
    if (worker.claims.length > 5) {
      adjustedScore += 0.1;
    }

    // Increase score if high-risk zone
    if (worker.zone?.riskTier >= 3) {
      adjustedScore += 0.05;
    }

    // Cap at 1.0
    adjustedScore = Math.min(adjustedScore, 1.0);

    // Build response
    const response = {
      workerId: worker.id,
      claimId: claimId || null,
      fraudScore: parseFloat(adjustedScore.toFixed(2)),
      riskLevel: fraudData.riskLevel,
      flags: fraudData.flags,
      recommendation: fraudData.recommendation,
      message: fraudData.message,
      details: {
        workerName: worker.name,
        zone: worker.zone?.name || 'Unknown',
        totalClaims: worker.claims.length,
        accountAge: Math.floor((Date.now() - new Date(worker.createdAt).getTime()) / (1000 * 60 * 60 * 24)),
        lastClaimDate: worker.claims[0]?.createdAt || null,
      },
      timestamp: new Date().toISOString(),
      mockMode: true,
    };

    // If fraud detected, optionally create fraud decision record
    if (claimId && adjustedScore > 0.5) {
      try {
        await prisma.fraudDecision.create({
          data: {
            claimId,
            fraudScore: adjustedScore,
            decision: fraudData.recommendation,
            reviewedBy: 'MOCK_SYSTEM',
            notes: `Mock fraud detection: ${fraudData.message}`,
          },
        });
      } catch (err) {
        console.error('Failed to create fraud decision:', err);
      }
    }

    res.json(response);
  } catch (error) {
    console.error('Mock fraud detection error:', error);
    res.status(500).json({ error: 'Fraud detection failed' });
  }
});

// ── GET /fraud-mock/scenarios ─────────────────────────────────────────────────
// List available fraud scenarios for testing
router.get('/scenarios', (req, res) => {
  const scenarios = Object.keys(FRAUD_SCENARIOS).map(key => ({
    id: key,
    name: key.replace('_', ' ').toUpperCase(),
    fraudScore: FRAUD_SCENARIOS[key].fraudScore,
    riskLevel: FRAUD_SCENARIOS[key].riskLevel,
    recommendation: FRAUD_SCENARIOS[key].recommendation,
  }));

  res.json({
    scenarios,
    usage: 'POST /fraud-mock/detect with { workerId, scenario: "normal|suspicious|fraud|gps_spoof|ring_fraud" }',
  });
});

// ── POST /fraud-mock/batch-test ───────────────────────────────────────────────
// Test multiple scenarios at once
router.post('/batch-test', requireAuth, async (req, res) => {
  const { workerId } = req.body;

  if (!workerId) {
    return res.status(400).json({ error: 'workerId required' });
  }

  try {
    const results = {};

    for (const scenario of Object.keys(FRAUD_SCENARIOS)) {
      const testReq = { body: { workerId, scenario } };
      const testRes = {
        json: (data) => { results[scenario] = data; },
        status: () => testRes,
      };

      // Simulate detection for each scenario
      const fraudData = FRAUD_SCENARIOS[scenario];
      results[scenario] = {
        scenario,
        fraudScore: fraudData.fraudScore,
        riskLevel: fraudData.riskLevel,
        recommendation: fraudData.recommendation,
        flags: fraudData.flags,
      };
    }

    res.json({
      workerId,
      testResults: results,
      summary: {
        totalScenarios: Object.keys(results).length,
        highRiskCount: Object.values(results).filter(r => r.riskLevel === 'HIGH' || r.riskLevel === 'CRITICAL').length,
      },
    });
  } catch (error) {
    console.error('Batch test error:', error);
    res.status(500).json({ error: 'Batch test failed' });
  }
});

export default router;
