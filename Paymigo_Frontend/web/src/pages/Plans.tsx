import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { Shield, CheckCircle2, ChevronRight, Calculator, CloudRain } from 'lucide-react';
import { cn } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Plan {
  id: string;
  name: string;
  price: number;
  payout: string;
  features: string[];
  recommended?: boolean;
}

interface FaqItem {
  q: string;
  a: string;
}

interface MonsoonHike {
  label: string;
  hike: string;
  desc: string;
}

// ─── Static data ─────────────────────────────────────────────────────────────

const MONSOON_HIKES: MonsoonHike[] = [
  { label: 'Basic Plan',   hike: '+₹30', desc: 'Covers essential monsoon disruptions.' },
  { label: 'Pro Plan',     hike: '+₹30', desc: 'Includes Stay-at-Home benefit.' },
  { label: 'Premium Plan', hike: '+₹40', desc: 'Full coverage for extreme floods.' },
];

const FAQ_ITEMS: FaqItem[] = [
  { q: 'Why weekly premiums?', a: 'Gig work is unpredictable. Weekly plans allow you to pause or switch plans based on your schedule and weather forecasts.' },
  { q: "What's a parametric trigger?", a: 'Unlike traditional insurance, we pay based on data (like rainfall mm/hr) rather than manual damage assessment. If the data hits the limit, you get paid.' },
  { q: 'How does the Loyalty Pool work?', a: "A portion of your premium goes into a pool. Every week you don't claim, your potential bonus grows. It's our way of rewarding safe weeks." },
  { q: 'Is this legal in India?', a: 'Yes, we operate as a parametric micro-insurance platform under the sandbox regulations for innovative fintech products.' },
];

