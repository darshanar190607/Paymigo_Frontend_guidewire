import express from 'express';
import axios from 'axios';
import admin from 'firebase-admin';
import prisma from '../lib/prisma.js';

const router = express.Router();
const ML = process.env.ML_URL || 'http://127.0.0.1:8000';

// ── Decision engine ───────────────────────────────────────────────────────────
function computeDecision(fraudProb, spoofProb, trustScore) {
  if (spoofProb > 0.9)  return { decision: 'REVIEW',      riskLevel: 'CRITICAL', color: 'red'    };
  if (fraudProb > 0.8)  return { decision: 'REVIEW',      riskLevel: 'HIGH',     color: 'red'    };
  if (trustScore < 40)  return { decision: 'APPROVE',     riskLevel: 'LOW',      color: 'green'  };
  if (fraudProb > 0.5)  return { decision: 'SOFT_CHECK',  riskLevel: 'MEDIUM',   color: 'yellow' };
  return                       { decision: 'APPROVE',     riskLevel: 'LOW',      color: 'green'  };
}

// ── Build fraud signal cards ──────────────────────────────────────────────────
function buildFraudSignals(features, fraudProb, spoofProb) {
  return [
    {
      category: 'GPS Spoof',
      icon: 'Navigation',
      score: spoofProb,
      flags: [
        spoofProb > 0.4 && 'Location jump detected',
        spoofProb > 0.6 && 'No movement detected',
        features.gps_spoof_probability > 0.3 && 'GPS signal inconsistency',
      ].filter(Boolean),
      status: spoofProb > 0.6 ? 'FLAGGED' : spoofProb > 0.3 ? 'WARNING' : 'CLEAR',
    },
    {
      category: 'Behavior',
      icon: 'Activity',
      score: features.behavioral_baseline_deviation,
      flags: [
        features.claim_frequency_30d > 5 && `${features.claim_frequency_30d} claims in last 30 days`,
        features.claim_timing_anomaly > 0.5 && 'Unusual claim timing detected',
        features.earnings_deviation > 0.4 && 'Earnings deviation flagged',
      ].filter(Boolean),
      status: features.behavioral_baseline_deviation > 0.6 ? 'FLAGGED' : features.behavioral_baseline_deviation > 0.3 ? 'WARNING' : 'CLEAR',
    },
    {
      category: 'Network',
      icon: 'Wifi',
      score: features.network_fraud_ring_score,
      flags: [
        features.network_fraud_ring_score > 0.5 && 'Coordinated network activity',
        features.login_anomaly_score > 0.5 && 'Login anomaly detected',
        features.device_change_count > 3 && `${features.device_change_count} device changes`,
      ].filter(Boolean),
      status: features.network_fraud_ring_score > 0.6 ? 'FLAGGED' : features.network_fraud_ring_score > 0.3 ? 'WARNING' : 'CLEAR',
    },
    {
      category: 'Pattern',
      icon: 'BarChart2',
      score: features.duplicate_claim_score,
      flags: [
        features.duplicate_claim_score > 0.5 && 'Duplicate claim pattern detected',
        features.peer_claim_correlation > 0.6 && 'High peer claim correlation',
        features.claim_amount_zscore > 2 && 'Claim amount is statistical outlier',
      ].filter(Boolean),
      status: features.duplicate_claim_score > 0.6 ? 'FLAGGED' : features.duplicate_claim_score > 0.3 ? 'WARNING' : 'CLEAR',
    },
    {
      category: 'Timing',
      icon: 'Clock',
      score: features.claim_timing_anomaly,
      flags: [
        features.claim_timing_anomaly > 0.5 && 'Claim submitted outside normal window',
        features.platform_switch_frequency > 0.5 && 'Frequent platform switching',
      ].filter(Boolean),
      status: features.claim_timing_anomaly > 0.6 ? 'FLAGGED' : features.claim_timing_anomaly > 0.3 ? 'WARNING' : 'CLEAR',
    },
    {
      category: 'Social',
      icon: 'Users',
      score: features.peer_claim_correlation,
      flags: [
        features.peer_claim_correlation > 0.6 && 'Coordinated claims with peers',
        features.network_fraud_ring_score > 0.5 && 'Possible fraud ring involvement',
      ].filter(Boolean),
      status: features.peer_claim_correlation > 0.6 ? 'FLAGGED' : features.peer_claim_correlation > 0.3 ? 'WARNING' : 'CLEAR',
    },
  ];
}

