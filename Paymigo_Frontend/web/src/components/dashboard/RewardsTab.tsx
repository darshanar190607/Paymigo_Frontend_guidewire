import React from 'react';
import { Gift, Droplets, Sun, Snowflake } from 'lucide-react';

const SEASONAL_PRODUCTS: Record<string, Array<{ name: string; brand: string; desc: string; cashback: string }>> = {
  Summer: [
    { name: 'SPF 50+ Sunscreen', brand: 'Premium Pharma', desc: 'Protect from intense UV', cashback: '15%' },
    { name: 'Hydrating Electrolytes', brand: 'HealthFirst', desc: 'Maintain energy in heat', cashback: '12%' },
  ],
  Monsoon: [
    { name: 'Waterproof Rain Gear', brand: 'Local Vendor', desc: 'Stay dry during deliveries', cashback: '20%' },
    { name: 'Anti-fungal Powder', brand: 'MediCare', desc: 'Prevent skin infections', cashback: '10%' },
  ],
  Winter: [
    { name: 'Thermal Innerwear', brand: 'WinterCraft', desc: 'Keep warm on cold rides', cashback: '15%' },
    { name: 'Heavy Moisturizer', brand: 'Nivea', desc: 'Skin protection from dry wind', cashback: '10%' },
  ],
};

const getCurrentSeason = (): 'Summer' | 'Monsoon' | 'Winter' => {
  const month = new Date().getMonth();
  if (month >= 2 && month <= 4) return 'Summer';
  if (month >= 5 && month <= 8) return 'Monsoon';
  return 'Winter';
};

const SeasonIcon = ({ season }: { season: string }) => {
  if (season === 'Summer') return <Sun className="w-10 h-10 text-warning" />;
  if (season === 'Monsoon') return <Droplets className="w-10 h-10 text-accent" />;
  return <Snowflake className="w-10 h-10 text-white" />;
};

const RewardsTab = () => {
  const season = getCurrentSeason();
  const products = SEASONAL_PRODUCTS[season];

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid md:grid-cols-2 gap-8">
        <div className="glass-card p-10 bg-gradient-to-br from-accent/20 to-transparent relative overflow-hidden">
          <Gift className="absolute -right-4 -bottom-4 w-40 h-40 text-accent/10" />
          <h2 className="text-sm font-bold uppercase tracking-widest text-text-secondary mb-2">Total Rewards Balance</h2>
          <div className="text-5xl font-mono font-bold tracking-tighter text-accent mb-6">₹420.00</div>
          <div className="flex gap-4">
            <button className="px-6 py-3 bg-accent text-background rounded-xl font-bold hover:glow-accent">Redeem to Bank</button>
            <button className="px-6 py-3 bg-white/5 border border-white/10 rounded-xl font-bold">History</button>
          </div>
        </div>

        <div className="glass-card p-8 flex flex-col justify-center">
          <h3 className="text-lg font-bold mb-4">Cashback Breakdown</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <span className="text-text-secondary">Fuel (IndianOil)</span>
              <span className="font-bold text-success">+₹250.00</span>
            </div>
            <div className="flex justify-between items-center pb-4 border-b border-white/5">
              <span className="text-text-secondary">Maintenance (Partner Garages)</span>
              <span className="font-bold text-success">+₹120.00</span>
            </div>
            <div className="flex justify-between items-center text-accent">
              <span className="font-bold">Next Milestone Unlock</span>
              <span className="font-bold">₹80 to go</span>
            </div>
          </div>
        </div>
      </div>

      <div className="glass-card p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h3 className="text-2xl font-display font-bold">Seasonal Care: {season} Offers</h3>
            <p className="text-text-secondary">Tailored health & protection suggestions for current gig-working conditions.</p>
          </div>
          <SeasonIcon season={season} />
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {products.map((prod, i) => (
            <div key={i} className="flex flex-col p-6 bg-white/5 border border-white/10 rounded-2xl hover:border-accent/40 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h4 className="font-bold text-lg">{prod.name}</h4>
                  <div className="text-xs text-text-secondary uppercase tracking-widest">{prod.brand}</div>
                </div>
                <div className="bg-accent/20 text-accent text-xs font-bold px-3 py-1 rounded-full">{prod.cashback} Cashback</div>
              </div>
              <p className="text-sm text-text-secondary mb-6">{prod.desc}</p>
              <button className="mt-auto w-full py-3 bg-white/5 hover:bg-white/10 rounded-xl font-bold transition-all text-sm">
                Claim Offer
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RewardsTab;
