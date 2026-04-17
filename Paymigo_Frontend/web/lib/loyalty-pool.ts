/**
 * Loyalty Pool & Payout Tier Calculation
 * 
 * Bonus based on consecutive weeks without a claim:
 * 1-4 weeks: 0%
 * 5-8 weeks: 5% (Tier 1)
 * 9-12 weeks: 15% (Tier 2)
 * 13+ weeks: 25% (Tier 3)
 */

export const calculateLoyaltyBonus = (consecutiveWeeks: number) => {
  if (consecutiveWeeks >= 13) return 0.25;
  if (consecutiveWeeks >= 9) return 0.15;
  if (consecutiveWeeks >= 5) return 0.05;
  return 0;
};

export const getLoyaltyTier = (consecutiveWeeks: number) => {
  if (consecutiveWeeks >= 13) return 3;
  if (consecutiveWeeks >= 9) return 2;
  if (consecutiveWeeks >= 5) return 1;
  return 0;
};

export const getTierLabel = (tier: number) => {
  const labels: Record<number, string> = {
    0: 'Base Tier',
    1: 'Tier 1 (5% Bonus)',
    2: 'Tier 2 (15% Bonus)',
    3: 'Tier 3 (25% Bonus)',
  };
  return labels[tier] || 'Base Tier';
};
