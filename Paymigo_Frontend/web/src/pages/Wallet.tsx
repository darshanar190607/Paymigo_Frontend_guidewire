import React from 'react';
import { motion } from 'motion/react';
import { 
  Wallet as WalletIcon, 
  Bell, 
  ArrowUpRight, 
  ArrowDownLeft,
  ChevronRight,
  Zap,
  CreditCard,
  Smartphone,
  CheckCircle2
} from 'lucide-react';
import { cn } from '@/lib/utils';

const Wallet = () => {
  const transactions = [
    { id: 'TX-99281', type: 'payout', title: 'Rain Payout (Chennai-4)', date: 'Oct 15, 2026 • 14:22', amt: '+₹1,500', status: 'success' },
    { id: 'TX-99280', type: 'premium', title: 'Weekly Premium (Pro)', date: 'Oct 12, 2026 • 09:00', amt: '-₹112', status: 'neutral' },
    { id: 'TX-99279', type: 'payout', title: 'Rain Payout (Chennai-4)', date: 'Oct 08, 2026 • 18:45', amt: '+₹500', status: 'success' },
    { id: 'TX-99278', type: 'payout', title: 'Rain Payout (Chennai-4)', date: 'Oct 05, 2026 • 11:12', amt: '+₹1,500', status: 'success' },
    { id: 'TX-99277', type: 'premium', title: 'Weekly Premium (Pro)', date: 'Oct 05, 2026 • 09:00', amt: '-₹112', status: 'neutral' },
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <main className="max-w-7xl mx-auto p-6 md:p-10">
        {/* Top Bar */}
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-2xl font-display font-bold">GigWallet</h1>
            <p className="text-sm text-text-secondary">Manage your earnings and payouts</p>
          </div>
          <div className="flex items-center gap-4">
            <button className="relative p-2 bg-white/5 rounded-xl text-text-secondary hover:bg-white/10 transition-all">
              <Bell className="w-6 h-6" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full border-2 border-background" />
            </button>
            <div className="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center font-bold text-accent">
              RK
            </div>
          </div>
        </header>

        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {/* Balance Card */}
            <section>
              <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="glass-card p-8 bg-gradient-to-br from-surface to-accent/5 relative overflow-hidden"
              >
                <div className="absolute top-0 right-0 p-8 opacity-10">
                  <WalletIcon className="w-40 h-40" />
                </div>
                
                <div className="relative z-10">
                  <div className="text-xs text-text-secondary font-bold uppercase tracking-widest mb-2">Available Balance</div>
                  <div className="text-5xl font-mono font-bold mb-8">₹4,250</div>
                  
                  <div className="flex flex-wrap gap-4">
                    <button className="px-8 py-3 bg-accent text-background rounded-xl font-bold text-sm hover:scale-105 transition-transform flex items-center gap-2 shadow-lg shadow-accent/20">
                      Withdraw to UPI <ArrowUpRight className="w-4 h-4" />
                    </button>
                    <button className="px-8 py-3 bg-white/5 border border-white/10 rounded-xl font-bold text-sm hover:bg-white/10 transition-all">
                      Add Money
                    </button>
                  </div>
                </div>
              </motion.div>
            </section>

            {/* Transaction History */}
            <section className="glass-card p-8">
              <div className="flex justify-between items-center mb-8">
                <h3 className="text-xl font-bold">Transaction History</h3>
                <button className="text-xs font-bold uppercase tracking-widest text-accent hover:underline">Download CSV</button>
              </div>
              
              <div className="space-y-6">
                {transactions.map((tx, i) => (
                  <div key={i} className="flex items-center justify-between p-4 rounded-xl hover:bg-white/5 transition-all group">
                    <div className="flex items-center gap-4">
                      <div className={cn(
                        "w-12 h-12 rounded-xl flex items-center justify-center",
                        tx.status === 'success' ? "bg-success/10 text-success" : "bg-white/5 text-text-secondary"
                      )}>
                        {tx.type === 'payout' ? <ArrowDownLeft className="w-6 h-6" /> : <ArrowUpRight className="w-6 h-6" />}
                      </div>
                      <div>
                        <div className="text-sm font-bold group-hover:text-accent transition-colors">{tx.title}</div>
                        <div className="text-[10px] text-text-secondary uppercase font-bold tracking-widest">{tx.date} • {tx.id}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={cn("text-lg font-mono font-bold", tx.status === 'success' ? "text-success" : "text-text-primary")}>
                        {tx.amt}
                      </div>
                      <div className="text-[10px] text-text-secondary uppercase font-bold">Completed</div>
                    </div>
                  </div>
                ))}
              </div>
              
              <button className="w-full mt-8 py-4 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2">
                Load More Transactions <ChevronRight className="w-4 h-4" />
              </button>
            </section>
          </div>

          <div className="space-y-8">
            {/* Linked Accounts */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold mb-6">Linked UPI IDs</h3>
              <div className="space-y-4">
                {[
                  { id: 'ravi.kumar@okaxis', primary: true, icon: Smartphone },
                  { id: '9876543210@paytm', primary: false, icon: CreditCard },
                ].map((acc, i) => (
                  <div key={i} className={cn(
                    "p-4 rounded-xl border flex items-center justify-between",
                    acc.primary ? "bg-accent/5 border-accent/20" : "bg-white/5 border-white/5"
                  )}>
                    <div className="flex items-center gap-3">
                      <acc.icon className={cn("w-5 h-5", acc.primary ? "text-accent" : "text-text-secondary")} />
                      <div className="text-sm font-mono">{acc.id}</div>
                    </div>
                    {acc.primary && <CheckCircle2 className="w-4 h-4 text-accent" />}
                  </div>
                ))}
                <button className="w-full py-3 border border-dashed border-white/10 rounded-xl text-xs font-bold text-text-secondary hover:border-accent hover:text-accent transition-all">
                  + Add New UPI ID
                </button>
              </div>
            </div>

            {/* Payout Stats */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-bold mb-6">Payout Insights</h3>
              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-text-secondary mb-2">
                    <span>This Month</span>
                    <span className="text-success">₹3,500</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-success w-[65%]" />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs font-bold uppercase tracking-widest text-text-secondary mb-2">
                    <span>Total Lifetime</span>
                    <span className="text-accent">₹12,400</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <div className="h-full bg-accent w-[85%]" />
                  </div>
                </div>
              </div>
              
              <div className="mt-8 p-4 bg-accent/5 border border-accent/10 rounded-xl flex gap-3">
                <Zap className="text-accent w-5 h-5 shrink-0" />
                <p className="text-[10px] text-text-secondary leading-relaxed">
                  You are in the <span className="text-accent font-bold">Priority Payout Tier</span>. Your claims are processed instantly via our AI risk engine.
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Wallet;
