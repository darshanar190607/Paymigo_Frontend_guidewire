import React from 'react';
import { cn } from '@/lib/utils';
import { ArrowUpRight, TrendingUp, Gift } from 'lucide-react';
import type { WalletData } from '../../types/dashboard';

interface WalletTabProps {
  walletData: WalletData | null;
}

const WalletTab = ({ walletData }: WalletTabProps) => (
  <div className="space-y-8">
    <div className="glass-card p-8 grid md:grid-cols-2 gap-8 items-center">
      <div>
        <div className="text-xs text-text-secondary font-bold uppercase tracking-widest mb-2">Total Balance</div>
        <div className="text-6xl font-mono font-bold mb-6">₹{walletData?.availableBalance ?? 0}</div>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-accent" />
            <div className="flex-grow text-sm text-text-secondary">Available Payout</div>
            <div className="font-bold">₹{walletData?.availableBalance ?? 0}</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-success" />
            <div className="flex-grow text-sm text-text-secondary">Loyalty Pool (Locked)</div>
            <div className="font-bold">₹{walletData?.loyaltyPoolBalance ?? 0}</div>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="flex-grow text-sm text-text-secondary">Fuel Cashback Returns</div>
            <div className="font-bold text-yellow-500">₹{walletData?.fuelCashbackEarned ?? 0}</div>
          </div>
        </div>
      </div>
      <div className="p-8 bg-white/5 rounded-3xl border border-white/5 text-center">
        <div className="text-sm text-text-secondary mb-4">Next Payout Estimate</div>
        <div className="text-4xl font-mono font-bold text-accent mb-2">₹1,500</div>
        <div className="text-[10px] text-text-secondary uppercase tracking-widest">Based on current rainfall</div>
      </div>
    </div>

    <div className="grid md:grid-cols-2 gap-8">
      <div className="glass-card p-8">
        <h3 className="text-xl font-bold mb-6">Withdraw Funds</h3>
        <div className="space-y-6">
          <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] text-text-secondary font-bold uppercase mb-2">Withdraw to UPI</div>
            <div className="text-xl font-mono font-bold">ravi.delivery@okaxis</div>
          </div>
          <div className="flex gap-4">
            <button className="flex-grow py-4 bg-accent text-background rounded-xl font-bold">
              Withdraw ₹{walletData?.availableBalance ?? 0}
            </button>
            <button className="px-6 py-4 bg-white/5 rounded-xl font-bold border border-white/10">Custom</button>
          </div>
        </div>
      </div>
      <div className="glass-card p-8">
        <h3 className="text-xl font-bold mb-6">Loyalty Milestones</h3>
        <div className="space-y-4">
          {[
            { week: 'Week 4', bonus: '₹50', status: 'Claimed' },
            { week: 'Week 9', bonus: '₹150', status: 'Claimed' },
            { week: 'Week 17', bonus: '₹250', status: 'Upcoming' },
          ].map((m, i) => (
            <div key={i} className="flex justify-between items-center p-4 bg-white/5 rounded-xl">
              <span className="font-bold">{m.week}</span>
              <div className="flex items-center gap-4">
                <span className="text-accent font-mono font-bold">{m.bonus}</span>
                <span className={cn('text-[10px] font-bold uppercase', m.status === 'Claimed' ? 'text-success' : 'text-text-secondary')}>
                  {m.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  </div>
);

export default WalletTab;
