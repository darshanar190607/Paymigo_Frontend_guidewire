import express from 'express';
import axios from 'axios';
import prisma from '../lib/prisma.js';

const router = express.Router();
const ML = 'http://127.0.0.1:8000';

// ── Helper: map fraud_probability → trust score (0–100) ──────────────────────
// Model outputs 0.0–1.0 (fraud probability).
// We invert: low fraud_prob = high trust score.
// Trust score = Math.round((1 - fraud_prob) * 100)
function toTrustScore(fraudProb) {
  return Math.round((1 - Math.min(Math.max(fraudProb, 0), 1)) * 100);
}

// ── Helper: derive timeline step from claimStatus ─────────────────────────────
function toTimelineState(claimStatus) {
  switch (claimStatus) {
    case 'approved': return 4;
    case 'review':   return 3;
    case 'processing': return 2;
    default:         return 1;
  }
}

// ── Helper: map raw feature scores → user-friendly signals ───────────────────
function buildSignals(payload, fraudData) {
  const prob  = fraudData.fraud_probability;
  const isFlagged = (score, threshold = 0.5) => score >= threshold;

  return [
    {
      name: 'GPS Location',
      status: isFlagged(payload.gps_spoof_probability, 0.4) ? 'Flagged' : payload.gps_spoof_probability > 0.2 ? 'Approximate' : 'Valid',
      description: payload.gps_spoof_probability < 0.2
        ? 'Location data is consistent with your registered zone.'
        : payload.gps_spoof_probability < 0.4
        ? 'Location signal is slightly uncertain — using nearby reference points.'
        : 'Location data shows unusual patterns. We are investigating.',
      score: 1 - payload.gps_spoof_probability,
    },
    {
      name: 'Behavioral Pattern',
      status: isFlagged(payload.behavioral_baseline_deviation, 0.6) ? 'Flagged' : payload.behavioral_baseline_deviation > 0.3 ? 'Approximate' : 'Valid',
      description: payload.behavioral_baseline_deviation < 0.3
        ? 'Your activity matches normal delivery patterns.'
        : payload.behavioral_baseline_deviation < 0.6
        ? 'Some unusual activity detected — within acceptable range.'
        : 'Activity patterns deviate significantly from your baseline.',
      score: 1 - payload.behavioral_baseline_deviation,
    },
    {
      name: 'Network Environment',
      status: isFlagged(payload.network_fraud_ring_score, 0.5) ? 'Flagged' : payload.network_fraud_ring_score > 0.25 ? 'Approximate' : 'Valid',
      description: payload.network_fraud_ring_score < 0.25
        ? 'Network environment is clean and verified.'
        : payload.network_fraud_ring_score < 0.5
        ? 'Network has minor anomalies — environment check in progress.'
        : 'Network activity shows coordinated patterns. Additional check initiated.',
      score: 1 - payload.network_fraud_ring_score,
    },
    {
      name: 'Claim Timing',
      status: isFlagged(payload.claim_timing_anomaly, 0.5) ? 'Flagged' : payload.claim_timing_anomaly > 0.3 ? 'Approximate' : 'Valid',
      description: payload.claim_timing_anomaly < 0.3
        ? 'Claim submitted at an expected time window.'
        : payload.claim_timing_anomaly < 0.5
        ? 'Claim timing is slightly outside normal window.'
        : 'Claim was submitted at an unusual time — reviewing context.',
      score: 1 - payload.claim_timing_anomaly,
    },
    {
      name: 'Delivery Route',
      status: isFlagged(payload.delivery_speed_anomaly, 0.6) ? 'Flagged' : payload.delivery_speed_anomaly > 0.3 ? 'Approximate' : 'Valid',
      description: payload.delivery_speed_anomaly < 0.3
        ? 'Delivery speed and route metrics are consistent.'
        : payload.delivery_speed_anomaly < 0.6
        ? 'Minor route deviation detected — within normal variance.'
        : 'Delivery speed shows an anomaly. Verifying route data.',
      score: 1 - payload.delivery_speed_anomaly,
    },
    {
      name: 'Barometric Check',
      status: payload.barometric_consistency < 0.4 ? 'Flagged' : payload.barometric_consistency < 0.7 ? 'Approximate' : 'Valid',
      description: payload.barometric_consistency >= 0.7
        ? 'Environmental sensors match claim conditions.'
        : payload.barometric_consistency >= 0.4
        ? 'Sensor data is partially consistent with reported conditions.'
        : 'Environmental data does not match reported conditions.',
      score: payload.barometric_consistency,
    },
    {
      name: 'Claim History',
      status: isFlagged(payload.duplicate_claim_score, 0.5) ? 'Flagged' : payload.duplicate_claim_score > 0.25 ? 'Approximate' : 'Valid',
      description: payload.duplicate_claim_score < 0.25
        ? 'No duplicate or suspicious claim patterns found.'
        : payload.duplicate_claim_score < 0.5
        ? 'Slightly elevated claim frequency — within policy limits.'
        : 'Claim pattern analysis flagged for further review.',
      score: 1 - payload.duplicate_claim_score,
    },
  ];
}

