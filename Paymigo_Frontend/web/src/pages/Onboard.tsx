import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Shield, 
  User, 
  MapPin, 
  CreditCard, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft,
  Smartphone,
  Zap,
  CloudRain,
  AlertTriangle,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '../App';

// ─── Types ───────────────────────────────────────────────────────────────────

interface WorkerFormData {
  name: string;
  phone: string;
  age: string;
  jobType: string;
  experienceYears: string;
  zone: string;
  plan: string;
  premium: number;
}

const Onboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [isMonsoon, setIsMonsoon] = useState(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('isMonsoon') !== null) {
      return localStorage.getItem('isMonsoon') === 'true';
    }
    const month = new Date().getMonth(); // 0-indexed (5 = June, 8 = September)
    return month >= 5 && month <= 8;
  });

  useEffect(() => {
    if (typeof window !== 'undefined') localStorage.setItem('isMonsoon', String(isMonsoon));
  }, [isMonsoon]);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiFactors, setAiFactors] = useState<string[]>([]);
  
  useEffect(() => {
    if (user) {
      if (user.pincode !== '000000' && !String(user.phone).startsWith('PENDING_')) {
        navigate('/dashboard', { replace: true });
      }
    }
  }, [user, navigate]);

  const [formData, setFormData] = useState<WorkerFormData>({
    name: '',
    phone: '',
    age: '',
    jobType: 'Delivery',
    experienceYears: '',
    zone: 'Coimbatore (Zone 1)',
    plan: 'Pro',
    premium: 49
  });

  const [isDetectingLocation, setIsDetectingLocation] = useState(false);
  const [hasAutoDetected, setHasAutoDetected] = useState(false);

  // Wrapped in useCallback so the step-2 effect can safely list it as a dep
  const detectLocation = useCallback(() => {
    setIsDetectingLocation(true);
    setHasAutoDetected(true);
    if (!('geolocation' in navigator)) {
      setTimeout(() => setIsDetectingLocation(false), 1000);
      return;
    }
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const { latitude, longitude } = position.coords;
          const res  = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}`);
          const data = await res.json();
          const city = `${data.address?.city ?? ''} ${data.address?.state_district ?? ''} ${data.address?.county ?? ''} ${data.address?.state ?? ''}`.toLowerCase();

          let zone = 'Coimbatore (Zone 1)';
          if (city.includes('chennai'))                              zone = 'Chennai (Zone 4)';
          else if (city.includes('bangalore') || city.includes('bengaluru')) zone = 'Bangalore East';
          else if (city.includes('mumbai'))                          zone = 'Mumbai West';

          setFormData(prev => ({ ...prev, zone }));
        } catch (err) {
          console.error('Geocoding failed:', err);
        } finally {
          setIsDetectingLocation(false);
        }
      },
      (err) => {
        console.error('Geolocation error:', err);
        setTimeout(() => setIsDetectingLocation(false), 1000);
      },
      { timeout: 10000 }
    );
  }, []);

  // Auto-detect location when user reaches step 3
  useEffect(() => {
    if (step === 3 && !hasAutoDetected) detectLocation();
  }, [step, hasAutoDetected, detectLocation]);

  useEffect(() => {
    // Zone-based warning logic
    let newFactors: string[] = [];
    if (formData.zone.includes('Coimbatore')) {
       newFactors = ['Low historical rainfall disruption', 'Disruption-less zone detected', '-₹100 risk discount applied'];
    } else if (formData.zone.includes('Chennai')) {
       newFactors = ['High historical urban flooding', 'Coastal cyclone risk factored', '+₹30 high-risk premium applied'];
    }

    // Call ML backend to get dynamic XGBoost premium and cluster info
    const fetchMLPremium = async () => {
      try {
        const token = localStorage.getItem('token');
        if (!token) return;
        
        const res = await fetch('http://localhost:3000/premium/calculate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            age: formData.age || 30,
            jobType: formData.jobType || "Delivery",
            experienceYears: formData.experienceYears || 0,
            zone: formData.zone
          })
        });
        
        if (res.ok) {
          const data = await res.json();
          setFormData(prev => ({ ...prev, premium: data.basePremium }));
          if (data.aiFactors && data.aiFactors.length > 0) {
            setAiFactors(data.aiFactors);
          } else {
            setAiFactors(newFactors);
          }
        }
      } catch (e) {
        console.error("Failed to fetch ML premium", e);
        setAiFactors(newFactors);
      }
    };

    fetchMLPremium();

    // Pre-fill name from auth profile (only on first load)
    if (user && !formData.name) {
      setFormData(prev => ({ ...prev, name: user.displayName || '' }));
    }
  }, [formData.zone, formData.age, formData.jobType, formData.experienceYears, user]);

  const zoneWarnings: Record<string, string> = {
    'Coimbatore (Zone 1)': 'Low disruption area. Special discounted pricing applied for Coimbatore partners.',
    'Chennai (Zone 4)': 'High rainfall risk in October. We recommend the Pro plan for maximum coverage.',
    'Bangalore East': 'Heavy wind risk during monsoon. Premium plan covers wind-related disruptions.',
    'Mumbai West': 'Extreme monsoon flooding risk. Pro or Premium plans are highly recommended.'
  };

  // Memoized so JSX renders don't recompute pricing on every keystroke
  const plans = useMemo(() => {
    const surge = isMonsoon ? 30 : 0;
    const basePrice = formData.premium || 69;
    let prices = { basic: basePrice, pro: basePrice + 20, premium: basePrice + 50 };

    return [
      { id: 'Basic',   price: prices.basic   + surge, label: 'Basic',   recommended: false, description: 'Essential protection for light rain.' },
      { id: 'Pro',     price: prices.pro     + surge, label: 'Pro',     recommended: true,  description: 'Best for full-time gig workers. Includes Stay-at-Home benefit & Fuel Cashback.' },
      { id: 'Premium', price: prices.premium + surge, label: 'Premium', recommended: false, description: 'Maximum coverage & Highest Fuel Cashback rate.' },
    ];
  }, [formData.premium, isMonsoon]);

  const getPlanPrice = (planId: string): number => {
    return plans.find(p => p.id === planId)?.price ?? 69;
  };

  const nextStep = async () => {
    setError(null);
    if (step === 1) {
      if (!formData.name.trim() || !formData.phone.trim()) {
        setError("Please provide your name and phone number.");
        return;
      }
    }
    if (step === 2) {
      if (!formData.age || !formData.experienceYears) {
        setError("Please provide your age and years of experience.");
        return;
      }
    }
    if (step === 5) {
      await saveUserData();
    } else {
      setStep(s => Math.min(s + 1, 6));
    }
  };

  const saveUserData = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) throw new Error('Authentication token not found. Please log in again.');

      let pincode = '000001';
      if (formData.zone.includes('Coimbatore')) pincode = '641001';
      else if (formData.zone.includes('Chennai')) pincode = '600001';
      else if (formData.zone.includes('Bangalore')) pincode = '560001';
      else if (formData.zone.includes('Mumbai')) pincode = '400001';

      const res = await fetch('http://localhost:3000/workers/onboard', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          phone: formData.phone,
          name: formData.name,
          age: parseInt(formData.age),
          jobType: formData.jobType,
          experienceYears: parseInt(formData.experienceYears),
          pincode,
          zone: formData.zone,
          plan: formData.plan,
          premium: getPlanPrice(formData.plan)
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to complete onboarding');

      localStorage.setItem('paymigo_user', JSON.stringify(data));
      setStep(6);
    } catch (error: any) {
      console.error("Onboarding error:", error);
      setError(error?.message || "Something went wrong. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const prevStep = () => setStep(s => Math.max(s - 1, 1));



  const renderStep = () => {
    switch(step) {
      case 1:
        return (
          <motion.div 
            key="step-1"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <h2 className="text-3xl font-display font-bold">Who are you?</h2>
              <p className="text-text-secondary">We need your basic details to start your protection.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-widest text-text-secondary">Full Name</label>
                <input 
                  type="text" 
                  placeholder="e.g. Ravi Kumar"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-4 focus:border-accent outline-none transition-colors"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-widest text-text-secondary">Phone Number (UPI Linked)</label>
                <div className="relative">
                  <Smartphone className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                  <input 
                    type="tel" 
                    placeholder="98765 43210"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-4 focus:border-accent outline-none transition-colors"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        );
      case 2:
        return (
          <motion.div 
            key="step-2"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <h2 className="text-3xl font-display font-bold">More about you</h2>
              <p className="text-text-secondary">This helps evaluate your personalized risk tier and premium discounts.</p>
            </div>
            <div className="space-y-4">
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-widest text-text-secondary">Age</label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-secondary" />
                  <input 
                    type="number" 
                    min="18"
                    max="100"
                    placeholder="e.g. 28"
                    className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-4 focus:border-accent outline-none transition-colors"
                    value={formData.age}
                    onChange={(e) => setFormData({...formData, age: e.target.value})}
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-widest text-text-secondary">Job Type</label>
                <div className="grid grid-cols-2 gap-3 mt-1">
                  {['Delivery', 'Rideshare', 'Courier', 'Other'].map(job => (
                    <button
                      key={job}
                      onClick={() => setFormData({...formData, jobType: job})}
                      className={cn(
                        "p-3 rounded-xl border text-sm font-bold transition-all",
                        formData.jobType === job ? "bg-accent/10 border-accent text-accent" : "bg-white/5 border-white/10 text-text-secondary hover:bg-white/10"
                      )}
                    >
                      {job}
                    </button>
                  ))}
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold uppercase tracking-widest text-text-secondary">Years of Experience</label>
                <input 
                  type="number" 
                  min="0"
                  max="50"
                  placeholder="e.g. 3"
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-4 focus:border-accent outline-none transition-colors"
                  value={formData.experienceYears}
                  onChange={(e) => setFormData({...formData, experienceYears: e.target.value})}
                />
              </div>
            </div>
          </motion.div>
        );
      case 3:
        return (
          <motion.div 
            key="step-3"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <h2 className="text-3xl font-display font-bold">Where do you work?</h2>
              <p className="text-text-secondary">Rainfall risk varies by zone. We use this to trigger your payouts.</p>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <button 
                onClick={detectLocation}
                disabled={isDetectingLocation}
                className="flex items-center justify-center gap-2 w-full p-4 rounded-xl border border-dashed border-accent text-accent bg-accent/5 hover:bg-accent/10 transition-colors mb-2"
              >
                {isDetectingLocation ? <Loader2 className="w-5 h-5 animate-spin" /> : <MapPin className="w-5 h-5" />}
                <span className="font-bold">{isDetectingLocation ? "Detecting Satellite Location..." : "Auto-Detect My Connected Zone"}</span>
              </button>
              {['Coimbatore (Zone 1)', 'Chennai (Zone 4)', 'Bangalore East', 'Mumbai West'].map((z) => (
                <button
                  key={z}
                  onClick={() => setFormData({...formData, zone: z})}
                  className={cn(
                    "flex items-center justify-between p-4 rounded-xl border transition-all",
                    formData.zone === z ? "bg-accent/10 border-accent text-accent" : "bg-white/5 border-white/10 text-text-secondary hover:bg-white/10"
                  )}
                >
                  <div className="flex items-center gap-3">
                    <MapPin className="w-5 h-5" />
                    <span className="font-bold">{z}</span>
                  </div>
                  {formData.zone === z && <CheckCircle2 className="w-5 h-5" />}
                </button>
              ))}
            </div>
            <div className="p-4 bg-warning/10 border border-warning/20 rounded-xl flex gap-3">
              <AlertTriangle className="text-warning w-5 h-5 shrink-0" />
              <p className="text-xs text-warning/80">{zoneWarnings[formData.zone] || 'Monitoring active in this zone.'}</p>
            </div>
            {aiFactors.length > 0 && (
              <div className="p-4 bg-accent/5 border border-accent/10 rounded-xl space-y-2">
                <div className="flex items-center gap-2 text-[10px] font-black text-accent uppercase tracking-widest">
                  <Zap className="w-3 h-3" /> AI Risk Analysis
                </div>
                <ul className="space-y-1">
                  {aiFactors.map((f, i) => (
                    <li key={i} className="text-[10px] text-text-secondary flex items-center gap-2">
                      <div className="w-1 h-1 bg-accent rounded-full" /> {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </motion.div>
        );
      case 4:
        return (
          <motion.div 
            key="step-4"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <h2 className="text-3xl font-display font-bold">Choose your shield</h2>
                <button 
                  onClick={() => setIsMonsoon(!isMonsoon)}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase transition-all border",
                    isMonsoon ? "bg-accent/20 border-accent text-accent" : "bg-white/5 border-white/10 text-text-secondary"
                  )}
                >
                  <CloudRain className={cn("w-3 h-3", isMonsoon && "animate-pulse")} />
                  Monsoon Mode {isMonsoon ? "ON" : "OFF"}
                </button>
              </div>
              <p className="text-text-secondary">Select a plan that fits your weekly earnings goal.</p>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {plans.map((p) => (
                <button
                  key={p.id}
                  onClick={() => setFormData({...formData, plan: p.id})}
                  className={cn(
                    "relative flex flex-col p-6 rounded-2xl border transition-all text-left",
                    formData.plan === p.id ? "bg-accent/10 border-accent" : "bg-white/5 border-white/10 hover:bg-white/10"
                  )}
                >
                  {p.recommended && (
                    <div className="absolute top-0 right-6 -translate-y-1/2 bg-accent text-background text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">
                      Recommended
                    </div>
                  )}
                  <div className="flex justify-between items-end mb-2">
                    <div>
                      <div className="text-xs font-bold uppercase tracking-widest text-text-secondary mb-1">{p.label}</div>
                      <div className="text-2xl font-display font-bold">{p.id}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-mono font-bold">₹{p.price}</div>
                      <div className="text-[10px] text-text-secondary uppercase">per week</div>
                    </div>
                  </div>
                  <p className="text-[10px] text-text-secondary mb-4 leading-relaxed">{p.description}</p>
                  <div className="flex flex-wrap gap-3 text-[10px] font-bold uppercase tracking-widest text-text-secondary mt-2">
                    <div className="flex items-center gap-1"><Zap className="w-3 h-3 text-accent" /> 90s Payout</div>
                    <div className="flex items-center gap-1"><CloudRain className="w-3 h-3 text-accent" /> 15mm Trigger</div>
                    {(p.id === 'Pro' || p.id === 'Premium') && (
                      <div className="flex items-center gap-1 text-accent"><CreditCard className="w-3 h-3 text-accent" /> Fuel Cashback</div>
                    )}
                    {isMonsoon && (
                      <div className="flex items-center gap-1 text-success"><CheckCircle2 className="w-3 h-3" /> Stay-at-Home Benefit</div>
                    )}
                  </div>
                </button>
              ))}
            </div>
            {isMonsoon && (
              <div className="p-4 bg-accent/5 border border-accent/10 rounded-xl">
                <p className="text-[10px] text-accent/80 leading-relaxed italic">
                  * During monsoon (June-Sept), premiums are adjusted (Basic +₹30, Pro +₹30, Premium +₹40). This activates the <b>Stay-at-Home</b> benefit, allowing you to claim insurance even if you are restricted to stay home due to severe rain or wind.
                </p>
              </div>
            )}
          </motion.div>
        );
      case 5:
        return (
          <motion.div 
            key="step-5"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            className="space-y-6"
          >
            <div className="space-y-2">
              <h2 className="text-3xl font-display font-bold">Final Step</h2>
              <p className="text-text-secondary">Complete your first weekly premium to activate protection.</p>
            </div>
            <div className="glass-card p-8 space-y-6">
              <div className="flex justify-between items-center pb-6 border-b border-white/5">
                <div>
                  <div className="text-sm font-bold">{formData.plan} Weekly Premium</div>
                  <div className="text-xs text-text-secondary">{formData.zone}</div>
                </div>
                <div className="text-xl font-mono font-bold">₹{getPlanPrice(formData.plan)}</div>
              </div>
              <div className="space-y-4">
                <div className="text-xs font-bold uppercase tracking-widest text-text-secondary">Test Payment Method</div>
                <button 
                  onClick={nextStep}
                  disabled={isSaving}
                  className="w-full py-6 bg-white/5 border border-white/10 rounded-2xl font-bold text-lg hover:bg-white/10 transition-all flex items-center justify-center gap-3 group"
                >
                  <CreditCard className="w-6 h-6 text-accent group-hover:scale-110 transition-transform" />
                  Simulate Test Payment
                </button>
                <p className="text-[10px] text-text-secondary text-center italic">
                  This is a sandbox environment. No real money will be charged.
                </p>
              </div>
              <div className="flex items-center gap-3 p-4 bg-success/10 border border-success/20 rounded-xl">
                <Shield className="text-success w-5 h-5 shrink-0" />
                <p className="text-[10px] text-success/80">Secure test environment active. {isMonsoon ? "Monsoon Stay-at-Home benefit active." : "Protection starts instantly after simulation."}</p>
              </div>
            </div>
          </motion.div>
        );
      case 6:
        return (
          <motion.div 
            key="step-6"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center space-y-8 py-10"
          >
            <div className="w-24 h-24 bg-success/20 rounded-full flex items-center justify-center mx-auto mb-8">
              <CheckCircle2 className="text-success w-12 h-12" />
            </div>
            <div className="space-y-2">
              <h2 className="text-4xl font-display font-bold">You're Protected!</h2>
              <p className="text-text-secondary">Welcome to the Paymigo family, {formData.name.split(' ')[0]}.</p>
            </div>
            <div className="glass-card p-6 max-w-sm mx-auto">
              <div className="text-xs text-text-secondary uppercase tracking-widest font-bold mb-4">Policy Details</div>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between"><span>Policy ID:</span> <span className="font-mono font-bold">PK-9928-X</span></div>
                <div className="flex justify-between"><span>Zone:</span> <span className="font-bold">{formData.zone}</span></div>
                <div className="flex justify-between"><span>Status:</span> <span className="text-success font-bold">Active</span></div>
              </div>
            </div>
            <button 
              onClick={() => navigate('/dashboard')}
              className="inline-flex items-center gap-2 px-10 py-4 bg-accent text-background rounded-xl font-bold hover:scale-105 transition-transform shadow-lg shadow-accent/20"
            >
              Go to Dashboard <ArrowRight className="w-5 h-5" />
            </button>
          </motion.div>
        );
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col pt-20">
      {/* Progress Bar */}
      <div className="w-full h-1 bg-white/5">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${(step / 6) * 100}%` }}
          className="h-full bg-accent"
        />
      </div>

      <main className="flex-grow flex items-center justify-center p-6">
        <div className="w-full max-w-xl">
          <AnimatePresence mode="wait">
            {error && (
              <motion.div 
                key="error-banner"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-danger/10 border border-danger/20 rounded-xl text-danger text-xs font-bold flex items-center gap-2"
              >
                <AlertTriangle className="w-4 h-4" />
                {error}
              </motion.div>
            )}
            {renderStep()}
          </AnimatePresence>

          {step < 6 && (
            <div className="mt-12 flex justify-between items-center">
              <button 
                onClick={prevStep}
                disabled={step === 1}
                className={cn(
                  "flex items-center gap-2 text-sm font-bold uppercase tracking-widest transition-all",
                  step === 1 ? "opacity-0 pointer-events-none" : "text-text-secondary hover:text-text-primary"
                )}
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button 
                onClick={nextStep}
                disabled={isSaving}
                className="flex items-center gap-2 px-8 py-4 bg-accent text-background rounded-xl font-bold hover:scale-105 transition-transform shadow-lg shadow-accent/20 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <div className="w-5 h-5 border-2 border-background border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    {step === 5 ? "Pay ₹" + getPlanPrice(formData.plan) : "Continue"} <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default Onboard;
