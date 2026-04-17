/**
 * Payout Calculator Logic
 * Formula: Rs.60 × hours × ZRM × tier × loyalty_pct
 * 
 * ZRM: Zone Risk Multiplier (1.0 to 2.5)
 * Tier: Plan Tier (1.0 for Basic, 1.5 for Standard, 2.0 for Premium)
 * Loyalty: Bonus based on consecutive weeks without claim (1.0 to 1.25)
 */

export const calculatePayout = (
  hours: number,
  zrm: number = 1.0,
  tier: number = 1.5,
  loyalty_pct: number = 1.0
) => {
  const baseRate = 60;
  const payout = baseRate * hours * zrm * tier * loyalty_pct;
  return Math.round(payout);
};

export const getZoneRiskMultiplier = (zone: string) => {
  const riskMap: Record<string, number> = {
    'Chennai Zone 4': 2.2,
    'Mumbai Zone 2': 1.8,
    'Delhi Zone 1': 1.5,
    'Bangalore Zone 5': 1.2,
  };
  return riskMap[zone] || 1.0;
};