// ── GET /fraud/claims ─────────────────────────────────────────────────────────
router.get('/claims', async (req, res) => {
  try {
    const db = admin.firestore();
    const { status, zone, limit = 50 } = req.query;

    let q = db.collection('claims').orderBy('createdAt', 'desc').limit(parseInt(limit));
    if (status && status !== 'ALL') q = q.where('status', '==', status);

    const snap = await q.get();
    const claims = snap.docs.map(d => {
      const data = d.data();
      // Deterministic fallback based on claim ID (no UI flicker on reload)
      const seed = parseInt(d.id.slice(-4), 16) / 65535;
      const fraudScore = data.fraudScore ?? parseFloat((seed * 0.4 + 0.05).toFixed(3));
      const spoofProb  = data.spoofProbability ?? parseFloat((seed * 0.3).toFixed(3));
      const trustScore = Math.round((1 - fraudScore) * 100);
      const { decision, riskLevel, color } = computeDecision(fraudScore, spoofProb, trustScore);

      return {
        id:          d.id,
        workerId:    data.workerId,
        workerName:  data.workerName  || 'Unknown Worker',
        zone:        data.workerZone  || 'Unknown Zone',
        type:        data.type        || 'Income Protection',
        amount:      data.amount      || 0,
        status:      data.status      || 'PENDING',
        fraudScore:  parseFloat(fraudScore.toFixed(3)),
        spoofProb:   parseFloat(spoofProb.toFixed(3)),
        trustScore,
        riskLevel,
        color,
        decision,
        createdAt:   data.createdAt?.toDate?.()?.toISOString() || new Date().toISOString(),
      };
    });

    // Sort by fraud score descending (most suspicious first)
    claims.sort((a, b) => b.fraudScore - a.fraudScore);

    res.json({ claims, total: claims.length });
  } catch (err) {
    console.error('GET /fraud/claims error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── GET /fraud/claims/:id ─────────────────────────────────────────────────────
router.get('/claims/:id', async (req, res) => {
  const { id } = req.params;
  try {
    const db  = admin.firestore();
    const ref = db.collection('claims').doc(id);
    const snap = await ref.get();

    if (!snap.exists) return res.status(404).json({ error: 'Claim not found.' });

    const data = snap.data();

    // Default feature payload for ML
    const features = {
      zone_risk_tier:               data.zoneRiskTier              ?? 1,
      claim_frequency_30d:          data.claimFrequency30d         ?? 1,
      claim_amount_zscore:          data.claimAmountZscore         ?? 0,
      location_jump_count:          data.locationJumpCount         ?? 0,
      gps_spoof_probability:        data.spoofProbability          ?? 0,
      policy_tenure_weeks:          data.policyTenureWeeks         ?? 4,
      earnings_deviation:           data.earningsDeviation         ?? 0,
      claim_timing_anomaly:         data.claimTimingAnomaly        ?? 0,
      peer_claim_correlation:       data.peerClaimCorrelation      ?? 0,
      device_change_count:          data.deviceChangeCount         ?? 0,
      login_anomaly_score:          data.loginAnomalyScore         ?? 0,
      route_deviation_score:        data.routeDeviationScore       ?? 0,
      delivery_speed_anomaly:       data.deliverySpeedAnomaly      ?? 0,
      duplicate_claim_score:        data.duplicateClaimScore       ?? 0,
      network_fraud_ring_score:     data.networkFraudRingScore     ?? 0,
      barometric_consistency:       data.barometricConsistency     ?? 1,
      zone_transition_anomaly:      data.zoneTransitionAnomaly     ?? 0,
      claim_photo_similarity_score: data.claimPhotoSimilarityScore ?? 0,
      platform_switch_frequency:    data.platformSwitchFrequency   ?? 0,
      behavioral_baseline_deviation: data.behavioralBaselineDeviation ?? 0,
    };

    // --- HACKATHON QUICK WIN: Dynamic Rule-Engine Fallback ---
    let fraudData = { is_fraud: false, fraud_probability: data.fraudScore ?? 0.15, threshold: 0.5 };
    let mlOnline  = false;
    let startTime = global.performance?.now?.() || Date.now();
    try {
      const mlRes = await axios.post(`${ML}/fraud/detect`, features, { timeout: 6000 });
      fraudData   = mlRes.data;
      mlOnline    = true;
      fraudData._ml_latency_ms = Math.round((global.performance?.now?.() || Date.now()) - startTime);
    } catch (error) {
      // Dynamic Fallback Calculation if ML goes down
      const baseRisk = data.fraudScore ?? 0.15;
      const penalty = (features.location_jump_count * 0.1) + 
                      (features.claim_amount_zscore > 1 ? 0.2 : 0) + 
                      (features.earnings_deviation > 0.4 ? 0.15 : 0);
      const computedFallback = Math.min(baseRisk + penalty, 0.99);

      fraudData = { 
        fallback: true, 
        reason: "ML service unavailable - Using Dynamic Rule-Engine", 
        is_fraud: computedFallback > 0.5, 
        fraud_probability: computedFallback, 
        threshold: 0.5,
        _ml_latency_ms: Math.round((global.performance?.now?.() || Date.now()) - startTime)
      };
    }

    const fraudProb  = fraudData.fraud_probability;
    const spoofProb  = features.gps_spoof_probability;
    const trustScore = Math.round((1 - fraudProb) * 100);
    const { decision, riskLevel, color } = computeDecision(fraudProb, spoofProb, trustScore);
    const signals = buildFraudSignals(features, fraudProb, spoofProb);

    // Fetch existing fraud decision if any
    let existingDecision = null;
    try {
      const fdSnap = await db.collection('fraudDecisions').where('claimId', '==', id).limit(1).get();
      if (!fdSnap.empty) existingDecision = { id: fdSnap.docs[0].id, ...fdSnap.docs[0].data() };
    } catch (_) {}

    res.json({
      claim: {
        id,
        workerId:   data.workerId,
        workerName: data.workerName  || 'Unknown Worker',
        zone:       data.workerZone  || 'Unknown Zone',
        type:       data.type,
        amount:     data.amount,
        status:     data.status,
        description: data.description,
        statement:  data.statement,
        createdAt:  data.createdAt?.toDate?.()?.toISOString() || new Date().toISOString(),
      },
      fraud: {
        fraudScore:  parseFloat(fraudProb.toFixed(4)),
        spoofProb:   parseFloat(spoofProb.toFixed(4)),
        trustScore,
        riskLevel,
        color,
        decision,
        mlOnline,
        threshold:   fraudData.threshold,
        signals,
      },
      existingDecision,
    });
  } catch (err) {
    console.error('GET /fraud/claims/:id error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── POST /fraud/decision ──────────────────────────────────────────────────────
router.post('/decision', async (req, res) => {
  const { claimId, decision, notes, reviewerId, flagWorker } = req.body;
  if (!claimId || !decision) return res.status(400).json({ error: 'claimId and decision required.' });

  const validDecisions = ['APPROVE', 'REJECT', 'REQUEST_PROOF', 'DEEP_REVIEW', 'FLAG_WORKER'];
  if (!validDecisions.includes(decision)) return res.status(400).json({ error: `decision must be one of: ${validDecisions.join(', ')}` });

  try {
    const db  = admin.firestore();
    const ref = db.collection('claims').doc(claimId);
    const snap = await ref.get();
    if (!snap.exists) return res.status(404).json({ error: 'Claim not found.' });

    const data = snap.data();

    // Map decision → claim status
    const statusMap = {
      APPROVE:       'APPROVED',
      REJECT:        'REJECTED',
      REQUEST_PROOF: 'PENDING',
      DEEP_REVIEW:   'PENDING',
      FLAG_WORKER:   'PENDING',
    };
    const newStatus = statusMap[decision];

    // Update claim
    await ref.update({
      status:      newStatus,
      adminComment: notes || '',
      updatedAt:   admin.firestore.FieldValue.serverTimestamp(),
    });

    // Store fraud decision record
    const fdRef = await db.collection('fraudDecisions').add({
      claimId,
      decision,
      notes:      notes || '',
      reviewerId: reviewerId || 'system',
      fraudScore: data.fraudScore || 0,
      spoofProb:  data.spoofProbability || 0,
      timestamp:  admin.firestore.FieldValue.serverTimestamp(),
    });

    // Notify worker
    const msgMap = {
      APPROVE:       `Your claim of ₹${data.amount} has been approved and will be credited shortly.`,
      REJECT:        `Your claim has been reviewed and rejected. ${notes ? 'Reason: ' + notes : ''}`,
      REQUEST_PROOF: 'We need additional proof for your claim. Please upload supporting documents.',
      DEEP_REVIEW:   'Your claim has been sent for deeper review. We will update you shortly.',
      FLAG_WORKER:   'Your account has been flagged for review. Please contact support.',
    };
    await db.collection('notifications').add({
      workerId:  data.workerId,
      title:     decision === 'APPROVE' ? 'Claim Approved ✅' : decision === 'REJECT' ? 'Claim Rejected' : 'Claim Update',
      message:   msgMap[decision],
      type:      decision === 'APPROVE' ? 'SUCCESS' : decision === 'REJECT' ? 'DANGER' : 'INFO',
      read:      false,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    // Credit wallet if approved
    if (decision === 'APPROVE' && data.amount) {
      const walletRef = db.collection('wallets').doc(data.workerId);
      await db.runTransaction(async t => {
        const wSnap = await t.get(walletRef);
        if (wSnap.exists) {
          t.update(walletRef, {
            availableBalance: (wSnap.data().availableBalance || 0) + data.amount,
            totalEarned:      (wSnap.data().totalEarned      || 0) + data.amount,
          });
        } else {
          t.set(walletRef, {
            workerId: data.workerId,
            availableBalance: data.amount,
            totalEarned:      data.amount,
            createdAt: admin.firestore.FieldValue.serverTimestamp(),
          });
        }
      });
    }

    // Flag worker in Prisma if requested
    if (flagWorker && data.workerId) {
      try {
        await prisma.worker.updateMany({
          where: { OR: [{ id: data.workerId }, { firebaseUid: data.workerId }] },
          data:  { trustedStatus: false },
        });
      } catch (_) {}
    }

    res.json({ success: true, decisionId: fdRef.id, newStatus });
  } catch (err) {
    console.error('POST /fraud/decision error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── POST /fraud/spoof-check ───────────────────────────────────────────────────
router.post('/spoof-check', async (req, res) => {
  const { workerId, latitude, longitude, speed, claimContext } = req.body;
  try {
    // Use GPS features from fraud model as proxy (GPS spoof model disabled)
    const features = {
      gps_spoof_probability:    claimContext?.gps_spoof_probability    ?? 0.1,
      location_jump_count:      claimContext?.location_jump_count      ?? 0,
      route_deviation_score:    claimContext?.route_deviation_score    ?? 0,
      delivery_speed_anomaly:   claimContext?.delivery_speed_anomaly   ?? 0,
      zone_transition_anomaly:  claimContext?.zone_transition_anomaly  ?? 0,
      behavioral_baseline_deviation: claimContext?.behavioral_baseline_deviation ?? 0,
    };

    const spoofScore = (
      features.gps_spoof_probability * 0.4 +
      Math.min(features.location_jump_count / 10, 1) * 0.2 +
      features.route_deviation_score * 0.2 +
      features.delivery_speed_anomaly * 0.1 +
      features.zone_transition_anomaly * 0.1
    );

    res.json({
      spoofProbability: parseFloat(spoofScore.toFixed(4)),
      isSpoofed:        spoofScore > 0.5,
      confidence:       spoofScore > 0.7 ? 'High' : spoofScore > 0.4 ? 'Medium' : 'Low',
      flags: [
        features.gps_spoof_probability > 0.4 && 'GPS signal inconsistency',
        features.location_jump_count > 3      && 'Multiple location jumps',
        features.route_deviation_score > 0.5  && 'Route deviation detected',
        features.delivery_speed_anomaly > 0.5 && 'Speed anomaly detected',
      ].filter(Boolean),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
