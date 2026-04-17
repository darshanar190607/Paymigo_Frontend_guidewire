import React from 'react';
import { motion } from 'motion/react';
import {
  CloudRain, TrendingUp, Zap, Shield, Wallet,
  CheckCircle2, AlertTriangle, ChevronRight,
  ArrowUpRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Worker, WalletData, Claim } from '../../types/dashboard';

interface OverviewTabProps {
  rainfall: number;
  triggerStatus: string;
  simulateRain: () => void;
  isSimulating: boolean;
  workerData: Worker | null;
  walletData: WalletData | null;
  recentClaims: Claim[];
}

const OverviewTab = ({
  rainfall,
  triggerStatus,
  workerData,
  walletData,
  recentClaims,
}: OverviewTabProps) => (
  <div className="space-y-8">
    {/* Zone Status Hero Card */}
    <section>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 relative overflow-hidden group"
      >
        <div className="absolute top-0 right-0 p-8 opacity-10 group-hover:opacity-20 transition-opacity">
          <CloudRain className="w-32 h-32" />
        </div>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 relative z-10">
          <div>
            <div className={cn(
              'inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold mb-4 uppercase border',
              triggerStatus === 'PAYOUT_TRIGGERED'
                ? 'bg-success/10 border-success/20 text-success'
                : 'bg-warning/10 border-warning/20 text-warning'
            )}>
              {triggerStatus === 'PAYOUT_TRIGGERED'
                ? <CheckCircle2 className="w-3 h-3" />
                : <AlertTriangle className="w-3 h-3" />}
              {triggerStatus === 'PAYOUT_TRIGGERED' ? 'Payout Triggered' : 'Monitoring Zone'}
            </div>
            <h2 className="text-4xl font-display font-bold mb-2">
              {triggerStatus === 'PAYOUT_TRIGGERED' ? 'Automatic Payout Initiated' : 'Monitor Closely'}
            </h2>
            <p className="text-text-secondary max-w-md">
              {triggerStatus === 'PAYOUT_TRIGGERED'
                ? 'Threshold reached! ₹1,500 will be credited to your GigWallet within 90 seconds.'
                : `Real-time weather monitoring active in ${workerData?.zone || 'your zone'}. Payout trigger threshold: 10mm/hr.`}
            </p>
          </div>

          <div className="flex flex-col items-end text-right">
            <div className={cn(
              'text-5xl font-mono font-bold mb-1',
              triggerStatus === 'PAYOUT_TRIGGERED' ? 'text-success' : 'text-warning'
            )}>
              {rainfall}<span className="text-xl">mm</span>
            </div>
            <div className="text-xs text-text-secondary uppercase tracking-widest font-bold">Current Rainfall</div>
            <div className="mt-4 flex gap-2">
              <div className="px-3 py-1 bg-white/5 rounded-lg text-[10px] font-bold">AQI: 45 (Good)</div>
              <div className="px-3 py-1 bg-white/5 rounded-lg text-[10px] font-bold">Next Renewal: 5 Days</div>
            </div>
          </div>
        </div>
      </motion.div>
    </section>

    {/* Stats Grid */}
    <section className="grid md:grid-cols-3 gap-6">
      {[
        { label: 'Weekly Premium', val: `₹${workerData?.weeklyPremium || 119}`, sub: `${workerData?.plan || 'Pro'} Plan`, icon: Shield },
        { label: 'Max Coverage', val: '₹1,500', sub: '₹500 / day max', icon: TrendingUp },
        { label: 'Payout Speed', val: '90s', sub: 'Priority Tier', icon: Zap },
      ].map((stat, i) => (
        <div key={i} className="glass-card p-6 flex items-center gap-4">
          <div className="w-12 h-12 bg-accent/10 rounded-xl flex items-center justify-center">
            <stat.icon className="w-6 h-6 text-accent" />
          </div>
          <div>
            <div className="text-xs text-text-secondary font-bold uppercase tracking-widest">{stat.label}</div>
            <div className="text-2xl font-mono font-bold">{stat.val}</div>
            <div className="text-[10px] text-text-secondary">{stat.sub}</div>
          </div>
        </div>
      ))}
    </section>

    <div className="grid lg:grid-cols-3 gap-8">
      <div className="lg:col-span-2 space-y-8">
        {/* Loyalty Pool Tracker */}
        <div className="glass-card p-8">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl font-bold">Loyalty Pool Tracker</h3>
            <div className="text-accent font-bold">14 / 26 Weeks</div>
          </div>
          <div className="relative h-4 bg-white/5 rounded-full overflow-hidden mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: '54%' }}
              transition={{ duration: 1, ease: 'easeOut' }}
              className="absolute top-0 left-0 h-full bg-accent glow-accent"
            />
          </div>
          <div className="flex justify-between text-[10px] text-text-secondary font-bold uppercase tracking-tighter">
            <span>Start</span><span>4 Weeks</span><span>9 Weeks</span>
            <span>17 Weeks</span><span>26 Weeks (Max)</span>
          </div>
          <div className="mt-6 p-4 bg-accent/5 border border-accent/10 rounded-xl flex items-center justify-between">
            <div className="flex flex-col gap-1 text-sm">
              <div><span className="text-accent font-bold">₹336 bonus</span> ready for your next claim.</div>
              <div className="text-xs text-success font-bold flex items-center gap-1 mt-1">
                <TrendingUp className="w-4 h-4" /> Continuous Payment: +10% Payout Bonus Active!
              </div>
            </div>
            <button className="text-xs font-bold flex items-center gap-1 text-accent hover:underline">
              View Milestones <ChevronRight className="w-3 h-3" />
            </button>
          </div>
        </div>

        {/* Partner Connection */}
        <div className="glass-card p-8 border-accent/20">
          <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-accent" /> Partner Integration
          </h3>
          <div className="grid md:grid-cols-2 gap-6">
            <div className="p-6 bg-white/5 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-accent/50 transition-all cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#E23744] rounded-xl flex items-center justify-center">
                  <span className="text-white font-black text-xl">Z</span>
                </div>
                <div>
                  <div className="font-bold">Zomato Partner</div>
                  <div className="text-[10px] text-success font-bold uppercase">Connected</div>
                </div>
              </div>
              <CheckCircle2 className="w-5 h-5 text-success" />
            </div>
            <div className="p-6 bg-white/5 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-accent/50 transition-all cursor-pointer">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-[#FC8019] rounded-xl flex items-center justify-center">
                  <span className="text-white font-black text-xl">S</span>
                </div>
                <div>
                  <div className="font-bold">Swiggy Delivery</div>
                  <div className="text-[10px] text-text-secondary font-bold uppercase">Not Linked</div>
                </div>
              </div>
              <ArrowUpRight className="w-5 h-5 text-text-secondary group-hover:text-accent transition-colors" />
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-8">
        {/* Live GigWallet — wired to real Firestore data */}
        <div className="glass-card p-6">
          <div className="flex items-center gap-2 mb-6">
            <Wallet className="w-5 h-5 text-accent" />
            <h3 className="font-bold">GigWallet</h3>
          </div>
          <div className="mb-6">
            <div className="text-xs text-text-secondary font-bold uppercase mb-1">Total Balance</div>
            <div className="text-4xl font-mono font-bold">
              ₹{walletData?.availableBalance ?? 0}
            </div>
          </div>
          <button className="w-full py-4 bg-accent text-background rounded-xl font-bold flex items-center justify-center gap-2 hover:glow-accent transition-all">
            Withdraw <ArrowUpRight className="w-5 h-5" />
          </button>
        </div>

        {/* Recent Events — wired to real claims data */}
        <div className="glass-card p-6">
          <h3 className="font-bold mb-6">Recent Events</h3>
          {recentClaims.length === 0 ? (
            <p className="text-xs text-text-secondary text-center py-4">No recent events yet.</p>
          ) : (
            <div className="space-y-6">
              {recentClaims.slice(0, 3).map((claim, i) => (
                <div key={i} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={cn(
                      'w-8 h-8 rounded-lg flex items-center justify-center',
                      claim.status === 'APPROVED' ? 'bg-success/10 text-success' : 'bg-accent/10 text-accent'
                    )}>
                      <CloudRain className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-bold">{claim.type}</div>
                      <div className="text-[10px] text-text-secondary">
                        {new Date(claim.createdAt?.toDate?.() || claim.createdAt).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                  <div className={cn('text-sm font-mono font-bold', claim.status === 'APPROVED' ? 'text-success' : 'text-accent')}>
                    ₹{claim.amount}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  </div>
);

export default OverviewTab;
