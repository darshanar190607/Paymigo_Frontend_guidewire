import React from 'react';
import { motion } from 'motion/react';
import { useNavigate, useParams } from 'react-router-dom';
import { Shield, CheckCircle2, ArrowLeft, Zap, CreditCard, ShieldCheck } from 'lucide-react';
import { cn, formatCurrency } from '@/lib/utils';

// ─── Types ────────────────────────────────────────────────────────────────────

interface PlanDetail {
  name: string;
  price: number;
  payout: number;
  features: string[];
}

type PlanId = 'basic' | 'pro' | 'premium';

// ─── Static data ─────────────────────────────────────────────────────────────

const isMonsoon = (): boolean => {
  if (typeof window !== 'undefined' && localStorage.getItem('isMonsoon') !== null) {
    return localStorage.getItem('isMonsoon') === 'true';
  }
  const month = new Date().getMonth();
  return month >= 5 && month <= 8;
};

const surge = isMonsoon() ? 30 : 0;

const PLAN_DETAILS: Record<PlanId, PlanDetail> = {
  basic: {
    name: 'Basic',
    price: 49 + surge,
    payout: 800,
    features: ['Rainfall > 25mm/hr', 'AQI > 400', '4-hour payout speed', 'Basic Loyalty Pool'],
  },
  pro: {
    name: 'Pro',
    price: 69 + surge,
    payout: 1500,
    features: ['Rainfall > 15mm/hr', 'AQI > 300', '90-second payout speed', 'Full Loyalty Pool', 'Fuel Cashback: Flat ₹20/wk'],
  },
  premium: {
    name: 'Premium',
    price: 119 + surge,
    payout: 2500,
    features: ['Rainfall > 10mm/hr', 'AQI > 200', 'Instant payout speed', 'Max Loyalty Pool', 'Fuel Cashback: Max ₹50/wk'],
  },
};

// ─── Component ────────────────────────────────────────────────────────────────

const PlanCheckout: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const plan = id ? PLAN_DETAILS[id.toLowerCase() as PlanId] : undefined;

  if (!plan) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Plan Not Found</h1>
          <button
            onClick={() => navigate('/plans')}
            className="text-accent font-bold hover:underline"
          >
            Back to Plans
          </button>
        </div>
      </div>
    );
  }

  const gst = plan.price * 0.18;
  const total = plan.price + gst;

  return (
    <div className="min-h-screen bg-background py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => navigate('/plans')}
          className="flex items-center gap-2 text-text-secondary hover:text-accent transition-colors mb-12 font-bold uppercase tracking-widest text-xs"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Plans
        </button>

        <div className="grid lg:grid-cols-2 gap-12">
          {/* Plan Summary */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-8"
          >
            <div className="glass-card p-10 border-accent/20">
              <div className="w-16 h-16 bg-accent/10 rounded-2xl flex items-center justify-center mb-6">
                <Shield className="w-8 h-8 text-accent" />
              </div>
              <h1 className="text-4xl font-display font-black mb-2">{plan.name}</h1>
              <div className="flex items-baseline gap-1 mb-8">
                <span className="text-5xl font-mono font-bold tracking-tighter">₹{plan.price}</span>
                <span className="text-text-secondary text-sm font-bold uppercase tracking-widest">/wk</span>
              </div>

              <div className="space-y-6">
                <p className="text-text-secondary font-medium">
                  You are selecting the {plan.name} protection plan. This plan provides up to {formatCurrency(plan.payout)} daily payout during triggered weather events.
                </p>
                <div className="space-y-4">
                  <p className="text-[10px] font-black text-text-secondary uppercase tracking-widest">Key Features</p>
                  {plan.features.map(f => (
                    <div key={f} className="flex items-center gap-3 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-success" />
                      <span className="text-text-secondary">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="glass-card p-8 bg-surface/50">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-accent" /> Automatic Activation
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                Once confirmed, your protection starts immediately. Our AI engine will monitor your zone 24/7. No claim forms required.
              </p>
            </div>
          </motion.div>

          {/* Checkout Panel */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-8"
          >
            <div className="glass-card p-10">
              <h2 className="text-2xl font-bold mb-8 flex items-center gap-3">
                <CreditCard className="w-6 h-6 text-accent" /> Confirm Selection
              </h2>
              <div className="space-y-6">
                <div className="p-6 bg-accent/5 border border-accent/10 rounded-2xl">
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm text-text-secondary">Weekly Premium</span>
                    <span className="font-mono font-bold">₹{plan.price}</span>
                  </div>
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-sm text-text-secondary">GST (18%)</span>
                    <span className="font-mono font-bold">₹{gst.toFixed(2)}</span>
                  </div>
                  <div className="h-px bg-accent/10 my-4" />
                  <div className="flex justify-between items-center">
                    <span className="font-bold">Total Amount</span>
                    <span className="text-2xl font-mono font-bold text-accent">₹{total.toFixed(2)}</span>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 border border-border rounded-xl bg-surface/50">
                    <ShieldCheck className="w-5 h-5 text-success" />
                    <div className="text-xs font-medium">Secure test simulation via Paymigo Sandbox</div>
                  </div>
                  <button
                    onClick={() => navigate('/dashboard')}
                    className="w-full py-5 bg-accent text-white rounded-2xl font-bold text-lg hover:glow-accent transition-all shadow-xl shadow-accent/20"
                  >
                    Confirm & Simulate Payment
                  </button>
                  <p className="text-[10px] text-center text-text-secondary uppercase tracking-widest font-bold">
                    This is a sandbox environment. No real money will be charged.
                  </p>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
};

export default PlanCheckout;
