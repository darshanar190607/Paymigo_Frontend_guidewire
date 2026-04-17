import express from 'express';
import axios from 'axios';
import prisma from '../lib/prisma.js';
import { getZoneFeatures } from '../lib/csvLoader.js';

const router = express.Router();

const ML = 'http://127.0.0.1:8000';

// ── Plan definitions ──────────────────────────────────────────────────────────
const PLAN_DEFS = [
  {
    id: 'basic',
    name: 'Basic Shield',
    payoutCap: 800,
    triggerThreshold: 25,
    triggerLabel: 'Rainfall > 25mm/hr',
    payoutSpeed: '4 hours',
    loyaltyPool: 'Basic',
    summary: 'Essential cover for light disruptions.',
  },
  {
    id: 'standard',
    name: 'Standard Shield',
    payoutCap: 1500,
    triggerThreshold: 15,
    triggerLabel: 'Rainfall > 15mm/hr',
    payoutSpeed: '90 seconds',
    loyaltyPool: 'Full',
    summary: 'Best balance of cost and protection.',
  },
  {
    id: 'premium',
    name: 'Premium Shield',
    payoutCap: 2500,
    triggerThreshold: 10,
    triggerLabel: 'Rainfall > 10mm/hr',
    payoutSpeed: 'Instant',
    loyaltyPool: 'Max (2×)',
    summary: 'Maximum cover for high-risk zones.',
  },
];

// ── Recommendation engine ─────────────────────────────────────────────────────
function computeRecommendation({ zoneRiskTier, triggerActive, loyaltyWeeks, basePremium }) {
  // High risk zone or active trigger → push Premium
  if (zoneRiskTier >= 3 || triggerActive) {
    return {
      planId: 'premium',
      confidence: 0.91,
      reasons: [
        zoneRiskTier >= 3 ? 'Your zone is classified as high risk.' : 'A disruption trigger is currently active.',
        'Premium Shield covers lower rainfall thresholds — you qualify for payouts sooner.',
        loyaltyWeeks >= 8 ? `Your ${loyaltyWeeks}-week loyalty discount reduces the effective cost.` : 'Upgrade now to start building loyalty benefits.',
      ],
      fallback: 'standard',
    };
  }
  // Medium risk → Standard
  if (zoneRiskTier === 2 || basePremium > 80) {
    return {
      planId: 'standard',
      confidence: 0.85,
      reasons: [
        'Your zone has moderate risk — Standard Shield covers the most common disruption events.',
        'The 90-second payout speed means money arrives before your shift ends.',
        loyaltyWeeks >= 4 ? `${loyaltyWeeks} paid weeks — loyalty discount is active.` : 'Build loyalty weeks to unlock discounts.',
      ],
      fallback: 'basic',
    };
  }
  // Low risk → Basic
  return {
    planId: 'basic',
    confidence: 0.78,
    reasons: [
      'Your zone has low historical disruption — Basic Shield is cost-effective.',
      'You can upgrade any week if conditions change.',
      'Start building your loyalty pool from week 1.',
    ],
    fallback: 'standard',
  };
}

