import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  LayoutDashboard, Wallet, Shield, History,
  Settings, Bell, CloudRain, Zap, CheckCircle2,
  FileText, Gift, User, Map as MapIcon, AlertTriangle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '../App';
import { db } from '../firebase';
import {
  doc, onSnapshot, collection,
  query, where, orderBy, updateDoc
} from 'firebase/firestore';

// Tab components
import OverviewTab from '../components/dashboard/OverviewTab';
import WalletTab from '../components/dashboard/WalletTab';
import PolicyTab from '../components/dashboard/PolicyTab';
import RewardsTab from '../components/dashboard/RewardsTab';
import ClaimsTab from '../components/dashboard/ClaimsTab';
import HistoryTab from '../components/dashboard/HistoryTab';
import SettingsTab from '../components/dashboard/SettingsTab';
import AvatarTab from '../components/dashboard/AvatarTab';
import LiveMapTab from '../components/dashboard/LiveMapTab';

// Types
import type { Worker, WalletData, Claim, AppNotification } from '../types/dashboard';

// ─── Static config arrays (outside component, zero re-creation) ──────────────

const NAV_ITEMS = [
  { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { id: 'avatar',    icon: User,            label: 'My Avatar'  },
  { id: 'live-map',  icon: MapIcon,         label: 'Live Map'   },
  { id: 'wallet',    icon: Wallet,          label: 'GigWallet'  },
  { id: 'policy',    icon: Shield,          label: 'My Policy'  },
  { id: 'rewards',   icon: Gift,            label: 'Rewards'    },
  { id: 'claims',    icon: FileText,        label: 'Claims'     },
  { id: 'history',   icon: History,         label: 'History'    },
  { id: 'settings',  icon: Settings,        label: 'Settings'   },
];

// ─── NavButton: single reusable nav component, eliminates duplicate map logic ─

interface NavItem { id: string; icon: React.ElementType; label: string; }

const NavButton = ({
  item, activeTab, onClick, mobile = false,
}: { item: NavItem; activeTab: string; onClick: (id: string) => void; mobile?: boolean }) => (
  <button
    key={item.id}
    onClick={() => onClick(item.id)}
    className={cn(
      'flex items-center gap-3 transition-all',
      mobile
        ? 'p-2 rounded-xl'
        : 'px-4 py-3 rounded-xl text-sm font-medium',
      activeTab === item.id
        ? (mobile ? 'text-accent bg-accent/10' : 'bg-accent text-background')
        : 'text-text-secondary hover:bg-white/5'
    )}
  >
    <item.icon className={mobile ? 'w-6 h-6' : 'w-5 h-5'} />
    {!mobile && <span>{item.label}</span>}
  </button>
);

// ─── Dashboard ────────────────────────────────────────────────────────────────

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab]         = useState('dashboard');
  const [isSimulating, setIsSimulating]   = useState(false);
  const [rainfall, setRainfall]           = useState(12.5);
  const [windSpeed, setWindSpeed]         = useState(25.0);
  const [waterLogging, setWaterLogging]   = useState(5.0);
  const [triggerStatus, setTriggerStatus] = useState('MONITORING');
  const [workerData, setWorkerData]       = useState<Worker | null>(null);
  const [walletData, setWalletData]       = useState<WalletData | null>(null);
  const [claims, setClaims]               = useState<Claim[]>([]);
  const [loading, setLoading]             = useState(true);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [weatherMode, setWeatherMode]     = useState('live');

  const intervalRef       = useRef<ReturnType<typeof setInterval> | null>(null);
  const triggerStatusRef  = useRef(triggerStatus);
  triggerStatusRef.current = triggerStatus;

  // ── FIX 1: sensorConfig derived inline — no repeated JSX blocks ────────────
  const sensorConfig = useMemo(() => [
    { label: 'Rainfall',      value: `${rainfall}mm`,     Icon: CloudRain,   active: rainfall     > 15 },
    { label: 'Wind Speed',    value: `${windSpeed}km/h`,  Icon: Zap,         active: windSpeed    > 45 },
    { label: 'Water Logging', value: `${waterLogging}cm`, Icon: AlertTriangle, active: waterLogging > 20 },
  ], [rainfall, windSpeed, waterLogging]);

  // ── FIX 3: Firestore subscriptions (4 listeners in one effect) ─────────────
  useEffect(() => {
    if (!user || !user.uid) return;

    const unsubWorker = onSnapshot(
      doc(db, 'workers', user.uid),
      (snap) => {
        if (snap.exists()) {
          setWorkerData({ id: snap.id, ...snap.data() } as Worker);
        } else {
          navigate('/onboard', { replace: true });
        }
        setLoading(false);
      },
      (err) => { console.error('Worker Snapshot:', err); setLoading(false); }
    );

    const unsubWallet = onSnapshot(
      doc(db, 'wallets', user.uid),
      (snap) => { if (snap.exists()) setWalletData(snap.data() as WalletData); },
      (err) => console.error('Wallet Snapshot:', err)
    );

    const unsubClaims = onSnapshot(
      query(collection(db, 'claims'), where('workerId', '==', user.uid)),
      (snap) => {
        const fetched = snap.docs
          .map(d => ({ id: d.id, ...d.data() } as Claim))
          .sort((a, b) => (b.createdAt?.toMillis?.() || 0) - (a.createdAt?.toMillis?.() || 0));
        setClaims(fetched);
      },
      (err) => console.error('Claims Snapshot:', err)
    );

    // ── FIX 4: Pre-format date strings at setState time, not in render ────────
    const unsubNotifications = onSnapshot(
      query(
        collection(db, 'notifications'),
        where('workerId', '==', user.uid),
        orderBy('createdAt', 'desc')
      ),
      (snap) => {
        setNotifications(
          snap.docs.map(d => {
            const data = d.data();
            return {
              id: d.id,
              ...data,
              formattedDate: new Date(data.createdAt?.toDate?.() || data.createdAt)
                .toLocaleDateString(),
            } as AppNotification;
          })
        );
      },
      (err) => console.error('Notifications Snapshot:', err)
    );

    return () => { unsubWorker(); unsubWallet(); unsubClaims(); unsubNotifications(); };
  }, [user]);

  // ── FIX: setInterval only depends on user — no competing intervals ─────────
  useEffect(() => {
    if (!user) return;

    const fetchTriggers = async () => {
      try {
        const { data } = await axios.get(`http://localhost:3000/api/triggers?mode=${weatherMode}`);
        setRainfall(data.rainfall);
        setWindSpeed(data.windSpeed);
        setWaterLogging(data.waterLogging);
        setTriggerStatus(data.status);

        if (data.status === 'PAYOUT_TRIGGERED' && triggerStatusRef.current !== 'PAYOUT_TRIGGERED') {
          try {
            await axios.post('http://localhost:3000/api/ai/trigger-payout', {
              workerId: user.uid,
              rainfall: data.rainfall,
              threshold: data.thresholds?.rainfall,
            });
          } catch (err: any) {
            if (err?.response?.status !== 400) console.error('Automated payout:', err);
          }
        }
      } catch (err) {
        console.error('Trigger fetch error:', err);
      }
    };

    fetchTriggers();
    intervalRef.current = setInterval(fetchTriggers, 10000);
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [user, weatherMode]);

  const markAsRead = async (id: string) => {
    try { await updateDoc(doc(db, 'notifications', id), { read: true }); }
    catch (err) { console.error('markAsRead:', err); }
  };

  const simulateRain = () => {
    setIsSimulating(true);
    let current = 12.5;
    const iv = setInterval(() => {
      current = parseFloat((current + 0.5).toFixed(1));
      setRainfall(current);
      if (current >= 18.5) { clearInterval(iv); setIsSimulating(false); }
    }, 200);
  };

  const renderTabContent = () => {
    if (!user) return null;
    switch (activeTab) {
      case 'dashboard': return (
        <div className="space-y-6">
          {/* Zero-Touch Banner */}
          <div className="p-4 bg-accent/10 border border-accent/20 rounded-xl flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Zap className="w-5 h-5 text-accent animate-pulse" />
              <div>
                <div className="text-xs font-black text-accent uppercase tracking-widest">Zero-Touch Claims Active</div>
                <div className="text-[10px] text-text-secondary">AI is monitoring your zone for automatic payouts.</div>
              </div>
            </div>
            <div className="text-[10px] font-bold text-success uppercase tracking-widest flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3" /> System Ready
            </div>
          </div>

          {/* ── FIX 1: Sensor grid via config array ── */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {sensorConfig.map(({ label, value, Icon, active }) => (
              <div key={label} className="glass-card p-4 flex items-center justify-between">
                <div>
                  <div className="text-[10px] text-text-secondary font-bold uppercase">{label}</div>
                  <div className="text-xl font-mono font-bold">{value}</div>
                </div>
                <Icon className={cn('w-5 h-5', active ? 'text-accent' : 'text-text-secondary')} />
              </div>
            ))}
          </div>

          <OverviewTab
            rainfall={rainfall}
            triggerStatus={triggerStatus}
            simulateRain={simulateRain}
            isSimulating={isSimulating}
            workerData={workerData}
            walletData={walletData}
            recentClaims={claims}
          />
        </div>
      );
      case 'avatar':   return <AvatarTab workerData={workerData} user={user} />;
      case 'live-map': return <LiveMapTab workerData={workerData} />;
      case 'wallet':   return <WalletTab walletData={walletData} />;
      case 'policy':   return <PolicyTab workerData={workerData} />;
      case 'rewards':  return <RewardsTab />;
      case 'claims':   return <ClaimsTab user={user} workerData={workerData} />;
      case 'history':  return <HistoryTab claims={claims} />;
      case 'settings': return <SettingsTab workerData={workerData} />;
      default:         return null;
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-12 h-12 border-4 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  );

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">

      {/* ── Sidebar — uses NavButton, no duplicate map logic ── */}
      <aside className="hidden md:flex w-64 border-r border-white/5 flex-col p-6 gap-8 shrink-0">
        <nav className="flex flex-col gap-2">
          {NAV_ITEMS.map(item => (
            <NavButton key={item.id} item={item} activeTab={activeTab} onClick={setActiveTab} />
          ))}
        </nav>
        <div className="mt-auto glass-card p-4">
          <div className="text-xs text-text-secondary mb-2 uppercase tracking-widest font-bold">Support</div>
          <p className="text-xs leading-relaxed mb-4">Need help with a claim? Our AI assistant is here.</p>
          <button className="w-full py-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-bold transition-all">
            Open Chat
          </button>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <main className="flex-grow p-6 md:p-10 overflow-y-auto pb-24 md:pb-10">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-2xl font-display font-bold">
              Namaste, {workerData?.name?.split(' ')[0] || user?.displayName?.split(' ')[0] || 'Worker'} 👋
            </h1>
            <p className="text-sm text-text-secondary">{workerData?.zone || 'Monitoring Zone'} • Week 1 Active</p>
          </div>
          <div className="flex items-center gap-4">
            {activeTab === 'dashboard' && (
              <button
                onClick={simulateRain}
                disabled={isSimulating}
                className={cn(
                  'px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2',
                  isSimulating ? 'bg-accent/20 text-accent cursor-not-allowed' : 'bg-accent text-background hover:scale-105'
                )}
              >
                <CloudRain className={cn('w-4 h-4', isSimulating && 'animate-bounce')} />
                {isSimulating ? 'Simulating...' : 'Simulate Rain'}
              </button>
            )}

            {/* Test Weather Env Dropdown */}
            {activeTab === 'dashboard' && (
              <select 
                value={weatherMode} 
                onChange={e => setWeatherMode(e.target.value)}
                className="bg-surface border border-white/10 rounded-xl px-3 py-2 text-xs font-bold text-text-primary focus:outline-none focus:border-accent"
              >
                <option value="live">Live Climate (OpenWeatherMap)</option>
                <option value="normal">Mock: Normal Day</option>
                <option value="flood">Mock: Flood Disaster</option>
                <option value="extreme_wind">Mock: Extreme Wind</option>
              </select>
            )}

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(p => !p)}
                className="p-2 bg-white/5 rounded-full relative hover:bg-white/10 transition-colors"
              >
                <Bell className="w-5 h-5 text-text-secondary" />
                {unreadCount > 0 && (
                  <span className="absolute top-0 right-0 w-2 h-2 bg-accent rounded-full border-2 border-background" />
                )}
              </button>

              <AnimatePresence>
                {showNotifications && (
                  <>
                    <div className="fixed inset-0 z-40" onClick={() => setShowNotifications(false)} />
                    <motion.div
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, y: 10, scale: 0.95 }}
                      className="absolute right-0 mt-4 w-80 glass-card p-4 z-50 shadow-2xl border-accent/20"
                    >
                      <div className="flex justify-between items-center mb-4">
                        <h3 className="font-bold text-sm">Notifications</h3>
                        <span className="text-[10px] font-black text-accent uppercase tracking-widest">{unreadCount} New</span>
                      </div>
                      <div className="space-y-2 max-h-[400px] overflow-y-auto pr-2">
                        {notifications.length === 0 ? (
                          <p className="text-xs text-text-secondary text-center py-8">No notifications yet.</p>
                        ) : notifications.map((n) => (
                          <div
                            key={n.id}
                            onClick={() => markAsRead(n.id)}
                            className={cn(
                              'p-3 rounded-xl border transition-all cursor-pointer',
                              n.read ? 'bg-white/5 border-white/5 opacity-60' : 'bg-accent/5 border-accent/20'
                            )}
                          >
                            <div className="flex justify-between items-start mb-1">
                              <p className="font-bold text-xs text-text-primary">{n.title}</p>
                              {/* ── FIX 4: formattedDate pre-computed at setState time ── */}
                              <span className="text-[8px] text-text-secondary">{n.formattedDate}</span>
                            </div>
                            <p className="text-[10px] text-text-secondary leading-relaxed">{n.message}</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  </>
                )}
              </AnimatePresence>
            </div>

            {user?.photoURL ? (
              <img src={user.photoURL} alt="Profile" className="w-10 h-10 rounded-full border border-white/20" referrerPolicy="no-referrer" />
            ) : (
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent to-indigo-600 border border-white/20" />
            )}
          </div>
        </header>

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -10 }}
            transition={{ duration: 0.2 }}
          >
            {renderTabContent()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* ── Mobile Tab Bar — reuses NavButton, no duplicate logic ── */}
      <nav className="md:hidden fixed bottom-0 w-full bg-background/80 backdrop-blur-md border-t border-white/5 flex justify-around p-4 z-50">
        {NAV_ITEMS.map(item => (
          <NavButton key={item.id} item={item} activeTab={activeTab} onClick={setActiveTab} mobile />
        ))}
      </nav>
    </div>
  );
};

export default Dashboard;
