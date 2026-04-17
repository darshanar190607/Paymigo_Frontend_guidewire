import React from 'react';
import { motion } from 'motion/react';
import { 
  Shield, 
  TrendingUp, 
  AlertTriangle, 
  Zap, 
  ArrowUpRight, 
  ArrowDownLeft,
  Search,
  Bell,
  Filter,
  Download,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { cn } from '@/lib/utils';

const mockPortfolioData = [
  { month: 'Jan', premium: 450000, claims: 120000 },
  { month: 'Feb', premium: 520000, claims: 150000 },
  { month: 'Mar', premium: 480000, claims: 280000 },
  { month: 'Apr', premium: 610000, claims: 190000 },
  { month: 'May', premium: 550000, claims: 210000 },
  { month: 'Jun', premium: 670000, claims: 320000 },
];

const Insurer = () => {
  const stats = [
    { label: "Active Policies", val: "12,450", change: "+12%", icon: Shield, color: "text-accent" },
    { label: "Total Premium", val: "₹5.2M", change: "+18%", icon: TrendingUp, color: "text-success" },
    { label: "Loss Ratio", val: "32.4%", change: "-2.1%", icon: AlertTriangle, color: "text-warning" },
    { label: "Avg. Payout", val: "₹1,240", change: "+5%", icon: Zap, color: "text-accent" },
  ];

  const recentClaims = [
    { id: 'CLM-99281', worker: 'Ravi Kumar', zone: 'Chennai-4', trigger: 'Rain (18mm)', amt: '₹1,500', status: 'Auto-Paid', time: '2m ago' },
    { id: 'CLM-99280', worker: 'Suresh Raina', zone: 'Mumbai-2', trigger: 'Rain (22mm)', amt: '₹1,500', status: 'Auto-Paid', time: '15m ago' },
    { id: 'CLM-99279', worker: 'Amit Shah', zone: 'Delhi-1', trigger: 'AQI (450)', amt: '₹500', status: 'Review', time: '45m ago' },
    { id: 'CLM-99278', worker: 'Priya Singh', zone: 'Bangalore-5', trigger: 'Rain (12mm)', amt: '₹0', status: 'Rejected', time: '1h ago' },
  ];

  return (
    <div className="min-h-screen bg-background text-text-primary">
      <main className="max-w-7xl mx-auto p-6 md:p-10">
        {/* Top Bar */}
        <header className="flex justify-between items-center mb-10">
          <div className="relative w-96 hidden md:block">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-text-secondary" />
            <input 
              type="text" 
              placeholder="Search policies, claims, or workers..."
              className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-sm focus:border-accent outline-none transition-all"
            />
          </div>
          <div className="flex items-center gap-4">
            <button className="relative p-2 bg-white/5 rounded-xl text-text-secondary hover:bg-white/10 transition-all">
              <Bell className="w-6 h-6" />
              <span className="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full border-2 border-background" />
            </button>
            <div className="flex items-center gap-3 pl-4 border-l border-white/5">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-bold">Aditya Varma</div>
                <div className="text-[10px] text-text-secondary uppercase font-bold">Risk Manager</div>
              </div>
              <div className="w-10 h-10 rounded-xl bg-accent/20 flex items-center justify-center font-bold text-accent">
                AV
              </div>
            </div>
          </div>
        </header>

        <div className="space-y-8">
          {/* Stats Grid */}
          <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {stats.map((stat, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-card p-6"
              >
                <div className="flex justify-between items-start mb-4">
                  <div className={cn("p-3 rounded-xl bg-white/5", stat.color)}>
                    <stat.icon className="w-6 h-6" />
                  </div>
                  <div className={cn(
                    "text-xs font-bold flex items-center gap-1",
                    stat.change.startsWith('+') ? "text-success" : "text-danger"
                  )}>
                    {stat.change} {stat.change.startsWith('+') ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownLeft className="w-3 h-3" />}
                  </div>
                </div>
                <div className="text-xs text-text-secondary font-bold uppercase tracking-widest mb-1">{stat.label}</div>
                <div className="text-3xl font-mono font-bold">{stat.val}</div>
              </motion.div>
            ))}
          </section>

          {/* Main Charts */}
          <section className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 glass-card p-8">
              <div className="flex justify-between items-center mb-8">
                <div>
                  <h3 className="text-xl font-bold">Premium vs. Claims</h3>
                  <p className="text-xs text-text-secondary">Monthly performance overview</p>
                </div>
                <div className="flex gap-4">
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase">
                    <div className="w-2 h-2 rounded-full bg-accent" /> Premium
                  </div>
                  <div className="flex items-center gap-2 text-[10px] font-bold uppercase">
                    <div className="w-2 h-2 rounded-full bg-danger" /> Claims
                  </div>
                </div>
              </div>
              <div className="h-[350px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={mockPortfolioData}>
                    <defs>
                      <linearGradient id="colorPremium" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#00D4FF" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#00D4FF" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorClaims" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#EF4444" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="month" stroke="#9CA3AF" fontSize={10} tickLine={false} axisLine={false} />
                    <YAxis stroke="#9CA3AF" fontSize={10} tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{ backgroundColor: '#111827', border: '1px solid #ffffff10', borderRadius: '12px' }}
                    />
                    <Area type="monotone" dataKey="premium" stroke="#00D4FF" fillOpacity={1} fill="url(#colorPremium)" strokeWidth={3} />
                    <Area type="monotone" dataKey="claims" stroke="#EF4444" fillOpacity={1} fill="url(#colorClaims)" strokeWidth={3} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="glass-card p-8">
              <h3 className="text-xl font-bold mb-8">Zone Risk Heatmap</h3>
              <div className="space-y-6">
                {[
                  { zone: 'Chennai-4', risk: 'High', color: 'text-danger', val: 85 },
                  { zone: 'Mumbai-2', risk: 'High', color: 'text-danger', val: 78 },
                  { zone: 'Delhi-1', risk: 'Medium', color: 'text-warning', val: 45 },
                  { zone: 'Bangalore-5', risk: 'Low', color: 'text-success', val: 12 },
                  { zone: 'Hyderabad-3', risk: 'Low', color: 'text-success', val: 8 },
                ].map((zone, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between items-end">
                      <div className="text-sm font-bold">{zone.zone}</div>
                      <div className={cn("text-[10px] font-bold uppercase", zone.color)}>{zone.risk} Risk</div>
                    </div>
                    <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${zone.val}%` }}
                        className={cn(
                          "h-full",
                          zone.risk === 'High' ? "bg-danger" : zone.risk === 'Medium' ? "bg-warning" : "bg-success"
                        )}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-10 py-4 bg-white/5 hover:bg-white/10 rounded-xl text-xs font-bold transition-all">
                View Full Analytics
              </button>
            </div>
          </section>

          {/* Recent Claims Table */}
          <section className="glass-card overflow-hidden">
            <div className="p-8 flex justify-between items-center border-b border-white/5">
              <h3 className="text-xl font-bold">Recent Claims Queue</h3>
              <div className="flex gap-2">
                <button className="p-2 bg-white/5 rounded-lg text-text-secondary hover:bg-white/10 transition-all">
                  <Filter className="w-4 h-4" />
                </button>
                <button className="p-2 bg-white/5 rounded-lg text-text-secondary hover:bg-white/10 transition-all">
                  <Download className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-white/2">
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Claim ID</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Worker</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Zone</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Trigger</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Amount</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Status</th>
                    <th className="px-8 py-4 text-[10px] font-bold uppercase tracking-widest text-text-secondary">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {recentClaims.map((claim, i) => (
                    <tr key={i} className="hover:bg-white/2 transition-all group">
                      <td className="px-8 py-6 text-sm font-mono">{claim.id}</td>
                      <td className="px-8 py-6 text-sm font-bold">{claim.worker}</td>
                      <td className="px-8 py-6 text-sm text-text-secondary">{claim.zone}</td>
                      <td className="px-8 py-6 text-sm text-text-secondary">{claim.trigger}</td>
                      <td className="px-8 py-6 text-sm font-mono font-bold">{claim.amt}</td>
                      <td className="px-8 py-6">
                        <div className={cn(
                          "inline-flex items-center gap-2 px-3 py-1 rounded-full text-[10px] font-bold uppercase",
                          claim.status === 'Auto-Paid' ? "bg-success/10 text-success" : 
                          claim.status === 'Review' ? "bg-warning/10 text-warning" : "bg-danger/10 text-danger"
                        )}>
                          {claim.status === 'Auto-Paid' ? <CheckCircle2 className="w-3 h-3" /> : 
                           claim.status === 'Review' ? <AlertTriangle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                          {claim.status}
                        </div>
                      </td>
                      <td className="px-8 py-6">
                        <button className="text-xs font-bold text-accent hover:underline">Details</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Insurer;