// ── GET /pricing/intelligence?workerId=... ────────────────────────────────────
router.get('/intelligence', async (req, res) => {
  const { workerId } = req.query;

  try {
    // 1. Fetch worker + zone from DB
    const worker = workerId
      ? await prisma.worker.findFirst({
          where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
          include: { zone: true, policies: { where: { isActive: true }, take: 1 } },
        })
      : await prisma.worker.findFirst({
          orderBy: { id: 'desc' },
          include: { zone: true, policies: { where: { isActive: true }, take: 1 } },
        });

    const zoneId   = worker?.zoneId   || 'default';
    const zoneName = worker?.zone?.name || 'Unknown Zone';
    const loyaltyWeeks = worker?.loyaltyWeeks || 0;
    const currentMonth = new Date().getMonth() + 1;

    // 2. Fetch live weather / trigger status
    let rainfall = 14.2, windSpeed = 22.5, weatherStatus = 'MONITORING';
    try {
      const wx = await axios.get('http://localhost:3000/api/triggers?mode=live', { timeout: 4000 });
      rainfall    = wx.data.rainfall    ?? rainfall;
      windSpeed   = wx.data.windSpeed   ?? windSpeed;
      weatherStatus = wx.data.status    ?? weatherStatus;
    } catch (_) {}

    // 3. Zone cluster → risk tier
    let zoneRiskTier = worker?.zone?.riskTier || 1;
    let clusterConfidence = 0.75;
    try {
      const stats = await getZoneFeatures(zoneId);
      if (stats.zone_risk_tier) {
        zoneRiskTier = stats.zone_risk_tier;
      } else {
        const cr = await axios.post(`${ML}/cluster/predict`, stats, { timeout: 4000 });
        zoneRiskTier = cr.data.zone_risk_tier || zoneRiskTier;
      }
      clusterConfidence = 0.88;
    } catch (_) {}

    // 4. Trigger classifier
    let triggerActive = weatherStatus === 'PAYOUT_TRIGGERED';
    let triggerConfidence = 0.72;
    let triggerReason = 'No active disruption detected.';
    try {
      const tr = await axios.post(`${ML}/trigger/predict`, {
        event_type:       'rain',
        severity:         rainfall,
        zone_id:          zoneRiskTier,
        duration_hours:   1.0,
        raw_value:        rainfall,
        source_confidence: 0.95,
        multi_source_match: 1,
        sustained_event:  rainfall > 10 ? 1 : 0,
        variability:      0.2,
        trend:            0.1,
        duration_minutes: 60,
      }, { timeout: 4000 });
      triggerActive     = tr.data.trigger?.approved === 1;
      triggerConfidence = tr.data.trigger?.confidence ?? triggerConfidence;
      triggerReason     = triggerActive
        ? `Rainfall of ${rainfall}mm exceeds disruption threshold.`
        : `Current rainfall (${rainfall}mm) is below trigger threshold.`;
    } catch (_) {
      triggerReason = triggerActive
        ? `Rainfall of ${rainfall}mm exceeds disruption threshold.`
        : `Current rainfall (${rainfall}mm) is below trigger threshold.`;
    }

    // 5. Premium engine — calculate for all 3 tiers
    const premiumBase = { basic: 49, standard: 69, premium: 119 };
    const pricedPlans = await Promise.all(
      ['Basic', 'Standard', 'Premium'].map(async (tier, i) => {
        let price = Object.values(premiumBase)[i];
        try {
          const pr = await axios.post(`${ML}/premium/predict`, {
            age:                        worker?.age || 28,
            job_type:                   worker?.jobType || 'Delivery',
            experience_years:           worker?.experienceYears || 1,
            incident_history:           0,
            zone_risk_tier:             zoneRiskTier,
            lstm_forecast_score:        triggerActive ? 0.8 : 0.3,
            aqi_7day_avg:               80,
            platform_tenure_weeks:      loyaltyWeeks || 4,
            loyalty_weeks_paid:         loyaltyWeeks || 4,
            historical_disruption_rate: zoneRiskTier > 2 ? 0.25 : 0.08,
            peer_claim_rate_zone:       0.05,
            current_month:              currentMonth,
            policy_tier:                tier,
          }, { timeout: 4000 });
          price = Math.round(pr.data.premium || price);
        } catch (_) {
          // Apply simple risk multiplier as fallback
          price = Math.round(price * (zoneRiskTier > 2 ? 1.3 : zoneRiskTier > 1 ? 1.1 : 1.0));
        }
        return { planId: PLAN_DEFS[i].id, weeklyPremium: price };
      })
    );

    // 6. Recommendation
    const basePremium = pricedPlans[1].weeklyPremium; // standard as reference
    const recommendation = computeRecommendation({
      zoneRiskTier,
      triggerActive,
      loyaltyWeeks,
      basePremium,
    });

    // 7. Build final plans array with live prices
    const plans = PLAN_DEFS.map((def, i) => ({
      ...def,
      weeklyPremium:   pricedPlans[i].weeklyPremium,
      isRecommended:   def.id === recommendation.planId,
    }));

    // 8. Store quote snapshot
    try {
      if (worker) {
        await prisma.premiumQuote.create({
          data: {
            workerId:    worker.id,
            recommended: pricedPlans[1].weeklyPremium,
            minRange:    pricedPlans[0].weeklyPremium,
            maxRange:    pricedPlans[2].weeklyPremium,
            confidence:  recommendation.confidence,
          },
        });
      }
    } catch (_) {}

    res.json({
      zone: { id: zoneId, name: zoneName, riskTier: zoneRiskTier },
      trigger: {
        active:     triggerActive,
        confidence: triggerConfidence,
        rainfall,
        windSpeed,
        status:     weatherStatus,
        reason:     triggerReason,
        eventType:  rainfall > 10 ? 'Heavy Rainfall' : 'Light Rain',
        threshold:  15,
      },
      plans,
      recommendation,
      worker: worker
        ? { loyaltyWeeks, jobType: worker.jobType, age: worker.age, activePolicy: worker.policies[0] || null }
        : null,
      meta: { clusterConfidence, lastUpdated: new Date().toISOString() },
    });
  } catch (err) {
    console.error('Pricing intelligence error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

// ── POST /pricing/select-plan ─────────────────────────────────────────────────
router.post('/select-plan', async (req, res) => {
  const { workerId, planId, weeklyPremium } = req.body;
  if (!workerId || !planId) return res.status(400).json({ error: 'workerId and planId required.' });

  try {
    const worker = await prisma.worker.findFirst({
      where: { OR: [{ id: workerId }, { firebaseUid: workerId }] },
    });
    if (!worker) return res.status(404).json({ error: 'Worker not found.' });

    // Deactivate existing policies
    await prisma.policy.updateMany({
      where: { workerId: worker.id, isActive: true },
      data:  { isActive: false, endDate: new Date() },
    });

    const tierMap = { basic: 'Basic', standard: 'Standard', premium: 'Premium' };
    const policy = await prisma.policy.create({
      data: {
        workerId:      worker.id,
        tier:          tierMap[planId] || 'Standard',
        weeklyPremium: weeklyPremium || 69,
        loyaltyPercent: 0,
        isActive:      true,
        startDate:     new Date(),
      },
    });

    res.json({ success: true, policy });
  } catch (err) {
    console.error('Select plan error:', err.message);
    res.status(500).json({ error: err.message });
  }
});

export default router;