// ── Helper: overall decision from trust score ─────────────────────────────────
function toDecision(fraudProb, isExistingClaim) {
  if (fraudProb < 0.35)  return { claimStatus: 'approved',    actionType: 'dashboard', payout: null };
  if (fraudProb < 0.75)  return { claimStatus: 'review',      actionType: 'soft_proof', payout: null };
  return                        { claimStatus: 'processing',   actionType: 'track',     payout: null };
}

// ── POST /geotruth/verify ─────────────────────────────────────────────────────
// Body: claimId (optional) + any known feature values from the frontend/claim
router.post('/verify', async (req, res) => {
  const { claimId, workerId, ...rawFeatures } = req.body;

  // ── 1. Build fraud model payload with sensible defaults ──────────────────
  const featureDefaults = {
    zone_risk_tier:               1.0,
    claim_frequency_30d:          0.0,
    claim_amount_zscore:          0.0,
    location_jump_count:          0.0,
    gps_spoof_probability:        0.0,
    policy_tenure_weeks:          4.0,
    earnings_deviation:           0.0,
    claim_timing_anomaly:         0.0,
    peer_claim_correlation:       0.0,
    device_change_count:          0.0,
    login_anomaly_score:          0.0,
    route_deviation_score:        0.0,
    delivery_speed_anomaly:       0.0,
    duplicate_claim_score:        0.0,
    network_fraud_ring_score:     0.0,
    barometric_consistency:       1.0,
    zone_transition_anomaly:      0.0,
    claim_photo_similarity_score: 0.0,
    platform_switch_frequency:    0.0,
    behavioral_baseline_deviation: 0.0,
  };

  // If workerId given, try to enrich from DB
  let workerMeta = null;
  if (workerId) {
    try {
      workerMeta = await prisma.worker.findFirst({
        where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
        include: { zone: true, policies: { where: { isActive: true }, take: 1 } },
      });
      if (workerMeta) {
        featureDefaults.zone_risk_tier      = workerMeta.zone?.riskTier || 1;
        featureDefaults.policy_tenure_weeks = workerMeta.loyaltyWeeks   || 4;
      }
    } catch (_) {}
  }

  const payload = { ...featureDefaults, ...rawFeatures };

  // ── 2. Call ML fraud endpoint ────────────────────────────────────────────
  let fraudData = { is_fraud: false, fraud_probability: 0.15, threshold: 0.5 };
  let mlOnline  = false;

  try {
    const mlRes = await axios.post(`${ML}/fraud/detect`, payload, { timeout: 6000 });
    fraudData   = mlRes.data;
    mlOnline    = true;
  } catch (_) {
    // ML offline — use default (low-risk) mock so UI never hard-crashes
  }

  // ── 3. Derive UX-safe values ─────────────────────────────────────────────
  const fraudProb  = fraudData.fraud_probability;
  const trustScore = toTrustScore(fraudProb);

  const confidence = fraudProb < 0.25 ? 'High' : fraudProb < 0.60 ? 'Medium' : 'Low';
  const signals    = buildSignals(payload, fraudData);
  const decision   = toDecision(fraudProb);
  const timeline   = toTimelineState(decision.claimStatus);

  // ── 4. Respond ───────────────────────────────────────────────────────────
  res.json({
    claimId:       claimId || null,
    claimStatus:   decision.claimStatus,
    trustScore,                          // 0–100, higher = more trusted
    fraudScore:    parseFloat(fraudProb.toFixed(4)),  // raw 0–1 (internal only, label it "Trust Index" on frontend)
    confidence,
    signals,
    timelineState: timeline,
    actionType:    decision.actionType,
    payout:        decision.payout,
    meta: {
      mlOnline,
      threshold: fraudData.threshold,
      lastChecked: new Date().toISOString(),
    },
  });
});

// ── GET /geotruth/verify/:claimId ─────────────────────────────────────────────
// Lightweight re-fetch for a known claim (re-runs ML with stored features)
router.get('/verify/:claimId', async (req, res) => {
  const { claimId } = req.params;
  // For now return a mock-safe processing state so the frontend can render
  res.json({
    claimId,
    claimStatus: 'processing',
    trustScore:  72,
    confidence:  'Medium',
    signals: [
      { name: 'GPS Location',      status: 'Valid',       description: 'Location data is consistent with your registered zone.',    score: 0.88 },
      { name: 'Behavioral Pattern',status: 'Valid',       description: 'Your activity matches normal delivery patterns.',           score: 0.82 },
      { name: 'Network Environment',status: 'Approximate',description: 'Network has minor anomalies — environment check in progress.', score: 0.65 },
      { name: 'Claim Timing',      status: 'Valid',       description: 'Claim submitted at an expected time window.',               score: 0.90 },
      { name: 'Delivery Route',    status: 'Approximate', description: 'Minor route deviation detected — within normal variance.',  score: 0.71 },
      { name: 'Barometric Check',  status: 'Valid',       description: 'Environmental sensors match claim conditions.',             score: 0.95 },
      { name: 'Claim History',     status: 'Valid',       description: 'No duplicate or suspicious claim patterns found.',         score: 0.92 },
    ],
    timelineState: 2,
    actionType:    'track',
    payout:        null,
    meta: { mlOnline: false, threshold: 0.5, lastChecked: new Date().toISOString() },
  });
});

export default router;
