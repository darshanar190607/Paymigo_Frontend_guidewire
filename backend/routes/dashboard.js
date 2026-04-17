import express from 'express';
import axios from 'axios';
import prisma from '../lib/prisma.js';
import admin from 'firebase-admin';

const router = express.Router();
const ML = 'http://127.0.0.1:8000';

// ── GET /dashboard/summary?workerId=... ───────────────────────────────────────
// Aggregates zone risk, trigger status, claim status, premium, forecast
// Returns UI-ready simplified data — no raw ML scores exposed
router.get('/summary', async (req, res) => {
  const { workerId } = req.query;
  if (!workerId) return res.status(400).json({ error: 'workerId required' });

  try {
    // 1. Fetch worker from Prisma
    const worker = await prisma.worker.findFirst({
      where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
      include: {
        zone: true,
        policies: { where: { isActive: true }, take: 1 },
      },
    }).catch(() => null);

    const zoneId       = worker?.zoneId       || 'default';
    const zoneName     = worker?.zone?.name   || 'Your Zone';
    const zoneRiskTier = worker?.zone?.riskTier || 1;
    const loyaltyWeeks = worker?.loyaltyWeeks  || 0;
    const activePolicy = worker?.policies?.[0] || null;
    const weeklyPremium = activePolicy?.weeklyPremium || worker?.weeklyPremium || 69;

    // 2. Trigger status (live weather)
    let triggerActive = false;
    let triggerLabel  = 'No active disruption';
    let rainfall      = 0;
    try {
      const wx = await axios.get('http://localhost:3000/api/triggers?mode=live', { timeout: 4000 });
      rainfall      = wx.data.rainfall ?? 0;
      triggerActive = wx.data.status === 'PAYOUT_TRIGGERED';
      triggerLabel  = triggerActive
        ? `Heavy Rain — ${rainfall}mm/hr detected`
        : wx.data.status === 'WARNING'
        ? `Rain Alert — ${rainfall}mm/hr`
        : 'No active disruption';
    } catch (_) {}

    // 3. Zone risk level (human-readable)
    const riskLevel = zoneRiskTier >= 3 ? 'high' : zoneRiskTier === 2 ? 'medium' : 'low';
    const riskLabel = zoneRiskTier >= 3
      ? 'High Risk Zone'
      : zoneRiskTier === 2
      ? 'Moderate Risk Zone'
      : 'Low Risk Zone';
    const riskMessage = zoneRiskTier >= 3
      ? 'You are in an active disruption-prone area.'
      : zoneRiskTier === 2
      ? 'Moderate disruption risk in your area.'
      : 'Your zone is currently stable.';

    // 4. Latest claim status from Firestore
    let claimStatus   = null;
    let claimAmount   = null;
    let claimId       = null;
    try {
      const db   = admin.firestore();
      const snap = await db.collection('claims')
        .where('workerId', '==', workerId)
        .orderBy('createdAt', 'desc')
        .limit(1)
        .get();
      if (!snap.empty) {
        const d    = snap.docs[0].data();
        claimId    = snap.docs[0].id;
        claimAmount = d.amount || null;
        const raw  = (d.status || '').toUpperCase();
        if (raw === 'APPROVED')  claimStatus = 'approved';
        else if (raw === 'PENDING') claimStatus = 'processing';
        else if (raw === 'REJECTED') claimStatus = 'review';
        else claimStatus = 'processing';
      }
    } catch (_) {}

    // 5. Forecast summary — delegate to analytics endpoint (has correct LSTM pipeline)
    let forecastLevel   = 'moderate';
    let forecastMessage = 'Moderate risk expected this week.';
    try {
      const fr = await axios.get('http://localhost:3000/api/analytics/forecast', { timeout: 8000 });
      const zoneF = fr.data.zones?.find((z) => z.zoneId === zoneId) || fr.data.global;
      const avg   = zoneF?.avgRiskScore ?? (fr.data.global?.avgRiskScore ?? 0.4);
      const scores = zoneF?.riskScores || fr.data.global?.riskScores || [];
      const peak  = scores.length ? Math.max(...scores) : avg;
      if (peak > 0.75) {
        forecastLevel   = 'high';
        forecastMessage = 'High risk expected mid-week. Stay prepared.';
      } else if (avg > 0.45) {
        forecastLevel   = 'moderate';
        forecastMessage = 'Moderate risk expected this week.';
      } else {
        forecastLevel   = 'low';
        forecastMessage = 'Low risk outlook for the week.';
      }
    } catch (_) {}

    // 6. Premium label
    const premiumLabel = zoneRiskTier >= 3
      ? 'Adjusted for high-risk conditions'
      : loyaltyWeeks >= 8
      ? `Loyalty discount applied (${loyaltyWeeks} weeks)`
      : 'Standard rate for your zone';

    res.json({
      zone:           zoneName,
      riskLevel,
      riskLabel,
      riskMessage,
      triggerActive,
      triggerLabel,
      claimStatus,
      claimAmount,
      claimId,
      premium:        weeklyPremium,
      premiumLabel,
      forecastLevel,
      forecastMessage,
      loyaltyWeeks,
      meta: { lastUpdated: new Date().toISOString() },
    });
  } catch (err) {
    console.error('Dashboard summary error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

export default router;