const CITY_OPTIONS = [
  { value: 'Coimbatore (Zone 1)', label: 'Coimbatore (Disruption Less)' },
  { value: 'Chennai (Zone 4)',     label: 'Chennai (High Monsoon Risk)' },
  { value: 'Mumbai (Zone 1)',      label: 'Mumbai (Flood Prone)' },
  { value: 'Bangalore (Zone 2)',   label: 'Bangalore (Traffic Heavy)' },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

const getBasePrice = (city: string): number => {
  if (city.includes('Coimbatore')) return 49;
  if (city.includes('Chennai') || city.includes('Mumbai')) return 149;
  return 119;
};

const buildPlans = (isMonsoon: boolean): Plan[] => {
  const surge = isMonsoon ? 30 : 0;
  const plans: Plan[] = [
    { id: 'basic',   name: 'Basic',   price: 49  + surge, payout: '800',   features: ['Rainfall > 25mm/hr', 'AQI > 400', '4-hour payout speed', 'Basic Loyalty Pool'] },
    { id: 'pro',     name: 'Pro',     price: 69  + surge, payout: '1,500', features: ['Rainfall > 15mm/hr', 'AQI > 300', '90-second payout speed', 'Full Loyalty Pool', 'Fuel Cashback'], recommended: true },
    { id: 'premium', name: 'Premium', price: 119 + surge, payout: '2,500', features: ['Rainfall > 10mm/hr', 'AQI > 200', 'Instant payout speed', 'Max Loyalty Pool', 'Max Fuel Cashback'] },
  ];
  if (isMonsoon) plans.forEach(p => p.features.push('Stay-at-Home Benefit'));
  return plans;
};

// ─── Component ────────────────────────────────────────────────────────────────

const Plans: React.FC = () => {
  const [isMonsoon, setIsMonsoon] = React.useState<boolean>(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('isMonsoon') !== null) {
      return localStorage.getItem('isMonsoon') === 'true';
    }
    const month = new Date().getMonth();
    return month >= 5 && month <= 8;
  });

  const [selectedCity, setSelectedCity] = React.useState('Coimbatore (Zone 1)');

  React.useEffect(() => {
    if (typeof window !== 'undefined') localStorage.setItem('isMonsoon', String(isMonsoon));
  }, [isMonsoon]);

  const plans  = buildPlans(isMonsoon);
  const basePrice = getBasePrice(selectedCity);

  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Header */}
      <header className="py-20 px-6 text-center relative overflow-hidden">
        <div className="absolute inset-0 hero-glow opacity-50 z-0" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative z-10 max-w-4xl mx-auto"
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent/10 border border-accent/20 text-accent text-[10px] font-bold mb-8 uppercase tracking-[0.2em]">
            Transparent & Automated
          </div>
          <div className="flex justify-center mb-8">
            <button
              onClick={() => setIsMonsoon(p => !p)}
              className={cn(
                'flex items-center gap-3 px-6 py-3 rounded-2xl font-bold uppercase transition-all border shadow-lg',
                isMonsoon ? 'bg-accent text-background border-accent shadow-accent/20' : 'bg-white/5 border-white/10 text-text-secondary'
              )}
            >
              <CloudRain className={cn('w-5 h-5', isMonsoon && 'animate-pulse')} />
              {isMonsoon ? 'Monsoon Season Active' : 'Switch to Monsoon Mode'}
            </button>
          </div>
          <h1 className="text-5xl md:text-7xl font-display font-black mb-8 tracking-tight">
            Choose Your <br />
            <span className="text-accent">Shield</span>
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            Parametric insurance that triggers automatically. No claims, no paperwork, just peace of mind.
          </p>
        </motion.div>
      </header>

      <div className="max-w-7xl mx-auto px-6 pb-32">
        {/* Dynamic Calculator */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          className="glass-card p-10 mb-24 max-w-4xl mx-auto border-accent/20 relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 blur-3xl rounded-full" />
          <h3 className="text-2xl font-bold mb-8 flex items-center gap-3">
            <Calculator className="w-6 h-6 text-accent" /> Dynamic Premium Estimator
          </h3>
          <div className="grid md:grid-cols-2 gap-10">
            <div className="space-y-6">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Select Your City</label>
                <select
                  value={selectedCity}
                  onChange={e => setSelectedCity(e.target.value)}
                  className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-5 outline-none focus:border-accent transition-all appearance-none cursor-pointer"
                >
                  {CITY_OPTIONS.map(opt => (
                    <option key={opt.value} className="bg-surface" value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-3">
                <label className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Coverage Period</label>
                <select className="w-full bg-white/5 border border-white/10 rounded-2xl py-4 px-5 outline-none focus:border-accent transition-all appearance-none cursor-pointer">
                  <option className="bg-surface">Current Week (Monsoon Peak)</option>
                  <option className="bg-surface">Next 4 Weeks (Bundle & Save)</option>
                </select>
              </div>
            </div>
            <div className="bg-accent/5 rounded-3xl border border-accent/20 p-8 flex flex-col justify-center items-center text-center">
              <div className="text-[10px] text-accent font-black uppercase tracking-[0.2em] mb-4">Estimated Weekly Premium</div>
              <div className="flex items-baseline gap-1 mb-2">
                <span className="text-5xl font-mono font-bold tracking-tighter text-accent">₹{basePrice}</span>
                <span className="text-text-secondary font-bold uppercase tracking-widest text-xs">/wk</span>
              </div>
              <div className="text-xs text-success font-bold bg-success/10 px-3 py-1 rounded-full mb-6">ML AI Repricing Applied ✨</div>
              <button className="w-full py-4 bg-accent text-background rounded-2xl font-bold hover:glow-accent transition-all shadow-xl shadow-accent/20">
                Lock This Rate
              </button>
            </div>
          </div>
        </motion.div>

        {/* Monsoon Hike Info */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          className="p-8 bg-accent/5 border border-accent/20 rounded-3xl mb-32 max-w-4xl mx-auto"
        >
          <div className="flex items-center gap-4 mb-6">
            <div className="w-12 h-12 bg-accent/20 rounded-2xl flex items-center justify-center">
              <CloudRain className="w-6 h-6 text-accent" />
            </div>
            <div>
              <h3 className="text-xl font-bold">Monsoon Pricing Policy (June - Sept)</h3>
              <p className="text-sm text-text-secondary">Automatic adjustments for peak risk periods.</p>
            </div>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            {MONSOON_HIKES.map(hike => (
              <div key={hike.label} className="p-4 bg-white/5 rounded-2xl border border-white/10">
                <div className="text-[10px] font-black text-text-secondary uppercase mb-2">{hike.label}</div>
                <div className="text-lg font-bold text-accent">{hike.hike}</div>
                <p className="text-[10px] text-text-secondary mt-1">{hike.desc}</p>
              </div>
            ))}
          </div>
          <p className="text-[10px] text-text-secondary mt-6 italic">
            * These hikes are automatically applied from June 1st to September 30th each year. During this period, all plans include the <b>Stay-at-Home Benefit</b>.
          </p>
        </motion.div>

        {/* Plan Cards */}
        <div className="grid md:grid-cols-3 gap-10 mb-32">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.id}
              whileHover={{ y: -10 }}
              className={cn(
                'glass-card p-10 flex flex-col relative transition-all duration-500',
                plan.recommended ? 'border-accent/50 glow-accent scale-105 z-10 bg-surface/90' : 'hover:border-white/20'
              )}
            >
              {plan.recommended && (
                <div className="absolute top-0 right-0 bg-accent text-background text-[10px] font-black px-4 py-1.5 uppercase tracking-widest rounded-bl-2xl">
                  Recommended
                </div>
              )}
              <h3 className="text-2xl font-display font-bold mb-3">{plan.name}</h3>
              <div className="flex items-baseline gap-1 mb-8">
                <span className="text-5xl font-mono font-bold tracking-tighter">₹{plan.price}</span>
                <span className="text-text-secondary text-sm font-bold uppercase tracking-widest">/wk</span>
              </div>
              <ul className="space-y-5 mb-10 flex-grow">
                {plan.features.map(f => (
                  <li key={f} className="flex items-center gap-4 text-sm group/item">
                    <div className="w-6 h-6 rounded-full bg-success/10 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-4 h-4 text-success" />
                    </div>
                    <span className="text-text-secondary group-hover/item:text-text-primary transition-colors">{f}</span>
                  </li>
                ))}
              </ul>
              {/* Use Link instead of <a> — proper SPA navigation */}
              <Link
                to={`/plans/${plan.id}`}
                className="w-full py-4 rounded-2xl font-bold transition-all duration-300 text-center bg-accent text-white hover:scale-[1.02] shadow-lg shadow-accent/20"
              >
                Select Plan
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Compare Table */}
        <div className="max-w-6xl mx-auto mb-32">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-display font-bold mb-4">Compare Protection Plans</h2>
            <p className="text-text-secondary">Explore all benefits stacked side by side.</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="py-6 px-4 font-bold text-text-secondary w-1/4">Features</th>
                  <th className="py-6 px-4 font-bold w-1/4">Basic</th>
                  <th className="py-6 px-4 font-bold text-accent w-1/4">Pro (Recommended)</th>
                  <th className="py-6 px-4 font-bold w-1/4">Premium</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {[
                  ['Rainfall Trigger', '> 25mm/hr', '> 15mm/hr', '> 10mm/hr'],
                  ['Payout Speed', '4 hours', '90 seconds', 'Instant'],
                  ['Max Daily Payout', '₹800', '₹1,500', '₹2,500'],
                  ['Loyalty Bonus', 'Basic Pool', 'Full Pool', 'Max Pool (2x multiplier)'],
                  ['Fuel Cashback', 'Not included', 'Flat ₹20/wk', 'Max ₹50/wk'],
                  ['Monsoon Hike', '+₹30', '+₹30', '+₹40'],
                ].map(([feature, basic, pro, premium]) => (
                  <tr key={feature} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-4 px-4 text-text-secondary font-bold">{feature}</td>
                    <td className="py-4 px-4">{basic}</td>
                    <td className="py-4 px-4 text-accent">{pro}</td>
                    <td className="py-4 px-4">{premium}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ */}
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-display font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-text-secondary">Everything you need to know about Paymigo.</p>
          </div>
          <div className="grid md:grid-cols-2 gap-6">
            {FAQ_ITEMS.map(faq => (
              <div key={faq.q} className="glass-card p-8 border-white/5 hover:border-white/10 transition-all group">
                <h4 className="font-bold mb-4 flex items-center justify-between group-hover:text-accent transition-colors">
                  {faq.q} <ChevronRight className="w-4 h-4 opacity-50" />
                </h4>
                <p className="text-sm text-text-secondary leading-relaxed">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Plans;
